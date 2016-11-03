# descriptor of DB for automated in-code use

tableDesc={
    'books': [
        ('id','INTEGER PRIMARY KEY AUTOINCREMENT'),
        ('title'     ,    'VARCHAR'),
        ('authorid'  ,    'INTEGER'),
        ('type'      ,    'INTEGER'),
        ('inhouse'   ,    'BOOLEAN'),
        ('notes'     ,    'VARCHAR'),
        ('languages' ,    'VARCHAR'),
        ('lasteditor',    'INTEGER'),
    ]
}
