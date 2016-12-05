from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, PasswordField
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
    # TO FIX BLA BLA
    booktype = StringField('booktype',validators=[DataRequired()])
    languages = StringField('booklanguages', validators=[DataRequired()])
    authors = StringField('bookauthors')
