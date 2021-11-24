import sys
import os


from qtpy import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt, QEventLoop, QEvent, QObject
from time import time

from gii.core import *

from gii.qt.controls.Window    import MainWindow
from .QtEditorModule            import QtEditorModule
from gii.qt.dialogs            import *
from gii.qt.IconCache					import getIcon, getGiiIcon

_QT_SETTING_FILE = 'qt.ini'

QEventName = {}
QEventName[0]   =	'None'
QEventName[130] =	'AccessibilityDescription'
QEventName[119] =	'AccessibilityHelp'
QEventName[86]  =	'AccessibilityPrepare'
QEventName[114] =	'ActionAdded'
QEventName[113] =	'ActionChanged'
QEventName[115] =	'ActionRemoved'
QEventName[99]  =	'ActivationChange'
QEventName[121] =	'ApplicationActivate'
QEventName[122] =	'ApplicationDeactivate'
QEventName[36]  =	'ApplicationFontChange'
QEventName[37]  =	'ApplicationLayoutDirectionChange'
QEventName[38]  =	'ApplicationPaletteChange'
QEventName[35]  =	'ApplicationWindowIconChange'
QEventName[68]  =	'ChildAdded'
QEventName[70]  =	'ChildInserted'
QEventName[69]  =	'ChildPolished'
QEventName[71]  =	'ChildRemoved'
QEventName[40]  =	'Clipboard'
QEventName[19]  =	'Close'
QEventName[200] =	'CloseSoftwareInputPanel'
QEventName[178] =	'ContentsRectChange'
QEventName[82]  =	'ContextMenu'
QEventName[183] =	'CursorChange'
QEventName[52]  =	'DeferredDelete'
QEventName[60]  =	'DragEnter'
QEventName[62]  =	'DragLeave'
QEventName[61]  =	'DragMove'
QEventName[63]  =	'Drop'
QEventName[98]  =	'EnabledChange'
QEventName[10]  =	'Enter'
QEventName[150] =	'EnterEditFocus'
QEventName[124] =	'EnterWhatsThisMode'
QEventName[116] =	'FileOpen'
QEventName[8]   =	'FocusIn'
QEventName[9]   =	'FocusOut'
QEventName[97]  =	'FontChange'
QEventName[188] =	'GrabKeyboard'
QEventName[186] =	'GrabMouse'
QEventName[159] =	'GraphicsSceneContextMenu'
QEventName[164] =	'GraphicsSceneDragEnter'
QEventName[166] =	'GraphicsSceneDragLeave'
QEventName[165] =	'GraphicsSceneDragMove'
QEventName[167] =	'GraphicsSceneDrop'
QEventName[163] =	'GraphicsSceneHelp'
QEventName[160] =	'GraphicsSceneHoverEnter'
QEventName[162] =	'GraphicsSceneHoverLeave'
QEventName[161] =	'GraphicsSceneHoverMove'
QEventName[158] =	'GraphicsSceneMouseDoubleClick'
QEventName[155] =	'GraphicsSceneMouseMove'
QEventName[156] =	'GraphicsSceneMousePress'
QEventName[157] =	'GraphicsSceneMouseRelease'
QEventName[182] =	'GraphicsSceneMove'
QEventName[181] =	'GraphicsSceneResize'
QEventName[168] =	'GraphicsSceneWheel'
QEventName[18]  =	'Hide'
QEventName[27]  =	'HideToParent'
QEventName[127] =	'HoverEnter'
QEventName[128] =	'HoverLeave'
QEventName[129] =	'HoverMove'
QEventName[96]  =	'IconDrag'
QEventName[101] =	'IconTextChange'
QEventName[83]  =	'InputMethod'
QEventName[6]   =	'  KeyPress'
QEventName[7]   =	'  KeyRelease'
QEventName[89]  =	'LanguageChange'
QEventName[90]  =	'LayoutDirectionChange'
QEventName[76]  =	'LayoutRequest'
QEventName[11]  =	'Leave'
QEventName[151] =	'LeaveEditFocus'
QEventName[125] =	'LeaveWhatsThisMode'
QEventName[88]  =	'LocaleChange'
QEventName[176] =	'NonClientAreaMouseButtonDblClick'
QEventName[174] =	'NonClientAreaMouseButtonPress'
QEventName[175] =	'NonClientAreaMouseButtonRelease'
QEventName[173] =	'NonClientAreaMouseMove'
QEventName[177] =	'MacSizeChange'
QEventName[153] =	'MenubarUpdated'
QEventName[43]  =	'MetaCall'
QEventName[102] =	'ModifiedChange'
QEventName[4]   =	'MouseButtonDblClick'
QEventName[2]   =	'MouseButtonPress'
QEventName[3]   =	'MouseButtonRelease'
QEventName[5]   =	'MouseMove'
QEventName[109] =	'MouseTrackingChange'
QEventName[13]  =	'Move'
QEventName[12]  =	'Paint'
QEventName[39]  =	'PaletteChange'
QEventName[131] =	'ParentAboutToChange'
QEventName[21]  =	'ParentChange'
QEventName[212] =	'PlatformPanel'
QEventName[75]  =	'Polish'
QEventName[74]  =	'PolishRequest'
QEventName[123] =	'QueryWhatsThis'
QEventName[199] =	'RequestSoftwareInputPanel'
QEventName[14]  =	'Resize'
QEventName[117] =	'Shortcut'
QEventName[51]  =	'ShortcutOverride'
QEventName[17]  =	'Show'
QEventName[26]  =	'ShowToParent'
QEventName[50]  =	'SockAct'
QEventName[192] =	'StateMachineSignal'
QEventName[193] =	'StateMachineWrapped'
QEventName[112] =	'StatusTip'
QEventName[100] =	'StyleChange'
QEventName[87]  =	'TabletMove'
QEventName[92]  =	'TabletPress'
QEventName[93]  =	'TabletRelease'
QEventName[94]  =	'OkRequest'
QEventName[171] =	'TabletEnterProximity'
QEventName[172] =	'TabletLeaveProximity'
QEventName[1]   =	'Timer'
QEventName[120] =	'ToolBarChange'
QEventName[110] =	'ToolTip'
QEventName[184] =	'ToolTipChange'
QEventName[189] =	'UngrabKeyboard'
QEventName[187] =	'UngrabMouse'
QEventName[78]  =	'UpdateLater'
QEventName[77]  =	'UpdateRequest'
QEventName[111] =	'WhatsThis'
QEventName[118] =	'WhatsThisClicked'
QEventName[31]  =	'Wheel'
QEventName[132] =	'WinEventAct'
QEventName[24]  =	'WindowActivate'
QEventName[103] =	'WindowBlocked'
QEventName[25]  =	'WindowDeactivate'
QEventName[34]  =	'WindowIconChange'
QEventName[105] =	'WindowStateChange'
QEventName[33]  =	'WindowTitleChange'
QEventName[104] =	'WindowUnblocked'
QEventName[126] =	'ZOrderChange'
QEventName[169] =	'KeyboardLayoutChange'
QEventName[170] =	'DynamicPropertyChange'
QEventName[194] =	'TouchBegin'
QEventName[195] =	'TouchUpdate'
QEventName[196] =	'TouchEnd'
QEventName[203] =	'WinIdChange'
QEventName[198] =	'Gesture'
QEventName[202] =	'GestureOverride'

##----------------------------------------------------------------##
eventTime = 0
#keep here for debugging
class QtSupportEventFilter(QObject):
	def eventFilter(self, obj, event):
		# global eventTime
		e = event.type()
		# t = time.time()
		# dt = (t - eventTime) * 1000
		# eventTime = t
		# if dt > 1:
		# 	if e != 1:
		# 		print int(dt), QEventName.get(e, '???' ), obj
		# if   e == QEvent.ApplicationActivate:
		# 	signals.emitNow('app.activate')
		# elif e == QEvent.ApplicationDeactivate:
		# 	signals.emitNow('app.deactivate')		
		return QObject.eventFilter( self, obj, event )

##----------------------------------------------------------------##
class QtSupport( QtEditorModule ):
	def __init__( self ):
		self.statusWindow = None

	def getName( self ):
		return 'qt'

	def getDependency( self ):
		return []

	def getBaseDependency( self ):
		return []

	def setupStyle( self ):
		logging.info( 'setup style' )
		# setup styles
		# QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create('Windows'))
		QtCore.QDir.setSearchPaths( 'theme', [ self.getApp().getPath( 'data/theme' ) ] )
		
		QtGui.QFontDatabase.addApplicationFont( self.getApp().getPath( 'data/default_font.ttf' ) )
		QtGui.QFontDatabase.addApplicationFont( self.getApp().getPath( 'data/iosevka.ttf' ) )
		QtGui.QFontDatabase.addApplicationFont( self.getApp().getPath( 'data/lekton0.otf' ) )
		QtGui.QFontDatabase.addApplicationFont( self.getApp().getPath( 'data/recursive.ttf' ) )
		try:
			# styleSheetName = 'dark.qss'
			styleSheetName = 'gii.qss'
			# styleSheetName = 'white.qss'
			self.qtApp.setStyleSheet(
					open( self.getApp().getPath( 'data/theme/' + styleSheetName ) ).read() 
				)
		except Exception as e:
			# logging.info('style sheet not load',e)
			# QtWidgets.QApplication.setStyle(QtWidgets.QStyleFactory.create('CDE'))
			self.qtApp.setStyleSheet('''
				QWidget{
					font: 10pt;				
				}

				QMainWindow::Separator{
					width:4px;
					height:4px;
					border:1px solid #c9c9c9;
				}
				''')

	def setupMainWindow( self ):
		logging.info( 'loading main window' )
		self.mainWindow = QtMainWindow( None )
		self.mainWindow.setBaseSize( 800, 600 )
		self.mainWindow.resize( 800, 600 )
		# self.mainWindow.setFixedSize(0,0)
		# self.mainWindow.show()
		# self.mainWindow.raise_() #bring app to front
		self.mainWindow.hide()
		self.mainWindow.module = self

		self.sharedMenuBar = QtWidgets.QMenuBar( None )
		self.mainWindow.setMenuWidget( self.sharedMenuBar )
		
		self.menu = self.addMenuBar( 'main', self.sharedMenuBar )
		self.menu.addChild('&File').addChild([
			'System Status',
			'----',
			'Open Location|Ctrl+G',
			'----',
			'Asset Editor|F2',
			'Scene Editor|F3',
			'Debug View|F9',
			'----',
			'Refresh Theme',
			'----',
			'E&xit|Ctrl+Q',
			]
		)	
		# self.menu.addChild('&Edit').addChild( [
		# 	'Undo|Ctrl+Z',
		# 	'Redo|Ctrl+Shift+Z',
		# 	]
		# )
		self.menu.addChild('&Find')
		self.menu.addChild('&Window')
		QtWidgets.QApplication.clipboard().dataChanged.connect( self.onClipboardChanged )

	def getSharedMenubar( self ):
		return self.sharedMenuBar

	def showSystemStatusWindow( self ):
		if not self.statusWindow:
			self.statusWindow = self.requestSubWindow( 'SystemStatus',
					title     = 'System Status',
					size      = (200,200),
					minSize   = (200,200)
				)
			self.statusWindow.body = self.statusWindow.addWidgetFromFile(
					self.getApp().getPath( 'data/ui/SystemStatus.ui' )
				)
		self.statusWindow.show()
		self.statusWindow.raise_()

	def setActiveWindow(self, window):
		self.qtApp.setActiveWindow(window)

	def onLoad( self ):
		QtCore.QCoreApplication.addLibraryPath(os.path.join(os.path.dirname( QtCore.__file__), "plugins"))
		QtCore.QCoreApplication.setAttribute( Qt.AA_ShareOpenGLContexts )
		QtCore.QCoreApplication.setAttribute( Qt.AA_UseDesktopOpenGL )
		# QtCore.QCoreApplication.setAttribute( Qt.AA_EnableHighDpiScaling )
		# QtCore.QCoreApplication.setAttribute( Qt.AA_ForceRasterWidgets )
		QtCore.QCoreApplication.setAttribute( Qt.AA_DontCreateNativeWidgetSiblings )
		QtCore.QCoreApplication.setAttribute( Qt.AA_CompressHighFrequencyEvents )
		QtCore.QCoreApplication.setAttribute( Qt.AA_DontCheckOpenGLContextThreadAffinity )
		# QtCore.QCoreApplication.setAttribute( Qt.AA_DisableHighDpiScaling )
		# QtCore.QCoreApplication.setAttribute( Qt.AA_NativeWindows )
		# QtCore.QCoreApplication.setAttribute( Qt.AA_ImmediateWidgetCreation )
		QtGui.QGuiApplication.setAttribute( Qt.AA_EnableHighDpiScaling )
		

		logging.info('loading qtApp')

		try:
			from PyQt4.QtCore import QT_VERSION_STR
			from PyQt4.Qt import PYQT_VERSION_STR
		except Exception as e:
			from PyQt5.QtCore import QT_VERSION_STR
			from PyQt5.QtCore import PYQT_VERSION_STR

		print( 'QT:',  QT_VERSION_STR )
		print( 'PYQT:',  PYQT_VERSION_STR )
		# qtApp.setAttribute( Qt.AA_ImmediateWidgetCreation )
		self.qtApp = qtApp   = QtApplication( [] )

		if self.getApp().getPlatformName() != 'Darwin':
			qtApp.setWindowIcon( getGiiIcon() )
			
		logging.info('loading qtSetting')
		self.qtSetting = QtCore.QSettings(
					self.getProject().getConfigPath( _QT_SETTING_FILE ),
					QtCore.QSettings.IniFormat
				)

		self.setupStyle()
		self.setupMainWindow()		

		try:
			from .Qt5Fix import MacClipboardFix
			self.qt5MimeFix = MacClipboardFix()
		except Exception as e:
			pass

		self.initialized = True
		self.running     = False
		return True

	
	def needUpdate( self ):
		return True

	def onClipboardChanged( self ):
		mime = QtWidgets.QApplication.clipboard().mimeData()
		pass

	def onUpdate( self ):
		# self.qtApp.processEvents( QEventLoop.ExcludeUserInputEvents | QEventLoop.ExcludeSocketNotifiers )
		# self.qtApp.processEvents( QEventLoop.AllEvents, 12 )
		self.qtApp.processEvents()
	
	def getMainWindow( self ):
		return self.mainWindow

	def getQtSettingObject( self ):
		return self.qtSetting

	def promptOpenLocation( self ):
		text = QtWidgets.QApplication.clipboard().text()
		default = ''
		if text and text.startswith( 'gii://' ):
			default = text
		location = requestString( 'Opening location', 'Location:', default )
		if location:
			self.openLocation( location )

	def openLocation( self, url ):
		processGiiURL( url )
	
	def onStart( self ):	
		self.restoreWindowState( self.mainWindow )
		self.qtApp.processEvents( QEventLoop.AllEvents )

	def onStop( self ):
		self.saveWindowState( self.mainWindow )

	def onMenu(self, node):
		name = node.name
		if name == 'exit':
			self.getApp().tryStop()
			
		elif name == 'system_status':
			self.showSystemStatusWindow()
		elif name == 'scene_editor':
			self.getModule('scene_editor').setFocus()
		elif name == 'debug_view':
			self.getModule('debug_view').setFocus()
		elif name == 'refresh_theme':
			self.setupStyle()
		elif name == 'open_location':
			self.promptOpenLocation()
			

		elif name == 'copy':
			print('copy')
		elif name == 'paste':
			print('paste')
		elif name == 'cut':
			print('cut')

		elif name == 'undo':
			stack = EditorCommandRegistry.get().getCommandStack( 'scene_editor' )
			stack.undoCommand()

		elif name == 'redo':
			stack = EditorCommandRegistry.get().getCommandStack( 'scene_editor' )
			stack.redoCommand()
			

##----------------------------------------------------------------##
class QtApplication( QtWidgets.QApplication ):
	def event(self, event):
		e = event.type()
		if e == QtCore.QEvent.Close and event.spontaneous():
			if sys.platform.startswith('darwin'):
				event.ignore()
				return False

		elif e == QtCore.QEvent.FileOpen:
			url = event.url()
			if url and url.scheme() == 'gii':
				processGiiURL( url.toString() )

		elif e == QEvent.ApplicationActivate:
			signals.emitNow('app.activate')

		elif e == QEvent.ApplicationDeactivate:
			signals.emitNow('app.deactivate')		

		return QtWidgets.QApplication.event( self, event )

##----------------------------------------------------------------##
class QtMainWindow( MainWindow ):
	"""docstring for QtMainWindow"""
	def __init__(self, parent,*args):
		super(QtMainWindow, self).__init__(parent, *args)
	
	def closeEvent(self,event):
		if self.module.alive:
			self.hide()
			event.ignore()
		else:
			pass

##----------------------------------------------------------------##
class QtGlobalModule( QtEditorModule ):
	"""docstring for QtGlobalModule"""
	def getMainWindow( self ):
		qt = self.getQtSupport()
		return qt.getMainWindow()

	def requestDockWindow( self, id = None, **windowOption ):
		raise Exception( 'only subwindow supported for globalModule' )

	def requestDocumentWindow( self, id = None, **windowOption ):
		raise Exception( 'only subwindow supported for globalModule' )

	def requestSubWindow( self, id = None, **windowOption ):
		if not id: id = self.getName()
		mainWindow = self.getMainWindow()
		container = mainWindow.requestSubWindow( id, **windowOption )
		# self.containers[id] = container
		return container
			


##----------------------------------------------------------------##
QtSupport().register()


