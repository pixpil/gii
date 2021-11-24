import sys

from qtpy import QtWidgets, QtGui
from pyqode.core.widgets import GenericCodeEdit
from pyqode.core.api import CodeEdit, ColorScheme
from pyqode.core import panels
from pyqode.core import modes
from pyqode.core.backend import server
from pyqode.core.api import CodeEdit, Panel, SyntaxHighlighter, \
		CharBasedFoldDetector, IndentFoldDetector, ColorScheme
from pyqode.core.modes import PygmentsSH

from .LuaSupport import modes as LuaSupportMode

class CodeEditor( CodeEdit ):
# generic
	mimetypes = []

	#: the list of mimetypes that use char based fold detector
	_char_based_mimetypes = [
			'text/x-php',
			'text/x-c++hdr',
			'text/x-c++src',
			'text/x-chdr',
			'text/x-csrc',
			'text/x-csharp',
			'text/x-lua',
			'application/javascript'
	]

	def __init__(self, parent=None ):
		super(CodeEditor, self).__init__( parent, False )
		# self.setObjectName( 'CodeEditor' )
		self.font_size = 12
		self.use_spaces_instead_of_tabs = False
		server_script = server.__file__
		interpreter = sys.executable
		# self.backend.start( server_script, interpreter, None, reuse=True )
		# append panels
		self.panels.append(panels.LineNumberPanel())
		self.panels.append(panels.SearchAndReplacePanel(),
											 Panel.Position.BOTTOM)

		self.panels.append(panels.FoldingPanel())

		# append modes
		# self.modes.append(modes.AutoCompleteMode())
		self.modes.append(modes.ExtendedSelectionMode())
		self.modes.append(modes.CaseConverterMode())
		# self.modes.append(modes.FileWatcherMode())
		self.modes.append(modes.CaretLineHighlighterMode())
		self.modes.append(modes.RightMarginMode())
		sh = self.modes.append(modes.PygmentsSH(
				self.document(), color_scheme=ColorScheme('monokai')))
		sh.fold_detector = IndentFoldDetector()
		self.modes.append( modes.ZoomMode() )
		# self.modes.append( modes.CodeCompletionMode() )
		self.modes.append( modes.AutoIndentMode() )
		self.modes.append( modes.IndenterMode() )
		self.modes.append( modes.SymbolMatcherMode() )
		self.modes.append( modes.OccurrencesHighlighterMode() )
		self.modes.append( modes.SmartBackSpaceMode() )
		self.modes.append( LuaSupportMode.CommentsMode() )
		# self.panels.append(panels.EncodingPanel(), Panel.Position.TOP)

	def setPlainText(self, txt, mime_type='', encoding=''):
		if mime_type is None:
			mime_type = self.file.mimetype
		if encoding is None:
			encoding = self.file.encoding
		if mime_type:
			self.syntax_highlighter.set_lexer_from_mime_type( mime_type )
		else:
			self.syntax_highlighter.set_lexer_from_filename(self.file.path)
		try:
			mimetype = self.syntax_highlighter._lexer.mimetypes[0]
		except (AttributeError, IndexError):
			mimetype = ''

		if mimetype in self._char_based_mimetypes:
			self.syntax_highlighter.fold_detector = CharBasedFoldDetector()
		else:
			self.syntax_highlighter.fold_detector = IndentFoldDetector()

		super(CodeEditor, self).setPlainText(txt, mime_type, encoding)

# sh.color_scheme = ColorScheme('monokai')