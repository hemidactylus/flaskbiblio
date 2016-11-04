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
