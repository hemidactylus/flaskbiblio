from flask import render_template, flash, redirect
from app import app
from .forms import LoginForm

from app.database.dbtools import    (
                                        dbGetDatabase,
                                        dbGetAll,
                                        dbMakeDict,
                                    )
from app.database.models import (
                                    tableToModel, 
                                )

# global static init lists and db
db=dbGetDatabase()
languages=list(dbGetAll('language'))
languagesDict=dbMakeDict(languages)
booktypes=list(dbGetAll('booktype'))
booktypesDict=dbMakeDict(booktypes)

@app.route('/')
@app.route('/index')
def ep_index():
    user = {'nickname': 'Miguel'}  # fake user
    posts = [  # fake array of posts
        { 
            'author': {'nickname': 'John'}, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': {'nickname': 'Susan'}, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
    return render_template("index.html",
                           title='Home',
                           user=user,
                           posts=posts)

@app.route('/languages')
def ep_languages():
    user = {'nickname': 'Miguel'}  # fake user
    return render_template  (
                                "languages.html",
                                user=user,
                                languages=languages,
                            )

@app.route('/booktypes')
def ep_booktypes():
    user = {'nickname': 'Miguel'}  # fake user
    return render_template  (
                                "booktypes.html",
                                user=user,
                                booktypes=booktypes,
                            )

@app.route('/login', methods=['GET', 'POST'])
def ep_login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for User="%s", remember_me=%s' %
              (form.username.data, str(form.remember_me.data)))
        return redirect('/index')
    return render_template('login.html', 
                           title='Sign In',
                           form=form)
