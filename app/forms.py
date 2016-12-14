from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField, SelectField
from wtforms.validators import DataRequired

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
    languages = StringField('booklanguages', validators=[DataRequired()])
    authors = StringField('bookauthors')

    def setBooktypes(self,btPairList):
        self.booktype.choices=map(lambda bt: (bt.tag, bt.name), btPairList)

class TestForm(FlaskForm):
    test = SelectField(
            'Programming Language',
            # choices=[('cpp', 'C++'), ('py', 'Python'), ('text', 'Plain Text')]
        )

    def setc(self,c):
        self.test.choices=c