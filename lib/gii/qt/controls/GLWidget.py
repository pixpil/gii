from qtpy import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt, QEvent, QCoreApplication


import time

##----------------------------------------------------------------##
_RedirectingEventTypes = [
	QEvent.MouseButtonPress,
	QEvent.MouseButtonRelease,
	QEvent.MouseButtonDblClick,
	QEvent.MouseMove,
	QEvent.FocusIn,
	QEvent.FocusOut,
	QEvent.FocusAboutToChange,
	QEvent.Enter,
	QEvent.Leave,
	QEvent.Wheel,
	QEvent.TabletMove,
	QEvent.TabletPress,
	QEvent.TabletRelease,
	QEvent.TabletEnterProximity,
	QEvent.TabletLeaveProximity,
	QEvent.TouchBegin,
	QEvent.TouchUpdate,
	QEvent.TouchEnd,
	QEvent.InputMethodQuery,
	QEvent.TouchCancel,

	QEvent.DragEnter,
	QEvent.DragLeave,
	QEvent.DragMove,
	QEvent.Drop,

]

##----------------------------------------------------------------##
class GLWidgetWindow(QtGui.QOpenGLWindow):
	def __init__( self, parentWidget ):
		self.parentWidget = parentWidget
		super( GLWidgetWindow, self ).__init__( GLWidget.getMainContext() )
		fmt =  QtGui.QSurfaceFormat()
		fmt.setVersion( 3, 3 )
		fmt.setProfile( QtGui.QSurfaceFormat.CoreProfile )
		fmt.setSwapInterval( 0 )
		fmt.setSwapBehavior( QtGui.QSurfaceFormat.DoubleBuffer )
		self.setFormat( fmt )

		self.setFlags( Qt.WindowTransparentForInput )
		self.setFlags( Qt.WindowDoesNotAcceptFocus )
		self.pixelRatio = None
		self.screenChanged.connect( self.onScreenChanged )
		# self.frameSwapped.connect( self.onFrameSwapped )

	# def initializeGL( self ):
	# 	self.parentWidget.pixelRatio = self.devicePixelRatio()
	# 	GL.glClearColor( 0,0,0,0 )
	# 	GL.glClear( GL.GL_COLOR_BUFFER_BIT )

	def paintGL( self ):
		self.parentWidget.paintGL()

	def resizeGL( self, w, h ):		
		return self.parentWidget.resizeGL( w, h )

	def onScreenChanged( self ):
		ratio1 = self.devicePixelRatio()
		if ratio1 != self.pixelRatio:
			self.pixelRatio = ratio1
			self.resizeGL( self.width(), self.height() )
			
		self.update()
		
	def event( self, ev ):
		t = ev.type()
		if t in _RedirectingEventTypes:
			return QCoreApplication.sendEvent( self.parentWidget, ev )
		return super( GLWidgetWindow, self ).event( ev )

	def swapBuffer( self ):
		context = self.context()
		context.swapBuffers( self )
		

##----------------------------------------------------------------##
class GLWidget(QtWidgets.QWidget):
	MainContextSurface = None
	MainContext = None

	@staticmethod
	def getMainContext():
		if not GLWidget.MainContext:
			fmt =  QtGui.QSurfaceFormat()
			fmt.setSwapBehavior( QtGui.QSurfaceFormat.DoubleBuffer )
			fmt.setSwapInterval( 0 )
			fmt.setVersion( 3, 3 )
			fmt.setProfile( QtGui.QSurfaceFormat.CoreProfile )
			
			GLWidget.MainContext = context = QtGui.QOpenGLContext()
			context.setFormat( fmt )
			GLWidget.MainContext.create()

		return GLWidget.MainContext

	@staticmethod
	def makeMainContextCurrent():
		if not GLWidget.MainContextSurface:
			fmt =  QtGui.QSurfaceFormat()
			fmt.setSwapBehavior( QtGui.QSurfaceFormat.DoubleBuffer )
			fmt.setSwapInterval( 0 )
			fmt.setVersion( 3, 3 )
			fmt.setProfile( QtGui.QSurfaceFormat.CoreProfile )
			GLWidget.MainContextSurface = surface = QtGui.QOffscreenSurface()
			surface.setFormat( fmt )
			surface.create()
			obtainedFormat = surface.requestedFormat()
			# print(('OPENGL Version:', obtainedFormat.majorVersion(), obtainedFormat.minorVersion()))
			
		GLWidget.getMainContext().makeCurrent( GLWidget.MainContextSurface )

	def __init__( self, parent=None, **option ):
		QtWidgets.QOpenGLWidget.__init__( self, parent )
		self.glWindow = GLWidgetWindow( self )
		self.glWindowContainer = self.createWindowContainer( self.glWindow, self )
		self.glWindowContainer.setWindowFlags( Qt.WindowTransparentForInput )
		self.glWindowContainer.setWindowFlags( Qt.WindowDoesNotAcceptFocus )
		self.pixelRatio = self.devicePixelRatio()

		self.cycle = 0

		# self.setAttribute( Qt.WA_NoSystemBackground, True )
		self.setAttribute( Qt.WA_OpaquePaintEvent, True )

		self.setMinimumSize( 32, 32 )

		self.allowRefresh   = False
		self.pendingRefresh = False

		self.mainLayout = QtWidgets.QVBoxLayout( self )
		self.mainLayout.setSpacing( 0 )
		self.mainLayout.setContentsMargins( 0,0,0,0 )
		self.mainLayout.addWidget( self.glWindowContainer )

		self.refreshTimer   = QtCore.QTimer(self)
		self.refreshTimer.setTimerType( Qt.PreciseTimer )
		
		# self.refreshTimer.setTimerType( Qt.CoarseTimer )
		self.refreshTimer.setSingleShot( True )
		self.refreshTimer.timeout.connect(self.onRefreshTimer)

		self.setFocusPolicy( QtCore.Qt.WheelFocus )
		self.setMouseTracking(True)


	def startRefreshTimer( self, fps = 60 ):
		# self.refreshTimer.start( 1000/fps )
		self.allowRefresh = True
		interval = 1000/fps
		self.refreshTimer.setInterval( interval )

	def stopRefreshTimer(self):
		self.allowRefresh = False
		self.refreshTimer.stop()

	def forceUpdateGL(self):
		self.allowRefresh = True
		self.refreshTimer.stop()
		self.update()

	# def makeCurrent( self ):
	# 	pass

	def pendRefresh( self ):
		self.allowRefresh = True

	# def minimumSizeHint(self):
	# 	return QtCore.QSize(50, 50)

	def onRefreshTimer(self): #auto render if has pending render
		self.allowRefresh = True
		if self.pendingRefresh:
			self.pendingRefresh = False
			self.update()

	def paintGL( self ):
		self.pixelRatio = self.devicePixelRatio()
		self.makeCurrent()
		self.onDraw()

	def updateGL( self ):
		return self.update()
		
	def update( self ):
		if self.allowRefresh:
			self.allowRefresh = False
			self.refreshTimer.start() #wait for next refresh
			self.glWindow.update()

		else:
			self.pendingRefresh = True

	def setCursor( self, cur ):
		self.glWindow.setCursor( cur )

	def cursor( self ):
		self.glWindow.cursor()

	def grabFramebuffer( self ):
		self.glWindow.swapBuffer()
		img = self.glWindow.grabFramebuffer()
		self.glWindow.swapBuffer()
		return img
		
	def onDraw(self):
		pass

