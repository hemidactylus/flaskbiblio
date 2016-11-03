import os

# directories and so on
basedir = os.path.abspath(os.path.dirname(__file__))
DB_DIRECTORY=os.path.join(basedir,'app/database')

DB_NAME='biblio.db'

# stuff for Flask
WTF_CSRF_ENABLED = True
SECRET_KEY = 'TestSecretKey_NotForProduction'
