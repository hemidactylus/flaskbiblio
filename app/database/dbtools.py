# dbtools.py : library to interface with the database

from orm import Database
import os

from datetime import datetime

from config import DB_DIRECTORY, DB_NAME, DATETIME_STR_FORMAT
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
            overwrites the fields of a book its id.
            Returns None if not found (or other errors)
    '''
    db=dbGetDatabase()
    newBook.lasteditdate=datetime.now().strftime(DATETIME_STR_FORMAT)
    Book.db=db
    if newBook.id is None:
        # if new-insertion, check for duplicates then proceed
        for qBook in Book.manager(db).all():
            if qBook.title==newBook.title and qBook.authors==newBook.authors: # TODO: here check ordering and tricks
                return None
        nAuthor.forceAscii()
        newBook.save()
        nBook=newBook
    else:
        # if replacement, find the replacee and proceed
        nBook=Book.manager(db).get(newBook.id)
        if nBook is not None:
            nBook.title=newBook.title
            nBook.inhouse=newBook.inhouse
            nBook.inhousenotes=newBook.inhousenotes
            nBook.notes=newBook.notes
            nBook.booktype=newBook.booktype
            nBook.languages=newBook.languages
            nBook.authors=newBook.authors
            nBook.lasteditor=newBook.lasteditor
            nBook.lasteditdate=newBook.lasteditdate
            nAuthor.forceAscii()
            nBook.update()
        else:
            return None
    db.commit()

    if resolve:
        return nBook.resolveReferences(**resolveParams)
    else:
        return nBook

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

def dbAddAuthor(firstname,lastname):
    '''
        Attempts adding an author and returns the new Author object.
        returns None if duplicates are detected
    '''
    db=dbGetDatabase()
    Author.db=db
    for qAuthor in Author.manager(db).all():
        if qAuthor.firstname==firstname and qAuthor.lastname==lastname:
            return None
    # no duplicates: add author through the orm
    nAuthor=Author(firstname=firstname,lastname=lastname)
    nAuthor.forceAscii()
    nAuthor.save()
    db.commit()
    return nAuthor

def dbDeleteAuthor(id):
    '''
        attempts deletion of an author. If deletion succeeds, returns its id
    '''
    db=dbGetDatabase()
    Author.db=db
    try:
        dAuthor=Author.manager(db).get(id)
        dAuthor.delete()
        db.commit()
        return id
    except:
        return None

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

def dbReplaceAuthor(id,firstname,lastname):
    '''
        overwrites the fields of an author given its id.
        Returns None if not found (or other errors)
    '''
    db=dbGetDatabase()
    Author.db=db
    nAuthor=Author.manager(db).get(id)
    if nAuthor is not None:
        nAuthor.firstname=firstname
        nAuthor.lastname=lastname
        nAuthor.forceAscii()
        nAuthor.update()
        db.commit()
        return nAuthor
