from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import  login_user, logout_user, current_user, login_required
from datetime import datetime

from app import app, db, lm
from .forms import (
                        LoginForm,
                        NewAuthorForm,
                        EditBookForm,
                    )

from config import DATETIME_STR_FORMAT, SHORT_DATETIME_STR_FORMAT

from app.database.dbtools import    (
                                        dbGetDatabase,
                                        dbGetAll,
                                        dbMakeDict,
                                        dbGetUser,
                                        dbDeleteAuthor,
                                        dbGetAuthor,
                                        dbAddReplaceAuthor,
                                        dbGetBook,
                                        dbDeleteBook,
                                        dbAddReplaceBook,
                                        registerLogin,
                                    )
from app.database.models import (
                                    tableToModel, 
                                    User,
                                    Book,
                                    Author,
                                )

from app import (
                    languages,
                    languagesDict,
                    booktypes,
                    booktypesDict,
                )

@app.before_request
def before_request():
    g.user = current_user

@app.route('/')
@app.route('/index')
def ep_index():
    user = g.user
    return render_template(
                            "index.html",
                            title='Home',
                            user=user,
                           )

@app.route('/languages')
@login_required
def ep_languages():
    user = g.user
    return render_template  (
                                "languages.html",
                                title='Languages',
                                user=user,
                                languages=languages,
                            )

@app.route('/booktypes')
@login_required
def ep_booktypes():
    user = g.user
    return render_template  (
                                "booktypes.html",
                                title='Book Types',
                                user=user,
                                booktypes=booktypes,
                            )

@app.route('/deletebook/<bookid>')
@login_required
def ep_deletebook(bookid):
    user=g.user
    if dbDeleteBook(int(bookid)):
        flash('Book successfully deleted.')
    else:
        flash('Could not delete book.')
    return redirect(url_for('ep_books'))

@app.route('/authors')
@login_required
def ep_authors():
    user = g.user
    authors=sorted(list(dbGetAll('author')))
    return render_template  (
                                "authors.html",
                                title='Authors',
                                user=user,
                                authors=authors,
                            )

@app.route('/newauthor', methods=['GET', 'POST'])
@login_required
def ep_newauthor():
    user=g.user
    form=NewAuthorForm()
    if form.validate_on_submit():
        authorToAdd=Author(id=None, firstname=form.firstname.data, lastname=form.lastname.data)
        status,newAuthor=dbAddReplaceAuthor(authorToAdd)
        if status:
            flash('Author %s inserted successfully.' % newAuthor)
        else:
            flash('Could not perform the insertion (error: %s).' % newAuthor)
        return redirect(url_for('ep_authors'))
    else:
        return render_template  (
                                    'newauthor.html',
                                    title='New Author',
                                    user=user,
                                    form=form,
            )

@app.route('/deleteauthor/<id>')
@login_required
def ep_deleteauthor(id):
    user=g.user
    status,delId=dbDeleteAuthor(int(id))
    if status:
        flash('Author successfully deleted.')
    else:
        flash('Could not delete author (error: %s).' % delId)
    return redirect(url_for('ep_authors'))

@app.route('/editauthor/<id>', methods=['GET', 'POST'])
@login_required
def ep_editauthor(id):
    user=g.user
    form=NewAuthorForm()
    if form.validate_on_submit():
        authorToInsert=Author(firstname=form.firstname.data, lastname=form.lastname.data, id=int(id))
        status,newAuthor=dbAddReplaceAuthor(authorToInsert)
        if status:
            flash('Author %s updated successfully.' % newAuthor)
        else:
            flash('Could not perform the update (error: %s).' % newAuthor)
        return redirect(url_for('ep_authors'))
    else:
        qAuthor=dbGetAuthor(int(id))
        if qAuthor:
            form.firstname.data=qAuthor.firstname
            form.lastname.data=qAuthor.lastname
            return render_template  (
                                        'newauthor.html',
                                        title='Edit Author',
                                        user=user,
                                        form=form,
                                        id=id,
                )
        else:
            flash('Internal error retrieving author.')
            return redirect(url_for('ep_authors'))

def ep_editauthor(id):
    user=g.user
    flash('Should edit author %s' % id)
    return redirect(url_for('ep_authors'))

def retrieveUsers():
    return dbMakeDict(dbGetAll('user'))

def resolveParams():
    # refresh authors list
    authors=list(dbGetAll('author'))
    authorsDict=dbMakeDict(authors)
    # pack the rest
    return {
                'authors': authorsDict,
                'languages': languagesDict,
                'booktypes': booktypesDict
            }

@app.route('/books')
@login_required
def ep_books():
    user = g.user
    # perform live query
    books=sorted(dbGetAll('book',resolve=True, resolveParams=resolveParams()))
    umap = retrieveUsers()
    for bo in books:
        lasteditor=umap.get(int(bo.lasteditor))
        if lasteditor:
            bo.lastedit=lasteditor.name
            if bo.lasteditdate:
                try:
                    bo.lastedit+=' (%s)' % datetime.strptime(str(bo.lasteditdate),DATETIME_STR_FORMAT).strftime(SHORT_DATETIME_STR_FORMAT)
                except:
                    pass
        else:
            bo.lastedit=''
    # done.
    return render_template  (
                                "books.html",
                                title='Books',
                                user=user,
                                books=books,
                            )

@app.route('/login', methods=['GET', 'POST'])
def ep_login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('ep_index'))
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        qUser=dbGetUser(form.username.data)
        if qUser and qUser.checkPassword(form.password.data):
            login_user(load_user(qUser.id))
            #
            lastlogin=qUser.lastlogindate
            #
            flash('Login successful. Welcome, %s! (last login: %s)' %
                (qUser.name,lastlogin if lastlogin else 'first login'))
            #
            registerLogin(qUser.id)
            #
            return redirect(url_for('ep_index'))
        else:
            flash('Invalid username/password provided')
            return redirect(url_for('ep_index'))
    return render_template('login.html', 
                           title='Log In',
                           form=form)

@app.route('/logout')
@login_required
def ep_logout():
    if g.user is not None and g.user.is_authenticated:
        flash('Logged out successfully.')
        logout_user()
    return redirect(url_for('ep_index'))        

@app.route('/editbook', methods=['GET', 'POST'])
@login_required
def ep_editbook():
    user=g.user
    form=EditBookForm()
    form.setBooktypes(resolveParams()['booktypes'].values())
    form.setLanguages(resolveParams()['languages'].values())
    if request.method=='GET':
        paramIdString=request.args.get('bookid')
        if paramIdString is not None and len(paramIdString)>0:
            paramId=int(paramIdString)
        else:
            paramId=None
        authorParameter=request.args.get('authorlist')
        # HERE should set form local properties from request
        form.title.data=request.args.get('title')
        form.inhouse.data=int(request.args.get('inhouse','1'))
        form.notes.data=request.args.get('notes')
        form.inhousenotes.data=request.args.get('inhousenotes')
        form.booktype.data=request.args.get('booktype')
        if len(request.args.get('languages',''))>0:
            form.languages.data=request.args['languages'].split(',')
        else:
            form.languages.data=[]
    else:
        paramId=form.bookid.data
        authorParameter=form.authorlist.data
    if paramId is not None and authorParameter is None:
        formTitle='Edit Book'
        qBook=dbGetBook(int(paramId))
        if qBook:
            authorParameter=qBook.authors
            form.title.data=qBook.title
            form.inhouse.data=int(qBook.inhouse)
            form.notes.data=qBook.notes
            form.inhousenotes.data=qBook.inhousenotes
            form.booktype.data=qBook.booktype
            form.languages.data=qBook.languages.split(',')
        else:
            flash('Internal error retrieving book')
            return redirect(url_for('ep_books'))
    else:
        formTitle='New Book'
    # parse the list
    if authorParameter:
        authorIdList=authorParameter.split(',')
    else:
        authorIdList=[]
    # all authors as objects
    allAuthors=sorted(list(dbGetAll('author')))
    presentAuthors=list(filter(lambda a: str(a.id) in authorIdList,allAuthors))
    form.setAuthorsToDelete(presentAuthors)
    # take out already-insertee authors
    availableAuthors=filter(lambda a: str(a.id) not in authorIdList,allAuthors)
    form.setAuthorsToAdd(availableAuthors)
    # HERE values are read off the form into a Book instance
    editedBook=Book(
        id=int(form.bookid.data) if form.bookid.data is not None and len(form.bookid.data)>0 else None,
        title=form.title.data,
        inhouse=int(form.inhouse.data),
        notes=form.notes.data,
        inhousenotes=form.inhousenotes.data,
        booktype=form.booktype.data,
        languages=','.join(form.languages.data) if form.languages.data is not None else '',
        authors=form.authorlist.data,
        lasteditor=user.id,
    )
    #
    if form.validate_on_submit():
        # here a button was pressed. Which one? (add or submit)
        if form.additem.data or form.delitem.data:
            if form.additem.data:
                # pressed the add-item button
                authorIdList.append(form.newauthors.data)
            else:
                # pressed the delete-item button
                authorIdList=[au for au in authorIdList if au != form.delauthors.data]
            # HERE must read values off the form and pass them to the url
            editedBook.authors=','.join(authorIdList)
            return redirect(url_for(
                                        'ep_editbook',
                                        authorlist=editedBook.authors,
                                        bookid=editedBook.id,
                                        title=editedBook.title,
                                        inhouse=editedBook.inhouse,
                                        inhousenotes=editedBook.inhousenotes,
                                        notes=editedBook.notes,
                                        booktype=editedBook.booktype,
                                        languages=editedBook.languages,
                                        authors=editedBook.authors,
                                    )
                           )
        else:
            # pressed the submit button
            # HERE the actual save/update is triggered
            newEntry=editedBook.id is None
            result,updatedBook=dbAddReplaceBook(editedBook,
                                resolve=True,
                                resolveParams=resolveParams())
            if result:
                if newEntry:
                    flash('"%s" successfully added.' % str(updatedBook))
                else:
                    flash('"%s" successfully updated.' % str(updatedBook))
            else:
                flash('Internal error updating the book table (error: %s).' % updatedBook)
            return redirect(url_for('ep_books'))
    else:
        # HERE the form's additionals are set
        form.authorlist.data=','.join(authorIdList)
        form.bookid.data=paramId
        return render_template( 'editbook.html',
                                formtitle=formTitle,
                                form=form,
                                items=[{'description': str(au), 'id': au.id} for au in presentAuthors],
                                authorlist=','.join(authorIdList))

# user loader function given to flask_login. This queries the db to fetch a user by id
@lm.user_loader
def load_user(id):
    return User.manager(db).get(int(id))
