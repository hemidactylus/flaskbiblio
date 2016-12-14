# Multi checkbox field. Adapted from: https://gist.github.com/doobeh/4668212

from wtforms import widgets, SelectMultipleField

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()
