import os

# directories and so on
basedir = os.path.abspath(os.path.dirname(__file__))
DB_DIRECTORY=os.path.join(basedir,'app/database')

DB_NAME='biblio.db'

# stuff for Flask
WTF_CSRF_ENABLED = True
SECRET_KEY = 'TestSecretKey_NotForProduction'

# formats, etc
DATETIME_STR_FORMAT = '%Y-%m-%d %H:%M:%S'
SHORT_DATETIME_STR_FORMAT = '%d/%m/%y'

# similarity thresholds for author (last- and complete-) names
SIMILAR_AUTHOR_THRESHOLD=0.9
SIMILAR_BOOK_THRESHOLD=0.93
