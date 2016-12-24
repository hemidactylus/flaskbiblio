# db test values to populate (minimally) the DB

# tablename -> list-of-rows
_testvalues={
    'user': [
                {
                    'name': 'Stefano',
                    'passwordhash': 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', #'123',
                },
                {
                    'name': 'Fiorenza',
                    'passwordhash': 'ed4090b094156d720dfe3c3139be353ddb89b3db36ceada7594fe84b6c34b9af', #'cagnoli',
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
                {
                    'tag': 'NO',
                    'name': 'Norwegian',
                },
                {
                    'tag': 'FR',
                    'name': 'French',
                },
                {
                    'tag': 'RU',
                    'name': 'Russian',
                },
                {
                    'tag': 'ZZ',
                    'name': '(Other)',
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
                {
                    'tag': 'ART',
                    'name': 'Art book',
                },
                {
                    'tag': 'OTH',
                    'name': '(Other)',
                },
            ],
    'book': [
                {
                    'title':         'Tutti i nomi',
                    'authors':       'Saramago',
                    'booktype':      'FIC',
                    'inhouse':       True,
                    'inhousenotes':  '',
                    'notes':         'Carino',
                    'languages':     'PT,IT',
                    'lasteditor':    1,
                    'lasteditdate':  '',
                },
                {
                    'title':         'Guida alle bucce',
                    'authors':       'Tolstoj,Sbucciapesche',
                    'booktype':      'ESS',
                    'inhouse':       False,
                    'inhousenotes':  'Nel frutteto',
                    'notes':         'Mediocre',
                    'languages':     'IT',
                    'lasteditor':    1,
                    'lasteditdate':  '',
                },
            ],
}
