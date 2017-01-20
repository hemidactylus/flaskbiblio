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
    statList={}
    # base book counter
    statList[('nbooks','')]=1
    # booktype
    statList[('G_booktype',qBook.booktype)]=1
    # language(s)
    for lang in qBook.languages.split(','):
        statList[('G_language',lang)]=1
    # inhouse
    statList[('G_inhouse',bool(int(qBook.inhouse)))]=1
    # house
    statList[('G_house',qBook.house)]=1
    # done
    return statList

def statFromAuthor(qAuthor):
    '''
        extracts a map (statname,statsubtype) -> counter
        from an author
    '''
    return {('nauthors',''): 1}
