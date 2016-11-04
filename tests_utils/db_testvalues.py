# db test values to populate (minimally) the DB

# tablename -> list-of-rows
_testvalues={
    'user': [
                {
                    'name': 'Stefano',
                    'passwordhash': '123',
                },
            ],
    'author': [
                {
                    'firstname': 'Jose',
                    'lastname': 'Saramago',
                },
                {
                    'firstname': 'Lev',
                    'lastname': 'Tolstoj',
                },
            ],
    'language': [
                {
                    'tag': 'IT',
                    'name': 'Italian',
                },
                {
                    'tag': 'EN',
                    'name': 'English',
                },
                {
                    'tag': 'DE',
                    'name': 'German',
                },
            ],
    'booktype': [
                {
                    'tag': 'DIZ',
                    'name': 'Dictionary',
                },
                {
                    'tag': 'BKT',
                    'name': 'Booklet',
                },
                {
                    'tag': 'FIC',
                    'name': 'Fiction',
                },
                {
                    'tag': 'ESS',
                    'name': 'Essay',
                },
            ],
    'book': [
                {
                    'title':         'Tutti i nomi',
                    'authors':       '1',
                    'booktype':      'FIC',
                    'inhouse':       True,
                    'notes':         'Carino',
                    'languages':     'PT,IT',
                    'lasteditor':    100,
                },
                {
                    'title':         'Guida alle bucce',
                    'authors':       '3',
                    'booktype':      'ESS',
                    'inhouse':       False,
                    'notes':         'Mediocre',
                    'languages':     'IT',
                    'lasteditor':    101,
                },
            ],
}
