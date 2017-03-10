#!/usr/bin/env python
# Generation of a new, empty house to the DB

from __future__ import print_function

import sqlite3 as lite
import sys
import os
from orm import Model, Database

import env

from config import DB_DIRECTORY, DB_NAME
from app.utils.interactive import ask_for_confirmation, logDo

from app.database.models import (
                                    House,
                                )
from app.database.dbtools import    (
                                        dbGetDatabase,
                                        dbGetAll,
                                    )
if __name__=='__main__':
    '''
        Insertion of an empty house to the DB
    '''
    _usageMsg='Usage: ./db_add_house.py houseName "House Description"'
    
    qargs=sys.argv[1:]
    if len(qargs)!=2:
        print(_usageMsg)
    else:
        houseName=qargs[0]
        houseDescription=qargs[1]
        houseNbooks=0
        # check for unicity
        houses=list(dbGetAll('house'))
        if any(h.name == houseName for h in houses):
            print('Duplicate houseName: aborting')
        else:
            db=logDo(lambda: dbGetDatabase(),'Opening DB')
            House.db=db
            nHouse=House(name=houseName,description=houseDescription,nbooks=houseNbooks)
            logDo(lambda: nHouse.save(),'Saving new house')
            logDo(lambda: db.commit(),'Committing to DB')
            print('House "%s" inserted.' % nHouse)