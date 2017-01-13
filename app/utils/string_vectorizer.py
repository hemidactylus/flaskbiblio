# string_vectorizer.py : utility to handle cosine-distance and standardised vectorisation of strings

from collections import Counter

from config import SIMILAR_USE_DIGRAMS

vectorCharacters=list(map(chr,range(ord('A'),ord('Z')+1)))

# which are the base elements in the similarity vector space?
if SIMILAR_USE_DIGRAMS:
    baseExtractor=lambda cleanString: map(lambda p: ''.join(p),(lambda l: zip(l[:-1],l[1:]))(cleanString))
    # a function string -> list of digrams
else:
    baseExtractor=lambda cleanString: cleanString
    # a function string -> list of letters

def makeIntoVector(qString):
    '''
        makes a string into a unitary vectors.
        No non-alphabetic, no case-sensitivity
    '''
    lCnt=Counter(baseExtractor([let for let in list(qString.upper()) if let in vectorCharacters]))
    lNorm=sum(map(lambda x: x**2.0,lCnt.values()))**0.5
    if lNorm>0:
        return {k: v/lNorm for k,v in lCnt.items()}
    else:
        return dict(lCnt)

def scalProd(di1,di2):
    '''
        scalar product of two vectors
    '''
    return sum([v*di2[k] for k,v in di1.items() if k in di2])
