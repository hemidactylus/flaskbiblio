# ascii_checks.py : miscellaneous utilities to handle with the ->ascii conversion and checks

validCharacters=''.join(map(chr,range(32,127)))
translatedCharacters={
    u'Á': 'A',
    u'á': 'a',
    u'ã': 'a',
    u'ä': 'ae',
    u'æ': 'ae',
    u'ç': 'c',
    u'č': 'c',
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

def nonAsciiCharacters(inString):
    '''
        returns all non-pure-ascii chars found in the string, taken once
    '''
    return set(list(inString))-set(list(validCharacters))

def isAscii(inString):
    '''
        returns True only if all chars in the input are basic ascii
    '''
    return len(nonAsciiCharacters(inString))==0

def ascifiiString(inString, forceAsciification=False):
    '''
        translates characters so that the result is an ascii-fication of the input string
        
        if forceAsciification is True, the string is forcefully converted to a pure ascii,
            even at the cost of losing characters (non-ascii which do not fall into the translation table)
    '''
    resString=inString
    for k,v in translatedCharacters.items():
        resString=resString.replace(k,v)
    if forceAsciification:
        return ''.join(c for c in resString if c in validCharacters)
    else:
        return resString
