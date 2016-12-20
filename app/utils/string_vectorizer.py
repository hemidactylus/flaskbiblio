# string_vectorizer.py : utility to handle cosine-distance and standardised vectorisation of strings

from collections import Counter

vectorCharacters=list(map(chr,range(ord('A'),ord('Z')+1)))

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

def scalProd(di1,di2):
    '''
        scalar product of two vectors
    '''
    return sum([v*di2[k] for k,v in di1.items() if k in di2])
