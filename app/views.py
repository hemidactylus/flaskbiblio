from flask import   (
                        render_template,
                        flash,
                        redirect,
                        session,
                        url_for,
                        request,
                        g,
                        send_file,
                        send_from_directory,
                    )
from flask_login import  login_user, logout_user, current_user, login_required
from datetime import datetime
from werkzeug.datastructures import MultiDict
from markupsafe import Markup
from io import BytesIO
import json
import uuid
import os

from app import app, lm
from .forms import (
                        LoginForm,
                        EditAuthorForm,
                        EditBookForm,
                        ConfirmForm,
                        UserSettingsForm,
                        ChangePasswordForm,
                        SearchBookForm,
                        SearchAuthorForm,
                        ExportDataForm,
                        UploadDataForm,
                    )
from app.utils.stringlists import unrollStringList

from config import (
                        DATETIME_STR_FORMAT,
                        SHORT_DATETIME_STR_FORMAT,
                        SIMILAR_AUTHOR_THRESHOLD,
                        SIMILAR_BOOK_THRESHOLD,
                        FILENAME_DATETIME_STR_FORMAT,
                        TEMP_DIRECTORY,
                    )

from app.utils.string_vectorizer import makeIntoVector, scalProd
from app.utils.importlibrary import (
                                        read_and_parse_csv,
                                        process_book_list,
                                        import_from_bilist_json,
                                    )
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
                                        dbGetUserById,
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
from app.statistics.statistics import sortStatistics

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
    return dbGetUserById(id)

@app.route('/')
@app.route('/index')
def ep_index():
    user = g.user
    if user is not None:
        rawStats=dbGetAll('statistic')
        message=sortStatistics(rawStats,resolveParams())
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

@app.route('/houses')
@login_required
def ep_houses():
    user = g.user
    # equip house-objects with the 'users' list
    # reload houses and users
    houses=sorted(list(dbGetAll('house')))
    allUsers=list(dbGetAll('user'))
    for hObj in houses:
        if user.canedit:
            hObj.users=[]
            for qU in sorted(u for u in allUsers if u.house==hObj.name):
                hObj.users.append({
                        'name': qU.name,
                        'strong': qU.name==user.name,
                    })
        else:
            hObj.users=len([u for u in allUsers if u.house==hObj.name])
    #
    return render_template  (
                                "houses.html",
                                title='Houses',
                                user=user,
                                houses=houses,
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
            status,delId=dbDeleteBook(int(id),userHouse=user.house)
            if status:
                flashMessage('info','Success','Book successfully deleted.')
            else:
                flashMessage('warning','Could not delete book', delId)
        return redirect(url_for('ep_books',restore='y'))
    else:
        flashMessage('error','Cannot proceed','user "%s" has no write privileges.' % user.name)
        return redirect(url_for('ep_books',restore='y'))

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
            # check that all books are in the user's house before proceeding
            for bookId in unrollStringList(rAuthor.booklist):
                qBook=dbGetBook(bookId)
                if qBook.house!=user.house:
                    flashMessage('warning','Cannot delete','author has books in other houses')
                    return redirect(url_for('ep_authors',restore='y'))
            #
            if user.requireconfirmation and rAuthor.bookcount>0 and not confirm:
                return redirect(url_for('ep_confirm',
                                        operation='deleteauthor',
                                        value=id,
                                        )
                                )
            else:
                status,delId=dbDeleteAuthor(int(id),userHouse=user.house)
                if status:
                    flashMessage('info','Success','author successfully deleted.')
                else:
                    flashMessage('warning','Could not delete author', delId)
        else:
            flashMessage('critical','Could not delete author','author not found')
        return redirect(url_for('ep_authors',restore='y'))
    else:
        flashMessage('error','Cannot proceed','user "%s" has no write privileges.' % user.name)
        return redirect(url_for('ep_authors',restore='y'))

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
        if user.checksimilarity and not form.force.data:
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
                                    editable=user.canedit,
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
                                editable=user.canedit,
                              )

def retrieveUsers():
    return dbMakeDict(dbGetAll('user'))

def resolveParams():
    # refresh authors list
    authors=list(dbGetAll('author'))
    authorsDict=dbMakeDict(authors)
    houses=list(dbGetAll('house'))
    housesDict=dbMakeDict(houses,fieldname='name')
    # pack the rest
    return {
                'authors': authorsDict,
                'languages': languagesDict,
                'booktypes': booktypesDict,
                'houses': housesDict,
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
    houses=sorted(list(dbGetAll('house')))
    form.setHouses(houses)
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
        if form.house.data!='-1':
            bookSearchArgs['house']=form.house.data
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
    #
    if 'house' not in reqargs:
        if user.defaulthousesearch:
            # ugly workaround to prepare default search criterion here and pass it fully prepared
            # to the DB primitive
            reqargs=MultiDict({k:v for k,v in list(reqargs.items())+[('house',user.house)]})
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
    houses=sorted(list(dbGetAll('house')))
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
        form.house.data=request.args.get('house')
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
        # editing an existing book
        qBook=dbGetBook(int(paramId))
        if form.title.data is None:
            if qBook:
                authorParameter=qBook.authors
                form.title.data=qBook.title
                form.inhouse.data=int(qBook.inhouse)
                form.notes.data=qBook.notes
                form.inhousenotes.data=qBook.inhousenotes
                form.booktype.data=qBook.booktype
                form.house.data=qBook.house
                form.languages.data=qBook.languages.split(',')
            else:
                flashMessage('critical','Internal error', 'error retrieving book')
                return redirect(url_for('ep_books'))
        form.setHouses(houses)
        bookEditable=user.canedit and user.house==qBook.house
        formTitle='Edit Book' if bookEditable else 'View Book'
    else:
        # new book
        formTitle='New Book'
        form.setHouses([h for h in houses if h.name==user.house])
        bookEditable=user.canedit
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
        house=form.house.data,
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
                                        house=editedBook.house,
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
            if user.checksimilarity and not form.force.data:
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
                return render_template  (
                                        'editbook.html',
                                        title=formTitle,
                                        formtitle=formTitle,
                                        form=form,
                                        user=user,
                                        items=[{'description': str(au), 'id': au.id} for au in presentAuthors],
                                        authorlist=','.join(authorIdList),
                                        showforce=True,
                                        editable=bookEditable,
                                    )
            else:
                # HERE the actual save/update is triggered
                newEntry=editedBook.id is None
                if bookEditable:
                    result,updatedBook=dbAddReplaceBook(editedBook,
                                        resolve=True,
                                        resolveParams=resolveParams(),
                                        userHouse=user.house)
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
        return render_template  (
                                    'editbook.html',
                                    title=formTitle,
                                    formtitle=formTitle,
                                    form=form,
                                    user=user,
                                    items=[{'description': str(au), 'id': au.id} for au in presentAuthors],
                                    authorlist=','.join(authorIdList),
                                    editable=bookEditable,
                                )

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
    houses=sorted(list(dbGetAll('house')))
    form.setHouses(houses)
    if form.validate_on_submit():
        user.requireconfirmation=bool(form.requireconfirmation.data)
        user.checksimilarity=bool(form.checksimilarity.data)
        user.defaulthousesearch=bool(form.defaulthousesearch.data)
        user.resultsperpage=int(form.resultsperpage.data)
        user.house=form.house.data
        result,newuser=dbReplaceUser(user)
        if result:
            flashMessage('info','Done','settings updated successfully.')
        else:
            flashMessage('critical','Warning', 'an error occurred trying to update the settings.')
        return redirect(url_for('ep_index'))
    else:
        form.checksimilarity.data=user.checksimilarity
        form.requireconfirmation.data=user.requireconfirmation
        form.resultsperpage.data=str(user.resultsperpage)
        form.defaulthousesearch.data=user.defaulthousesearch
        form.house.data=user.house
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

@app.route('/advanced')
@login_required
def ep_advanced():
    user=g.user
    return render_template  (
                                'advanced.html',
                                title='Advanced operations',
                                user=user,
                            )

@app.route('/exportdata', methods=['GET','POST'])
@login_required
def ep_exportdata():
    user=g.user
    resParams=resolveParams()
    form=ExportDataForm()
    houses=sorted(list(dbGetAll('house')))
    form.setHouses(houses,default=user.house if user.defaulthousesearch else '')
    if form.validate_on_submit():
        userList=dbMakeDict(dbGetAll('user'))
        # prepare and export the whole structure
        exportedFileName='exportedBiblio_%s.json' % datetime.now().strftime(FILENAME_DATETIME_STR_FORMAT)
        if form.house.data=='':
            bookFilter=lambda bo: True
        else:
            bookFilter=lambda bo: bo.house==form.house.data
        if form.includemetadata.data:
            exportForm='long'
        else:
            exportForm='short'
        bookList=[
            bk.exportableDict(resolveParams=resParams, userList=userList, form=exportForm)
            for bk in sorted(dbGetAll('book'))
            if bookFilter(bk)
        ]
        exportableStructure={'books': bookList}
        if form.includeauthors.data:
            authorList=[au.exportableDict(resolveParams=resParams) for au in sorted(dbGetAll('author'))]
            exportableStructure['authors']=authorList
        bIO = BytesIO()
        bIO.write(json.dumps(exportableStructure,indent=4,sort_keys=True).encode('utf-8'))
        bIO.seek(0)
        return send_file    (
                                bIO,
                                attachment_filename=exportedFileName,
                                as_attachment=True,
                            )
    else:
        return render_template  (
                                    'exportdataform.html',
                                    form=form,
                                    user=user,
                                    title='Export data',
                                )

@app.route('/importhelp')
@login_required
def ep_importhelp():
    user=g.user
    return render_template  (
                                'importhelp.html',
                                user=user,
                            )

@app.route('/importdata')
@login_required
def ep_importdata():
    user=g.user
    if not user.canedit:
        flashMessage('error','Cannot proceed','user "%s" has no write privileges.' % user.name)
        return redirect(url_for('ep_advanced'))
    return render_template  (
                                'importdata.html',
                                user=user,
                            )

@app.route('/importstep/<_step>',methods=['GET','POST'])
@login_required
def ep_importstep(_step):
    # validation of parameter:
    # Steps 1,2,3 -> csv-to-bookjson, bookjson-to-fulljson, fulljson-to-DB
    if _step not in ['1','2','3']:
        flashMessage('critical','Malformed link','this link is invalid.')
        return(redirect(url_for('ep_index')))
    else:
        step=int(_step)
    user=g.user
    if not user.canedit:
        flashMessage('error','Cannot proceed','user "%s" has no write privileges.' % user.name)
        return redirect(url_for('ep_advanced'))
    #
    form=UploadDataForm()
    if form.validate_on_submit():
        # actual handling of uploaded data according to the processing step
        try:
            # make the uploaded file into a string and pass it to the full import procedure
            fileString=form.file.data.read().decode('utf-8').split('\n')
            if step==1:
                # csv to json
                parsedCSV=read_and_parse_csv(fileString,skipHeader=form.checkbox.data)
                # store the response in a local file, ready to serve it.
                storedFileName='step%i_%s.json' % (step,uuid.uuid4())
                json.dump(parsedCSV,open(os.path.join(TEMP_DIRECTORY,storedFileName),'w'),indent=4,sort_keys=True)
                session['returnfile']={
                    'step': step,
                    'filename': storedFileName,
                    'reportname': None,
                }
                return redirect(url_for('ep_importsucceeded',_step=step))
            elif step==2:
                # bookJson to fullJson
                fullJson=process_book_list(fileString)
                storedFileName='step%i_%s.json' % (step,uuid.uuid4())
                json.dump(fullJson,open(os.path.join(TEMP_DIRECTORY,storedFileName),'w'),indent=4,sort_keys=True)
                # prepare a report
                warningJson={
                    'books': [
                        bs['title']
                        for bs in fullJson['books']
                        if '_warnings' in bs
                    ],
                    'authors': [
                        '%s, %s' % (au['lastname'],au['firstname'])
                        for au in fullJson['authors']
                        if '_warnings' in au
                    ],
                }
                reportFileName='report_step%i_%s.json' % (step,uuid.uuid4())
                json.dump(warningJson,open(os.path.join(TEMP_DIRECTORY,reportFileName),'w'),indent=4,sort_keys=True)
                #
                session['returnfile']={
                    'step': step,
                    'filename': storedFileName,
                    'reportname': reportFileName,
                }
                return redirect(url_for('ep_importsucceeded',_step=step))
            elif step==3:
                # fullJson to database
                db=dbGetDatabase()
                resultReport=import_from_bilist_json(fileString,user,db)
                # store the report
                reportFileName='report_step%i_%s.json' % (step,uuid.uuid4())
                json.dump(resultReport,open(os.path.join(TEMP_DIRECTORY,reportFileName),'w'),indent=4,sort_keys=True)
                # done
                session['returnfile']={
                    'step': step,
                    'filename': None,
                    'reportname': reportFileName,
                }
                db.commit()
                return redirect(url_for('ep_importsucceeded',_step=step))
            else:
                flashMessage('critical','Malformed request','inconsistent value of "step".')
                return redirect(url_for('ep_importdata'))
        except Exception as e:
            flashMessage('critical','Error during operation','exception "%s" occurred.' % e)
            return redirect(url_for('ep_importdata'))
    else:
        # finalise the appearance of the dialog and display it
        showCheckbox=[True,False,False][step-1]
        checkboxLabel=[
            'Skip a first header line',
            '(none)',
            '(none)',
        ][step-1]
        formTitle=[
            'CSV to book-JSON conversion',
            'book-JSON to full-JSON conversion',
            'Import full-JSON',
        ][step-1]
        return render_template  (
                                    'uploaddataform.html',
                                    form=form,
                                    user=user,
                                    step=step,
                                    title=formTitle,
                                    showCheckbox=showCheckbox,
                                    checkboxLabel=checkboxLabel,
                                )

@app.route('/importsucceeded/<_step>')
@login_required
def ep_importsucceeded(_step):
    user=g.user
    if 'returnfile' in session and _step in ['1','2','3']:
        # here the user lands after submitting a file for one of the import steps
        # Display a report and provide a download link
        # prepare the report
        step=int(_step)
        if session['returnfile']['reportname'] is not None:
            # load report-file to display it
            reportFileName=os.path.join(TEMP_DIRECTORY,session['returnfile']['reportname'])
            loadedReport=json.load(open(reportFileName))
            # prepare report to display
            report=[] # a triple for each line to display in the page
            if step==3:
                # compile a list of report items
                report.append(('Authors inserted (%i)' % len(loadedReport['authors_insertion']['success']),'',''))
                for eAu,eErrList in loadedReport['authors_insertion']['success'].items():
                    report.append(('',eAu,', '.join(eErrList)))
                report.append(('Books inserted (%i)' % len(loadedReport['books_insertion']['success']),'',''))
                for bAu,bErrList in loadedReport['books_insertion']['success'].items():
                    report.append(('',bAu,', '.join(bErrList)))
                if len(loadedReport['authors_insertion']['errors'])>0:
                    report.append(('Error while inserting authors:','',''))
                    for eAu,eErrList in loadedReport['authors_insertion']['errors'].items():
                        report.append(('',eAu,', '.join(eErrList)))
                if len(loadedReport['books_insertion']['errors'])>0:
                    report.append(('Error while inserting books:','',''))
                    for bAu,bErrList in loadedReport['books_insertion']['errors'].items():
                        report.append(('',bAu,', '.join(bErrList)))
            elif step==2:
                report.append(('Authors with warnings (%i)' % len(loadedReport['authors']),'',''))
                for au in loadedReport['authors']:
                    report.append(('',au,''))
                report.append(('Books with warnings (%i)' % len(loadedReport['books']),'',''))
                for bo in loadedReport['books']:
                    report.append(('',bo,''))
            else:
                #should never happen
                report=('report',('',('',json.dumps(loadedReport))))
            os.remove(reportFileName)
            session['returnfile']['reportname']=None
        else:
            report=None
        # display everything
        title='Operation successful'
        return render_template  (
                                    'importsucceeded.html',
                                    user=user,
                                    step=step,
                                    title=title,
                                    nextstep=int(step)!=3,
                                    report=report,
                                )
    else:
        flashMessage('critical','Malformed link','this link is invalid.')
        return redirect(url_for('ep_importdata'))

@app.route('/getimportresults/<step>')
@login_required
def ep_getimportresults(step):
    if 'returnfile' in session and session['returnfile']['filename'] is not None:
        servedFileName=os.path.join(TEMP_DIRECTORY,session['returnfile']['filename'])
        if os.path.isfile(servedFileName):
            loadedFile=open(servedFileName).read()
            fileTitle='import-Step%i-%s.json' % (
                session['returnfile']['step'],
                datetime.now().strftime(FILENAME_DATETIME_STR_FORMAT)
            )
            bIO = BytesIO()
            bIO.write(loadedFile.encode())
            bIO.seek(0)
            os.remove(servedFileName)
            session['returnfile']['filename']=None
            return send_file    (
                                    bIO,
                                    attachment_filename=fileTitle,
                                    as_attachment=True,
                                )
            del session['returnfile']
        else:
            flashMessage('critical','Malformed link','this link is invalid.')
            return redirect(url_for('ep_importdata'))
    else:
        flashMessage('critical','Malformed link','this link is invalid.')
        return redirect(url_for('ep_importdata'))

@app.route('/about')
def ep_about():
    user=g.user
    return render_template  (
                                'about.html',
                                user=user,
                            )

@app.route('/emptyhouse')
@login_required
def ep_emptyhouse():
    user=g.user
    if not user.canedit:
        flashMessage('error','Cannot proceed','user "%s" has no write privileges.' % user.name)
        return redirect(url_for('ep_advanced'))
    return render_template(
        'deletedataform.html',
        title='Delete data',
    )

@app.route('/deletedata')
@app.route('/deletedata/<authors>')
@login_required
def ep_deletedata(authors='n'):
    user=g.user
    if not user.canedit:
        flashMessage('error','Cannot proceed','user "%s" has no write privileges.' % user.name)
        return redirect(url_for('ep_advanced'))
    report={}
    db=dbGetDatabase()
    if authors=='y':
        report['au_kept']=0
        report['au_deleted']=0
        report['au_errors']=0
        # delete those authors whose only books belong to user's house
        for qAu in dbGetAll('author'):
            if any([
                dbGetBook(bookId).house!=user.house
                for bookId in unrollStringList(qAu.booklist)
            ]):
                report['au_kept']+=1
            else:
                success,_=dbDeleteAuthor(qAu.id,db=db,userHouse=user.house)
                if success:
                    report['au_deleted']+=1
                else:
                    report['au_errors']+=1
    # now deal with books
    report['bo_deleted']=0
    report['bo_errors']=0
    report['bo_kept']=0
    for qBo in dbGetAll('book'):
        if qBo.house==user.house:
            success,_=dbDeleteBook(qBo.id,db=db,userHouse=user.house)
            if success:
                report['bo_deleted']+=1
            else:
                report['bo_errors']+=1
        else:
            report['bo_kept']+=1
    # done.
    db.commit()
    # return final counters - (mandatory_msg, key, description)
    reportDesc=[
        (True,'bo_deleted','Books deleted'),
        (False,'bo_kept','Book kept'),
        (False,'bo_errors','Book with errors'),
        (True,'au_deleted','Authors deleted'),
        (False,'au_kept','Authors kept'),
        (False,'au_errors','Authors with errors'),
    ]
    #
    flashMessage(
        'info',
        'Delete succeeded',
        '%s.' % (
            '. '.join([
                '%s: %i' % (desc, report[key])
                for mandatory,key,desc in reportDesc
                if key in report and (mandatory or report[key]>0)
            ])
        )
    )
    return redirect(url_for('ep_advanced'))

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
