# validators.py: custom validators for use with WTForms

from wtforms.validators import ValidationError, StopValidation
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

class IntegerString():
    '''
        Validates (optionally empty strings or) integer-looking strings
    '''
    def __init__(self, allowEmpty=True, message=None):
        if not message:
            message='Please insert a number%s.' % (' or leave blank' if allowEmpty else '')
        self.message=message
        self.allowEmpty=allowEmpty

    def __call__(self,form,field):
        if self.allowEmpty and field.data=='':
            return
        try:
            qnum=int(field.data)
        except:
            # we interrupt the validation chain since usually the next ones, if any, assume numeric
            raise StopValidation(self.message)
        return
