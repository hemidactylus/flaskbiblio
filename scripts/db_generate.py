# test DB creation script

from __future__ import print_function

import os
import sys
import sqlite3 as lite
from operator import itemgetter

from orm import Model, Database

import env

from config import DB_DIRECTORY, DB_NAME
from app.utils.interactive import ask_for_confirmation, logDo
from db_testvalues import _testvalues

from app.database.models import (
                                    tableToModel, 
                                    User,
                                    Author,
                                    Language,
                                    Booktype,
                                    Book,
                                )
from app.database.dbtools import    (
                                        dbAddReplaceAuthor,
                                        dbAddReplaceBook,
                                        dbGetUser,
                                        dbGetHouse,
                                    )

def clearToProceed(dbfilename):
    '''
        Combines a file-existence check and a prompt to the user
        in case it exists. Returns:
            True:  file does not exist [anymore?], proceed
            False: file exists and is to keep, abort
    '''
    # if it does exist, erase it
    if os.path.isfile(dbfilename):
        deletePrompt='File "%s" exists. Are you sure you want to lose its contents?'
        if ask_for_confirmation(deletePrompt % dbfilename,['y','yes','yeah']):
            os.remove(dbfilename)
            return True
        else:
            return False
    else:
        return True

def generate_db(dbFile):
    '''
        returns an orm Database object
    '''
    return Database(dbFile)

def populate_db(db):
    '''
        populates the DB through the use of ORMs.
    '''
    print('')
    # populate other tables
    for qTable,qModel in filter(lambda qtP: qtP[0] not in ['book','author','user'], tableToModel.items()):
        print('    %s' % qTable)
        qModel.db=db
        for item in _testvalues[qTable]:
            qObject=qModel(**item)
            qObject.save()
    db.commit()
    # add users
    User.db=db
    print('    %s' % 'user')
    for item in _testvalues['user']:
        # check if house is valid
        if dbGetHouse(item['house']) is None:
            raise ValueError()
        nUser=User(**item)
        nUser.save()
    db.commit()
    # add authors
    auLNameMap={} # used later for books
    Author.db=db
    print('    %s' % 'author')
    for item in _testvalues['author']:
        nAuthor=Author(id=None,**item)
        result,newAu=dbAddReplaceAuthor(nAuthor)
        if not result:
            raise ValueError()
        else:
            auLNameMap[newAu.lastname]=newAu.id
    # add books with author resolution
    Book.db=db
    print('    %s' % 'book')
    for item in _testvalues['book']:
        # authors to autorlist string
        authorList=','.join(map(str, sorted([auLNameMap[auLName] for auLName in item['authors'].split(',')])))
        #
        del item['authors']
        item['lasteditor']=dbGetUser(item['lasteditor']).id
        nBook=Book  (
                        id=None,
                        authors=authorList,
                        **item
                    )
        result,newBo=dbAddReplaceBook(nBook)
        if not result:
            raise ValueError()
    # done.
    db.commit()

if __name__=='__main__':

    dbFile=os.path.join(DB_DIRECTORY,DB_NAME)
    print('Database file: %s' % dbFile)

    if clearToProceed(dbFile):
        db=logDo(lambda: generate_db(dbFile),'Generating DB')
        logDo(lambda: populate_db(db),'Populating DB')
        print('Finished.')
    else:
        print('Operation aborted.')
