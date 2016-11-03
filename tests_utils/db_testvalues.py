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
    'books': [
                {
                    'title':         'Tutti i nomi',
                    'authorid':      1,
                    'type':          2,
                    'inhouse':       True,
                    'notes':         'Carino',
                    'languages':     'PT,IT',
                    'lasteditor':    100,
                },
                {
                    'title':         'Tutti i nomi',
                    'authorid':      1,
                    'type':          2,
                    'inhouse':       True,
                    'notes':         'Carino',
                    'languages':     'PT,IT',
                    'lasteditor':    100,
                },
            ],
}
