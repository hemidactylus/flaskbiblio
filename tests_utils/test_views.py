# tools in 'views.py' tester

import env

from app.views import load_user

def main():
    print('Loading user 1')
    u=load_user(1)
    print('Loaded %s' % u)
    print ('    name=%s, passwordhash=%s, id=%i' % (u.name,u.passwordhash,u.id))
    print('Done.')

if __name__=='__main__':
    main()
