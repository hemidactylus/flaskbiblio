# validators.py: custom validators for use with WTForms

from wtforms.validators import ValidationError

from app.utils.ascii_checks import isAscii

# a validator is any function accepting (form,field) as arguments
# and capable of raising wtforms.validators.ValidationError

class AsciiOnly():
    '''
        Validator concerning the usage of strictly ascii chars in a text field
    '''
    def __init__(self,message=None):
        if not message:
            message='Please use only ASCII characters.'
        self.message=message

    def __call__(self,form,field):
        if not isAscii(field.data):
            raise ValidationError(self.message)
