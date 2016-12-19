import sys

def ask_for_confirmation(prompt, okresponses):
    print(prompt)
    res=sys.stdin.readline()
    if res.strip().upper() in map(str.upper,okresponses):
        return True
    else:
        return False

def logDo(fct,msg):
    '''
        utility function to log start/end of an operation (a zero-arg function)
    '''
    print('%s ... ' % msg,end='')
    sys.stdout.flush()
    retval=fct()
    print('Done.')
    sys.stdout.flush()
    return retval
