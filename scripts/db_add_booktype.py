#!/usr/bin/env python
# Generation of a new booktype to the DB

from __future__ import print_function

import sqlite3 as lite
import sys
import os
from orm import Model, Database

import env

from config import DB_DIRECTORY, DB_NAME
from app.utils.interactive import ask_for_confirmation, logDo

from app.database.models import (
                                    Booktype,
                                )
from app.database.dbtools import    (
                                        dbGetDatabase,
                                        dbGetAll,
                                    )
if __name__=='__main__':
    '''
        Insertion of a new booktype to the DB
    '''
    _usageMsg='Usage: ./db_add_booktype.py bTypeTag bTypeName bTypeDesc'
    
    qargs=sys.argv[1:]
    if len(qargs)!=3:
        print(_usageMsg)
    else:
        btypeTag=qargs[0]
        btypeName=qargs[1]
        btypeDesc=qargs[2]
        # check for unicity
        btypes=list(dbGetAll('booktype'))
        if any(bt.tag == btypeTag for bt in btypes):
            print('Duplicate booktype tag: aborting')
        else:
            db=logDo(lambda: dbGetDatabase(),'Opening DB')
            Booktype.db=db
            nBooktype=Booktype(
                tag=btypeTag,
                name=btypeName,
                description=btypeDesc
            )
            logDo(lambda: nBooktype.save(),'Saving new booktype')
            logDo(lambda: db.commit(),'Committing to DB')
            print('Booktype "%s" inserted.' % nBooktype)