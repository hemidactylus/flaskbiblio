# db test values to populate (minimally) the DB

'''
            [id]
    title         VARCHAR,
    authorid      INTEGER,
    type          INTEGER,
    inhouse       BOOLEAN,
    notes         VARCHAR,
    languages     VARCHAR,
    lasteditor    INTEGER
'''

# tablename -> list-of-rows
_testvalues={
    'users': [
                {
                    'name': 'Stefano',
                    'passwordhash': '123',
                },
            ],
    'authors': [
                {
                    'firstname': 'Jose',
                    'lastname': 'Saramago',
                },
                {
                    'firstname': 'Lev',
                    'lastname': 'Tolstoj',
                },
            ],
    'languages': [
                {
                    'id': 'IT',
                    'name': 'Italian',
                },
                {
                    'id': 'EN',
                    'name': 'English',
                },
                {
                    'id': 'DE',
                    'name': 'German',
                },
            ],
    'booktypes': [
                {
                    'id': 'DIZ',
                    'name': 'Dictionary',
                },
                {
                    'id': 'BKT',
                    'name': 'Booklet',
                },
                {
                    'id': 'FIC',
                    'name': 'Fiction',
                },
                {
                    'id': 'SAG',
                    'name': 'Essay',
                },
            ],
    'books': [
                {
                    'title':         'Tutti i nomi',
                    'authors':       '1',
                    'type':          2,
                    'inhouse':       True,
                    'notes':         'Carino',
                    'languages':     'PT,IT',
                    'lasteditor':    100,
                },
                {
                    'title':         'Guida alle bucce',
                    'authors':       '3',
                    'type':          -2,
                    'inhouse':       False,
                    'notes':         'Mediocre',
                    'languages':     'IT',
                    'lasteditor':    101,
                },
            ],
}
