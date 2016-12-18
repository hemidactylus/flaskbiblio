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

# utility functions to sort out list population
def _sortTagNamePair(pairList):
    return sorted(map(lambda la: (la.tag, la.name), pairList),key=lambda p: p[1])
def _sortAuthorPair(pairList):
    # either here id->string, or in the form coerce=int (and other conversions) must be done
    # see: http://stackoverflow.com/questions/13964152/not-a-valid-choice-for-dynamic-select-field-wtforms#13964913
    return sorted(map(lambda au: (str(au.id), str(au)), pairList),key=lambda p: str(p[1]))

class LoginForm(FlaskForm):
    username = StringField('UserName', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class NewAuthorForm(FlaskForm):
    firstname = StringField('authorfirstname', validators=[DataRequired()])
    lastname = StringField('authorlastname', validators=[DataRequired()])

# class NewBookForm(FlaskForm):
#     title = StringField('booktitle', validators=[DataRequired()])
#     inhouse = BooleanField('bookinhouse', default=True)
#     notes = StringField('booknotes')
#     booktype = SelectField('booktype')
#     # TO FIX ONE-TO-MANY
#     languages = MultiCheckboxField('languages')
#     authors = StringField('bookauthors')

#     def setBooktypes(self,btPairList):
#         self.booktype.choices=_sortTagNamePair(btPairList)

#     def setLanguages(self,laPairList):
#         self.languages.choices=_sortTagNamePair(laPairList)

class TestForm(FlaskForm):

    title = StringField('booktitle')
    inhouse = BooleanField('bookinhouse', default=True)
    notes = StringField('booknotes')
    booktype = SelectField('booktype')
    languages = MultiCheckboxField('languages')
    additem=SubmitField('AddItem')
    delitem=SubmitField('DelItem')
    submit=SubmitField('GoGo')
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
            if self.title.data and self.title.data!='':
                return True
            else:
                self.name.errors.append('Cannot be empty~')
                return False

    def setAuthorsToAdd(self,auPairList):
        self.newauthors.choices=[('-1','<Please select>')]+_sortAuthorPair(auPairList)

    def setAuthorsToDelete(self,auPairList):
        self.delauthors.choices=[('-1','<Please select>')]+_sortAuthorPair(auPairList)

    def setBooktypes(self,btPairList):
        self.booktype.choices=_sortTagNamePair(btPairList)

    def setLanguages(self,laPairList):
        self.languages.choices=_sortTagNamePair(laPairList)
