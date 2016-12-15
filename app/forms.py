from flask_wtf import FlaskForm
from wtforms import (
                        StringField,
                        BooleanField,
                        PasswordField,
                        SelectField,
                        SelectMultipleField,
                        SubmitField,
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
    additem=SubmitField('AddItem')
    submit=SubmitField('GoGo')
    newitem=SelectField('newitem')

    def validate(self):
        rv=FlaskForm.validate(self)
        if not rv:
            return False
        elif self.additem.data and (self.newitem.data is None or self.newitem.data=='-1'):
            self.newitem.errors.append('Choose something')
            return False
        else:
            return True

    def setAuthors(self,auPairList):
        self.newitem.choices=[('-1','<Please select>')]+_sortAuthorPair(auPairList)
