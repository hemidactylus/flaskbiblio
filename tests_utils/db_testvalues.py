# db test values to populate (minimally) the DB

# tablename -> list-of-rows
_testvalues={
    'user': [
                {
                    'name': 'Stefano',
                    'passwordhash': '123',
                },
                {
                    'name': 'Annabelle',
                    'passwordhash': 'qwerty',
                },
                {
                    'name': 'Fiorenza',
                    'passwordhash': 'cagnoli',
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
                {
                    'firstname': 'Gennaro',
                    'lastname': 'Sbucciapesche',
                },
                {
                    'firstname': 'Filippo',
                    'lastname': 'Roditorsoli',
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
                {
                    'tag': 'PT',
                    'name': 'Portuguese',
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
                    'lasteditor':    1,
                    'lasteditdate':  '',
                },
                {
                    'title':         'Guida alle bucce',
                    'authors':       '3,4',
                    'booktype':      'ESS',
                    'inhouse':       False,
                    'notes':         'Mediocre',
                    'languages':     'IT',
                    'lasteditor':    1,
                    'lasteditdate':  '',
                },
            ],
}
