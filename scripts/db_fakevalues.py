'''
    db_fakevalues.py

    Fake author/book values to insert for tests
'''
dbFakeValues={
    'author': [
                {
                    'firstname': 'Jose',
                    'lastname': 'Saramago',
                    'notes': '',
                },
                {
                    'firstname': 'Lev',
                    'lastname': 'Tolstoj',
                    'notes': '',
                },
                {
                    'firstname': 'Gennaro',
                    'lastname': 'Sbucciapesche',
                    'notes': 'Inventato',
                },
                {
                    'firstname': 'Filippo',
                    'lastname': 'Roditorsoli',
                    'notes': 'Erfunden',
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
                    'lasteditor':    'Stefano',
                    'lasteditdate':  '',
                    'house':         'VillaMu',
                },
                {
                    'title':         'Guida alle bucce',
                    'authors':       'Tolstoj,Sbucciapesche',
                    'booktype':      'ESS',
                    'inhouse':       False,
                    'inhousenotes':  'Nel frutteto',
                    'notes':         'Mediocre',
                    'languages':     'IT',
                    'lasteditor':    'Stefano',
                    'lasteditdate':  '',
                    'house':         'Mansarda',
                },
            ],
}
