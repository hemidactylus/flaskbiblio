# db test values to populate (minimally) the DB

# tablename -> list-of-rows
_testvalues={
    'statistic': [
            ],
    'house':[
                {
                    'name': 'VillaMu',
                    'description': 'Villa Musichins',
                    'nbooks': 0,
                },
                {
                    'name': 'Mansarda',
                    'description': 'Mansarda San Giovanni Bosco',
                    'nbooks': 0,
                },
            ],
    'user': [
                {
                    'name': 'Stefano',
                    'passwordhash': 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', #'123',
                    'canedit': 1,
                    'resultsperpage': 10,
                    'requireconfirmation': 1,
                    'checksimilarity': 1,
                    'house': 'VillaMu',
                    'defaulthousesearch': 0,
                },
                {
                    'name': 'Fiorenza',
                    'passwordhash': 'ed4090b094156d720dfe3c3139be353ddb89b3db36ceada7594fe84b6c34b9af', #'cagnoli',
                    'canedit': 0,
                    'resultsperpage': 10,
                    'requireconfirmation': 1,
                    'checksimilarity': 1,
                    'house': 'VillaMu',
                    'defaulthousesearch': 1,
                },
                {
                    'name': 'Carla',
                    'passwordhash': '490cb1006519621f1927f13c77a51bcef714e5e909c7e7fc771a925c5b2894da', # 'Volpe'
                    'canedit': 1,
                    'resultsperpage': 10,
                    'requireconfirmation': 1,
                    'checksimilarity': 1,
                    'house': 'Mansarda',
                    'defaulthousesearch': 0,
                },
            ],
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
