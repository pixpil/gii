import sys
from pyqode.core import api, modes, panels
from pyqode.core.api import Panel, ColorScheme
from pyqode.core.backend import server
from pyqode.json import modes as json_modes, panels as json_panels
from pyqode.json.api import JSONFoldDetector


class JSONCodeEdit(api.CodeEdit):
    """
    Pre-configured JSON code editor widgets that provides a better support for
    JSON than :class:`pyqode.core.widgets.GenericCodeEdit`.
    """
    #: list of supported mime-types
    mimetypes = ['application/json', 'text/x-json']

    def __init__(self, parent=None,
                 server_script=server.__file__,
                 interpreter=sys.executable, args=None,
                 create_default_actions=True, color_scheme='qt',
                 reuse_backend=False):
        super(JSONCodeEdit, self).__init__(
            parent, create_default_actions=create_default_actions)

        self.backend.start(server_script, interpreter, args,
                           reuse=reuse_backend)

        # append panels
        self.panels.append(panels.SearchAndReplacePanel(),
                           Panel.Position.BOTTOM)
        self.panels.append(panels.FoldingPanel())
        self.panels.append(panels.LineNumberPanel())
        self.panels.append(json_panels.NavigationPanel(), Panel.Position.TOP)
        self.panels.append(panels.CheckerPanel())

        # append modes
        self.modes.append(json_modes.AutoCompleteMode())
        self.add_separator()
        self.modes.append(modes.ExtendedSelectionMode())
        self.modes.append(modes.CaseConverterMode())
        self.modes.append(modes.FileWatcherMode())
        self.modes.append(modes.CaretLineHighlighterMode())
        self.sh = self.modes.append(json_modes.JSONSyntaxHighlighter(
            self.document(), color_scheme=ColorScheme(color_scheme)))
        self.modes.append(modes.IndenterMode())
        self.modes.append(modes.ZoomMode())
        self.modes.append(modes.CodeCompletionMode())
        self.modes.append(modes.AutoIndentMode())
        self.modes.append(json_modes.AutoIndentMode())
        self.modes.append(modes.SymbolMatcherMode())
        self.modes.append(modes.OccurrencesHighlighterMode())
        self.modes.append(modes.SmartBackSpaceMode())
        self.modes.append(json_modes.JSONLinter())
        self.syntax_highlighter.fold_detector = JSONFoldDetector()

        self.panels.append(panels.EncodingPanel(), Panel.Position.TOP)
        self.panels.append(panels.ReadOnlyPanel(), Panel.Position.TOP)

    def clone(self):
        clone = self.__class__(
            parent=self.parent(), server_script=self.backend.server_script,
            interpreter=self.backend.interpreter, args=self.backend.args,
            color_scheme=self.syntax_highlighter.color_scheme.name)
        return clone

    def setPlainText(self, txt, mime_type='application/json',
                     encoding='utf-8'):
        super(JSONCodeEdit, self).setPlainText(txt, mime_type, encoding)
