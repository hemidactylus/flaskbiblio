from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import  login_user, logout_user, current_user, login_required
from datetime import datetime
from werkzeug.datastructures import MultiDict
from markupsafe import Markup

from app import app, db, lm
from .forms import (
                        LoginForm,
                        EditAuthorForm,
                        EditBookForm,
                        ConfirmForm,
                        UserSettingsForm,
                        ChangePasswordForm,
                        SearchBookForm,
                        SearchAuthorForm,
                        BTestForm,
                    )
from app.utils.stringlists import unrollStringList

from config import (
                        DATETIME_STR_FORMAT,
                        SHORT_DATETIME_STR_FORMAT,
                        SIMILAR_AUTHOR_THRESHOLD,
                        SIMILAR_BOOK_THRESHOLD,
                    )

from app.utils.string_vectorizer import makeIntoVector, scalProd
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
                                        dbReplaceUser,
                                        dbQueryBooks,
                                        dbQueryAuthors,
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

def flashMessage(msgType,msgHeading,msgBody):
    '''
        Enqueues a flashed structured message for use by the render template
        
            'msgType' can be: critical, error, warning, info
    '''
    flash(Markup('<strong>%s: </strong> %s' % (msgHeading,msgBody)), msgType)

@app.before_request
def before_request():
    g.user = current_user

# user loader function given to flask_login. This queries the db to fetch a user by id
@lm.user_loader
def load_user(id):
    return User.manager(db).get(int(id))

@app.route('/')
@app.route('/index')
def ep_index():
    user = g.user
    if user:
        message=[{'description': qStat.description, 'value': qStat.value} for qStat in dbGetAll('statistic')]
    else:
        message=None
    return render_template(
                            "index.html",
                            title='Home',
                            user=user,
                            statistics=message,
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

@app.route('/deletebook/<id>/<confirm>')
@app.route('/deletebook/<id>')
@login_required
def ep_deletebook(id, confirm=None):
    user=g.user
    if user.canedit:
        if user.requireconfirmation and not confirm:
            return redirect(url_for('ep_confirm',
                                    operation='deletebook',
                                    value=id,
                                    )
                            )
        else:
            status,delId=dbDeleteBook(int(id))
            if status:
                flashMessage('info','Success','Book successfully deleted.')
            else:
                flashMessage('warning','Could not delete book', delId)
        return redirect(url_for('ep_books'))
    else:
        flashMessage('error','Cannot proceed','user "%s" has no write privileges.' % user.name)
        return redirect(url_for('ep_books'))

@app.route('/goback/<default>')
@login_required
def ep_goback(default='ep_books'):
    '''
        This is where the 'cancel' buttons lead, from
        both a confirm-dialog and a cancel-edit button.
        If there is a stored lastquery, we are
        redirecting there; if there is no lastquery, the default prevails.
    '''
    if 'lastquery' in session:
        goal=session['lastquery']['page']
        return redirect(url_for(goal,restore='y'))
    else:
        return redirect(url_for(default))

@app.route('/authors/<restore>')
@app.route('/authors')
@login_required
def ep_authors(restore=None):
    user = g.user
    # store the last query for future use
    if restore=='y':
        reqargs=MultiDict(session['lastquery']['args'])
    else:
        session['lastquery']={'page':'ep_authors','args': request.args}
        reqargs=request.args
    #
    result,authors=dbQueryAuthors   (
                                        queryArgs=reqargs,
                                        resultsperpage=user.resultsperpage,
                                    )
    # prepare arglist for pagination commands by keeping the rest of the multidict
    prevquery=None
    nextquery=None
    if 'nextstartfrom' in result:
        nextquery=reqargs.copy()
        nextquery['startfrom'] = result['nextstartfrom']
    if 'prevstartfrom' in result:
        prevquery=reqargs.copy()
        prevquery['startfrom'] = result['prevstartfrom']
    return render_template  (
                                "authors.html",
                                title='Authors',
                                user=user,
                                authors=authors,
                                queryresult=result,
                                nextquery=nextquery,
                                prevquery=prevquery,
                            )

@app.route('/deleteauthor/<id>')
@app.route('/deleteauthor/<id>/<confirm>')
@login_required
def ep_deleteauthor(id,confirm=None):
    user=g.user
    # try and get the book count for the requested author
    if user.canedit:
        rAuthor=dbGetAuthor(int(id))
        #
        if rAuthor:
            if user.requireconfirmation and rAuthor.bookcount>0 and not confirm:
                return redirect(url_for('ep_confirm',
                                        operation='deleteauthor',
                                        value=id,
                                        )
                                )
            else:
                status,delId=dbDeleteAuthor(int(id))
                if status:
                    flashMessage('info','Success','author successfully deleted.')
                else:
                    flashMessage('warning','Could not delete author', delId)
        else:
            flashMessage('critical','Could not delete author','author not found')
        return redirect(url_for('ep_authors'))
    else:
        flashMessage('error','Cannot proceed','user "%s" has no write privileges.' % user.name)
        return redirect(url_for('ep_authors'))
'''
    This call, similarly to the editbook below,
    handles both 'new' and 'edit' operations. It supports
    reiterated action (in particular for books, see the author-list handling).
    New/edit is determined bu the request 'id' parameter if passed,
    other details also are rerouted as req args,
    depending on that we decide whether to self-pass params (as the case for books)
    or to fill the form with DB-extracted values.
    A bit cumbersome to handle but completely static forms.
'''
@app.route('/editauthor', methods=['GET', 'POST'])
@login_required
def ep_editauthor():
    user=g.user
    form=EditAuthorForm()
    if request.method=='GET':
        paramIdString=request.args.get('id')
        if paramIdString is not None and len(paramIdString)>0:
            paramId=int(paramIdString)
        else:
            paramId=None
        # HERE should set form local properties from request
        form.firstname.data=request.args.get('firstname')
        form.lastname.data=request.args.get('lastname')
        form.notes.data=request.args.get('notes')
    else:
        paramId=form.authorid.data
    if paramId is not None and paramId!='':
        formTitle='Edit Author'
        if form.firstname.data is None:
            qAuthor=dbGetAuthor(int(paramId))
            if qAuthor:
                form.firstname.data=qAuthor.firstname
                form.lastname.data=qAuthor.lastname
                form.notes.data=qAuthor.notes
            else:
                flashMessage('critical','Error','internal error retrieving author')
                return redirect(url_for('ep_authors'))
    else:
        formTitle='New Author'
    # HERE values are read off the form into an Author instance
    editedAuthor=Author(
        id=int(form.authorid.data) if form.authorid.data is not None and len(form.authorid.data)>0 else None,
        firstname=form.firstname.data,
        lastname=form.lastname.data,
        notes=form.notes.data,
    )
    # if necessary, retrieve booklist/bookcount from DB
    if editedAuthor.id is not None:
        qAuthor=dbGetAuthor(int(editedAuthor.id))
        editedAuthor.bookcount=qAuthor.bookcount
        editedAuthor.booklist=qAuthor.booklist
    #
    if form.validate_on_submit():
        # here 'save' button was pressed
        newEntry=editedAuthor.id is None
        # Here almost-duplicates could be detected
        similarAuthors=[]
        if user.requireconfirmation and not form.force.data:
            aVecs={
                'last': makeIntoVector(editedAuthor.lastname),
                'full': makeIntoVector(editedAuthor.firstname+editedAuthor.lastname)
            }
            for otAu in dbGetAll('author',resolve=False):
                if otAu.id != editedAuthor.id:
                    oVecs={
                        'last': makeIntoVector(otAu.lastname),
                        'full': makeIntoVector(otAu.firstname+otAu.lastname)
                    }
                    # if either vector is too similar to the insertee's corresponding one
                    if any([scalProd(aVecs[vkey],oVecs[vkey])>SIMILAR_AUTHOR_THRESHOLD for vkey in aVecs.keys()]):
                        similarAuthors.append(otAu)
            #
        if similarAuthors:
            flashMessage('warning','Confirm operation','similar existing author(s) found (%s). Confirm to proceed.' % ','.join(map(str,similarAuthors)))
            if not newEntry:
                booklist=[{'id': bId, 'title': dbGetBook(bId).title} for bId in unrollStringList(editedAuthor.booklist)]
                bookcount=qAuthor.bookcount
            else:
                booklist=None
                bookcount=None
            return render_template( 'editauthor.html',
                                    title=formTitle,
                                    id=paramId,
                                    formtitle=formTitle,
                                    form=form,
                                    bookcount=bookcount,
                                    booklist=booklist,
                                    showforce=True,
                                    user=user,
                                  )
        else:
            #
            if user.canedit:
                result,updatedAuthor=dbAddReplaceAuthor(editedAuthor)
                if result:
                    if newEntry:
                        flashMessage('info','Insertion successful','"%s"' % str(updatedAuthor))
                    else:
                        flashMessage('info','Update successful','"%s"' % str(updatedAuthor))
                else:
                    flashMessage('critical','Internal error', '"%s"' % updatedAuthor)
            else:
                flashMessage('error','Cannot proceed','user "%s" has no write privileges.' % user.name)
            return redirect(url_for('ep_goback',default='ep_authors'))
    else:
        # HERE the form's additionals are set
        form.authorid.data=paramId
        if paramId:
            booklist=[{'id': bId, 'title': dbGetBook(bId).title} for bId in unrollStringList(qAuthor.booklist)]
            bookcount=qAuthor.bookcount
        else:
            booklist=None
            bookcount=None
        return render_template( 'editauthor.html',
                                title=formTitle,
                                id=paramId,
                                formtitle=formTitle,
                                form=form,
                                bookcount=bookcount,
                                booklist=booklist,
                                user=user,
                              )

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

@app.route('/authorsearch',methods=['GET','POST'])
@login_required
def ep_authorsearch():
    user=g.user
    form=SearchAuthorForm()
    if form.validate_on_submit():
        # prepare request for search endpoint
        # In the future a multidict may be built here
        authorSearchArgs={}
        if form.firstname.data:
            authorSearchArgs['firstname']=form.firstname.data
        if form.lastname.data:
            authorSearchArgs['lastname']=form.lastname.data
        authorSearchArgs['sortby']=form.sortby.data
        return redirect(url_for('ep_authors',**authorSearchArgs))
    else:
        return render_template  (
                                    'authorsearch.html',
                                    title='Author search',
                                    user=user,
                                    form=form,
                                )

@app.route('/booksearch',methods=['GET','POST'])
@login_required
def ep_booksearch():
    user = g.user
    form=SearchBookForm()
    form.setBooktypes(resolveParams()['booktypes'].values())
    form.setLanguages(resolveParams()['languages'].values())
    allAuthors=sorted(list(dbGetAll('author')))
    form.setAuthors(allAuthors)
    if form.validate_on_submit():
        # prepare request for search endpoint
        # In the future this may become a multidict.
        bookSearchArgs={}
        if form.title.data:
            bookSearchArgs['title']=form.title.data
        if form.author.data!='-1':
            bookSearchArgs['author']=form.author.data
        if form.booktype.data!='-1':
            bookSearchArgs['booktype']=form.booktype.data
        if form.language.data!='-1':
            bookSearchArgs['language']=form.language.data
        if form.inhouse.data!='-1':
            bookSearchArgs['inhouse']=form.inhouse.data
        bookSearchArgs['sortby']=form.sortby.data
        return redirect(url_for('ep_books',**bookSearchArgs))
    else:
        return render_template  (
                                    'booksearch.html',
                                    title='Book search',
                                    user=user,
                                    form=form,
                                )

@app.route('/books/<restore>')
@app.route('/books')
@login_required
def ep_books(restore=None):
    user = g.user
    # store the last request for future use
    if restore=='y':
        reqargs=MultiDict(session['lastquery']['args'])
    else:
        session['lastquery']={'page':'ep_books','args': request.args}
        reqargs=request.args
    # perform live query
    result,books=dbQueryBooks   (
                                    queryArgs=reqargs,
                                    resultsperpage=user.resultsperpage,
                                    resolve=True,
                                    resolveParams=resolveParams(),
                                )
    umap = retrieveUsers()
    for bo in books:
        lasteditor=umap.get(int(bo.lasteditor))
        if lasteditor:
            bo.lastedit=[lasteditor.name]
            if bo.lasteditdate:
                try:
                    bo.lastedit+=[datetime.strptime(str(bo.lasteditdate),
                        DATETIME_STR_FORMAT).strftime(SHORT_DATETIME_STR_FORMAT)]
                except:
                    pass
        else:
            bo.lastedit=''
    # done.
    # prepare arglist for pagination commands by keeping the rest of the multidict
    prevquery=None
    nextquery=None
    if 'nextstartfrom' in result:
        nextquery=reqargs.copy()
        nextquery['startfrom'] = result['nextstartfrom']
    if 'prevstartfrom' in result:
        prevquery=reqargs.copy()
        prevquery['startfrom'] = result['prevstartfrom']
    # render results list page
    return render_template  (
                                "books.html",
                                title='Books',
                                user=user,
                                books=books,
                                queryresult=result,
                                nextquery=nextquery,
                                prevquery=prevquery,
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
            flashMessage('info','Login successful', 'welcome, %s! (last login: %s)' %
                (qUser.name,lastlogin if lastlogin else 'first login'))
            #
            registerLogin(qUser.id)
            #
            return redirect(url_for('ep_index'))
        else:
            flashMessage('warning','Cannot log in','invalid username/password provided')
            return redirect(url_for('ep_index'))
    return render_template('login.html', 
                           title='Log in',
                           form=form)

@app.route('/logout')
@login_required
def ep_logout():
    if g.user is not None and g.user.is_authenticated:
        flashMessage('info','Logged out successfully','goodbye')
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
        paramIdString=request.args.get('id')
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
    if paramId is not None and paramId!='':
        formTitle='Edit Book'
        if form.title.data is None:
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
                flashMessage('critical','Internal error', 'error retrieving book')
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
                                        id=editedBook.id,
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
            newEntry=editedBook.id is None
            # Here almost-duplicates could be detected
            similarBooks=[]
            if user.requireconfirmation and not form.force.data:
                bVecs={
                    'full': makeIntoVector(editedBook.title)
                }
                for otBo in dbGetAll('book',resolve=False):
                    if otBo.id != editedBook.id:
                        oVecs={
                            'full': makeIntoVector(otBo.title)
                        }
                        # if either vector is too similar to the insertee's corresponding one
                        if any([scalProd(bVecs[vkey],oVecs[vkey])>SIMILAR_BOOK_THRESHOLD for vkey in bVecs.keys()]):
                            similarBooks.append(otBo)
                #
            if similarBooks:
                flashMessage('warning','Confirm operation','similar existing book(s) found (%s). Confirm to proceed.' % ','.join(map(str,similarBooks)))
                # if not newEntry:
                #     booklist=[{'id': bId, 'title': dbGetBook(bId).title} for bId in unrollStringList(editedAuthor.booklist)]
                #     bookcount=qAuthor.bookcount
                # else:
                #     booklist=None
                #     bookcount=None
                form.authorlist.data=','.join(authorIdList)
                form.bookid.data=paramId
                return render_template( 'editbook.html',
                                        title=formTitle,
                                        formtitle=formTitle,
                                        form=form,
                                        user=user,
                                        items=[{'description': str(au), 'id': au.id} for au in presentAuthors],
                                        authorlist=','.join(authorIdList),
                                        showforce=True)
            else:
                # HERE the actual save/update is triggered
                newEntry=editedBook.id is None
                if user.canedit:
                    result,updatedBook=dbAddReplaceBook(editedBook,
                                        resolve=True,
                                        resolveParams=resolveParams())
                    if result:
                        if newEntry:
                            flashMessage('info','Insert successful','"%s"' % str(updatedBook))
                        else:
                            flashMessage('info','Update successful','"%s"' % str(updatedBook))
                    else:
                        flashMessage('critical','Internal error', '%s' % updatedBook)
                    return redirect(url_for('ep_goback',default='ep_books'))
                else:
                    flashMessage('error','Cannot proceed', 'user "%s" has no write privileges.' % user.name)
                    return redirect(url_for('ep_goback',default='ep_books'))
    else:
        # HERE the form's additionals are set
        form.authorlist.data=','.join(authorIdList)
        form.bookid.data=paramId
        return render_template( 'editbook.html',
                                title=formTitle,
                                formtitle=formTitle,
                                form=form,
                                user=user,
                                items=[{'description': str(au), 'id': au.id} for au in presentAuthors],
                                authorlist=','.join(authorIdList))

# Generic do-you-want-to-proceed 'dialog' (intermediate form).
# This is called to confirm an operation, handles a Y/N answer retrieval
# and calls the appropriate url to proceed if it is the case.
# There are a handful of registered 'operation's

def makeDeleteAuthorMessage(saId):
    '''
        constructs a confirm-message before deleting a bookful author
    '''
    rAuthor=dbGetAuthor(int(saId))
    return '"%s" authors %i book%s: really proceed?' %  (
                                                            str(rAuthor),
                                                            rAuthor.bookcount,
                                                            's' if rAuthor.bookcount>1 else '',
                                                        )

def makeDeleteBookMessage(sbId):
    '''
        constructs a confirm-message before deleting a book (any book)
    '''
    rBook=dbGetBook(int(sbId))
    return 'Really delete book "%s"?' % (
                                            str(rBook),
                                        )

confirmOperations={
    'deleteauthor': {
        'message': makeDeleteAuthorMessage, # function from (author) ID to string message
        'okurl': 'ep_deleteauthor', # name of endpoint to go to in case of 'Y'
        # it is implicit that id=id and confirm=1 are passed to this endpoint
        'cancelurl': 'ep_authors',
    },
    'deletebook': {
        'message': makeDeleteBookMessage,
        'okurl': 'ep_deletebook',
        'cancelurl': 'ep_books',
    },
}

@app.route('/usersettings', methods=['GET', 'POST'])
@login_required
def ep_usersettings():
    user=g.user
    form=UserSettingsForm()
    #
    if form.validate_on_submit():
        user.requireconfirmation=int(form.requireconfirmation.data)
        user.resultsperpage=int(form.resultsperpage.data)
        result,newuser=dbReplaceUser(user)
        if result:
            flashMessage('info','Done','settings updated successfully.')
        else:
            flashMessage('critical','Warning', 'an error occurred trying to update the settings.')
        return redirect(url_for('ep_index'))
    else:
        form.requireconfirmation.data=user.requireconfirmation
        form.resultsperpage.data=str(user.resultsperpage)
        return render_template  (
                                    'usersettings.html',
                                    title='User settings',
                                    form=form,
                                    user=user,
                                )

@app.route('/changepassword', methods=['GET', 'POST'])
@login_required
def ep_changepassword():
    user=g.user
    form=ChangePasswordForm()
    #
    if form.validate_on_submit():
        # actual password change. Alter current User object and save it back
        if user.checkPassword(form.oldpassword.data):
            user.passwordhash=User._hashString(form.newpassword.data)
            result,newuser=dbReplaceUser(user)
            if result:
                flashMessage('info','Done','password changed successfully')
            else:
                flashMessage('warning','Warning','an error occurred trying to change the password.')
        else:
            flashMessage('warning','Warning','wrong password.')
        return redirect(url_for('ep_index'))
    else:
        return render_template  (
                                    'changepassword.html',
                                    form=form,
                                    title='Change password',
                                    user=user,
                                )

@app.route('/confirm/<operation>/<value>',methods=['GET','POST'])
@login_required
def ep_confirm(operation,value):
    user=g.user
    #
    if operation not in confirmOperations:
        flashMessage('critical','Error','internal error in "confirm"')
        return redirect(url_for('ep_index'))
    else:
        tOpe=confirmOperations[operation]
        #
        form=ConfirmForm()
        if form.validate_on_submit():
            if form.ok.data:
                return redirect(url_for(tOpe['okurl'],id=value,confirm=1))
            else:
                return redirect(url_for(tOpe['cancelurl'],restore='y'))
        else:
            form.redirecturl.data=str(value)
            return render_template  (
                                        'confirm.html',
                                        title='Confirm operation?',
                                        form=form,
                                        submiturl='ep_confirm',
                                        value=value,
                                        operation=operation,
                                        message=tOpe['message'](value),
                                    )

@app.route('/btest', methods=['GET','POST'])
@login_required
def ep_btest():
    form=BTestForm()
    if form.validate_on_submit():
        if form.yesButton.data:
            flashMessage('info','Done','The operation completed successfully.')
        elif form.noButton.data:
            flashMessage('warning','Try Again','It looks that your attempt temporarily failed.')
        else:
            flash('WTF?')
        return redirect(url_for('ep_index'))
    else:
        form.text.data='Sample text.'
        return render_template('btest.html', form=form)

@app.route('/fbex')
def ep_fbex():
    from markupsafe import Markup
    flash(Markup('<strong>Critical</strong> message'), 'critical')
    return render_template('fbex.html', title='Aaa')
