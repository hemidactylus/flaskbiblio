#/usr/bin/env python
from __future__ import print_function

import os
import sys
from operator import itemgetter
import csv, re
import json

import env
from app.utils.interactive import ask_for_confirmation, logDo
from db_testvalues import _testvalues

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
    return {
        'author': csvLine[0],
        'title': csvLine[1],
        'languages': csvLine[2],
        'inhouse': csvLine[3],
        'notes': csvLine[4],
    }

def normalizeParsedLine(pLine):
    '''
        converts a base structure into a proper structure, modulo references among tables
    '''
    print(json.dumps(pLine,indent=4))

def read_and_parse_csv(inFile):
    '''
        main driver of the extraction. Handles the top-level operations
    '''
    # 1. make valid lines into base structures
    parsedLines=list(map(parseBookLine,[li for li in csv.reader(open(inFile))][1:]))
    # TEMP DEBUG
    parsedLines=parsedLines[:1]
    # 2. apply a normalisation function to each line
    
    # TEMP DEBUG
    return 'Pi'

if __name__=='__main__':

    # a valid csv file must be provided
    inFile=None
    if len(sys.argv)>2:
        inFile=sys.argv[1]
        outFile=sys.argv[2]
        if clearToExtract(inFile,outFile):
            parsedCSV=logDo(lambda: read_and_parse_csv(inFile),'Reading from "%s"' % inFile)
            print('Finished.')
        else:
            print('Operation aborted.')
    else:
        print('Two cmdline args are required: inputCSV, outputPY.')
