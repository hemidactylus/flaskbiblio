# dbtools.py : library to interface with the database

from functools import reduce
from operator import mul
from orm import Database
import os
from werkzeug.datastructures import ImmutableMultiDict
from pytz import timezone
from datetime import datetime
import time

from config import (
    DB_DIRECTORY,
    DB_NAME,
    DATETIME_STR_FORMAT,
    ALLOW_DUPLICATE_BOOKS,
    USERS_TIMEZONE,
    SIMILAR_AUTHOR_THRESHOLD,
    SIMILAR_BOOK_THRESHOLD,
    MINIMUM_SIMILAR_BOOK_TOKEN_SIZE,
)
from app.utils.stringlists import   (
                                        rollStringList,
                                        unrollStringList,
                                        addToStringList,
                                        expungeFromStringList,
                                    )
from app.utils.string_vectorizer import (
                                            makeIntoVector,
                                            scalProd,
                                        )
from app.database.models import (
                                    tableToModel, 
                                    User,
                                    Author,
                                    Language,
                                    Booktype,
                                    Book,
                                    Statistic,
                                    House,
                                )
from app.statistics.statistics import statFromBook, statFromAuthor

def dbIncrementStatistic(db,statDeltasMinus,statDeltasPlus):
    '''
        Increments/decrements a list of statistics stored
        in the DB.
        It assumes it is called within a transaction
        hence it does not invoke any commit()

        statDeltas' are maps of: (name,subtype) -> delta
        and are going to be algebraically summed
    '''
    # prepare a map of the plus-minus pruning zeroes
    statDeltas={
        h:w for h,w in
        {
            k: statDeltasPlus.get(k,0)-statDeltasMinus.get(k,0)
            for k in set(statDeltasMinus.keys()) | set(statDeltasPlus.keys())
        }.items()
        if w!=0
    }
    #
    Statistic.db=db
    keysDone=set()
    # all items already present -> updates
    for stat in Statistic.manager(db).all():
        thisKey=(stat.name,stat.subtype)
        if thisKey in statDeltas:
            stat.value+=statDeltas[thisKey]
            keysDone.add(thisKey)
            stat.update()
    # new items -> create
    for newKey in set(statDeltas.keys())-keysDone:
        nStat=Statistic(name=newKey[0],subtype=newKey[1],value=statDeltas[newKey])
        nStat.save()

def dbGetDatabase():
    '''
        Opens a DB connection and returns a cursor on it
    '''
    dbFile=os.path.join(DB_DIRECTORY,DB_NAME)    
    return Database(dbFile)

def dbTableFilterQuery( tableName, startfrom=0,
                        nresults=100, filterList=[],
                        sorter=None):
    '''
        Given a table name, list-slicing arguments
        and a list of filter functions Object->bool,
        the resulting query result is returned as (result,list) pair:
            Sorting is applied before slicing.
            Result is a dict that may contain keys:
                [error          = an error message. Ignore all other keys!]
                 ntotal         = number of total matches before slicing
                 firstitem      = index of first item here
                 lastitem       = index of last item here
                [nextstartfrom  = startfrom for the next batch]
                [prevstartfrom  = startfrom for the prev batch]
    '''
    # whole filters combined
    wholeFilters = lambda obj: reduce(mul,(ffunc(obj) for ffunc in filterList),1.0)
    # perform query and filters
    qlist=list(filter(
        lambda obj: wholeFilters(obj)>0,
        (dbGetAll(tableName))
    ))
    # sort results (either with default or explicit sorting key)
    if sorter is None:
        reslist=sorted(qlist)
    else:
        reslist=list(sorted(qlist,key= lambda bk: sorter(bk,wholeFilters)))
    # determine numbers
    result={'ntotal': len(reslist)}
    result['firstitem']=startfrom
    result['lastitem']=min(len(reslist),startfrom+nresults)-1
    if startfrom>0:
        result['prevstartfrom']=max(0,startfrom-nresults)
    if len(reslist)>startfrom+nresults:
        result['nextstartfrom']=startfrom+nresults
    # trim section of interest from list
    trimmedlist=reslist[startfrom:startfrom+nresults]
    if len(trimmedlist)==0:
        result['firstitem']=-1
    return (result,trimmedlist)

def makeBookFilter(fName,fValue,useSimilarity=False):
    '''
        Interprets an argument name/vale in the query string
        and produces a corresponding boolean filter
    '''
    if fName=='author':
        def aufinder(bo,v=fValue):
            return 1.0 if int(v) in unrollStringList(bo.authors) else 0.0
        return aufinder
    elif fName=='title':
        if useSimilarity:
            # prepare and store vector
            vVector=makeIntoVector(fValue.lower())
            if sum(vVector.values()):
                def tifinder(bo,vec=vVector):
                    matchSum=0.0
                    boTitleVector=makeIntoVector(bo.title.lower())
                    boTitleTokens=[t.lower() for t in bo.title.lower().split(' ')]
                    if scalProd(vec,boTitleVector)>=SIMILAR_BOOK_THRESHOLD:
                        matchSum += (1.0+scalProd(vec,boTitleVector))*(1+len(boTitleTokens))
                    for tok in boTitleTokens:
                        if scalProd(vec,makeIntoVector(tok))>=SIMILAR_BOOK_THRESHOLD and \
                        len(tok)>=MINIMUM_SIMILAR_BOOK_TOKEN_SIZE:
                            matchSum+=(1.0+scalProd(vec,makeIntoVector(tok)))
                    #
                    return matchSum
                return tifinder
            else:
                return makeBookFilter(fName,fValue,useSimilarity=False)
        else:
            def tifinder(bo,v=fValue):
                matchSum=0.0
                botoks = bo.title.lower().split(' ')
                if len(botoks):
                    for vpart in v.lower().split(' '):
                        #
                        maxMatch = max(
                            (len(vpart)+ ((1.0+len(vpart))/len(btok)) ) if vpart in btok else 0
                            for btok in botoks
                        )
                        matchSum+=maxMatch
                return matchSum
            return tifinder
    elif fName=='booktype':
        def btfinder(bo,v=fValue):
            return 1.0 if bo.booktype.upper()==v.upper() else 0.0
        return btfinder
    elif fName=='language':
        def lafinder(bo,v=fValue):
            return 1.0 if v.upper() in bo.languages.split(',') else 0.0
        return lafinder
    elif fName=='inhouse':
        def ihfinder(bo,v=fValue):
            return 1.0 if bool(bo.inhouse)==bool(int(v)) else 0.0
        return ihfinder
    elif fName=='house':
        if fValue!='-2':
            def hofinder(bo,v=fValue):
                return 1.0 if bo.house==v else 0.0
        else:
            # special all-house filter
            def hofinder(bo,v=fValue):
                return 1.0
        return hofinder
    else:
        return lambda: 1.0

def makeAuthorFilter(fName, fValue, useSimilarity=False):
    '''
        Same as above but for the 'author' objects
    '''
    if fName=='firstname':
        if useSimilarity:
            # prepare and store vector
            vVector=makeIntoVector(fValue)
            if sum(vVector.values()):
                def fnfinder(au,vec=vVector):
                    return scalProd(vec,makeIntoVector(au.firstname))>=SIMILAR_AUTHOR_THRESHOLD
                return fnfinder
            else:
                return makeAuthorFilter(fName,fValue,useSimilarity=False)
        else:
            def fnfinder(au,v=fValue):
                return v.lower() in au.firstname.lower()
            return fnfinder
    elif fName=='lastname':
        if useSimilarity:
            # prepare and store vector
            vVector=makeIntoVector(fValue)
            if sum(vVector.values()):
                def lnfinder(au,vec=vVector):
                    return scalProd(vec,makeIntoVector(au.lastname))>=SIMILAR_AUTHOR_THRESHOLD
                return lnfinder
            else:
                return makeAuthorFilter(fName,fValue,useSimilarity=False)
        else:
            def lnfinder(au,v=fValue):
                return v.lower() in au.lastname.lower()
            return lnfinder
    elif fName=='name':
        def nafinder(au,v=fValue):
            return  (v.lower() in au.firstname.lower()) or \
                    (v.lower() in au.lastname.lower())
        return nafinder
    else:
        return lambda: True

def makeBookSorter(sName):
    '''
        returns an 'extractor of sortable attribute'
        to use when sorting results.
    '''
    if sName=='title':
        def tisorter(bo,filtering):
            return bo.title
        return tisorter
    elif sName=='booktype':
        def btsorter(bo,filtering):
            return bo.booktype
        return btsorter
    elif sName=='lastedit':
        def lesorter(bo,filtering):
            try:
                return -time.mktime(datetime.strptime(bo.lasteditdate,DATETIME_STR_FORMAT).timetuple())
            except:
                return 0
        return lesorter
    elif sName=='relevance':
        def resorter(bo,filtering):
            return -filtering(bo)
        return resorter
    else:
        return None

def makeAuthorSorter(sName):
    '''
        returns an 'extractor of sortable attribute'
        to use when sorting results.
    '''
    if sName=='firstname':
        def fnsorter(au,filtering):
            return au.firstname
        return fnsorter
    elif sName=='lastname':
        def lnsorter(au,filtering):
            return au.lastname
        return lnsorter
    else:
        return None

def dbQueryBooks(   queryArgs=ImmutableMultiDict(), resultsperpage=100,
                    resolve=False, resolveParams={}):
    '''
        A query is interpreted from arguments and executed
        on books. The results, trimmed and polished, are then returned
        in a standard format: result, list_of_books.
        All query-specific terms are stored in 'queryArgs'
        'result' is a dict with various settings, depending on the query.
    '''
    #
    filters=[]
    startfrom=0
    sorter=None
    # queryArgs is in principle a multidict:
    # first determine if searches are by-similarity
    useSimilarity=False
    if 'similarity' in queryArgs:
        for v in queryArgs.getlist('similarity'):
            try:
                useSimilarity=bool(int(v))
            except:
                pass
    for k in queryArgs.keys():
        for v in queryArgs.getlist(k):
            # first deal with the non-filtering arguments
            if k=='startfrom':
                startfrom=int(v)
            elif k=='sortby':
                sorter=makeBookSorter(v)
            elif k=='similarity':
                pass # already dealt with
            else:
                filters.append(makeBookFilter(k,v,useSimilarity=useSimilarity))
    #
    result,booklist=dbTableFilterQuery('book',startfrom,resultsperpage,filters,sorter)
    if resolve:
        return result,[obj.resolveReferences(**resolveParams) for obj in booklist]
    else:
        return result,booklist

def dbQueryAuthors( queryArgs=ImmutableMultiDict(), resultsperpage=100):
    '''
        A query is interpreted from arguments and executed
        on authors. The results, trimmed and polished, are then returned
        in a standard format:  result, list_of_authors.
        All query-specific terms are stored in 'queryArgs'.
        'result' is a dict with various settings, depending on the query.
    '''
    filters=[]
    startfrom=0
    sorter=None
    # queryArgs is in principle a multidict:
    # first determine if searches are by-similarity
    useSimilarity=False
    if 'similarity' in queryArgs:
        for v in queryArgs.getlist('similarity'):
            try:
                useSimilarity=bool(int(v))
            except:
                pass
    for k in queryArgs.keys():
        for v in queryArgs.getlist(k):
            # first deal with the non-filtering arguments
            if k=='startfrom':
                startfrom=int(v)
            elif k=='sortby':
                sorter=makeAuthorSorter(v)
            elif k=='similarity':
                pass # already dealt with
            else:
                filters.append(makeAuthorFilter(k,v,useSimilarity=useSimilarity))
    #
    result,authorlist=dbTableFilterQuery('author',startfrom,resultsperpage,filters,sorter)
    return result,authorlist

def dbGetAll(tableName, resolve=False, resolveParams=None):
    '''
        returns a list of all items from the required table

        If resolve=True, instead of a generator a List is returned
        and on each item the method resolveReferences is invoked.

    '''
    db=dbGetDatabase()
    qModel=tableToModel[tableName]
    mgr=qModel.manager(db)
    if resolve:
        return [obj.resolveReferences(**resolveParams) for obj in mgr.all()]
    else:
        return mgr.all()

def dbMakeDict(objList, fieldname='id'):
    '''
        assuming rows have a unique 'id', makes a generator
        into a dict id -> object, for ease of lookup
    '''
    return {getattr(obj,fieldname): obj for obj in objList}

# table-specific tools
def dbGetHouse(name):
    '''
        Returns a user object from its name,
        None if not found
    '''
    db=dbGetDatabase()
    for qHouse in House.manager(db).all():
        if qHouse.name==name:
            return qHouse

def dbGetUser(name):
    '''
        Returns a user object from its name,
        None if not found
    '''
    db=dbGetDatabase()
    for qUser in User.manager(db).all():
        if qUser.name==name:
            return qUser

def dbGetUserById(id):
    '''
        Returns a user object from its id.
    '''
    db=dbGetDatabase()
    return User.manager(db).get(id)

def dbReplaceUser(newUser):
    '''
        updates an existing User object given its id

        Returns a 2-tuple (success=0/1, new_User_object)
    '''
    db=dbGetDatabase()
    User.db=db
    nUser=User.manager(db).get(newUser.id)
    if nUser:
        for k,q in newUser.__dict__.items():
            if k != 'id':
                setattr(nUser,k,q)
        nUser.update()
        db.commit()
        return (1,newUser)
    else:
        return (0,None)

def dbAddReplaceBook(newBook,resolve=False, resolveParams=None, db=None, userHouse=None):
    '''
        Add/Replace a book to DB

        if book.id is None:
            Attempts adding a book and returns the new Book object.
        else:
            overwrites the fields of the book with the specified id

        Takes care of authors' bookcounters

        Always returns a 2-uple (status,object), where:
            status = 0,1 for failure,success
            object = errormessage or book_object, resp.

        Passing db: it is the caller's responsibility
        to ensure no lockup is achieved via proper commit()

        If userHouse is passed, the constraint is enforced
        that only users sharing the book's house can edit it
    '''
    if db is None:
        doCommit=True
        db=dbGetDatabase()
    else:
        doCommit=False
    newBook.lasteditdate=datetime.now().strftime(DATETIME_STR_FORMAT)
    oldBookStats={}
    newBookStats=statFromBook(newBook)
    Book.db=db
    if newBook.id is None:
        if not ALLOW_DUPLICATE_BOOKS:
            # if new-insertion, check for duplicates then proceed
            for qBook in Book.manager(db).all():
                if qBook.title.lower()==newBook.title.lower() and qBook.authors.lower()==newBook.authors.lower(): # TODO: here check ordering and tricks
                    return (0,'Duplicate detected.')
        if userHouse is None or userHouse==newBook.house:
            newBook.forceAscii()
            prevAuthorList=''
            oldHouse=None
            newHouse=newBook.house
            newBook.save()
            nBook=newBook
        else:
            return (0,'Houses mismatch')
    else:
        # if replacement, find the replacee and proceed
        for qBook in Book.manager(db).all():
            if not ALLOW_DUPLICATE_BOOKS:
                if qBook.id != newBook.id and \
                        (qBook.title.lower()==newBook.title.lower() and qBook.authors.lower()==newBook.authors.lower()):
                    return (0,'Duplicate detected.')
        nBook=Book.manager(db).get(newBook.id)
        if nBook is not None:
            oldBookStats=statFromBook(nBook)
            oldHouse=nBook.house
            newHouse=newBook.house
            # automatic handling of object attributes except those handled manually:
            if userHouse is None or userHouse==nBook.house:
                prevAuthorList=''
                for k,q in newBook.__dict__.items():
                    if k == 'authors':
                        prevAuthorList=getattr(nBook,k)
                        _auIdSet={au.id for au in dbGetAll('author')}
                        _bookAuList=rollStringList(set(unrollStringList(q)) & _auIdSet)
                        setattr(nBook,k,_bookAuList)
                    else:
                        setattr(nBook,k,q)
                nBook.forceAscii()
                nBook.update()
            else:
                return (0,'Houses mismatch')
        else:
            return (0,'Not found.')
    # reflect authorlist changes to the authors table. Current book's id is nBook.id
    oldAuthorSet=set(unrollStringList(prevAuthorList))
    newAuthorSet=set(unrollStringList(nBook.authors))
    wonAuthors=newAuthorSet-oldAuthorSet
    lostAuthors=oldAuthorSet-newAuthorSet
    # apply stats update
    dbIncrementStatistic(db,oldBookStats,newBookStats)
    #
    updateBookCounters(db,nBook.id,lost=lostAuthors,won=wonAuthors)
    if oldHouse:
        dbIncrementHouseBookCount(db,oldHouse,-1)
    dbIncrementHouseBookCount(db,newHouse,1)
    #
    if doCommit:
        db.commit()

    if resolve:
        return (1,nBook.resolveReferences(**resolveParams))
    else:
        return (1,nBook)

def dbIncrementHouseBookCount(dbSession,houseName,delta):
    '''
        Updates the nbooks house attribute for the given
        house by applying the provided delta to the counter
    '''
    House.db=dbSession
    for qHouse in House.manager(dbSession).all():
        if qHouse.name==houseName:
            qHouse.nbooks+=delta
            qHouse.update()

def updateBookCounters(dbSession,bookId,lost,won):
    '''
        updates some author objects to reflect a pending change
        in a book's author list. Takes care of counters and comma-separated id list
    '''
    Author.db=dbSession
    for lostAu in lost:
        qAuthor=Author.manager(dbSession).get(lostAu)
        if qAuthor:
            newList,listCount=expungeFromStringList(qAuthor.booklist, bookId)
            qAuthor.booklist=newList
            qAuthor.bookcount=listCount
            qAuthor.update()
        else:
            raise ValueError
    for wonAu in won:
        qAuthor=Author.manager(dbSession).get(wonAu)
        if qAuthor:
            newList,listCount=addToStringList(qAuthor.booklist, bookId)
            qAuthor.booklist=newList
            qAuthor.bookcount=listCount
            qAuthor.update()
        else:
            raise ValueError

def dbDeleteBook(id,db=None,userHouse=None):
    '''
        attempts deletion of a book. If deletion succeeds, returns True
        It also takes care of deregistering authors associated to that book,
        transactionally.

        If userHouse is provided, the constraint if enforced that
        only the users housed in the same house as the book can proceed
    '''
    if db is None:
        doCommit=True
        db=dbGetDatabase()
    else:
        doCommit=False
    Book.db=db
    try:
        dBook=Book.manager(db).get(id)
        if userHouse is None or dBook.house==userHouse:
            oldAuthorSet=set(unrollStringList(dBook.authors))
            oldHouse=dBook.house
            dbIncrementStatistic(db,statFromBook(dBook),{})
            updateBookCounters(db,dBook.id,lost=oldAuthorSet,won=set())
            dBook.delete()
            dbIncrementHouseBookCount(db,oldHouse,-1)
            if doCommit:
                db.commit()
            return (1,id)
        else:
            return (0,'Houses mismatch')
    except:
        return (0,'Cannot delete')

def registerLogin(userId):
    '''
        registers a login by a given user and returns the string
        expressing the current date. Empty string if errors occur.
    '''
    db=dbGetDatabase()
    User.db=db
    localTimezone=timezone(USERS_TIMEZONE)
    try:
        qUser=User.manager(db).get(userId)
        qUser.lastlogindate=datetime.now(localTimezone).strftime(DATETIME_STR_FORMAT)
        qUser.update()
        db.commit()
        return qUser.lastlogindate
    except:
        return ''

def dbDeleteAuthor(id,db=None,userHouse=None):
    '''
        attempts deletion of an author. If deletion succeeds, returns its id
        Always a 2-uple (success,stuff)

        It must deregister author as author of all its books before deleting it,
        transactionally.

        If an user ID is provided, an additional constraint has to be honoured,
        namely no book authored by author can belong to a different house
        than the one the user belongs to.
    '''
    if db is None:
        doCommit=True
        db=dbGetDatabase()
    else:
        doCommit=False
    Author.db=db
    try:
        dAuthor=Author.manager(db).get(id)
        # if a userHouse is provided, check the my-books-only constraint
        Book.db=db
        if userHouse is not None:
            for bookId in unrollStringList(dAuthor.booklist):
                qBook=Book.manager(db).get(bookId)
                if qBook.house!=userHouse:
                    return (0,'Author has books in other houses')
        # browse through all books authored by this author
        for bookId in unrollStringList(dAuthor.booklist):
            qBook=Book.manager(db).get(bookId)
            qBook.authors,_=expungeFromStringList(qBook.authors,id)
            qBook.update()
        #
        dbIncrementStatistic(db,statFromAuthor(dAuthor),{})
        dAuthor.delete()
        if doCommit:
            db.commit()
        return (1,id)
    except:
        return (0,'Cannot delete')

def dbGetByIdFactory(className):
    '''
        factory function to generate getters-by-id
        for various object types.
        The getters return None if the id is not found
    '''
    def _byIdGetter(id):
        db=dbGetDatabase()
        try:
            qObject=className.manager(db).get(id)
            return qObject
        except:
            return None
    return _byIdGetter

dbGetAuthor=dbGetByIdFactory(Author)
dbGetBook=dbGetByIdFactory(Book)

def dbAddReplaceAuthor(newAuthor, db=None):
    '''
        Add/Replace an author to DB

        if author.id is None:
            Attempts adding an author and returns the new Author object.
            returns None if duplicates are detected
        else:
            overwrites the fields of the author with the requested id
            Returns None if not found (or other errors)

        Passing db: it is the caller's responsibility
        to ensure no lockup is achieved via proper commit()
    '''
    oldAuthorStats={}
    newAuthorStats=statFromAuthor(newAuthor)
    if db is None:
        doCommit=True
        db=dbGetDatabase()
    else:
        doCommit=False
    Author.db=db
    if newAuthor.id is None:
        # new insertion: check for duplicates then proceed
        for qAuthor in Author.manager(db).all():
            if qAuthor.firstname.lower()==newAuthor.firstname.lower() and qAuthor.lastname.lower()==newAuthor.lastname.lower():
                return (0,'Duplicate detected')
        # no duplicates: add author through the orm
        newAuthor.bookcount=0
        newAuthor.booklist=''
        newAuthor.forceAscii()
        newAuthor.save()
        nAuthor=newAuthor
    else:
        # if replacement, find the replacee and proceed
        for qAuthor in Author.manager(db).all():
            if qAuthor.id != newAuthor.id and \
                    (qAuthor.firstname.lower()==newAuthor.firstname.lower() and qAuthor.lastname.lower()==newAuthor.lastname.lower()):
                return (0,'Duplicate detected')
        nAuthor=Author.manager(db).get(newAuthor.id)
        if nAuthor is not None:

            oldAuthorStats=statFromAuthor(nAuthor)

            for k,q in newAuthor.__dict__.items():
                if k in ['bookcount','booklist']:
                    pass
                else:
                    setattr(nAuthor,k,q)
            nAuthor.forceAscii()
            nAuthor.update()
        else:
            return (0,'Not found')
    # apply stat changes
    dbIncrementStatistic(db,oldAuthorStats,newAuthorStats)
    #
    if doCommit:
        db.commit()
    return (1,nAuthor)

def erase_db_table(db,tableName):
    '''
        Deletes *all* records from a (book,author) table of the given DB
    '''
    if db is None:
        doCommit=True
        db=dbGetDatabase()
    else:
        doCommit=False

    tObject=tableToModel[tableName]
    tObject.db=db
    idList=[obj.id for obj in tObject.manager(db).all()]
    deleteds=[]
    for oId in idList:
        if tableName=='book':
            dbDeleteBook(oId,db=db)
        elif tableName=='author':
            dbDeleteAuthor(oId,db=db)
        else:
            raise NotImplementedError
        deleteds.append(oId)
    if doCommit:
        db.commit()
    return {'deleted_%s' % tableName: deleteds}
