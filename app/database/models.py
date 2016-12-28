'''
    Sqlite ORM models
'''

import hashlib

from orm import Model
from app.utils.ascii_checks import ascifiiString
from app.utils.stringlists import unrollStringList

class AutoModel(Model):
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self,k,v)
    # a method to ascifii string fields - not optimally implemented, perhaps
    def forceAscii(self):
        for k,q in self.__dict__.items():
            if isinstance(q,str):
                setattr(self,k,ascifiiString(q,forceAsciification=True))

class Book(AutoModel):
    title=str
    authors=str
    booktype=str
    inhouse=int # bool
    inhousenotes=str
    notes=str
    languages=str
    lasteditor=str
    lasteditdate=str

    def resolveReferences(self,authors={},languages={},booktypes={}):
        self.resAuthors=sorted([authors[int(aID)] for aID in self.authors.split(',') if len(aID)>0 and int(aID) in authors])
        self.resLanguages=sorted([languages[lID] for lID in self.languages.split(',') if lID in languages])
        self.resBooktype=booktypes.get(self.booktype,'')
        return self

    def __str__(self):
        if 'resAuthors' in self.__dict__:
            return '%s (%s)' % (self.title, ' - '.join([a.lastname for a in self.resAuthors]))
        else:
            return '%s' % (self.title)

    def __lt__(self,other):
        return self.title.lower() < other.title.lower()

class User(AutoModel):
    name=str
    passwordhash=str
    lastlogindate=str
    canedit=int

    @staticmethod
    def _hashString(message):
        return hashlib.sha256(message.encode()).hexdigest()

    def checkPassword(self,stringToCheck):
        return self._hashString(stringToCheck) == self.passwordhash

    @property
    def is_authenticated(self):
        # True unless the object represents a user that should not be allowed to authenticate for some reason
        return True

    @property
    def is_active(self):
        # True for users unless they are inactive, for example because they have been banned
        return True

    @property
    def is_anonymous(self):
        # True only for fake users that are not supposed to log in to the system
        return False

    def get_id(self):
        # unique identifier for the user, in unicode format
        return str(self.id)  # python 3

    def __repr__(self):
        return '<User %r>' % (self.name)

class Author(AutoModel):
    firstname=str
    lastname=str
    bookcount=int
    booklist=str

    def resolveReferences(self,books={}):
        self.resBooks=sorted([books[bID] for bID in unrollStringList(self.booklist) if bID in books])
        return self

    def __str__(self):
        return '%s, %s' % (self.lastname, self.firstname)

    def __lt__(self,other):
        if self.lastname.lower()!=other.lastname.lower():
            return self.lastname.lower() < other.lastname.lower()
        else:
            return self.firstname.lower() < other.lastname.lower()

class Language(AutoModel):
    tag=str
    name=str

    def __lt__(self,other):
        return self.name.lower() < other.name.lower()

class Booktype(AutoModel):
    tag=str
    name=str

    def __lt__(self,other):
        return self.name.lower() < other.name.lower()

tableToModel={
    'user': User,
    'author': Author,
    'language': Language,
    'booktype': Booktype,
    'book': Book,
}
