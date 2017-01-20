'''
    statistics.py : tools to uniformly deal with biblio statistics
'''

'''
                {
                    'name': 'nbooks',
                    'description': 'Number of books',
                    'value': '0',
                },
                {
                    'name': 'nauthors',
                    'description': 'Number of authors',
                    'value': '0',
                },
'''

def statFromBook(qBook):
    '''
        extracts a map (statname,statsubtype) -> counter
        from a book
    '''
    return {('nbooks',''): 1}

def statFromAuthor(qAuthor):
    '''
        extracts a map (statname,statsubtype) -> counter
        from an author
    '''
    return {('nauthors',''): 1}
