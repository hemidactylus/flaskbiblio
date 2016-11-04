# test DB creation script

import os
import sys
import sqlite3 as lite
from operator import itemgetter

import env

from config import DB_DIRECTORY, DB_NAME
from app.utils.interactive import ask_for_confirmation
from app.database.db_description import tableDesc
from db_testvalues import _testvalues

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

def generate_db(dbfilename):
    '''
        Creates a standard database file, using table descriptors in /database
    '''
    with lite.connect(dbfilename) as dbcon:
        cur=dbcon.cursor()
        # automated table creation
        for tableName, tableFields in tableDesc.items():
            creationCommand='CREATE TABLE %s (%s)' % (
                    tableName,
                    ','.join(['%s %s' % fPair for fPair in tableFields])
                )
            cur.execute(creationCommand)

def populate_db(dbfilename):
    '''
        using the db table descriptors in /database and the local dummy values, populates the db
    '''
    with lite.connect(dbfilename) as dbcon:
        cur=dbcon.cursor()
        # for each table in the testvalues list, insert the provided rows
        for tableName, tableRows in _testvalues.items():
            for tRow in tableRows:
                # make each one into a proper tuple as required by the sqllite driver before insertion
                tFields=list(filter(lambda fld: fld in tRow,map(itemgetter(0),tableDesc[tableName])))
                actualFields=tuple(tRow[fld] for fld in tFields)
                fDesc=','.join(tFields)
                qMarks=','.join(['?']*len(actualFields))
                cur.execute('INSERT INTO %s (%s) VALUES (%s)' % (tableName,fDesc,qMarks), actualFields)

def logDo(fct,msg):
    '''
        utility function to log start/end of an operation (a zero-arg function)
    '''
    print('%s ... ' % msg,end='')
    sys.stdout.flush()
    fct()
    print('Done.')
    sys.stdout.flush()

if __name__=='__main__':

    dbFile=os.path.join(DB_DIRECTORY,DB_NAME)
    print('Database file: %s' % dbFile)

    if clearToProceed(dbFile):
        logDo(lambda: generate_db(dbFile),'Generating DB')
        logDo(lambda: populate_db(dbFile),'Populating DB')
        print('Finished.')
    else:
        print('Operation aborted.')
