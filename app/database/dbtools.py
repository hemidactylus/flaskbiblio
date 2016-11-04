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

def dbGetAll(tableName):
    '''
        returns a list of all items from the required table
    '''
    db=dbGetDatabase()
    qModel=tableToModel[tableName]
    mgr=qModel.manager(db)
    return mgr.all()

def dbMakeDict(objList):
    '''
        assuming rows have a unique 'id', makes a generator
        into a dict id -> object, for ease of lookup
    '''
    return {obj.id: obj for obj in objList}
