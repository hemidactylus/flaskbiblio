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
                                        dbAddReplaceAuthor,
                                        dbAddReplaceBook,
                                        dbDeleteBook,
                                        dbDeleteAuthor,
                                    )

# import tools are all in this subpackage:
from app.importlibrary.importlibrary import read_and_parse_csv

def clearToExtract(inFile,outFile):
    '''
        Asks for confirmation of the extraction CSV -> structure in plain text
    '''
    # if it does exist, erase it
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

def clearToImport(inFile1,inFile2):
    '''
        Asks for confirmation of the insertion into DB
    '''
    # if it does exist, erase it
    if os.path.isfile(inFile1) and os.path.isfile(inFile2):
        insertPrompt='Are you sure you want to overwrite the DB with data from "%s" and "%s"?'
        if ask_for_confirmation(insertPrompt % (inFile1,inFile2),['y','yes','yeah']):
            return True
        else:
            return False
    else:
        print('Source files "%s" and "%s" must exist.' % (inFile1, inFile2))
        return False


if __name__=='__main__':

    _helpMsg='''Usage: python script.py ARGS.
    Args can specify the import mode:
        (1) -e input.csv outputBooks.json [-h for skipping a one-line header]
            EXTRACT: from csv to book list as 'userName'
        (2) -a inputBooks.csv outputAuthors.json userName
            AUTHORLIST: check and normalize the authors found throughout books as 'userName'
        (3) -i inputBooks.json inputAuthors.json userName
            INSERT: read books/authors's jsons and insert data into the DB as 'userName'
'''

    # a valid csv file must be provided
    if len(sys.argv)>1:
        if sys.argv[1]=='-e':
            print('-e or EXTRACT mode.')
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
                    # stats
                    # warningBooks=len(list(filter(lambda bs: '_warnings' in bs,parsedCSV['booklist'])))
                    # if warningBooks:
                    #     print('Books with warning: %s. Go and fix them.' % warningBooks)
                    #     print('Similarity:')
                    #     # clashing books explicit print
                    #     def _boFormatMaster(bo,addendum):
                    #         titString=bo['title'] if len(bo['title'])<50 else '%s ...' % bo['title'][:46]
                    #         return '%-50s %s' % (titString,addendum) if addendum else '%-50s' % titString
                    #     _boformatPlain=lambda bo: _boFormatMaster(bo,None)
                    #     _boformatPlus=lambda bo: _boFormatMaster(bo,'%4.2f' % bo['_norm'])
                    #     for bo in parsedCSV['booklist']:
                    #         if '_warnings' in bo and 'similarity' in bo['_warnings']:
                    #             print('    %s' % _boformatPlain(bo))
                    #             for wbo in bo['_warnings']['similarity']:
                    #                 print('        %s' % _boformatPlus(wbo))
                    print('Finished.')
                else:
                    print('Operation aborted.')
            else:
                print('At least three cmdline args are required.')
                print(_helpMsg)
        elif sys.argv[1]=='-a':
            print('-a or AUTHORLIST mode.')
            if len(sys.argv)>4:
                inFile=sys.argv[2]
                outFile=sys.argv[3]
                importingUser=sys.argv[4]
                if clearToExtract(inFile,outFile):
                    authorList=logDo(lambda: extract_author_list(inFile),'Extracting authors from "%s"' % inFile)
                    logDo(lambda: open(outFile,'w').write('%s\n' % authorList['json']),'Saving to json "%s"' % outFile)
                    # stats
                    warningAuthors=len(list(filter(lambda bs: '_warnings' in bs,authorList['authorlist'])))
                    if warningAuthors:
                        print('Authors with warning: %s. Go and check them.' % warningAuthors)
                        print('Similarity:')
                        # clashing authors explicit print
                        def _auFormatMaster(au,addendum):
                            _auString='%s, %s' % (au['lastname'],au['firstname'])
                            auString=_auString if len(_auString)<40 else '%s ...' % _auString[:36]
                            return '%-40s %s' % (auString,addendum) if addendum else '%-40s' % auString
                        _auFormatBase=lambda au: _auFormatMaster(au,None)
                        _auFormatPlus=lambda au: _auFormatMaster(au,'(%4.2f)' % au['_norm'])
                        for au in authorList['authorlist']:
                            if '_warnings' in au and 'similarity' in au['_warnings']:
                                print('    %s' % _auFormatBase(au))
                                for wau in au['_warnings']['similarity']:
                                    print('        %s' % _auFormatPlus(wau))
                        print('Shortname:')
                        for au in authorList['authorlist']:
                            if '_warnings' in au and 'abbreviations' in au['_warnings']:
                                print('    %s' % _auFormatBase(au))
                    print('Finished.')
                else:
                    print('Operation aborted.')
                    print(_helpMsg)
            else:
                print('Three cmdline args are required: inputBookJSON, outputAuthorsJSON, userName.')
        elif sys.argv[1]=='-i':
            print('-i or INSERT mode.')

            if len(sys.argv)>4:
                bookFile=sys.argv[2]
                authorFile=sys.argv[3]
                importingUser=sys.argv[4]
                if clearToImport(bookFile,authorFile):
                    testUser=logDo(lambda:dbGetUser(importingUser),'Checking for user validity')
                    if testUser is not None:
                        db=logDo(lambda: dbGetDatabase(),'Opening DB')
                        operationLog={}
                        for tableToDelete in ['author','book']:
                            operationLog.update(logDo(lambda: erase_db_table(db,tableToDelete),
                                                      'Erasing table "%s"' % tableToDelete))
                        deletionLog=', '.join(map(lambda kv: '%s[%i]' % (kv[0],len(kv[1])),operationLog.items()))
                        print('Deletions: %s' % deletionLog)
                        authorToId=logDo(lambda: insert_authors_from_json(authorFile,db), 'Inserting authors from "%s"' % authorFile)
                        bookInsertLog=logDo(lambda: insert_books_from_json(bookFile,authorToId,importingUser,db),'Inserting books from "%s"' % bookFile)
                        print('Insertions: %i authors, %i books.' % tuple(map(len,[authorToId,bookInsertLog])))
                        print('Finished.')
                    else:
                        print('User <%s> not recognised. Operation failed' % importingUser)
                else:
                    print('Operation aborted.')
            else:
                print('Three cmdline args are required: inputBookJSON, inputAuthorsJSON, userName.')
                print(_helpMsg)
        else:
            print('No valid operation provided. Quitting.')
            print(_helpMsg)
    else:
        print('No valid operation provided. Quitting.')
        print(_helpMsg)
