'''
    statistics.py : tools to uniformly deal with biblio statistics
'''

# stat descriptors structure. Higher orders come first. Zero is reserved
statDescriptors={
    'nbooks': {
        'order': 100,
        'simple': True,
        'description': lambda statname: 'Number of books',
        'subtype': lambda subtype,resPar: '',
    },
    'nauthors': {
        'order': 90,
        'simple': True,
        'description': lambda statname: 'Number of authors',
        'subtype': lambda subtype,resPar: '',
    },
    'G_language': {
        'order': 40,
        'simple': False,
        'description': lambda statname: 'Books by language',
        'subtype': lambda subtype,resPar: resPar['languages'][subtype].name,
    },
    'G_booktype': {
        'order': 30,
        'simple': False,
        'description': lambda statname: 'Books by type',
        'subtype': lambda subtype,resPar: resPar['booktypes'][subtype].name,
    },
    'G_house': {
        'order': 20,
        'simple': False,
        'description': lambda statname: 'Books by house',
        'subtype': lambda subtype,resPar: resPar['houses'][subtype].name,
    },
    'G_inhouse': {
        'order': 10,
        'simple': False,
        'description': lambda statname: 'Books by in-house status',
        'subtype': lambda subtype,resPar: {
            'True': 'In-house',
            'False': 'Out',
        }.get(subtype,'(other)'),
    },
    'G_nofirstname': {
        'order': 5,
        'simple': False,
        'description': lambda statname: 'Authors by first-name',
        'subtype': lambda subtype,resPar: {
            'False': 'Have first name',
            'True': 'No first name',
        }.get(subtype,'(other)'),
    },
}
defaultDescriptor={
    'order': 0,
    'simple': True,
    'description': lambda statname: statname,
    'subtype': lambda subtype,resPar: '(%s)' % subtype,
}

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
    statList[('G_inhouse',str(bool(qBook.inhouse)))]=1
    # house
    statList[('G_house',qBook.house)]=1
    # done
    return statList

def statFromAuthor(qAuthor):
    '''
        extracts a map (statname,statsubtype) -> counter
        from an author
    '''
    statList={}
    # base author counter
    statList[('nauthors','')]=1
    # has first name?
    statList[('G_nofirstname',str(qAuthor.firstname==''))]=1    
    #
    return statList

def sortStatistics(statIterator,resolveParams):
    '''
        Converts the raw iterator on all statistics retrieved from DB
        into a sorted, grouped, formatted list of items ready-for-the-table
    '''
    # 1. regroup
    statGroups={}
    for qStat in statIterator:
        if qStat.name not in statGroups:
            statGroups[qStat.name]={
                'order': statDescriptors.get(qStat.name,defaultDescriptor)['order'],
                'items': [],
            }
        statGroups[qStat.name]['items'].append(qStat)
    from pprint import pprint
    # 2. make into a neat list. Simple and unregistered groups become
    #    ordered list items with name and subtype if any,
    #    while unsimple group gain a headings and subtype-only list items
    statList=[]
    for sGName, sGList in sorted(statGroups.items(),key=lambda it: it[1]['order'],reverse=True):
        qDesc=statDescriptors.get(sGName,defaultDescriptor)
        if qDesc['simple']:
            for sItem in sGList['items']:
                statList.append({
                        'description': qDesc['description'](sItem.name),
                        'subtype': qDesc['subtype'](sItem.subtype,resolveParams),
                        'value': sItem.value,
                    })
        else:
            # sort by decreasing value within a group, apply formatting function,
            # add a header
            statList.append({
                'description': qDesc['description'](sItem.name),
                'subtype': '',
                'value': '',
            })
            for sItem in sorted(sGList['items'],key=lambda elem: elem.value,reverse=True):
                statList.append({
                    'description': '',
                    'subtype': qDesc['subtype'](sItem.subtype,resolveParams),
                    'value': sItem.value,
                })
    return statList
