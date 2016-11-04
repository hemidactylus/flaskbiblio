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
    lasteditor=int

    def resolveReferences(self,authors={},languages={},booktypes={}):
        self.resAuthors=[authors[int(aID)] for aID in self.authors.split(',') if int(aID) in authors]
        self.resLanguages=[languages[lID] for lID in self.languages.split(',') if lID in languages]
        self.resBooktype=booktypes.get(self.booktype,'')
        return self

class User(AutoModel):
    name=str
    passwordhash=str

class Author(AutoModel):
    firstname=str
    lastname=str

class Language(AutoModel):
    tag=str
    name=str

class Booktype(AutoModel):
    tag=str
    name=str

tableToModel={
    'user': User,
    'author': Author,
    'language': Language,
    'booktype': Booktype,
    'book': Book,
}
