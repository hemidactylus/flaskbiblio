from orm import Model

class AutoModel(Model):
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self,k,v)

class Book(AutoModel):
    title=str
    authors=str
    booktype=str
    inhouse=int # bool
    notes=str
    languages=str
    lasteditor=str

    def resolveReferences(self,authors={},languages={},booktypes={}):
        self.resAuthors=sorted([authors[int(aID)] for aID in self.authors.split(',') if len(aID)>0 and int(aID) in authors])
        self.resLanguages=sorted([languages[lID] for lID in self.languages.split(',') if lID in languages])
        self.resBooktype=booktypes.get(self.booktype,'')
        return self

    def __str__(self):
        return '%s (%s)' % (self.title, ' - '.join([a.lastname for a in self.resAuthors]))

class User(AutoModel):
    name=str
    passwordhash=str

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

    def __str__(self):
        return '%s, %s' % (self.lastname, self.firstname)

    def __lt__(self,other):
        if self.lastname!=other.lastname:
            return self.lastname < other.lastname
        else:
            return self.firstname < other.lastname

class Language(AutoModel):
    tag=str
    name=str

    def __lt__(self,other):
        return self.name < other.name

class Booktype(AutoModel):
    tag=str
    name=str

    def __lt__(self,other):
        return self.name < other.name

tableToModel={
    'user': User,
    'author': Author,
    'language': Language,
    'booktype': Booktype,
    'book': Book,
}
