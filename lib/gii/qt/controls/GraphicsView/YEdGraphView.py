# -*- coding: utf-8 -*-
import sys
import math

from qtpy import QtWidgets, QtGui, QtCore, QtOpenGL, uic
from qtpy.QtCore import Qt, QObject, QEvent, Signal
from qtpy.QtCore import QPoint, QRect, QSize
from qtpy.QtCore import QPointF, QRectF, QSizeF
from qtpy.QtGui import QColor

from .GraphicsViewHelper import *
from util.YEd import *


_DEFAULT_BG = makeBrush( color = '#222' )

makeStyle( 'ynode',     '#333',    '#a0a0a0'    )
makeStyle( 'ygroup',    '#333',    ('#a0a0a0',0.3)    )
makeStyle( 'yedge',     '#555', None )

##----------------------------------------------------------------##
class YEdEdgeItem( QtWidgets.QGraphicsPathItem ):
	_pen                  = makePen( color = '#888', width = 1 )
	_polyTri = QtGui.QPolygonF([
			QPointF(  0,   0 ),
			QPointF( -12, -6 ),
			QPointF( -12,  6 ),
			])

	def __init__( self, *args, **kwargs ):
		super( YEdEdgeItem, self ).__init__( *args, **kwargs )
		self.setPen( YEdEdgeItem._pen )
		self.edge = None

	def setEdge( self, edge ):
		self.edge = edge
		points = edge.getAttr( 'path', [] )
		self.hasArrow = edge.getAttr( 'arrow-target', 'none' ) != 'none'
		path = QtGui.QPainterPath()
		head = True
		for i, p in enumerate( points ):
			if i > 0:
				path.lineTo( *p )
			else:
				path.moveTo( *p )
		self.setPath( path )

	def paint( self, painter, option, widget ):
		super( YEdEdgeItem, self ).paint( painter, option, widget )
		#draw arrow
		if self.hasArrow:
			path = self.path()
			midDir   = path.angleAtPercent( 0.5 )
			midPoint = path.pointAtPercent( 0.5 )
			trans = QTransform()
			trans.translate( midPoint.x(), midPoint.y() )
			trans.rotate( -midDir )
			painter.setTransform( trans, True )
			painter.drawPolygon( YEdEdgeItem._polyTri )

##----------------------------------------------------------------##
class YEdNodeItem( QtWidgets.QGraphicsRectItem, StyledItemMixin ):
	def __init__( self, *args, **kwargs ):
		super( YEdNodeItem, self ).__init__( *args, **kwargs )
		self.setZValue( 10 )
		self.setCursor( Qt.PointingHandCursor )
		self.setFlag( self.ItemIsSelectable, True )
		self.node = None
		self.brush = None
		self.text = None
		self.setItemType( 'ynode' )
		self.setItemState( 'normal' )
		self.setRect( 0,0,100, 100 )

	def isGroup( self ):
		return False

	def setNode( self, node ):
		self.node = node
		geom = node.getAttr( 'geometry', None )
		if geom:
			x,y,w,h = geom
			self.setRect( x,y,w,h )
		self.text = node.getAttr( 'label', None )
		self.updateStyle()
		self.setZValue( node.getDepth() )
		self.update()

	def updateStyle( self ):
		node = self.node
		color = node.getAttr( 'fill-color', None )
		if color:
			self.brush = makeBrush( color = color, alpha = 0.8 )
		else:
			self.brush = makeBrush( color = '#ffffff', alpha = 0.05 )

	def onPaint( self, painter, option, widget ):
		rect = self.rect()
		painter.setBrush( self.brush )
		painter.drawRoundedRect( rect, 5, 5 )
		if self.text:
			trect = rect.adjusted( 2,2, -2,-2 )
			painter.drawText( trect, Qt.AlignCenter|Qt.AlignVCenter, self.text )

	def mouseDoubleClickEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			self.parentView.onNodeDClicked( self )
			
##----------------------------------------------------------------##
class YEdGroupNodeItem( YEdNodeItem ):
	_textPen  = makePen( color = '#ccc', width = 2 )
	def __init__( self, *args, **kwargs ):
		super( YEdGroupNodeItem, self ).__init__( *args, **kwargs )
		self.setItemType( 'ygroup' )

	def isGroup( self ):
		return True

	def updateStyle( self ):
		super( YEdGroupNodeItem, self ).updateStyle()
		if self.brush:
			c = self.brush.color()
			c.setAlphaF( 0.3 )
			self.brush.setColor( c )

	def onPaint( self, painter, option, widget ):
		rect = self.rect()
		painter.setBrush( self.brush )
		painter.drawRoundedRect( rect, 10, 10 )
		if self.text:
			trect = rect.adjusted( 8,6, -2,-2 )
			painter.setPen( YEdGroupNodeItem._textPen )
			painter.drawText( trect, Qt.AlignLeft|Qt.AlignTop, self.text )


##----------------------------------------------------------------##
class YEdGraphView( GLGraphicsView ):
	selectionChanged   = Signal()
	scrollXChanged     = Signal( float )
	scrollYChanged     = Signal( float )
	zoomChanged        = Signal( float )

	def __init__(self, *args, **kwargs ):
		super(YEdGraphView, self).__init__( *args, **kwargs )
		self.updating = False
		self.updatingSelection = False
		scene = GLGraphicsScene()
		self.setScene( scene )
		
		self.setBackgroundBrush( _DEFAULT_BG )
		# self.gridBackground = GridBackground()
		# scene.addItem( self.gridBackground )

		scene.sceneRectChanged.connect( self.onRectChanged )
		scene.selectionChanged.connect( self.notifySceneItemSelectionChanged )

		self.rebuilding = False
		self.panning = False
		self.scrollX = 0
		self.scrollY = 0
		self.scrollXMin = None
		self.scrollXMax = None

		self.zoom = 1
		self.unitScale = 0.7
		self.scene().setSceneRect( QRectF( -10000,-10000, 20000, 20000 ) )
		self.setZoom( 1.0 )

		self.nodeToItem = {}
		self.edgeToItem = {}

	def clear( self ):
		scn = self.scene()
		scn.clear()
		self.nodeToItem = {}
		self.edgeToItem = {}

	def loadGraph( self, graph ):
		self.clear()
		self.graph = graph
		for id, node in list(graph.nodes.items()):
			self.addNode( node )

		for id, edge in list(graph.edges.items()):
			self.addEdge( edge )
		self.zoom = 1
		self.scrollX = 0
		self.scrollY = 0
		self.updateTransfrom()

	def getGraph( self ):
		return self.graph

	def createNodeItem( self, node ):
		if isinstance( node, YEdGraphGroup ):
			item = YEdGroupNodeItem()
		else:
			item = YEdNodeItem()
		return item

	def createEdgeItem( self, edge ):
		item = YEdEdgeItem()
		return item

	def addNode( self, node ):
		item = self.createNodeItem( node )
		item.setNode( node )
		item.parentView = self
		self.nodeToItem[ node ] = item
		self.scene().addItem( item )

	def addEdge( self, edge ):
		item = self.createEdgeItem( edge )
		item.setEdge( edge )
		item.parentView = self
		self.edgeToItem[ edge ] = item
		self.scene().addItem( item )

	def getNodeItem( self, node ):
		return self.nodeToItem.get( node, None )

	def getEdgeItem( self, edge ):
		return self.edgeToItem.get( edge, None )

	def onRectChanged( self, rect ):
		# self.gridBackground.setRect( rect )
		pass

	def onZoomChanged( self ):
		self.updateTransfrom()

	def fitAll( self ):
		aabb = None
		for node, item in list(self.nodeToItem.items()):
			nodeRect = item.sceneBoundingRect()
			if not aabb:
				aabb = nodeRect
			else:
				aabb = aabb.united( nodeRect )
		margin = 20
		aabb.adjust( -margin, -margin, margin, margin )
		self.fitSceneRect( aabb.left(), aabb.top(), aabb.right(), aabb.bottom() )

	def fitSceneRect( self, x0, y0, x1, y1 ):
		w = float( x1 - x0 )
		h = float( y1 - y0 )
		if w == 0 or h == 0: return False
		vw = float( self.width() )
		vh = float( self.height() )
		if vw == 0 or vh == 0: return False
		ox = 0 
		oy = 0
		if vw/w > vh/h: #fit height
			zoom = vh / h
			ox = ( vw / zoom - w ) / 2.0
		else: #fit width
			th = vh/vw * w
			zoom = vw / w
			oy = ( vh / zoom - h ) / 2.0
		self.setZoom( zoom )
		self.setScroll( x0 - ox, y0 - oy )

	def setZoom( self, zoom ):
		self.zoom = zoom
		self.onZoomChanged()

	def setScroll( self, x, y ):
		self.scrollX = x
		self.scrollY = y
		self.scrollXChanged.emit( self.scrollX )
		self.scrollYChanged.emit( self.scrollY )
		self.updateTransfrom()

	def valueToPos( self, x, y ):
		z = self.zoom
		u = self.unitScale
		return x * z * u, y * z * u

	def posToValue( self, x, y ):
		z = self.zoom
		u = self.unitScale
		return x / z / u, y / z / u

	def wheelEvent(self, event):
		steps = event.pixelDelta().y() / 120.0;
		dx = 0
		dy = 0
		zoomRate = 1.1
		dy = steps
		if dy>0:
			self.setZoom( self.zoom * zoomRate )
		else:
			self.setZoom( self.zoom / zoomRate )

	def mouseMoveEvent( self, event ):
		super( YEdGraphView, self ).mouseMoveEvent( event )
		if self.panning:
			p1 = event.pos()
			p0, off0 = self.panning
			dx = p0.x() - p1.x()
			dy = p0.y() - p1.y()
			offX0, offY0 = off0
			offX1 = offX0 + dx
			offY1 = offY0 + dy
			x , y = self.posToValue( offX1, offY1 )
			self.setScroll( x, y )

	def mousePressEvent( self, event ):
		super( YEdGraphView, self ).mousePressEvent( event )
		if event.button() == Qt.MidButton:
			offX0, offY0 = self.valueToPos( self.scrollX, self.scrollY )
			self.panning = ( event.pos(), ( offX0, offY0 ) )

	def mouseReleaseEvent( self, event ):
		super( YEdGraphView, self ).mouseReleaseEvent( event )
		if event.button() == Qt.MidButton :
			if self.panning:
				self.panning = False

	def updateTransfrom( self ):
		if self.updating : return
		self.updating = True
		trans = QTransform()
		z = self.zoom
		x, y = -self.scrollX, - self.scrollY
		trans.scale( z, z )
		trans.translate( x, y )
		
		self.setTransform( trans )
		self.update()
		self.updating = False

	def notifySceneItemSelectionChanged( self ):
		if self.updatingSelection: return
		self.selectionChanged.emit()

	def onNodeDClicked( self, node ):
		pass

	def __del__( self ):
		self.deleteLater()


##----------------------------------------------------------------##
if __name__ == '__main__':
	class TestView( QtWidgets.QWidget ):
		def __init__(self, *args, **kwargs ):
			super(TestView, self).__init__( *args, **kwargs )
			layout = QtWidgets.QVBoxLayout( self )
			layout.setSpacing( 0 )
			layout.setContentsMargins( 0 , 0 , 0 , 0 )
			self.view = YEdGraphView( parent = self, antialias = True )
			layout.addWidget( self.view )
			parser = YEdGraphMLParser()
			g = parser.parse( 'test2.graphml' )
			self.view.loadGraph( g )

			# self.view.scene().addItem( YEdNodeItem() )

	app = QtWidgets.QApplication( sys.argv )
	styleSheetName = 'gii.qss'
	app.setStyleSheet(
			open( '/Users/tommo/prj/gii/data/theme/' + styleSheetName ).read() 
		)

	g = TestView()
	g.resize( 600, 300 )
	g.show()
	g.raise_()
	# Graph.setZoom( 10 )
	# Graph.selectTrack( dataset[1] )

	app.exec_()