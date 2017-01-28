import os

# directories and so on
basedir = os.path.abspath(os.path.dirname(__file__))
DB_DIRECTORY=os.path.join(basedir,'app/database')

DB_NAME='biblio.db'

# stuff for Flask
WTF_CSRF_ENABLED = True
from sensible_config import SECRET_KEY

# formats, etc
DATETIME_STR_FORMAT = '%Y-%m-%d %H:%M:%S'
SHORT_DATETIME_STR_FORMAT = '%d/%m/%y'
FILENAME_DATETIME_STR_FORMAT = '%Y_%m_%d'

# similarity thresholds for author (last- and complete-) names
SIMILAR_USE_DIGRAMS=True # otherwise: use single-letter grams
# Different thresholds are required depending on the type of vectoring
if SIMILAR_USE_DIGRAMS:
    SIMILAR_AUTHOR_THRESHOLD=0.7
    SIMILAR_BOOK_THRESHOLD=0.7
else:
    SIMILAR_AUTHOR_THRESHOLD=0.90
    SIMILAR_BOOK_THRESHOLD=0.93

# Are multiple books with the same title allowed? (suggested: yes)
ALLOW_DUPLICATE_BOOKS=True

# temporary directory for storing import-related files
TEMP_DIRECTORY=os.path.join(basedir,'app/temp')
