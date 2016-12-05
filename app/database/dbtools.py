# dbtools.py : library to interface with the database

from orm import Database
import os

from config import DB_DIRECTORY, DB_NAME
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

def dbAddBook(title,inhouse,notes,booktype,languages,authors,lasteditor):
    '''
        Attempts adding a book and returns the new Book object.
        returns None if duplicates are detected
    '''
    db=dbGetDatabase()
    Book.db=db
    for qBook in Book.manager(db).all():
        if qBook.title==title and qBook.authors==authors: # TODO: here check ordering and tricks
            return None
    # no duplicates: add author through the orm
    nBook=Book(
        title=title,
        inhouse=inhouse,
        notes=notes,
        booktype=booktype,
        languages=languages,
        authors=authors,
        lasteditor=lasteditor,
    )
    nBook.save()
    db.commit()
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
    nAuthor.save()
    db.commit()
    return nAuthor

def dbDeleteAuthor(id):
    '''
        attempts deletion of an author. If deletion succeeds, returns True
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

def dbGetAuthor(id):
    '''
        Returns a user object from its id,
        None if not found
    '''
    db=dbGetDatabase()
    try:
        qAuthor=Author.manager(db).get(id)
        return qAuthor
    except:
        return None

def dbReplaceAuthor(id,firstname,lastname):
    '''
        overwrites the fields of an author given its id.
        Returns None if not found (or other errors)
    '''
    db=dbGetDatabase()
    Author.db=db
    nAuthor=Author.manager(db).get(id)
    nAuthor.firstname=firstname
    nAuthor.lastname=lastname
    nAuthor.update()
    db.commit()
    return nAuthor
