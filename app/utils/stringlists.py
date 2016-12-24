'''
    stringlists.py : utilities to deal with the encoding of lists of integers
    as comma-separated strings
'''

def unrollStringList(sList):
    '''
        Unrolls a comma-separated string with a list of ids
        and returns a sorted list of the int values.
        Handles the case of empty string
    '''
    return sorted(map(int,filter(lambda s: s!='', sList.split(','))))

def rollStringList(values):
    '''
        Sorts a list of integers and makes them into a comma-separated string
    '''
    return ','.join(map(str,sorted(values)))

def expungeFromStringList(sList, intVal):
    '''
        removes the integer value from the list and
        returns (newlist, newcount)
    '''
    nIntList=[val for val in unrollStringList(sList) if val!=intVal]
    return rollStringList(nIntList),len(nIntList)

def addToStringList(sList, intVal):
    '''
        adds a number to a string-list
        and returns (newlist, newcount)
    '''
    nIntList=list(set(unrollStringList(sList)+[intVal]))
    return rollStringList(nIntList),len(nIntList)
