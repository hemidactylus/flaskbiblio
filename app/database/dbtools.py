# dbtools.py : library to interface with the database

from orm import Database
import os

from datetime import datetime

from config import DB_DIRECTORY, DB_NAME, DATETIME_STR_FORMAT
from app.utils.stringlists import   (
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
                                )

def dbGetDatabase():
    '''
        Opens a DB connection and returns a cursor on it
    '''
    dbFile=os.path.join(DB_DIRECTORY,DB_NAME)    
    return Database(dbFile)

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

def dbAddReplaceBook(newBook,resolve=False, resolveParams=None):
    '''
        Add/Replace a book to DB

        if book.id is None:
            Attempts adding a book and returns the new Book object.
            returns None if duplicates are detected
        else:
            overwrites the fields of the book with the specified id
            Returns None if not found (or other errors)

        Takes care of authors' bookcounters
    '''
    db=dbGetDatabase()
    newBook.lasteditdate=datetime.now().strftime(DATETIME_STR_FORMAT)
    Book.db=db
    if newBook.id is None:
        # if new-insertion, check for duplicates then proceed
        for qBook in Book.manager(db).all():
            if qBook.title.lower()==newBook.title.lower() and qBook.authors.lower()==newBook.authors.lower(): # TODO: here check ordering and tricks
                return (0,'Duplicate detected.')
        newBook.forceAscii()
        prevAuthorList=''
        newBook.save()
        nBook=newBook
    else:
        # if replacement, find the replacee and proceed
        for qBook in Book.manager(db).all():
            if qBook.id != newBook.id and \
                    (qBook.title.lower()==newBook.title.lower() and qBook.authors.lower()==newBook.authors.lower()):
                return (0,'Duplicate detected.')
        nBook=Book.manager(db).get(newBook.id)
        if nBook is not None:
            prevAuthorList=nBook.authors
            nBook.title=newBook.title
            nBook.inhouse=newBook.inhouse
            nBook.inhousenotes=newBook.inhousenotes
            nBook.notes=newBook.notes
            nBook.booktype=newBook.booktype
            nBook.languages=newBook.languages
            nBook.authors=newBook.authors
            nBook.lasteditor=newBook.lasteditor
            nBook.lasteditdate=newBook.lasteditdate
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

def dbDeleteBook(id):
    '''
        attempts deletion of a book. If deletion succeeds, returns True
    '''
    db=dbGetDatabase()
    Book.db=db
    try:
        dBook=Book.manager(db).get(id)
        dBook.delete()
        db.commit()
        return id
    except:
        return None

def registerLogin(userId):
    db=dbGetDatabase()
    User.db=db
    qUser=User.manager(db).get(userId)
    qUser.lastlogindate=datetime.now().strftime(DATETIME_STR_FORMAT)
    qUser.update()
    db.commit()
    return qUser.lastlogindate

def dbDeleteAuthor(id):
    '''
        attempts deletion of an author. If deletion succeeds, returns its id
        Always a 2-uple (success,stuff)
    '''
    db=dbGetDatabase()
    Author.db=db
    try:
        dAuthor=Author.manager(db).get(id)
        dAuthor.delete()
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

def dbAddReplaceAuthor(newAuthor):
    '''
        Add/Replace an author to DB

        if author.id is None:
            Attempts adding an author and returns the new Author object.
            returns None if duplicates are detected
        else:
            overwrites the fields of the author with the requested id
            Returns None if not found (or other errors)
    '''
    db=dbGetDatabase()
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
            nAuthor.firstname=newAuthor.firstname
            nAuthor.lastname=newAuthor.lastname
            nAuthor.forceAscii()
            nAuthor.update()
        else:
            return (0,'Not found')
    db.commit()
    return (1,nAuthor)
