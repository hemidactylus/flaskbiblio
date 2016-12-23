#/usr/bin/env python
from __future__ import print_function

import os
import sys
from operator import itemgetter
import csv, re
import json
from datetime import datetime
from collections import Counter

import env
from config import DATETIME_STR_FORMAT
from app.utils.interactive import ask_for_confirmation, logDo
from db_testvalues import _testvalues
from app.database.dbtools import    (
                                        dbGetDatabase,
                                        dbGetUser,
                                        dbAddAuthor,
                                        dbAddReplaceBook,
                                    )
from app.database.models import (
                                    tableToModel, 
                                    Book,
                                )

from app.utils.ascii_checks import  (
                                        validCharacters,
                                        translatedCharacters,
                                        ascifiiString
                                    )
from app.utils.string_vectorizer import (
                                            makeIntoVector,
                                            scalProd
                                        )

# tools
langFinder=re.compile('\[([A-Z]{2,2})\]')
abbreviationFinder=re.compile('[A-Za-z]{1,3}\.')

importingUser='Stefano'

# validity w.r.t. test values
validLanguages=[lang['tag'] for lang in _testvalues['language']]
validBooktypes=[booktype['tag'] for booktype in _testvalues['booktype']]
if len(list(filter(lambda u: u['name']==importingUser,_testvalues['user'])))==0:
    raise ValueError('User %s not found.' % importingUser)

# used to make strings into a vector
MIN_COSINE_ALERT=0.9 # to raise a similarity error

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

def parseBookLine(csvLine):
    '''
        csvLine[0] is the line number, csvLine[1] the actual list of entries
    '''
    return plainifyStruct({
        'linenumber': str(csvLine[0]+1),
        'author': csvLine[1][0],
        'title': csvLine[1][1],
        'languages': csvLine[1][2],
        'inhouse': csvLine[1][3],
        'notes': csvLine[1][4],
    })

def plainifyStruct(inStruct):
    return {k:ascifiiString(v) for k,v in inStruct.items()}

def addWarningToStruct(bStruct,wField,wContents):
    '''
        adds a field to the warning metadata for the book
    '''
    if '_warnings' not in bStruct:
        bStruct['_warnings']={}
    if wField not in bStruct['_warnings']:
        bStruct['_warnings'][wField]=[]
    bStruct['_warnings'][wField].append(wContents)

def parseAuthor(auString,comma=True):
    '''
        Author strings are usually in the form 'Lastname, first_name_and_other'.
        Sometimes a single string is available, in which case it is taken to be
        lastname (with empty firstname)

        Also some special cases are taken care of
    '''
    if auString=='Fruttero E Lucentini':
        return [{'lastname': 'Fruttero','firstname':''},{'lastname': 'Lucentini', 'firstname':''}]
    if auString=='Fruttero e Fruttero':
        return [{'lastname': 'Fruttero','firstname':''}]
    else:
        if comma:
            # form "Saramago, Jose"
            parts=[pt.strip() for pt in auString.split(',')]
            return [{'firstname': ', '.join(parts[1:]), 'lastname': parts[0]}]
        else:
            # form "Jose Saramago"
            parts=[pt.strip() for pt in auString.split(' ')]
            return [{'firstname': ' '.join(parts[:-1]), 'lastname': parts[-1]}]

def guessAuthors(auRest):
    '''
        eats something like 'John Rivera' or 'J. E. Moretti e Stan Lowe'
        and tries to extract an array of well-formed authors
    '''
    auPieces=[pc.strip() for bigpart in auRest.split(' e ') for pc in bigpart.split(',')]
    authors=list(filter(lambda p: p is not None,[au for pc in auPieces for au in parseAuthor(pc,comma=False)]))
    return authors

def normalizeParsedLine(pLine,iUser,iDate):
    '''
        converts a base structure into a proper structure, modulo references among tables.
        Returns a structure encoding errors/warnings as well as the result
    '''
    bookStructure={
        'title':         None,                  # HANDLED
        'authors':       [],                    # HANDLED
        'booktype':      None,                  # HANDLED
        'inhouse':       None,                  # HANDLED
        'notes':         '',                    # HANDLED
        'inhousenotes':  None,                  # HANDLED
        'languages':     [],                    # HANDLED
        'lasteditor':    iUser,                 # HANDLED
        'lasteditdate':  iDate,                 # HANDLED
        '_linenumber':   pLine['linenumber'],   # HANDLED
    }
    # languages
    _langlist=langFinder.findall(pLine['languages'])
    for _la in _langlist:
        if _la.upper() not in validLanguages:
            addWarningToStruct(bookStructure,'languages',_la.upper())
        else:
            bookStructure['languages'].append(_la.upper())
    # inhouse
    if 'M' in pLine['inhouse'].upper():
        bookStructure['inhouse']=True
    elif 'V' in pLine['inhouse'].upper():
        bookStructure['inhouse']=False
    else:
        addWarningToStruct(bookStructure,'inhouse',pLine['inhouse'])
    # inhousenotes
    if bookStructure['inhouse']!=True:
        if pLine['notes'].strip()=='':
            addWarningToStruct(bookStructure,'inhousenotes',pLine['notes'])
        else:
            bookStructure['inhousenotes']=pLine['notes']
    else:
        if pLine['notes'].strip()!='':
            addWarningToStruct(bookStructure,'inhousenotes',pLine['notes'])
        else:
            bookStructure['inhousenotes']=pLine['notes']
    # booktype from special authors
    _author=pLine['author']
    if _author=='AAVV':
        _author=None
        bookStructure['booktype']='OTH'
        addWarningToStruct(bookStructure,'booktype','OTH*AAVV')
    elif _author=='DIZ':
        _author=None
        bookStructure['booktype']='DIZ'
    elif _author=='NN':
        _author=None
        bookStructure['booktype']='OTH'
        addWarningToStruct(bookStructure,'booktype','OTH*NN')
    else:
        bookStructure['booktype']='FIC'
    if bookStructure['booktype'] not in validBooktypes:
        addWarningToStruct(bookstructure,'booktype',bookStructure['booktype'])
    # notes/title: the former as extracted from the second title
    obpos=pLine['title'].find('(')
    cbpos=pLine['title'].find(')')
    if obpos>0 and cbpos>obpos:
        # there's a proper open-and-closed bracket in the title
        bookStructure['notes']=pLine['title'][obpos+1:cbpos].strip()
        bookStructure['title']=pLine['title'][:obpos].strip()+pLine['title'][cbpos+1:].strip()
        addWarningToStruct(bookStructure,'notes-title',pLine['title'])
    else:
        bookStructure['title']=pLine['title']
    # author(s)
    if _author is not None:
        bookStructure['authors']+=parseAuthor(_author)
    if len(bookStructure['notes'])>0:
        # there might be some more authors hidden here
        if 'con ' in bookStructure['notes']:
            conpos=bookStructure['notes'].lower().find('con ')
            if conpos>=0:
                notesRest=(bookStructure['notes']+' ')[conpos+len('con '):]
                bookStructure['authors']+=guessAuthors(notesRest)
        # 
        addWarningToStruct(bookStructure,'authors-from-notes',bookStructure['notes'])
    # done.
    return bookStructure

def collectCharacters(pLines):
    '''
        scans the standard fields of parsed-line list and collects
        all characters appearing at least once in some text field,
        this is for the purpose of cleaning input strings
    '''
    return set([char
                    for pLine in pLines
                    for v in pLine.values()
                    for char in list(v) if isinstance(v,str) or isinstance(v,unicode)])

def read_and_parse_csv(inFile):
    '''
        main driver of the extraction. Handles the top-level operations
    '''
    # 1. make valid lines into base structures
    parsedLines=list(map(parseBookLine,[li for li in enumerate(csv.reader(open(inFile)))][1:]))
    # 1b. must check for non-ascii chars here already and if necessary treat the various warnings
    passingCharacters=set(list(validCharacters)) | set(translatedCharacters.keys())
    untreatedCharSet=list(filter(lambda c: c not in passingCharacters, collectCharacters(parsedLines)))
    if len(untreatedCharSet)>0:
        raise ValueError('Some untreated special chars to check: "%s"' % ''.join(sorted(list(untreatedCharSet))))
    # 2. apply a normalisation function to each line
    importDate=datetime.now().strftime(DATETIME_STR_FORMAT)
    normalizer=lambda pL: normalizeParsedLine(pL,importingUser,importDate)
    bookList=list(map(normalizer,parsedLines))

    # 3. format the result as a large json-encoded  and return it along with some other info
    return {
        'booklist': bookList,
        'count': len(bookList),
        'json': json.dumps(bookList,indent=4),
    }

def isOnlyAbbreviations(aName):
    '''
        Raises an error if names with only abbreviations are found.

        Ok ''
        Ok 'James P.'
        Ok 'A'

        NO 'J.'
        NO 'A. F.'
    '''
    def _isNotAbbrev(piece):
        return len(abbreviationFinder.findall(piece))==0
    oktoks=list(filter(_isNotAbbrev,aName.split(' ')))
    return len(oktoks)==0

def makeAuthorIntoVector(lName,fName):
    '''
        generates two unitary-norm vectors, one from lName and one from the combination
    '''
    return {
        '_normLast': makeIntoVector(lName),
        '_normFull': makeIntoVector('%s%s' % (lName,fName))
    }

def insert_author_to_list(newA,aList,linenumber=None):
    '''
        checks for duplicates against firstname and lastname
        and returns True if duplicate found
    '''
    for pAu in aList:
        if all([pAu[fld].lower()==newA[fld].lower() for fld in ['firstname','lastname']]):
            if linenumber:
                pAu['_books'].append(linenumber)
            return True
    return False

def extract_author_list(inFile):
    '''
        this opens a json with the book list and extracts all authors found there.
        It raises warnings for no-lastname authors and for authors suspiciously similar (but not identical)
        to already-inserted authors.
    '''
    authorList=[]
    bookList=json.load(open(inFile))
    for bStr in bookList:
        for au in bStr['authors']:
            # handle insertion of author 'au' to the full list
            # found=False
            found=insert_author_to_list(au,authorList,bStr['_linenumber'])
            if not found:
                au.update(makeAuthorIntoVector(au['lastname'],au['firstname']))
                au['_books']=[bStr['_linenumber']]
                # check if the new author is too similar to any existing one
                scalsL=[]
                scalsF=[]
                def _copyAu(au):
                    return {'firstname': au['firstname'], 'lastname': au['lastname']}
                for pAu in authorList:
                    scalsL.append((scalProd(pAu['_normLast'],au['_normLast']),_copyAu(pAu)))
                    scalsF.append((scalProd(pAu['_normFull'],au['_normFull']),_copyAu(pAu)))
                scalsL=list(filter(lambda t: t[0]>=MIN_COSINE_ALERT,sorted(scalsL,key=itemgetter(0),reverse=True)))
                scalsF=list(filter(lambda t: t[0]>=MIN_COSINE_ALERT,sorted(scalsF,key=itemgetter(0),reverse=True)))
                if (len(scalsL)+len(scalsF)) > 0:
                    finalWarnings=[]
                    for _,wAu in scalsL+scalsF:
                        if not insert_author_to_list(wAu,finalWarnings):
                            finalWarnings.append(_copyAu(wAu))
                    for wau in finalWarnings:
                        addWarningToStruct(au,'similarity',wau)
                # check if the first name is only punctuated abbreviations
                if isOnlyAbbreviations(au['firstname']):
                    addWarningToStruct(au,'abbreviations',au['firstname'])
                #
                authorList.append(au)
    # remove the norm information
    for au in authorList:
        del au['_normLast']
        del au['_normFull']

    return {
        'authorlist': authorList,
        'json': json.dumps(authorList,indent=4),
        'count': len(authorList),
    }

def erase_db_table(db,tableName):
    '''
        Deletes *all* records from a table of the given DB
    '''
    tObject=tableToModel[tableName]
    tObject.db=db
    idList=[obj.id for obj in tObject.manager(db).all()]
    deleteds=[]
    for oId in idList:
        tObject.manager(db).get(oId).delete()
        deleteds.append(oId)
    db.commit()
    return {'deleted_%s' % tableName: deleteds}

def insert_authors_from_json(inFile):
    '''
        Reads an author list off a json file
        and inserts all authors to DB.
        Returns a dictionary from the 2-uple (lastname,firstname) to the database ID
    '''
    auList=json.load(open(inFile))
    report={}
    for nAu in auList:
        # insert new author
        nObj=dbAddAuthor(nAu['firstname'],nAu['lastname'])
        # register the map
        report[(nAu['lastname'],nAu['firstname'])]=nObj.id
    return report

def insert_books_from_json(inFile,authorMap):
    '''
        Given a map (lastname,firstname)->authorId, book insertions are done.
        Returned is a list of IDs in the insertion order.
    '''
    fieldsToKill=['_linenumber','_warnings']
    boList=json.load(open(inFile))
    report=[]
    for nBo in boList:
        # resolve references, adjust fields
        nBo['lasteditor']=dbGetUser(nBo['lasteditor']).id
        _auList=','.join([str(authorMap[(au['lastname'],au['firstname'])]) for au in nBo['authors']])
        nBo['authors']=_auList
        nBo['lasteditdate']=datetime.strptime(nBo['lasteditdate'],DATETIME_STR_FORMAT)
        nBo['languages']=','.join(nBo['languages'])
        nBo['id']=None
        #
        for fld in fieldsToKill:
            if fld in nBo:
                del nBo[fld]
        #
        newBookObject=Book(**nBo)
        #
        nBookReturned=dbAddReplaceBook(newBookObject)
        report.append(nBookReturned.id)
    return report

if __name__=='__main__':

    # usage: "-i <infile.csv> <bookoutfile.json>" to import
    # and later "-a <bookoutfile.json> <authoroutfile.json>" to make author list

    _helpMsg='''Usage: python script.py ARGS.
    Args can specify the import mode:
        (1) -e input.csv outputBooks.json
            EXTRACT: from csv to book list
        (2) -a inputBooks.csv outputAuthors.json
            AUTHORLIST: check and normalize the authors found throughout books
        (3) -i inputBooks.json inputAuthors.jsos
            INSERT: read books/authors's jsons and insert data into the DB
'''

    # a valid csv file must be provided
    if len(sys.argv)>1:
        if sys.argv[1]=='-e':
            print('-e or EXTRACT mode.')
            if len(sys.argv)>3:
                inFile=sys.argv[2]
                outFile=sys.argv[3]
                if clearToExtract(inFile,outFile):
                    parsedCSV=logDo(lambda: read_and_parse_csv(inFile),'Reading from "%s"' % inFile)
                    logDo(lambda: open(outFile,'w').write('%s\n' % parsedCSV['json']),'Saving to json "%s"' % outFile)
                    # stats
                    warningBooks=len(list(filter(lambda bs: '_warnings' in bs,parsedCSV['booklist'])))
                    if warningBooks:
                        print('Books with warning: %s. Go and fix them.' % warningBooks)
                    print('Finished.')
                else:
                    print('Operation aborted.')
            else:
                print('Two cmdline args are required: inputCSV, outputBookJSON.')
                print(_helpMsg)
        elif sys.argv[1]=='-a':
            print('-a or AUTHORLIST mode.')
            if len(sys.argv)>3:
                inFile=sys.argv[2]
                outFile=sys.argv[3]
                if clearToExtract(inFile,outFile):
                    authorList=logDo(lambda: extract_author_list(inFile),'Extracting authors from "%s"' % inFile)
                    logDo(lambda: open(outFile,'w').write('%s\n' % authorList['json']),'Saving to json "%s"' % outFile)
                    # stats
                    warningAuthors=len(list(filter(lambda bs: '_warnings' in bs,authorList['authorlist'])))
                    if warningAuthors:
                        print('Authors with warning: %s. Go and check them.' % warningAuthors)
                        print('Similarity:')
                        # clashing authors explicit print
                        def _auformat(au):
                            return '%-40s' % ('%s, %s' % (au['lastname'],au['firstname']))
                        for au in authorList['authorlist']:
                            if '_warnings' in au and 'similarity' in au['_warnings']:
                                print('    %s' % _auformat(au))
                                for wau in au['_warnings']['similarity']:
                                    print('        %s' % _auformat(wau))
                        print('Shortname:')
                        for au in authorList['authorlist']:
                            if '_warnings' in au and 'abbreviations' in au['_warnings']:
                                print('    %s' % _auformat(au))
                    print('Finished.')
                else:
                    print('Operation aborted.')
                    print(_helpMsg)
            else:
                print('Two cmdline args are required: inputBookJSON, outputAuthorsJSON.')
        elif sys.argv[1]=='-i':
            print('-i or INSERT mode.')

            if len(sys.argv)>3:
                bookFile=sys.argv[2]
                authorFile=sys.argv[3]
                if clearToImport(bookFile,authorFile):
                    db=logDo(lambda: dbGetDatabase(),'Opening DB')
                    operationLog={}
                    for tableToDelete in ['author','book']:
                        operationLog.update(logDo(lambda: erase_db_table(db,tableToDelete),
                                                  'Erasing table "%s"' % tableToDelete))
                    deletionLog=', '.join(map(lambda kv: '%s[%i]' % (kv[0],len(kv[1])),operationLog.items()))
                    print('Deletions: %s' % deletionLog)
                    authorToId=logDo(lambda: insert_authors_from_json(authorFile), 'Inserting authors from "%s"' % authorFile)
                    bookInsertLog=logDo(lambda: insert_books_from_json(bookFile,authorToId),'Inserting books from "%s"' % bookFile)
                    print('Insertions: %i authors, %i books.' % tuple(map(len,[authorToId,bookInsertLog])))
                    print('Finished.')
                else:
                    print('Operation aborted.')
            else:
                print('Two cmdline args are required: inputBookJSON, inputAuthorsJSON.')
                print(_helpMsg)
        else:
            print('No valid operation provided. Quitting.')
            print(_helpMsg)
    else:
        print('No valid operation provided. Quitting.')
        print(_helpMsg)