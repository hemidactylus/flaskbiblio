# dbtools.py : library to interface with the database

from orm import Database
import os
from werkzeug.datastructures import ImmutableMultiDict

from datetime import datetime

from config import DB_DIRECTORY, DB_NAME, DATETIME_STR_FORMAT, ALLOW_DUPLICATE_BOOKS
from app.utils.stringlists import   (
                                        rollStringList,
                                        unrollStringList,
                                        addToStringList,
                                        expungeFromStringList,
                                    )
from app.database.models import (
                                    tableToModel, 
                                    User,
                                    Author,
                                    Language,
                                    Booktype,
                                    Book,
                                    Statistic,
                                )

def dbIncrementStatistic(db,statName,statDelta):
    '''
        Increments/decrements a statistic stored
        in the DB.
        It assumes it is called within a transaction
        hence it does not invoke any commit()

        If statName is not found, an error is raised
    '''
    Statistic.db=db
    stat=[istat for istat in Statistic.manager(db).all() if istat.name==statName]
    if len(stat)!=1:
        raise ValueError('Error with statistic name "%s".' % statName)
    else:
        istat=stat[0]
        istat.value=str(int(istat.value)+statDelta)
        istat.update()

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
    # perform query and filters
    qlist=list(filter(  lambda obj: all([ffunc(obj) for ffunc in filterList]),
                        (dbGetAll(tableName))
                     )
               )
    # sort results (either with default or explicit sorting key)
    if sorter is None:
        reslist=sorted(qlist)
    else:
        reslist=list(sorted(qlist,key=sorter))
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

def makeBookFilter(fName,fValue):
    '''
        Interprets an argument name/vale in the query string
        and produces a corresponding boolean filter
    '''
    if fName=='author':
        def aufinder(bo,v=fValue):
            return int(v) in unrollStringList(bo.authors)
        return aufinder
    elif fName=='title':
        def tifinder(bo,v=fValue):
            #return v.lower() in bo.title.lower()
            return any(vpart.lower() in bo.title.lower() for vpart in v.split(' '))
        return tifinder
    elif fName=='booktype':
        def btfinder(bo,v=fValue):
            return bo.booktype.upper()==v.upper()
        return btfinder
    elif fName=='language':
        def lafinder(bo,v=fValue):
            return v.upper() in bo.languages.split(',')
        return lafinder
    elif fName=='inhouse':
        def ihfinder(bo,v=fValue):
            return bool(bo.inhouse)==bool(int(v))
        return ihfinder
    else:
        return lambda: True

def makeAuthorFilter(fName, fValue):
    '''
        Same as above but for the 'author' objects
    '''
    if fName=='firstname':
        def fnfinder(au,v=fValue):
            return v.lower() in au.firstname.lower()
        return fnfinder
    elif fName=='lastname':
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
        def tisorter(bo):
            return bo.title
        return tisorter
    elif sName=='booktype':
        def btsorter(bo):
            return bo.booktype
        return btsorter
    else:
        return None

def makeAuthorSorter(sName):
    '''
        returns an 'extractor of sortable attribute'
        to use when sorting results.
    '''
    if sName=='firstname':
        def fnsorter(au):
            return au.firstname
        return fnsorter
    elif sName=='lastname':
        def lnsorter(au):
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
    for k in queryArgs.keys():
        for v in queryArgs.getlist(k):
            # first deal with the non-filtering arguments
            if k=='startfrom':
                startfrom=int(v)
            elif k=='sortby':
                sorter=makeBookSorter(v)
            else:
                filters.append(makeBookFilter(k,v))
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
    for k in queryArgs.keys():
        for v in queryArgs.getlist(k):
            # first deal with the non-filtering arguments
            if k=='startfrom':
                startfrom=int(v)
            elif k=='sortby':
                sorter=makeAuthorSorter(v)
            else:
                filters.append(makeAuthorFilter(k,v))
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
def dbGetUser(name):
    '''
        Returns a user object from its name,
        None if not found
    '''
    db=dbGetDatabase()
    for qUser in User.manager(db).all():
        if qUser.name==name:
            return qUser

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

def dbAddReplaceBook(newBook,resolve=False, resolveParams=None, db=None):
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
    '''
    if db is None:
        doCommit=True
        db=dbGetDatabase()
    else:
        doCommit=False
    newBook.lasteditdate=datetime.now().strftime(DATETIME_STR_FORMAT)
    Book.db=db
    if newBook.id is None:
        if not ALLOW_DUPLICATE_BOOKS:
            # if new-insertion, check for duplicates then proceed
            for qBook in Book.manager(db).all():
                if qBook.title.lower()==newBook.title.lower() and qBook.authors.lower()==newBook.authors.lower(): # TODO: here check ordering and tricks
                    return (0,'Duplicate detected.')
        newBook.forceAscii()
        prevAuthorList=''
        dbIncrementStatistic(db,'nbooks',1)
        newBook.save()
        nBook=newBook
    else:
        # if replacement, find the replacee and proceed
        for qBook in Book.manager(db).all():
            if not ALLOW_DUPLICATE_BOOKS:
                if qBook.id != newBook.id and \
                        (qBook.title.lower()==newBook.title.lower() and qBook.authors.lower()==newBook.authors.lower()):
                    return (0,'Duplicate detected.')
        nBook=Book.manager(db).get(newBook.id)
        if nBook is not None:
            # automatic handling of object attributes except those handled manually:
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
            return (0,'Not found.')
    # reflect authorlist changes to the authors table. Current book's id is nBook.id
    oldAuthorSet=set(unrollStringList(prevAuthorList))
    newAuthorSet=set(unrollStringList(nBook.authors))
    wonAuthors=newAuthorSet-oldAuthorSet
    lostAuthors=oldAuthorSet-newAuthorSet
    updateBookCounters(db,nBook.id,lost=lostAuthors,won=wonAuthors)
    #
    if doCommit:
        db.commit()

    if resolve:
        return (1,nBook.resolveReferences(**resolveParams))
    else:
        return (1,nBook)

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

def dbDeleteBook(id,db=None):
    '''
        attempts deletion of a book. If deletion succeeds, returns True
        It also takes care of deregistering authors associated to that book,
        transactionally
    '''
    if db is None:
        doCommit=True
        db=dbGetDatabase()
    else:
        doCommit=False
    Book.db=db
    try:
        dBook=Book.manager(db).get(id)
        oldAuthorSet=set(unrollStringList(dBook.authors))
        updateBookCounters(db,dBook.id,lost=oldAuthorSet,won=set())
        dBook.delete()
        dbIncrementStatistic(db,'nbooks',-1)
        if doCommit:
            db.commit()
        return (1,id)
    except:
        return (0,'Cannot delete')

def registerLogin(userId):
    '''
        registers a login by a given user and returns the string
        expressing the current date. Empty string if errors occur.
    '''
    db=dbGetDatabase()
    User.db=db
    try:
        qUser=User.manager(db).get(userId)
        qUser.lastlogindate=datetime.now().strftime(DATETIME_STR_FORMAT)
        qUser.update()
        db.commit()
        return qUser.lastlogindate
    except:
        return ''

def dbDeleteAuthor(id,db=None):
    '''
        attempts deletion of an author. If deletion succeeds, returns its id
        Always a 2-uple (success,stuff)

        It must deregister author as author of all its books before deleting it,
        transactionally.
    '''
    if db is None:
        doCommit=True
        db=dbGetDatabase()
    else:
        doCommit=False
    Author.db=db
    try:
        dAuthor=Author.manager(db).get(id)
        # browse through all books authored by this author
        Book.db=db
        for bookId in unrollStringList(dAuthor.booklist):
            qBook=Book.manager(db).get(bookId)
            qBook.authors,_=expungeFromStringList(qBook.authors,id)
            qBook.update()
        #
        dbIncrementStatistic(db,'nauthors',-1)
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
        dbIncrementStatistic(db,'nauthors',1)
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

            for k,q in newAuthor.__dict__.items():
                if k in ['bookcount','booklist']:
                    pass
                else:
                    setattr(nAuthor,k,q)
            nAuthor.forceAscii()
            nAuthor.update()
        else:
            return (0,'Not found')
    if doCommit:
        db.commit()
    return (1,nAuthor)
