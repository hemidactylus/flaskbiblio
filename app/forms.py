from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (
                        StringField,
                        BooleanField,
                        PasswordField,
                        SelectField,
                        SelectMultipleField,
                        SubmitField,
                        HiddenField,
                        IntegerField,
                    )
from wtforms.validators import DataRequired, NumberRange, EqualTo, Required

from app.utils.MultiCheckboxField import MultiCheckboxField
from app.utils.validators import AsciiOnly

# utility functions to sort out list population
def _sortTagNamePair(pairList):
    return sorted(map(lambda la: (la.tag, la.name), pairList),key=lambda p: p[1])
def _sortNameDescPair(pairList):
    return sorted(map(lambda la: (la.name, la.description), pairList),key=lambda p: p[0])
def _sortAuthorPair(pairList):
    # either here id->string, or in the form coerce=int (and other conversions) must be done
    # see: http://stackoverflow.com/questions/13964152/not-a-valid-choice-for-dynamic-select-field-wtforms#13964913
    return sorted(map(lambda au: (str(au.id), str(au)), pairList),key=lambda p: str(p[1]))

class ExportDataForm(FlaskForm):
    includeauthors = BooleanField('includeauthors', default = True)
    includemetadata=BooleanField('includemetadata', default=True)
    house=SelectField('house')
    submit = SubmitField('Export')

    def setHouses(self,hoPairList):
        self.house.choices=[('','(Include all houses)')]+_sortNameDescPair(hoPairList)
    def setDefaultHouse(self,default):
        self.house.data=default

class UploadDataForm(FlaskForm):
    file=FileField(validators=[FileRequired()])
    checkbox=BooleanField('checkbox', default=False)
    submit = SubmitField('Process data')

class LoginForm(FlaskForm):
    username = StringField('UserName', validators=[DataRequired(),AsciiOnly()])
    password = PasswordField('Password', validators=[DataRequired(),AsciiOnly()])
    login = SubmitField('Log In')

class EditAuthorForm(FlaskForm):
    force = BooleanField('force',default=False)
    firstname = StringField('authorfirstname', validators=[AsciiOnly()])
    lastname = StringField('authorlastname', validators=[DataRequired(),AsciiOnly()])
    notes=StringField('authornotes')
    authorid=HiddenField('authorid')
    submit=SubmitField('Save Author')

class ConfirmForm(FlaskForm):
    ok = SubmitField('OK')
    cancel = SubmitField('Cancel')
    redirecturl=HiddenField('redirecturl')

class UserSettingsForm(FlaskForm):
    submit = SubmitField('Save settings')
    requireconfirmation = BooleanField('requireconfirmation', default=True)
    checksimilarity = BooleanField('checksimilarity', default=True)
    defaulthousesearch = BooleanField('defaulthousesearch',default=True)
    resultsperpage = IntegerField('resultsperpage', validators=[Required(),NumberRange(min=1)])
    house=SelectField('house')
    def setHouses(self,hoPairList):
        self.house.choices=_sortNameDescPair(hoPairList)

class ChangePasswordForm(FlaskForm):
    submit = SubmitField('Change password')
    oldpassword = PasswordField('oldpassword', validators=[DataRequired(), AsciiOnly()])
    newpassword = PasswordField('newpassword', [Required(), AsciiOnly(),
                                                EqualTo('confirmpassword', message='New password mismatch')])
    confirmpassword  = PasswordField('confirmpassword')

class SearchAuthorForm(FlaskForm):
    # search criteria
    firstname=StringField('firstname',validators=[AsciiOnly()])
    lastname=StringField('lastname',validators=[AsciiOnly()])
    similarity=BooleanField('similarity')
    # sorting options
    sortby=SelectField('sortby', choices=[
        ('lastname','Last name'),
        ('firstname','First name'),
    ])
    #
    submit=SubmitField('Search')

class SearchBookForm(FlaskForm):
    # Search criteria
    title=StringField('title', validators=[AsciiOnly()])
    author=SelectField('author')
    booktype=SelectField('booktype')
    language=SelectField('language')
    inhouse=SelectField('inhouse',choices=[('-1','<Optional>'),('1','In-house'),('0','Out')])
    house=SelectField('house')
    similarity=BooleanField('similarity')
    def setHouses(self,hoPairList):
        self.house.choices=[('-1','<Optional>'),('-2','(Include all houses)')]+_sortNameDescPair(hoPairList)
    # sorting options
    sortby=SelectField('sortby', choices=[
        ('relevance','Relevance'),
        ('title','Title'),
        ('booktype','Booktype'),
        ('lastedit','Last edit'),
    ])
    #
    submit=SubmitField('Search')

    def setAuthors(self,auPairList):
        self.author.choices=[('-1','<Optional>')]+_sortAuthorPair(auPairList)

    def setBooktypes(self,btPairList):
        self.booktype.choices=[('-1','<Optional>')]+_sortTagNamePair(btPairList)

    def setLanguages(self,laPairList):
        self.language.choices=[('-1','<Optional>')]+_sortTagNamePair(laPairList)

class EditBookForm(FlaskForm):
    force = BooleanField('force',default=False)
    title = StringField('booktitle',validators=[AsciiOnly()])
    inhouse = BooleanField('bookinhouse', default=True)
    notes = StringField('booknotes',validators=[AsciiOnly()])
    inhousenotes = StringField('inhousenotes',validators=[AsciiOnly()])
    booktype = SelectField('booktype')
    languages = MultiCheckboxField('languages')
    additem=SubmitField('Add author')
    delitem=SubmitField('Remove author')
    submit=SubmitField('Save book')
    newauthors=SelectField('newauthors')
    delauthors=SelectField('delauthors')
    authorlist=HiddenField('authorlist')
    bookid=HiddenField('bookid')
    house=SelectField('house')

    def setHouses(self,hoPairList):
        self.house.choices=_sortNameDescPair(hoPairList)
    def validate(self):
        rv=FlaskForm.validate(self)
        if not rv:
            return False
        elif self.additem.data:
            if (self.newauthors.data is None or self.newauthors.data=='-1'):
                self.newauthors.errors.append('Choose something')
                return False
            else:
                return True
        elif self.delitem.data:
            if (self.delauthors.data is None or self.delauthors.data=='-1'):
                self.delauthors.errors.append('Choose something')
                return False
            else:
                return True
        else:
            toret=True
            if not(self.title.data and self.title.data!=''):
                self.title.errors.append('Please enter a title')
                toret = False
            if not self.inhouse.data and not (self.inhousenotes.data and self.inhousenotes.data!=''):
                self.inhousenotes.errors.append('Please specify a location')
                toret = False
            return toret

    def setAuthorsToAdd(self,auPairList):
        self.newauthors.choices=[('-1','<Please select>')]+_sortAuthorPair(auPairList)

    def setAuthorsToDelete(self,auPairList):
        self.delauthors.choices=[('-1','<Please select>')]+_sortAuthorPair(auPairList)

    def setBooktypes(self,btPairList):
        self.booktype.choices=_sortTagNamePair(btPairList)

    def setLanguages(self,laPairList):
        self.languages.choices=_sortTagNamePair(laPairList)
