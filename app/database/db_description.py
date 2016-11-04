# descriptor of DB for automated in-code use

tableDesc={
    'books': [
        ('id','INTEGER PRIMARY KEY AUTOINCREMENT'),
        ('title'     ,      'VARCHAR'),
        ('authors'   ,      'VARCHAR'),
        ('type'      ,      'INTEGER'),
        ('inhouse'   ,      'BOOLEAN'),
        ('notes'     ,      'VARCHAR'),
        ('languages' ,      'VARCHAR'),
        ('lasteditor',      'INTEGER'),
    ],
    'users': [
        ('id','INTEGER PRIMARY KEY AUTOINCREMENT'),
        ('name',            'VARCHAR'),
        ('passwordhash',    'VARCHAR'),
    ],
    'authors': [
        ('id','INTEGER PRIMARY KEY AUTOINCREMENT'),
        ('firstname',       'VARCHAR'),
        ('lastname',        'VARCHAR'),
    ],
    'languages': [
        ('id',              'VARCHAR'),
        ('name',            'VARCHAR'),
    ],
    'booktypes': [
        ('id',              'VARCHAR'),
        ('name',            'VARCHAR'),
    ],
}
