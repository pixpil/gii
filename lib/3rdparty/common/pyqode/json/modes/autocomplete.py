from pyqode.core import modes
from pyqode.core.api import TextHelper


class AutoCompleteMode(modes.AutoCompleteMode):
    """
    Customised auto complete mode, specialised for JSON.
    """
    def __init__(self):
        super(AutoCompleteMode, self).__init__()
        try:
            self.QUOTES_FORMATS.pop("'")
            self.SELECTED_QUOTES_FORMATS.pop("'")
            self.MAPPING.pop("'")
        except KeyError:
            pass

    def _on_key_pressed(self, event):
        helper = TextHelper(self.editor)
        indent = helper.line_indent() * ' '
        if self.editor.textCursor().positionInBlock() == len(indent):
            self.QUOTES_FORMATS['"'] = '%s:'
        else:
            self.QUOTES_FORMATS['"'] = '%s'
        self.QUOTES_FORMATS['{'] = '\n' + indent + '%s'
        self.QUOTES_FORMATS['['] = '\n' + indent + '%s'
        super(AutoCompleteMode, self)._on_key_pressed(event)
