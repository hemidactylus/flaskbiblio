#!/usr/bin/env python
from __future__ import print_function

import os
import sys
import json

import env
from app.utils.interactive import ask_for_confirmation, logDo
from app.database.dbtools import    (
                                        dbGetDatabase,
                                        dbGetUser,
                                    )

# import tools are all in this subpackage:
from app.utils.importlibrary import (
                                                read_and_parse_csv,
                                                process_book_list,
                                                import_from_bilist_json,
                                            )

def clearToExtract(inFile,outFile):
    '''
        Asks for confirmation of the extraction CSV -> structure in plain text
    '''
    # if it does exist, get confirmation
    if os.path.isfile(inFile):
        if os.path.isfile(outFile):
            overwritePrompt='Are you sure you want to extract data from "%s" onto EXISTING file "%s"?'
            if ask_for_confirmation(overwritePrompt % (inFile,outFile),['y','yes','yeah']):
                return True
            else:
                return False
        else:
            return True
    else:
        print('Source file "%s" must exist.' % (inFile))
        return False

def clearToImport(inFile,actingUser):
    '''
        Asks for confirmation of the insertion into DB
    '''
    # if it does exist, erase it
    if os.path.isfile(inFile):
        insertPrompt='Are you sure you want to merge the data from "%s" in the DB as user "%s"?'
        if ask_for_confirmation(insertPrompt % (inFile, actingUser),['y','yes','yeah']):
            return True
        else:
            return False
    else:
        print('Source file "%s" must exist.' % (inFile))
        return False

if __name__=='__main__':
    _helpMsg='''Usage: python script.py ARGS.
    Args can specify the import mode:
        (1) -e input.csv books.json [-h for skipping a one-line header]
            EXTRACT: from csv to book list as 'userName'
        (2) -p books.json fixedlibrary.json
            PROCESS: from the books-only to a books/author bilist, checked for consistency
        (3) -i inputlibrary.json userName
            INSERT: read books/authors's json and insert data into the DB as 'userName'
'''

    # a valid csv file must be provided
    if len(sys.argv)>1:
        if sys.argv[1]=='-e':
            print('-e or EXTRACT mode.')
            # from a csv to a books-only-json, with book-local minimal parsing-and-warnings
            if len(sys.argv)>=4:
                inFile=sys.argv[2]
                outFile=sys.argv[3]
                skipHeader = '-h' in sys.argv[4:]
                print('SkipHeader="%s"' % ('Y' if skipHeader else 'N'))
                if clearToExtract(inFile,outFile):
                    inFileHandle=open(inFile)
                    parsedCSV=logDo(
                            lambda: read_and_parse_csv(inFileHandle,skipHeader=skipHeader),
                            'Reading from "%s"' % inFile
                    )
                    logDo(
                            lambda: open(outFile,'w').write('%s\n' % json.dumps(parsedCSV,indent=4,sort_keys=True)),
                            'Saving to json "%s"' % outFile
                    )
                    warningBooks=len(list(filter(lambda bs: '_warnings' in bs,parsedCSV['books'])))
                    if warningBooks:
                        print('Books with warning: %s. Go and fix them.' % warningBooks)
                    print('Finished.')
                else:
                    print('Operation aborted.')
            else:
                print('At least three cmdline args are required.')
                print(_helpMsg)
        elif sys.argv[1]=='-p':
            print('-p or PROCESS mode.')
            if len(sys.argv)>3:
                inFile=sys.argv[2]
                outFile=sys.argv[3]
                if clearToExtract(inFile,outFile):
                    inFileHandle=open(inFile)
                    bilistStructure=logDo(
                            lambda: process_book_list(inFileHandle),
                            'Processing book list from "%s"' % inFile
                    )
                    logDo(
                            lambda: open(outFile,'w').write('%s\n' % json.dumps(bilistStructure,indent=4,sort_keys=True)),
                            'Saving to json "%s"' % outFile
                    )
                    warningBooks=len(list(filter(lambda bs: '_warnings' in bs,bilistStructure['books'])))
                    warningAuthors=len(list(filter(lambda bs: '_warnings' in bs,bilistStructure['authors'])))
                    if warningBooks or warningAuthors:
                        print('Authors with warning: %s. Go and fix them.' % warningAuthors)
                        print('Books with warning: %s. Go and fix them.' % warningBooks)
                    print('Finished.')
                else:
                    print('Operation aborted.')
                    print(_helpMsg)
            else:
                print('At least three cmdline args are required.')
                print(_helpMsg)
        elif sys.argv[1]=='-i':
            print('-i or INSERT mode.')
            if len(sys.argv)>3:
                inFile=sys.argv[2]
                importingUser=sys.argv[3]
                if clearToImport(inFile,importingUser):
                    actingUser=logDo(lambda:dbGetUser(importingUser),'Checking for user validity')
                    if actingUser is not None:
                        if actingUser.canedit:
                            db=logDo(lambda: dbGetDatabase(),'Opening DB')
                            inFileHandle=open(inFile)
                            result=logDo(lambda: import_from_bilist_json(inFileHandle,actingUser,db), 'Importing from "%s"' % inFile)
                            print('Insertion log:')
                            for k,v in sorted(result.items()):
                                print('  # %s' % k)
                                for k2,v2 in sorted(v.items()):
                                    if len(v2):
                                        print('    * %s' % k2)
                                        for it,lst in sorted(v2.items()):
                                            print('      - "%s"' % it)
                                            for msg in lst:
                                                print('        %s' % msg)
                            db.commit()
                            print('Finished.')
                        else:
                            print('User <%s> has no write privileges on the DB. Operation failed' % importingUser)
                    else:
                        print('User <%s> not recognised in the DB. Operation failed' % importingUser)
                else:
                    print('Operation aborted.')
            else:
                print('At least three cmdline args are required.')
                print(_helpMsg)
        else:
            print('No valid operation provided. Quitting.')
            print(_helpMsg)
    else:
        print('No valid operation provided. Quitting.')
        print(_helpMsg)
