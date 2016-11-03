import sys

def ask_for_confirmation(prompt, okresponses):
    print(prompt)
    res=sys.stdin.readline()
    if res.strip().upper() in map(str.upper,okresponses):
        return True
    else:
        return False
