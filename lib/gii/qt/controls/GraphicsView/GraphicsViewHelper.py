from qtpy import QtWidgets, QtGui, QtCore, QtOpenGL, uic
from qtpy.QtCore import Qt, QObject, QEvent, Signal
from qtpy.QtCore import QPoint, QRect, QSize
from qtpy.QtCore import QPointF, QRectF, QSizeF
from qtpy.QtGui  import QColor, QTransform
from qtpy.QtOpenGL import QGLContext

try:
	from gii.qt.controls.GLWidget import GLWidget

	def getSharedGLWidget():
		return GLWidget.getSharedWidget()

	def makeSharedGLWidget( *args, **option ):
		sharedWidget = None
		fmt = QtOpenGL.QGLFormat.defaultFormat()
		sharedWidget = getSharedGLWidget()
		return QtOpenGL.QGLWidget( fmt, None, sharedWidget )

	def makeNewGLWidget( *args, **option ):
		fmt = QtOpenGL.QGLFormat()
		fmt.setRgba(True)
		fmt.setDepth(False)
		fmt.setDoubleBuffer(True)
		fmt.setSwapInterval(0)
		fmt.setSampleBuffers( True )
		viewport = QtOpenGL.QGLWidget( fmt )
		return viewport

	def makeGLWidget( *args, **options ):
		return makeSharedGLWidget( *args, **options )

except Exception as e:
	def getSharedGLWidget():
		return None

	def makeGLWidget( *args, **option ):
		fmt = QtOpenGL.QGLFormat()
		fmt.setRgba(True)
		fmt.setDepth(False)
		fmt.setDoubleBuffer(True)
		fmt.setSwapInterval(0)
		fmt.setSampleBuffers( True )
		viewport = QtOpenGL.QGLWidget( fmt )
		return viewport


def makeBrush( **option ):
	brush = QtGui.QBrush()
	brush.setStyle( option.get( 'style', Qt.SolidPattern ) )
	color = QColor( option.get( 'color', '#ffffff' ) )
	color.setAlphaF( option.get( 'alpha', 1 ) )
	brush.setColor( color )
	return brush

def makePen( **option ):
	pen = QtGui.QPen()
	pen.setStyle( option.get( 'style', Qt.SolidLine ) )
	color = QColor( option.get( 'color', '#ffffff' ) )
	color.setAlphaF( option.get( 'alpha', 1 ) )
	pen.setColor( color )
	pen.setWidth( option.get( 'width', .0 ) )
	return pen

_ItemStyleRegistry = {}

def registerStyle( id, pen, brush, penText = None ):
	_ItemStyleRegistry[ id ] = ( pen, brush, penText or pen )

def applyStyle( id, painter ):
	if id in _ItemStyleRegistry:
		pen, brush, penText = _ItemStyleRegistry[ id ]
		painter.setPen( pen )
		painter.setBrush( brush )
		def drawStyledText( rect, flags, text ):
			painter.setPen( penText )
			painter.drawText( rect, flags, text )
			painter.setPen( pen )
		painter.drawStyledText = drawStyledText
	else:
		print(('no style found', id))

def makeStyle( id, penOption, brushOption, textOption = None ):
	pen = None
	brush = None
	penText = None
	if isinstance( penOption, dict ):
		pen = makePen( **penOption )
	elif isinstance( penOption, str ):
		pen = makePen( color = penOption )
	elif isinstance( penOption, tuple ):
		color, alpha = penOption
		pen = makePen( color = color, alpha = alpha )
	elif penOption is None:
		pen = Qt.transparent

	if isinstance( brushOption, dict ):
		brush = makeBrush( **brushOption )
	elif isinstance( brushOption, str ):
		brush = makeBrush( color = brushOption )
	elif isinstance( brushOption, tuple ):
		color, alpha = brushOption
		brush = makeBrush( color = color, alpha = alpha )
	elif brushOption is None:
		brush = Qt.transparent

	if isinstance( textOption, dict ):
		penText = makePen( **textOption )
	elif isinstance( textOption, str ):
		penText = makePen( color = textOption )
	elif textOption is None:
		penText = Qt.transparent

	return registerStyle( id, pen, brush, penText )


##----------------------------------------------------------------##

class StyledItemMixin( object ):
	def setItemType( self, t ):
		self.itemType = t

	def setItemState( self, state ):
		self.itemState = state

	def getItemType( self ):
		return getattr( self, 'itemType', 'unknown' )

	def getItemState( self ):
		return getattr( self, 'itemState', 'normal' )

	def findItemStyleName( self ):
		n = '%s:%s' % ( self.getItemType(), self.getItemState() )
		if n in _ItemStyleRegistry:
			return n
		if self.itemType in _ItemStyleRegistry:
			return self.itemType
		return 'default'

	def updateItemState( self ):
		self.activeStyleId = self.findItemStyleName()

	def paint( self, painter, option, widget ):
		self.updateItemState()
		applyStyle( self.findItemStyleName(), painter )
		self.onPaint( painter, option, widget )

	def onPaint( self, paint, option, widget ):
		pass


##----------------------------------------------------------------##
class GLGraphicsScene( QtWidgets.QGraphicsScene ):
	def __init__( self, *arg, **kwargs ):
		super( GLGraphicsScene, self ).__init__( *arg, **kwargs )
		self.pressedButtons = 0

	def mousePressEvent( self, ev ):
		self.pressedButtons = int( ev.buttons() )
		return super( GLGraphicsScene, self ).mousePressEvent( ev )

	def mouseReleaseEvent( self, ev ):
		self.pressedButtons = int( ev.buttons() )
		super( GLGraphicsScene, self ).mouseReleaseEvent( ev )

	def mouseMoveEvent( self, ev ):
		if int( ev.buttons() ) != self.pressedButtons:
			#WORKAROUND: ev.buttons() might become 0 before release event, force sync.
			return
		return super( GLGraphicsScene, self ).mouseMoveEvent( ev )
		

_USE_GL = False
# _USE_GL = True

##----------------------------------------------------------------##
class GLGraphicsView( QtWidgets.QGraphicsView ):
	def __init__( self, *args, **kwargs ):
		option = kwargs
		super( GLGraphicsView, self ).__init__( *args, parent = option.get('parent', None) )
		self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
		self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
		# self.setAttribute( Qt.WA_NoSystemBackground, True )
		self.setAttribute( Qt.WA_OpaquePaintEvent, True )
		self.usingGL = _USE_GL and option.get( 'use_gl', True )
		if self.usingGL:
			self.setViewportUpdateMode( QtWidgets.QGraphicsView.SmartViewportUpdate )		
			# self.setViewportUpdateMode( QtWidgets.QGraphicsView.FullViewportUpdate )		
			viewport = option.get( 'gl_viewport', makeGLWidget() )
			self.glViewport = viewport
			self.setViewport( viewport )
		else:
			self.setViewportUpdateMode( QtWidgets.QGraphicsView.MinimalViewportUpdate )
		
		flag = QtWidgets.QGraphicsView.DontSavePainterState
		
		if option.get( 'antialias', False):
			self.setRenderHint( QtGui.QPainter.Antialiasing, True )
			self.setRenderHint( QtGui.QPainter.HighQualityAntialiasing, True )
			self.setRenderHint( QtGui.QPainter.NonCosmeticDefaultPen, True )
		else:
			self.setRenderHint( QtGui.QPainter.Antialiasing, False )
			self.setRenderHint( QtGui.QPainter.HighQualityAntialiasing, False )
			self.setRenderHint( QtGui.QPainter.NonCosmeticDefaultPen, False )
			flag |= QtWidgets.QGraphicsView.DontAdjustForAntialiasing

		self.setTransformationAnchor( self.NoAnchor )
		self.setOptimizationFlags( flag )
		self.viewport().setAttribute( Qt.WA_AcceptTouchEvents, True )
		self.viewport().setAttribute( Qt.WA_TouchPadAcceptSingleTouchEvents, True )
		
	# 	self.refreshTimer   = QtCore.QTimer(self)
	# 	self.refreshTimer.timeout.connect(self.onRefreshTimer)
	# 	self.refreshTimer.setInterval( 1000/30 )
	# 	self.refreshTimer.setSingleShot( True )

	# 	self.pendingRefresh = True
	# 	self.allowRefresh   = True

	# def onRefreshTimer(self): #auto render if has pending render
	# 	if self.pendingRefresh:
	# 		self.pendingRefresh = False
	# 		self.allowRefresh = True
	# 		self.update()
	# 	self.allowRefresh = True

	# def paintEvent( self, ev ):
	# 	if not self.allowRefresh:
	# 		self.pendingRefresh = True
	# 		return
	# 	self.allowRefresh = False
	# 	if _USE_GL:
	# 		self.glViewport.makeCurrentCanvas()
	# 		super( GLGraphicsView, self ).paintEvent( ev )
	# 		self.glViewport.doneCurrent() #dirty workaround...
	# 		shared = getSharedGLWidget()
	# 		if shared:
	# 			shared.makeCurrentCanvas()
	# 	else:
	# 		super( GLGraphicsView, self ).paintEvent( ev )
	# def viewportEvent( self, ev ):
	# 	et = ev.type()
	# 	if et == QtCore.QEvent.TouchBegin:
	# 		print 'touchBegin'
	# 		ev.accept()
	# 		print ev.touchPoints()
	# 		return True
	# 	elif et == QtCore.QEvent.TouchEnd:
	# 		print 'touchEnd'
	# 	elif et == QtCore.QEvent.TouchUpdate:
	# 		print 'touchUpdate'
	# 		print len( ev.touchPoints() )
	# 	return super( GLGraphicsView, self ).viewportEvent( ev )

	def paintEvent( self, ev ):
		if self.usingGL:
			current = QGLContext.currentContext()
			self.glViewport.makeCurrentCanvas()
			super( GLGraphicsView, self ).paintEvent( ev )
			self.glViewport.doneCurrent() #dirty workaround...
			if current:
				current.makeCurrentCanvas()
		else:
			super( GLGraphicsView, self ).paintEvent( ev )


##----------------------------------------------------------------##
class GridBackground( QtWidgets.QGraphicsRectItem ):
	_gridPenV  = makePen( color = '#222', width = 1 )
	_gridPenH  = makePen( color = '#222', width = 1 )
	_cursorPen  = makePen( color = '#a3ff00', width = 1 )
	def __init__( self ):
		super( GridBackground, self ).__init__()
		self.setZValue( -100 )
		self.gridWidth = 50
		self.gridHeight = 50 
		self.offsetX = 0
		self.offsetY = 0
		self.cursorPos  = 0
		self.cursorVisible = False
		self.XAxisVisible = True
		self.YAxisVisible = True
		self.cursorPen = GridBackground._cursorPen

	def setAxisVisible( self, xAxis, yAxis ):
		self.XAxisVisible = xAxis
		self.YAxisVisible = yAxis

	def setOffset( self, x, y ):
		self.offsetX = x
		self.offsetY = y

	def setGridSize( self, width, height = None ):
		if not height:
			height = width
		self.gridWidth = width
		self.gridHeight = height
		self.update()

	def setGridWidth( self, width ):
		self.setGridSize( width, self.gridHeight )

	def setGridHeight( self, height ):
		self.setGridSize( self.gridWidth, height )

	def setCursorPos( self, pos ):
		self.cursorPos = pos

	def setCursorVisible( self, visible ):
		self.cursorVisible = visible

	def paint( self, painter, option, widget ):
		painter.setRenderHint( QtGui.QPainter.Antialiasing, False )
		rect = painter.viewport()
		transform = painter.transform()
		dx = transform.dx() 
		dy = transform.dy()
		tw = self.gridWidth
		th = self.gridHeight
		w = rect.width()
		h = rect.height()
		rows = int( h/self.gridHeight ) + 1
		cols = int( w/self.gridWidth ) + 1
		x0 = -dx
		y0 = -dy
		x1 = x0 + w
		y1 = y0 + h
		ox = (dx) % tw
		oy = (dy) % th

		if self.YAxisVisible:
			offx = self.offsetX
			painter.setPen( GridBackground._gridPenV )
			for col in range( cols ): #V lines
				x = col * tw + ox + x0 + offx
				painter.drawLine( x, y0, x, y1 )
		
		if self.XAxisVisible:
			# x0 = max( x0, _HEAD_OFFSET )
			offy = self.offsetY
			painter.setPen( GridBackground._gridPenH )
			for row in range( rows ): #H lines
				y = row * th + oy + y0 + offy
				painter.drawLine( x0, y, x1, y )

		if self.cursorVisible:
			painter.setPen( self.cursorPen )
			x = int(self.cursorPos)
			painter.drawLine( x, y0, x, y1 )
