import tempfile
import os
import sys

from qtpy import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore import Qt, QEvent, QObject

from gii    import signals
from gii.SceneEditor import SceneEditorModule

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

ConsoleUI,BaseClass = uic.loadUiType( _getModulePath('console.ui') )

signals.register( 'console.exec' )
signals.register( 'console.exec_remote' )

##----------------------------------------------------------------##
class StdouCapture():
	def __init__(self):
		self.prevfd = None
		self.prev = None

		self.file = file = tempfile.NamedTemporaryFile()
		self.where=file.tell()

		sys.stdout.flush()
		self.prevfd = os.dup(sys.stdout.fileno())
		os.dup2(file.fileno(), sys.stdout.fileno())
		self.prev = sys.stdout
		sys.stdout = os.fdopen(self.prevfd, "w")

	def stop(self):
		os.dup2(self.prevfd, self.prev.fileno())
		sys.stdout = self.prev
		self.file.close()

	def read(self):
		file=self.file
		file.seek(self.where)
		output=None
		while True:
			line = file.readline()
			if not line:
				self.where = file.tell()
				return output
			else:
				if not output: output=''
				output+=line
		
class Console( SceneEditorModule ):
	name       = 'console'
	# dependency = 'debug_view'
	def write(self,text):
		self.panel.appendText(text)		

	def onLoad(self):
		self.container = self.requestDockWindow(
				'Console',
				title   = 'Console',
				minSize = (100,100),
				dock    = 'bottom',
				toolWindow = False
			)

		self.panel = self.container.addWidget(
				ConsoleWindow()
			)
		self.panel.module = self

		# self.stdoutCapture = StdouCapture()
		# self.stdOutFile=self.stdoutCapture.file
		# self.refreshTimer=self.container.startTimer( 10, self.doRefresh)
		# sys.stdout=self

	def doRefresh(self):
		if self.alive:
			self.panel.appendText(self.stdoutCapture.read())

	def onUnload(self):
		pass

##----------------------------------------------------------------##
class ConsoleWindow( QtWidgets.QWidget ):
	"""docstring for ConsoleWindow"""
	def __init__(self):
		super(ConsoleWindow, self).__init__()
		
		self.ui = ConsoleUI()
		self.ui.setupUi( self )

		self.history=[]
		self.historyCursor=0		
		self.ui.buttonExec.clicked.connect(self.execCommand)
		self.ui.buttonClear.clicked.connect(self.clearText)		
		
		self.ui.textInput.installEventFilter(self)
		self.ui.textInput.setFocusPolicy(Qt.StrongFocus)
		self.setFocusPolicy(Qt.StrongFocus)

	def eventFilter(self, obj, event):
		if event.type() == QEvent.KeyPress:
			if self.inputKeyPressEvent(event):
				return True

		return QObject.eventFilter(self, obj, event)

	def inputKeyPressEvent(self, event):
		key=event.key()
		if key == Qt.Key_Down: #next cmd history
			self.nextHistory()
		elif key == Qt.Key_Up: #prev
			self.prevHistory()
		elif key == Qt.Key_Escape: #clear
			self.ui.textInput.clear()
		elif key == Qt.Key_Return or key == Qt.Key_Enter:
			self.execCommand()
		else:
			return False
		return True

	def execCommand(self):
		text = self.ui.textInput.text()
		self.history.append(text)
		if len(self.history) > 10: self.history.pop(1)
		self.historyCursor=len(self.history)
		self.ui.textInput.clear()
		# self.appendText(self.module.stdoutCapture.read())
		self.appendText(">>")
		self.appendText(text)
		self.appendText("\n")

		targetName = self.ui.comboTarget.currentText()
		if targetName == 'Game':
			signals.emit( 'console.exec_remote', text.encode('utf-8') )
		elif targetName == 'Editor':
			signals.emit( 'console.exec', text.encode('utf-8') )

	def prevHistory(self):
		count=len(self.history)
		if count == 0: return
		self.historyCursor = max(self.historyCursor-1, 0)
		self.ui.textInput.setText(self.history[self.historyCursor])

	def nextHistory(self):
		count=len(self.history)
		if count<= self.historyCursor:
			self.historyCursor=count-1
			self.ui.textInput.clear()
			return
		self.historyCursor = min(self.historyCursor+1, count-1)
		if self.historyCursor<0: return
		self.ui.textInput.setText(self.history[self.historyCursor])

	def appendText(self, text):
		if not text: return
		self.ui.textOutput.insertPlainText(text)
		self.ui.textOutput.moveCursor(QtGui.QTextCursor.End)

	def clearText(self):
		self.ui.textOutput.clear()

