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
    for qTable,qModel in tableToModel.items():
        print('    %s' % qTable)
        qModel.db=db
        for item in _testvalues[qTable]:
            qObject=qModel(**item)
            qObject.save()

def commit_db(db):
    db.commit()

if __name__=='__main__':

    dbFile=os.path.join(DB_DIRECTORY,DB_NAME)
    print('Database file: %s' % dbFile)

    if clearToProceed(dbFile):
        db=logDo(lambda: generate_db(dbFile),'Generating DB')
        logDo(lambda: populate_db(db),'Populating DB')
        logDo(lambda: commit_db(db),'Closing DB')
        print('Finished.')
    else:
        print('Operation aborted.')
