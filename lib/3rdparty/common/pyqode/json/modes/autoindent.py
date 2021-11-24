from pyqode.core import modes


class AutoIndentMode(modes.AutoIndentMode):
    """
    Provides automatic json specific auto indentation.
    """
    def _get_indent(self, cursor):
        text = cursor.block().text().strip()
        pre, post = super(AutoIndentMode, self)._get_indent(cursor)
        if text.endswith(('{', '[')):
            post += self.editor.tab_length * ' '
        elif text.endswith(('}', ']')) or not text.endswith(','):
            post = post[self.editor.tab_length:]
        return pre, post
