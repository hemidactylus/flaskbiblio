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

# tools
langFinder=re.compile('\[([A-Z]{2,2})\]')
importingUser='Stefano'

# validity w.r.t. test values
validLanguages=[lang['tag'] for lang in _testvalues['language']]
validBooktypes=[booktype['tag'] for booktype in _testvalues['booktype']]
if len(list(filter(lambda u: u['name']==importingUser,_testvalues['user'])))==0:
    raise ValueError('User %s not found.' % importingUser)
validCharacters="\" !&'()+,-./0123456789:;?ABCDEFGHIJKLMNOPQRSTUVWXYZ[]abcdefghijklmnopqrstuvwxyz"
translatedCharacters={
    u'Á': 'A',
    u'á': 'a',
    u'ã': 'a',
    u'ä': 'ae',
    u'æ': 'ae',
    u'ç': 'c',
    u'è': 'e',
    u'é': 'e',
    u'í': 'i',
    u'ò': 'o',
    u'ó': 'o',
    u'õ': 'o',
    u'ö': 'oe',
    u'ù': 'u',
    u'ú': 'u',
    u'ü': 'ue',
    u'à': 'a',
}
# used to make strings into a vector
vectorCharacters=list(map(chr,range(ord('A'),ord('Z')+1)))
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
    return {k:normalizeCharacters(v) for k,v in inStruct.items()}

def normalizeCharacters(inString):
    '''
        parses away all non-ascii characters
    '''
    resString=inString
    for k,v in translatedCharacters.items():
        resString=resString.replace(k,v)
    return resString

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
    untreatedCharSet=list(filter(lambda c: c not in validCharacters and c not in translatedCharacters.keys(),collectCharacters(parsedLines)))
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

def makeIntoVector(qString):
    '''
        makes a string into a unitary vectors.
        No non-alphabetic, no case-sensitivity
    '''
    lCnt=Counter([let for let in list(qString.upper()) if let in vectorCharacters])
    lNorm=sum(map(lambda x: x**2.0,lCnt.values()))**0.5
    if lNorm>0:
        return {k: v/lNorm for k,v in lCnt.items()}
    else:
        return dict(lCnt)

def makeAuthorIntoVector(lName,fName):
    '''
        generates two unitary-norm vectors, one from lName and one from the combination
    '''
    return {
        '_normLast': makeIntoVector(lName),
        '_normFull': makeIntoVector('%s%s' % (lName,fName))
    }

def scalProd(di1,di2):
    '''
        scalar product of two vectors
    '''
    return sum([v*di2[k] for k,v in di1.items() if k in di2])

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

if __name__=='__main__':

    # usage: "-i <infile.csv> <bookoutfile.json>" to import
    # and later "-a <bookoutfile.json> <authoroutfile.json>" to make author list

    # a valid csv file must be provided
    if len(sys.argv)>1:
        if sys.argv[1]=='-i':
            print('-i or IMPORT mode.')
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
                        print('Authors with warning: %s. Go and fix them.' % warningAuthors)
                        # clashing authors explicit print
                        def _auformat(au):
                            return '%-40s' % ('%s, %s' % (au['lastname'],au['firstname']))
                        for au in authorList['authorlist']:
                            if '_warnings' in au:
                                print('    %s' % _auformat(au))
                                for wau in au['_warnings']['similarity']:
                                    print('        %s' % _auformat(wau))
                    print('Finished.')
                else:
                    print('Operation aborted.')
            else:
                print('Two cmdline args are required: inputBookJSON, outputAuthorJSON.')
