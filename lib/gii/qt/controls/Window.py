from gii.core import signals
from gii.qt.helpers import restrainWidgetToScreen
from gii.qt.IconCache               import getIcon

from qtpy import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore import Qt, QPoint
from qtpy.QtWidgets import QStyle

from .ToolWindowManager import ToolWindowManager

#include <QProxyStyle> 
#include <QStyleOption> 
#include <QPainter> 

XXXX = 0

# class IconDockWidgetStyle( QtWidgets.QProxyStyle ):
# 	def __init__( self, icon, style ):
# 		super( IconDockWidgetStyle, self ).__init__( style )
# 		self._icon = icon
# 	def drawControl( element, option, painter, widget ):
# 		base = self.baseStyle()
# 		if element == QStyle.CE_DockWidgetTitle:
# 			width = self.pixelMetric( QStyle.PM_ToolBarIconSize )
# 			margin = base.pixelMetric( QStyle.PM_DockWidgetTitleMargin )
# 			# spacing = base.pixelMetric( QStyle.PM_LayoutHorizontalSpacing )
# 			rect = option.rect
# 			iconPoint = QPoint( rect.left() + margin, rect.center().y() + margin - width/2 )
# 			painter.drawPixmap( iconPoint, self._icon.pixmap( width, width ) )
# 			option.rect = rect.adjusted( width, 0, 0, 0 )

# 		return base.drawControl( element, option, painter, widget )

##----------------------------------------------------------------##
def getWindowScreenId(window):
	desktop=QtWidgets.QApplication.desktop()
	return desktop.screenNumber(window)
	
def moveWindowToCenter(window):
	desktop=QtWidgets.QApplication.desktop()
	geom=desktop.availableGeometry(window)
	x=(geom.width()-window.width())/2 +geom.x()
	y=(geom.height()-window.height())/2+geom.y()
	window.move(x,y)


##----------------------------------------------------------------##
class MainWindowDocumentTabBar( QtWidgets.QTabBar ):
	def mousePressEvent( self, ev ):
		if ev.button() == Qt.MidButton:
			idx = self.tabAt( ev.pos() )
			if idx >= 0:
				widget = self.parent().widget( idx )
				if widget:
					if widget.close():
						self.parent().removeTab( idx )

		return super( MainWindowDocumentTabBar, self ).mousePressEvent( ev )

##----------------------------------------------------------------##
class MainWindowDocumentTab( QtWidgets.QTabWidget ):
	def __init__(self, parent):
		super( MainWindowDocumentTab, self ).__init__( parent )
		self.setTabBar( MainWindowDocumentTabBar( self ) )

##----------------------------------------------------------------##
class MainWindowTimer( QtCore.QTimer ):
	def __init__(self, parent):
		QtCore.QTimer.__init__( self, parent )
		self.setTimerType( Qt.PreciseTimer )
		
##----------------------------------------------------------------##
class MainWindow(QtWidgets.QMainWindow):
	"""docstring for MainWindow"""
	def __init__(self, parent):
		super( MainWindow, self ).__init__(parent)
		self._dockWindows = []		
		self.setAnimated( False )
		# self.setDocumentMode(True)
		
		self.defaultToolBarIconSize = 16
		self.setUnifiedTitleAndToolBarOnMac( False )

		self.setDockOptions(
			QtWidgets.QMainWindow.AllowNestedDocks | 
			QtWidgets.QMainWindow.AllowTabbedDocks
			# QtWidgets.QMainWindow.GroupedDragging
			# QtWidgets.QMainWindow.ForceTabbedDocks
		)

		self.setTabPosition( Qt.AllDockWidgetAreas, QtWidgets.QTabWidget.South)

		font=QtGui.QFont()
		font.setPointSize(11)
		self.setFont(font)
		self.setIconSize( QtCore.QSize( 16, 16 ) )
		self.setFocusPolicy( Qt.WheelFocus )
		
		self.centerTabWidget = MainWindowDocumentTab( self )
		self.setCentralWidget( self.centerTabWidget )
		
		self.centerTabWidget.currentChanged.connect( self.onDocumentTabChanged )

		# self.centerTabWidget.setDocumentMode(True)
		self.centerTabWidget.setMovable(True)
		self.centerTabWidget.setTabsClosable(True)
		self.centerTabWidget.tabCloseRequested.connect( self.onTabCloseRequested )

		self.resetCorners()

	def resetCorners( self ):
		self.setCorner( Qt.TopLeftCorner, Qt.LeftDockWidgetArea )
		self.setCorner( Qt.BottomLeftCorner, Qt.BottomDockWidgetArea )
		self.setCorner( Qt.TopRightCorner, Qt.RightDockWidgetArea )
		self.setCorner( Qt.BottomRightCorner, Qt.RightDockWidgetArea )

	def moveToCenter(self):
		moveWindowToCenter(self)

	def ensureVisible(self):
		restrainWidgetToScreen(self)

	def startTimer(self, fps, trigger):
		assert(hasattr(trigger,'__call__'))
		interval = 1000/fps
		timer = MainWindowTimer(self)
		timer.timeout.connect(trigger)
		timer.start(interval)
		return timer

	def requestSubWindow(self, id, **windowOption ):
		title = windowOption.get('title',id)
		window = SubWindow(self)
		window.setWindowTitle(title)

		icon  = windowOption.get('icon', None)
		if icon:
			window.setWindowIcon( getIcon( icon ) )

		window.windowMode = 'sub'
		window.titleBase = title


		minSize=windowOption.get('minSize',None)
		if minSize:
			window.setMinimumSize(*minSize)
		# else:
		# 	window.setMinimumSize(20,20)

		maxSize=windowOption.get('maxSize',None)
		if maxSize:
			window.setMaximumSize( *maxSize )

		size=windowOption.get('size',None)
		if size:
			window.resize(*size)

		if windowOption.get( 'tool', False ):
			window.setWindowFlags( Qt.Tool )

		return window

	def requestDocumentWindow(self, id, **windowOption ):
		title  = windowOption.get('title',id)
		
		window = DocumentWindow( self.centerTabWidget )
		window.setWindowOptions( windowOption )
		# window = DocumentWindow( self.toolWindowMgr )
		# self.toolWindowMgr.addToolWindow( window, ToolWindowManager.EmptySpace )
		window.parentWindow = self
		window.setWindowTitle( title )
		# self.centerTabWidget.addTab( window, title )

		window.windowMode = 'tab'
		window.titleBase = title


		# minSize = windowOption.get('minSize',None)
		# if minSize:
		# 	window.setMinimumSize(*minSize)
		# else:
		# 	window.setMinimumSize(20,20)

		size = windowOption.get('size',None)
		if size:
			window.resize(*size)
		return window

	def updateTopLevel( self ):
		for window in self._dockWindows:
			window.onTopLevelChanged()

	def requestDockWindow(self, id, **dockOptions ):
		dockArea=dockOptions.get('dock','left')
		if dockArea=='left':
			dockArea=Qt.LeftDockWidgetArea

		elif dockArea=='right':
			dockArea=Qt.RightDockWidgetArea

		elif dockArea=='top':
			dockArea=Qt.TopDockWidgetArea

		elif dockArea=='bottom':
			dockArea=Qt.BottomDockWidgetArea

		elif dockArea=='main':
			dockArea='center'

		elif dockArea=='float':
			dockArea = False

		elif dockArea:
			raise Exception('unsupported dock area:%s'%dockArea)
		
		isToolWindow = dockOptions.get( 'toolWindow', False )
		window = DockWindow( self )
		title = dockOptions.get( 'title', id )
		if title:
			window.setWindowTitle(title)

		# iconPath  = dockOptions.get('icon', None)
		# if iconPath:
		# 	icon = getIcon( icon )
		# 	if icon:
		# 		style = IconDockWidgetStyle( icon, window.style() )
		# 		window.setStyle( style )
		# 	# window.setWindowIcon( getIcon( icon ) )

		window.setObjectName('_dock_' + id)
		
		window.windowMode = 'dock'
		window.titleBase = title
		self._dockWindows.append( window )

		# if dockOptions.get( 'allowDock', True ):
		# 	window.setAllowedAreas( Qt.AllDockWidgetAreas )
		# else:
		# 	window.setAllowedAreas( Qt.NoDockWidgetArea )
		# 	dockArea = None
			
		# if dockArea and dockArea!='center':
		# 	self.addDockWidget(dockArea, window)

		# elif dockArea=='center':
		# 	self.setCentralWidget(window)
		# 	window.setFeatures(QtWidgets.QDockWidget.NoDockWidgetFeatures)
		# 	window.hideTitleBar()

		# else:
		# 	window.setFloating(True)
		# 	window.setWindowOptions( Qt.Window )

			# window.setupCustomTitleBar()
		global XXXX
		XXXX += 1
		if dockArea and XXXX < 33:
			self.addDockWidget(dockArea, window )
			
		else:
			window.setFloating(True)
			window.setWindowOptions( Qt.Window )

		# minSize=dockOptions.get('minSize',None)
		# if minSize:
		# 	window.setMinimumSize(*minSize)
		# else:
		# 	window.setMinimumSize(20,20)

		size=dockOptions.get('size',None)
		# if size:
			# window.resize(*size)

		# if not dockOptions.get('autohide',False):
		# 	window._useWindowFlags()

		window.dockOptions=dockOptions

		return window


	def onTabCloseRequested( self, idx ):
		subwindow = self.centerTabWidget.widget( idx )
		if subwindow.close():
			self.centerTabWidget.removeTab( idx )

	def requestToolBar( self, name, **options ):
		toolbar = QtWidgets.QToolBar( self )
		toolbar.setFloatable( options.get( 'floatable', False ) )
		toolbar.setMovable(   options.get( 'movable',   True ) )		
		toolbar.setObjectName( 'toolbar-%s' % name )
		iconSize = options.get('icon_size', self.defaultToolBarIconSize )
		self.addToolBar( toolbar )
		toolbar.setIconSize( QtCore.QSize( iconSize, iconSize ) )
		toolbar._icon_size = iconSize
		return toolbar
		
	def onDocumentTabChanged( self, idx ):
		w = self.centerTabWidget.currentWidget()
		if w: w.setFocus()
	


##----------------------------------------------------------------##
class SubWindowMixin( object ):	
	def setWindowOptions( self, options ):
		self.windowOptions = options

	def getWindowOption( self, key, default = None ):
		if hasattr( self, 'windowOptions' ):
			return self.windowOptions.get( key, default )
		else:
			return None

	def setDocumentName( self, name ):
		self.documentName = name
		if name:
			title = '%s - %s' % ( self.documentName, self.titleBase )
			self.setWindowTitle( title )
		else:
			self.setWindowTitle( self.titleBase )
	
	def setCallbackOnClose( self, callback ):
		self.callbackOnClose = callback

	def setCallbackOnFocusIn( self, callback ):
		self.callbackOnFocusIn = callback

	def setCallbackOnFocusOut( self, callback ):
		self.callbackOnFocusOut = callback
		
	def setupUi(self):
		self.callbackOnClose = None
		self.callbackOnFocusIn = None
		self.callbackOnFocusOut = None

		self.container = self.createContainer()

		self.mainLayout = QtWidgets.QVBoxLayout(self.container)
		self.mainLayout.setSpacing(0)
		self.mainLayout.setContentsMargins(0,0,0,0)
		self.mainLayout.setObjectName('MainLayout')

	def createContainer(self):
		container = QtWidgets.QWidget(self)
		self.setWidget(container)
		return container

	def addWidget(self, widget, **layoutOption):
		# widget.setParent(self)		
		if layoutOption.get('fixed', False):
			widget.setSizePolicy(
				QtWidgets.QSizePolicy.Fixed,
				QtWidgets.QSizePolicy.Fixed
				)
		elif layoutOption.get('expanding', True):
			widget.setSizePolicy(
				QtWidgets.QSizePolicy.Expanding,
				QtWidgets.QSizePolicy.Expanding
				)
		self.mainLayout.addWidget(widget)
		return widget

	def addSeparator( self ):
		line = QtWidgets.QFrame( self )
		line.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Fixed
		)
		# line.setStyleSheet('background:none; border:none; ')
		line.setStyleSheet('background:none; border-top:1px solid #353535; margin: 2px 0 2px 0;')
		line.setMinimumSize( 30, 7 )
		self.mainLayout.addWidget( line )

	def addLabel( self, text ):
		label = QtWidgets.QLabel( self )
		label.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Fixed
		)
		label.setText( text )
		self.mainLayout.addWidget( label )

	def addWidgetFromFile(self, uiFile, **layoutOption):
		form = uic.loadUi(uiFile)
		return self.addWidget(form, **layoutOption)	

	def moveToCenter(self):
		moveWindowToCenter(self)

	def ensureVisible(self):
		restrainWidgetToScreen(self)

	def onClose( self ):
		if self.callbackOnClose:
			return self.callbackOnClose()
		return True

	def onFocusOut( self ):
		if self.callbackOnFocusOut:
			return self.callbackOnFocusOut()
		return True

	def onFocusIn( self ):
		if self.callbackOnFocusIn:
			return self.callbackOnFocusIn()
		return True

##----------------------------------------------------------------##
class SubWindow( SubWindowMixin, QtWidgets.QMainWindow  ):
	def __init__( self, parent ):
		super(SubWindow, self).__init__(parent)
		self.setupUi()
		self.stayOnTop = False
		self.setFocusPolicy( Qt.StrongFocus )

	def hideTitleBar(self):
		pass
		# emptyTitle=QtWidgets.QWidget()
		# self.setTitleBarWidget(emptyTitle)

	def createContainer(self):
		container=QtWidgets.QWidget(self)
		self.setCentralWidget(container)
		return container

	def addToolBar(self):
		return self.addWidget( QtWidgets.QToolBar(), expanding = False ) 

	def startTimer(self, fps, trigger):
		assert(hasattr(trigger,'__call__'))
		interval = 1000/fps
		timer = MainWindowTimer(self)
		timer.timeout.connect(trigger)
		timer.start(interval)
		return timer

	def focusOutEvent(self, event):
		self.onFocusOut()
		return super( SubWindow, self ).focusOutEvent( event )

	def focusInEvent(self, event):
		self.onFocusIn()
		return super( SubWindow, self ).focusInEvent( event )

	def closeEvent( self, event ):
		if self.onClose():
			return super( SubWindow, self ).closeEvent( event )
		else:
			event.ignore()

##----------------------------------------------------------------##
class DocumentWindow( SubWindow ):
	def show( self, *args ):
		tab = self.parentWindow.centerTabWidget
		idx = tab.indexOf( self )
		if idx < 0:
			idx = tab.addTab( self, self.windowTitle() )
			iconPath = self.getWindowOption( 'icon' )
			if iconPath:
				tab.tabBar().setTabIcon( idx, getIcon( iconPath ) )
		super( DocumentWindow, self ).show( *args )
		tab.setCurrentIndex( idx )

	def setWindowTitle( self, title ):
		super( DocumentWindow, self ).setWindowTitle( title )
		tabParent = self.parentWindow.centerTabWidget
		idx = tabParent.indexOf( self )
		tabParent.setTabText( idx, title )
		
	def addToolBar(self):
		return self.addWidget( QtWidgets.QToolBar(), expanding = False ) 

	
##----------------------------------------------------------------##
class DockWindowTitleBar( QtWidgets.QWidget ):
	"""docstring for DockWindowTitleBar"""
	def __init__(self, *args):
		super(DockWindowTitleBar, self).__init__(*args)
		# self.setWindowFlags( Qt.Dialog )

	def sizeHint(self):
		return QtCore.QSize(20,15)

	def minimumSizeHint(self):
		return QtCore.QSize(20,15)

##----------------------------------------------------------------##
class DockWindow( SubWindowMixin, QtWidgets.QDockWidget ):
	"""docstring for DockWindow"""	
	def __init__(self, parent, **option):
		# super(DockWindow, self).__init__(parent)
		QtWidgets.QDockWidget.__init__( self, parent )
		self.setupUi()
		font = QtGui.QFont()
		font.setPointSize(11)
		self.setFont(font) 
		self.topLevel  = False
		self.stayOnTop = False
		self.topLevelChanged.connect( self.onTopLevelChanged )
		self.isToolWindow = option.get( 'toolWindow', False )
		self.setFocusPolicy( Qt.StrongFocus )
		# self.setupCustomTitleBar()
		self.setWindowOptions( Qt.Window )

	def setupCustomTitleBar(self):
		self.originTitleBar = self.titleBarWidget()
		self.customTitleBar = DockWindowTitleBar( self )
		# self.customTitleBar = self.originTitleBar
		# self.setTitleBarWidget( self.customTitleBar )

	def _useWindowFlags(self):
		pass

	def setStayOnTop( self, stayOnTop ):
		self.stayOnTop = stayOnTop
		if stayOnTop and self.topLevel:
			self.setWindowFlags( Qt.Window | Qt.WindowStaysOnTopHint )
		
	def hideTitleBar(self):
		emptyTitle = QtWidgets.QWidget()
		self.setTitleBarWidget(emptyTitle)

	def startTimer(self, fps, trigger):
		assert(hasattr(trigger,'__call__'))
		interval = 1000/fps
		timer = MainWindowTimer(self)
		timer.timeout.connect(trigger)
		timer.start(interval)
		return timer

	def onTopLevelChanged( self, newTopLevel = None ):
		if newTopLevel != None:
			self.topLevel = newTopLevel
		if self.topLevel:
			vis = self.isVisible()
			# self.setTitleBarWidget( self.customTitleBar )
			if self.isToolWindow:
				flag = Qt.Tool
			else:
				flag = Qt.Window
			if self.stayOnTop:
				flag |= Qt.WindowStaysOnTopHint
			self.setWindowFlags( flag )
			if newTopLevel != None:
				self.show()
			else:
				if vis:
					self.show()
		else:
			pass
			# self.setTitleBarWidget( self.originTitleBar )

	def addToolBar(self):
		return self.addWidget( QtWidgets.QToolBar(), expanding = False ) 

	def closeEvent( self, event ):
		if self.onClose():
			return super( DockWindow, self ).closeEvent( event )
		else:
			event.ignore()

	def focusOutEvent(self, event):
		self.onFocusOut()
		return super( DockWindow, self ).focusOutEvent( event )

	def focusInEvent(self, event):
		self.onFocusIn()
		return super( DockWindow, self ).focusInEvent( event )