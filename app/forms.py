from flask_wtf import FlaskForm
from wtforms import (
                        StringField,
                        BooleanField,
                        PasswordField,
                        SelectField,
                        SelectMultipleField,
                        SubmitField,
                        HiddenField,
                    )
from wtforms.validators import DataRequired

from app.utils.MultiCheckboxField import MultiCheckboxField
from app.utils.validators import AsciiOnly

# utility functions to sort out list population
def _sortTagNamePair(pairList):
    return sorted(map(lambda la: (la.tag, la.name), pairList),key=lambda p: p[1])
def _sortAuthorPair(pairList):
    # either here id->string, or in the form coerce=int (and other conversions) must be done
    # see: http://stackoverflow.com/questions/13964152/not-a-valid-choice-for-dynamic-select-field-wtforms#13964913
    return sorted(map(lambda au: (str(au.id), str(au)), pairList),key=lambda p: str(p[1]))

class LoginForm(FlaskForm):
    username = StringField('UserName', validators=[DataRequired(),AsciiOnly()])
    password = PasswordField('Password', validators=[DataRequired(),AsciiOnly()])
    remember_me = BooleanField('remember_me', default=False)

class EditAuthorForm(FlaskForm):
    force = BooleanField('force',default=False)
    firstname = StringField('authorfirstname', validators=[AsciiOnly()])
    lastname = StringField('authorlastname', validators=[DataRequired(),AsciiOnly()])
    authorid=HiddenField('authorid')

class ConfirmForm(FlaskForm):
    ok = SubmitField('OK')
    cancel = SubmitField('Cancel')
    redirecturl=HiddenField('redirecturl')

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
