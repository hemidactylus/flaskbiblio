from flask_wtf import FlaskForm
from wtforms import (
                        StringField,
                        BooleanField,
                        PasswordField,
                        SelectField,
                        SelectMultipleField,
                    )
from wtforms.validators import DataRequired

from app.utils.MultiCheckboxField import MultiCheckboxField

# utility functions to sort out list population
def _sortTagNamePair(pairList):
    return sorted(map(lambda la: (la.tag, la.name), pairList),key=lambda p: p[1])

class LoginForm(FlaskForm):
    username = StringField('UserName', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

class NewAuthorForm(FlaskForm):
    firstname = StringField('authorfirstname', validators=[DataRequired()])
    lastname = StringField('authorlastname', validators=[DataRequired()])

class NewBookForm(FlaskForm):
    title = StringField('booktitle', validators=[DataRequired()])
    inhouse = BooleanField('bookinhouse', default=True)
    notes = StringField('booknotes')
    booktype = SelectField('booktype')
    # TO FIX ONE-TO-MANY
    languages = MultiCheckboxField('languages')
    authors = StringField('bookauthors')

    def setBooktypes(self,btPairList):
        self.booktype.choices=_sortTagNamePair(btPairList)

    def setLanguages(self,laPairList):
        self.languages.choices=_sortTagNamePair(laPairList)

class TestForm(FlaskForm):
    test=MultiCheckboxField('test')

    def setLanguages(self,laPairList):
        self.test.choices=_sortTagNamePair(laPairList)
