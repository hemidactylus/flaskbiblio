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
    return sorted(map(lambda au: (au.id, str(au)), pairList),key=lambda p: str(p[1]))

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
    # authors=SelectField('author',choices=[(1,'a'),(2,'b')],validators=[DataRequired()])
    additem=SubmitField('AddItem')
    submit=SubmitField('GoGo')
    newitem=StringField('newitem')

    def validate(self):
        rv=FlaskForm.validate(self)
        if not rv:
            return False
        elif self.additem.data and len(self.newitem.data)==0:
            self.newitem.errors.append('Insert something')
            return False
        else:
            return True

    # def setAuthors(self,auPairList):
    #     self.authors.choices=_sortAuthorPair(auPairList)
