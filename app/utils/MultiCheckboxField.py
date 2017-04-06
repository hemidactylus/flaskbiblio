# Multi checkbox field. Adapted from: https://gist.github.com/doobeh/4668212

from wtforms import widgets, SelectMultipleField

def _encloseTags(tagName,attrDict,body):
    '''
        prepares a "<tagName k="v"...>body</tagName>" string
    '''
    dictDesc=' %s' % (' '.join('%s="%s"' % (k,v) for k,v in attrDict.items())) if attrDict else ''
    return '<%s%s>%s</%s>' % (tagName,dictDesc,body,tagName)

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

    def __call__(self,*pargs,**kwargs):
        '''
            Self-generation of the whole part of the form.
            The generated lsit of checkboxes must resemble the following
                <ul class="list-inline" disabled="disabled" id="languages" size="80">
                    <li>
                        <input id="languages-0" name="languages" type="checkbox" value="ZZ">
                        <label for="languages-0">(Other)</label>
                    <li>
                    ...
                </ul>
            The 'disabled' field can be passed or not and the rendering must change accordingly.
            See https://github.com/wtforms/wtforms/pull/81 where this code took inspiration from.
        '''
        disDict={}
        if 'disabled' in kwargs:
            disDict['disabled']=kwargs['disabled']
            del kwargs['disabled']
        if 'class_' in kwargs:
            disDict['class']=kwargs['class_']
        if 'tabindex' in kwargs:
            disDict['tabindex']=kwargs['tabindex']
            del kwargs['tabindex']
        ulDict={(k if k[-1]!='_' else k[:-1]):v for k,v in kwargs.items()}
        return widgets.HTMLString(_encloseTags(
            'ul',
            ulDict,
            '\n'.join(
                _encloseTags(
                    'li',
                    {},
                    sub(**disDict) + '\n' + _encloseTags(
                        'label',
                        {'for': '%s-%i' % (self.name,objIndex)},
                        sub.label
                    ),
                ) for objIndex,sub in enumerate(self)
            )
        ))
