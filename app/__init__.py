import os
from flask import Flask
from flask_login import LoginManager
from flask_bootstrap import Bootstrap

from config import basedir

from app.database.dbtools import    (
                                        dbGetDatabase,
                                        dbGetAll,
                                        dbMakeDict,
                                    )

app = Flask(__name__,static_folder='static', static_url_path='/static')
Bootstrap(app)
app.config.from_object('config')

lm = LoginManager()
lm.init_app(app)

# global static init lists and db
languages=sorted(list(dbGetAll('language')))
languagesDict=dbMakeDict(languages,'tag')
booktypes=sorted(list(dbGetAll('booktype')))
booktypesDict=dbMakeDict(booktypes,'tag')

# this must be AFTER the above, otherwise 'db' is circularly not found in the imports
from app import views
