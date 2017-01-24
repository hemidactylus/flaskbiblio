'''
    importlibrary.py : functions and utilities to deal with all steps of the import process
'''

import csv, re
from operator import itemgetter
from datetime import datetime
from collections import Counter
import json

from app import languagesDict, booktypesDict
from config import DATETIME_STR_FORMAT, SIMILAR_AUTHOR_THRESHOLD, SIMILAR_BOOK_THRESHOLD
from app.database.models import (
                                    tableToModel,
                                    Book,
                                    Author,
                                )
from app.database.dbtools import    (
                                        dbGetAll,
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

def process_book_list(inFileHandle):
    '''
        main driver of the booklist-to-structuredlists conversion.

        Handles the author extraction from books,
        the validation of authors with warnings,
        the generation of the annotated book list
    '''
    # db-listings of authors and books are needed at this point
    def _auObjCopy(auO):
        return {
            'firstname': auO.firstname,
            'lastname': auO.lastname,
            'notes': auO.notes,
        }
    authorFromDB=[_auObjCopy(au) for au in list(dbGetAll('author'))]
    #
    inputContents=inFileHandle.read()
    auList=extract_author_list(inputContents,authorFromDB)
    return auList

def read_and_parse_csv(inFileHandle,skipHeader=False):
    '''
        main driver of the csv-to-json conversion.

        Handles the top-level operations and returns a dict {'books': [list of book object]}

    '''
    # 1. make valid lines into base structures
    parsedLines=list(
        map(
            parseBookLine,
            [
                li for li in enumerate(csv.reader(inFileHandle))
            ][(1 if skipHeader else 0):]
        )
    )
    # 1b. must check for non-ascii chars here already and if necessary treat the various warnings
    passingCharacters=set(list(validCharacters)) | set(translatedCharacters.keys())
    untreatedCharSet=list(filter(lambda c: c not in passingCharacters, collectCharacters(parsedLines)))
    if len(untreatedCharSet)>0:
        raise ValueError('Some untreated special chars to check: "%s"' % ''.join(sorted(list(untreatedCharSet))))
    # 2. apply a normalisation function to each line
    importDate=datetime.now().strftime(DATETIME_STR_FORMAT)
    normalizer=lambda pL,listSoFar: normalizeParsedLine(pL,listSoFar)
    # the book list is built incrementally so that similarities are detectable
    bookList=[]
    for pLi in parsedLines:
        bookList.append(normalizer(pLi,bookList))
    # clean out similarity-vector fields
    for qBo in bookList:
        if '_normTitle' in qBo:
            del qBo['_normTitle']

    # 3. encapsulate the result and return it
    return {
        'books': bookList,
    }

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

def guessKVFromDict(kvDict):
    '''
        Tries to match with either the key or the value of a dict
        Returns the key or None if nothing succeeds
    '''
    def _guesser(lString,kvDict=kvDict):
        if lString.upper() in kvDict:
            return lString.upper()
        else:
            matchingNames=[lK for lK,lN in kvDict.items() if lString.upper()==lN.upper()]
            if len(matchingNames)==1:
                return matchingNames[0]
            else:
                return None
    return _guesser

# special cases of the above
guessLanguage=guessKVFromDict(languagesDict)
guessBooktype=guessKVFromDict(booktypesDict)

def normalizeParsedLine(pLine,bListSoFar):
    '''
        converts a base structure into a proper structure, modulo references among tables.
        Returns a structure encoding errors/warnings as well as the result.

        Requires the already-done-lines list to check for similarities
    '''
    bookStructure={
        'title':         None,
        'authors':       [],
        'booktype':      None,
        'inhouse':       None,
        'notes':         '',
        'inhousenotes':  None,
        'languages':     [],
        '_linenumber':   pLine['linenumber'],
    }
    # languages
    _langlist=langFinder.findall(pLine['languages'])
    for _la in _langlist:
        _guessedLang=guessLanguage(_la)
        if _guessedLang is None:
            addWarningToStruct(bookStructure,'languages',_la)
        else:
            bookStructure['languages'].append(languagesDict[_guessedLang].name)
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
    _bt=guessBooktype(bookStructure['booktype'])
    if _bt is None:
        addWarningToStruct(bookstructure,'booktype',bookStructure['booktype'])
    else:
        bookStructure['booktype']=booktypesDict[_bt].name
    # notes/title: the former as extracted from the second title
    obpos=pLine['title'].find('(')
    cbpos=pLine['title'].find(')')
    if obpos>0 and cbpos>obpos:
        # there's a proper open-and-closed bracket in the title
        bookStructure['notes']=pLine['title'][obpos+1:cbpos].strip()
        bookStructure['title']=pLine['title'][:obpos].strip()+pLine['title'][cbpos+1:].strip()
        addWarningToStruct(bookStructure,'original_title',pLine['title'])
    else:
        bookStructure['title']=pLine['title']
    # # similarity checks:
    # bookStructure.update(makeBookIntoVector(bookStructure['title']))
    # scalsT=[]
    # def _copyBo(bo):
    #     return {
    #         'title': bo['title'],
    #         '_linenumber': bo['_linenumber'],
    #     }
    # for pBo in bListSoFar:
    #     scalsT.append((scalProd(pBo['_normTitle'],bookStructure['_normTitle']),_copyBo(pBo)))
    # scalsT=list(filter(lambda t: t[0]>=SIMILAR_BOOK_THRESHOLD,sorted(scalsT,key=itemgetter(0),reverse=True)))
    # if len(scalsT) > 0:
    #     finalWarnings=[]
    #     for normVal,wBo in scalsT:
    #         boToInsert=_copyBo(wBo)
    #         boToInsert['_norm']=normVal
    #         finalWarnings.append(boToInsert)
    #     for wbo in finalWarnings:
    #         addWarningToStruct(bookStructure,'similarity',wbo)
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
        addWarningToStruct(bookStructure,'notes_may_contain_authors',bookStructure['notes'])
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
        '_normFull': makeIntoVector('%s %s' % (lName,fName))
    }

def makeBookIntoVector(bTitle):
    '''
        generates a unitary-norm vector from the book title
    '''
    return {
        '_normTitle': makeIntoVector(bTitle),
    }

def insert_author_to_list(newA,aList,preexistingList,linenumber=None):
    '''
        checks for duplicates against firstname and lastname
        and returns True if duplicate found
    '''
    for pAu in aList:
        if all([pAu[fld].lower()==newA[fld].lower() for fld in ['firstname','lastname']]):
            if linenumber:
                pAu['_books'].append(linenumber)
            return True
    for pAu in preexistingList:
        if all([pAu[fld].lower()==newA[fld].lower() for fld in ['firstname','lastname']]):
            return True
    return False

def extract_author_list(inputContents, preexistingAuthors):
    '''
        this opens a json with the book list and extracts all authors found there.
        It raises warnings for no-lastname authors and for authors suspiciously similar (but not identical)
        to already-inserted authors.

        'preexistingAuthors' is a list of Author objects retrieved from DB: they are also to be checked
        (both for duplicates and similarity checks)

    '''
    def _copyAu(au):
        return {    
            'firstname': au['firstname'],
            'lastname': au['lastname'],
            'notes': au['notes'],
        }
    # parse the pre-existing authors into a standard structure
    preexistingList=[
        _copyAu(au)
        for au in preexistingAuthors
    ]
    for au in preexistingList:
        au.update(makeAuthorIntoVector(au['lastname'],au['firstname']))
    #
    authorList=[]
    bookList=json.loads(inputContents)
    for bStr in bookList['books']:
        for au in bStr['authors']:
            au['notes']=au.get('notes','')
            # handle insertion of author 'au' to the full list
            # found=False
            found=insert_author_to_list(au,authorList,preexistingList,bStr['_linenumber'])
            if not found:
                au.update(makeAuthorIntoVector(au['lastname'],au['firstname']))
                au['_books']=[bStr['_linenumber']]
                # check if the new author is too similar to any existing one
                scalsA=[]
                for origin,aulist in zip(['new','present'],[authorList,preexistingList]):
                    for pAu in aulist:
                        scalsA.append((
                            max(
                                scalProd(pAu['_normLast'],au['_normLast']),
                                scalProd(pAu['_normFull'],au['_normFull']),
                            ),
                            _copyAu(pAu),
                            origin,
                        ))
                scalsA=list(filter(lambda t: t[0]>=SIMILAR_AUTHOR_THRESHOLD,sorted(scalsA,key=itemgetter(0),reverse=True)))
                if len(scalsA) > 0:
                    finalWarnings=[]
                    for normVal,wAu,wOrigin in scalsA:
                        if not insert_author_to_list(wAu,finalWarnings,[]):
                            auToInsert=_copyAu(wAu)
                            auToInsert['_norm']=normVal
                            auToInsert['_origin']=wOrigin
                            finalWarnings.append(auToInsert)
                    for wau in finalWarnings:
                        addWarningToStruct(au,'similarity',wau)
                # check if the first name is only punctuated abbreviations
                if isOnlyAbbreviations(au['firstname']):
                    addWarningToStruct(au,'abbreviations',au['firstname'])
                    au['notes']='First name abbreviated'
                #
                authorList.append(au)
    # remove the norm information
    for au in authorList:
        del au['_normLast']
        del au['_normFull']

    return {
        'authors': authorList,
    }

# def erase_db_table(db,tableName):
#     '''
#         Deletes *all* records from a table of the given DB
#     '''
#     tObject=tableToModel[tableName]
#     tObject.db=db
#     idList=[obj.id for obj in tObject.manager(db).all()]
#     deleteds=[]
#     for oId in idList:
#         if tableName=='book':
#             dbDeleteBook(oId,db=db)
#         elif tableName=='author':
#             dbDeleteAuthor(oId,db=db)
#         deleteds.append(oId)
#     db.commit()
#     return {'deleted_%s' % tableName: deleteds}

def insert_authors_from_json(inFile,db):
    '''
        Reads an author list off a json file
        and inserts all authors to DB.
        Returns a dictionary from the 2-uple (lastname,firstname) to the database ID
    '''
    auList=json.load(open(inFile))
    report={}
    for nAu in auList:
        # insert new author
        newAuthor=Author(id=None,firstname=nAu['firstname'],lastname=nAu['lastname'],notes=nAu.get('notes',''))
        status,nObj=dbAddReplaceAuthor(newAuthor,db=db)
        # register the map
        if status:
            report[(nAu['lastname'],nAu['firstname'])]=nObj.id
        else:
            raise ValueError()
    db.commit()
    return report

def insert_books_from_json(inFile,authorMap,importingUser,db):
    '''
        Given a map (lastname,firstname)->authorId, book insertions are done.
        Returned is a list of IDs in the insertion order.
    '''
    fieldsToKill=['_linenumber','_warnings']
    boList=json.load(open(inFile))
    report=[]
    for nBo in boList:
        # resolve references, adjust fields
        insertorUser=dbGetUser(importingUser)
        nBo['lasteditor']=insertorUser.id
        nBo['house']=insertorUser.house
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
        status,nBookReturned=dbAddReplaceBook(newBookObject,db=db)
        if status:
            report.append(nBookReturned.id)
        else:
            raise ValueError('Could not insert book "%s" (error: %s' % (newBookObject.title,nBookReturned))
    db.commit()
    return report
