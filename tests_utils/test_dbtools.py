# dbtools tester

import env

from app.database.dbtools import    (
                                        dbGetDatabase,
                                        dbGetAll,
                                        dbMakeDict,
                                    )
from app.database.models import (
                                    tableToModel, 
                                    User,
                                    Author,
                                    Language,
                                    Booktype,
                                    Book,
                                )

def main():
    db=dbGetDatabase()
    # get and display all languages
    print('Object list:')
    for tname,tobj in tableToModel.items():
        print('  Objects of type "%s":' % tname)
        rows=dbMakeDict(dbGetAll(tname))
        for rowIndex,row in rows.items():
            print('    %04i -> %s' % (rowIndex,row))
        #
    print('Done.')

if __name__=='__main__':
    main()
