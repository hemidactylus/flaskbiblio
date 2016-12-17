from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import  login_user, logout_user, current_user, login_required

from app import app, db, lm
from .forms import (
                        LoginForm,
                        NewAuthorForm,
                        NewBookForm,
                        TestForm,
                    )

from app.database.dbtools import    (
                                        dbGetDatabase,
                                        dbGetAll,
                                        dbMakeDict,
                                        dbGetUser,
                                        dbAddAuthor,
                                        dbDeleteAuthor,
                                        dbGetAuthor,
                                        dbReplaceAuthor,
                                        dbAddBook,
                                        dbGetBook,
                                        dbDeleteBook,
                                        dbReplaceBook,
                                    )
from app.database.models import (
                                    tableToModel, 
                                    User,
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

@app.route('/deletebook/<id>')
@login_required
def ep_deletebook(id):
    user=g.user
    if dbDeleteBook(int(id)):
        flash('Book successfully deleted.')
    else:
        flash('Could not delete book.')
    return redirect(url_for('ep_books'))

@app.route('/editbook', methods=['GET', 'POST'])
@login_required
def ep_alterbook():
    '''
        'id' is read from the query params
        id is None for new books, it is set for edits
    '''
    user=g.user
    id=request.args.get('id')
    form=NewBookForm()
    form.setBooktypes(resolveParams()['booktypes'].values())
    form.setLanguages(resolveParams()['languages'].values())
    if form.validate_on_submit():
        if id is None:
            changer=dbAddBook
            opName='Add'
        else:
            changer=dbReplaceBook
            opName='Edit'
        newBook=changer (
                            id,
                            form.title.data,
                            form.inhouse.data,
                            form.notes.data,
                            form.booktype.data,
                            ','.join(form.languages.data),
                            form.authors.data,
                            user.id,
                            resolve=True,
                            resolveParams=resolveParams(),
                        )
        if newBook is not None:
            flash('"%s" %sed successfully.' % (newBook,opName))
        else:
            flash('Could not perform the %s operation.' % opName)
        return redirect(url_for('ep_books'))
    else:
        if id is None:
            return render_template  (
                                        'newbook.html',
                                        title='New Book',
                                        user=user,
                                        form=form,
                )
        else:
            qBook=dbGetBook(int(id))
            if qBook:
                form.title.data=qBook.title
                form.inhouse.dataq=int(qBook.inhouse)
                form.notes.data=qBook.notes
                form.booktype.data=qBook.booktype
                form.languages.data=qBook.languages.split(',')
                form.authors.data=qBook.authors
                return render_template  (
                                            'newbook.html',
                                            title='Edit Book',
                                            user=user,
                                            form=form,
                                            id=id,
                    )
            else:
                flash('Internal error retrieving book')
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
        newAuthor=dbAddAuthor(form.firstname.data,form.lastname.data)
        if newAuthor is not None:
            flash('Author %s inserted successfully.' % newAuthor)
        else:
            flash('Could not perform the insertion.')
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
    if dbDeleteAuthor(int(id)):
        flash('Author successfully deleted.')
    else:
        flash('Could not delete author.')
    return redirect(url_for('ep_authors'))

@app.route('/editauthor/<id>', methods=['GET', 'POST'])
@login_required
def ep_editauthor(id):
    user=g.user
    form=NewAuthorForm()
    if form.validate_on_submit():
        newAuthor=dbReplaceAuthor(id,form.firstname.data,form.lastname.data)
        if newAuthor is not None:
            flash('Author %s updated successfully.' % newAuthor)
        else:
            flash('Could not perform the update.')
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
    books=dbGetAll('book',resolve=True, resolveParams=resolveParams())
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
        if qUser and qUser.passwordhash==form.password.data:
            login_user(load_user(qUser.id))
            flash('Login successful. Welcome, %s!' % qUser.name)
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

@app.route('/test', methods=['GET', 'POST'])
def ep_test():
    form=TestForm()
    # parse the list
    authorParameter=request.args.get('authorlist')
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
    #
    if form.validate_on_submit():
        # here a button was pressed. Which one? (add or submit)
        if form.additem.data:
            # pressed the add-item button
            authorIdList.append(form.newauthors.data)
            msg=form.name.data
            flash('Adding another one (now: <%s>)' % '/'.join(authorIdList))
            return redirect(url_for('ep_test',authorlist=','.join(authorIdList),name=msg))
        elif form.delitem.data:
            # pressed the delete-item button
            authorIdList=[au for au in authorIdList if au != form.delauthors.data]
            msg=form.name.data
            flash('Deleting one (now: <%s>)' % '/'.join(authorIdList))
            return redirect(url_for('ep_test',authorlist=','.join(authorIdList),name=msg))
        else:
            # pressed the submit button
            flash('Finished adding. Final: <%s>, name=%s' % ('/'.join(authorIdList), form.name.data))
            return redirect(url_for('ep_index'))
    else:
        # produce the form
        msg=request.args.get('name')
        if msg:
            form.name.data=msg
        return render_template( 'test.html',
                                title='Test Form',
                                form=form,
                                items=[{'description': str(au), 'id': au.id} for au in presentAuthors],
                                authorlist=','.join(authorIdList))

# user loader function given to flask_login. This queries the db to fetch a user by id
@lm.user_loader
def load_user(id):
    return User.manager(db).get(int(id))
