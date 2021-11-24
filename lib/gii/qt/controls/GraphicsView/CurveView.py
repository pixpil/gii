import sys
import math

from functools import cmp_to_key

from qtpy import QtWidgets, QtGui, QtCore, QtOpenGL, uic
from qtpy.QtCore import Qt, QObject, QEvent, Signal
from qtpy.QtCore import QPoint, QRect, QSize
from qtpy.QtCore import QPointF, QRectF, QSizeF
from qtpy.QtGui import QColor, QTransform
from qtpy.QtWidgets import QStyle

from .GraphicsViewHelper import *
from .TimelineViewCommon import *


##----------------------------------------------------------------##
CV_INNER_SIZE = 6
CV_SIZE = 15
BP_INNER_SIZE = 6
BP_SIZE = 15

_PIXEL_PER_UNIT = 100.0 #basic scale
_HEAD_OFFSET = 15

##----------------------------------------------------------------##
_DEFAULT_BG = makeBrush( color = '#222' )
makeStyle( 'cv',                '#acbcff',    '#000000'              )
makeStyle( 'cv:selected',       '#ffffff',    '#4d9fff'              )
makeStyle( 'bp',                dict( color = '#b940d6', alpha=0.5 ),    '#000000'    )
makeStyle( 'bp:selected',       dict( color = '#ffffff', alpha=1.0 ),    '#b940d6'    )
makeStyle( 'curve',             '#7f7f7f',    None             )


##----------------------------------------------------------------##
TWEEN_MODE_CONSTANT = 0
TWEEN_MODE_LINEAR   = 1
TWEEN_MODE_BEZIER   = 2
TANGENT_MODE_AUTO    = 0
TANGENT_MODE_SPLIT   = 1
TANGENT_MODE_SMOOTH  = 2

##----------------------------------------------------------------##
class AxisGridBackground( QtWidgets.QGraphicsRectItem ):
	_gridPen  = makePen( color = '#333', width = 1 )
	_axisPen  = makePen( color = '#777', width = 1 )
	_originPen  = makePen( color = '#204800', width = 2 )
	_cursorPen  = makePen( color = '#a3ff00', width = 1 )
	def __init__( self ):
		super( AxisGridBackground, self ).__init__()
		self.setZValue( -100 )
		self.gridWidth = 50
		self.gridHeight = 50 
		self.offsetX = 1
		self.offsetY = 1
		self.zoomX = 2
		self.zoomY = 1
		self.XAxisVisible = True
		self.YAxisVisible = True
		self.cursorVisible = False
		self.cursorPosX = 0
		self.cursorPen = AxisGridBackground._cursorPen
		self.maxRange = 0 
		self.rangeVisible = False

	def setOffset( self, x, y ):
		self.offsetX = x
		self.offsetY = y
		self.updateTransfrom()

	def setCursorPosX( self, pos ):
		self.cursorPosX = pos

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

	def paint( self, painter, option, widget ):
		# painter.setRenderHint( QtGui.QPainter.Antialiasing, False )
		rect = painter.viewport()
		transform = painter.transform()
		dx = transform.dx() 
		dy = transform.dy()
		w = rect.width()
		h = rect.height()
		x0 = -dx
		y0 = -dy
		x1 = x0 + w
		y1 = y0 + h

		gridSize = 100.0
		
		#
		u = 1.0
		
		ux = u * self.zoomX
		uy = u * self.zoomY
		vx0 = x0 / ux
		vy0 = y0 / uy
		dvx = w / ux
		dvy = h / uy
		vx1 = vx0 + dvx
		vy1 = vy0 + dvy

		stepx = max( int ( gridSize / ux / 5.0 ) * 5.0, 1.0 )
		stepy = max( int ( gridSize / uy / 5.0 ) * 5.0, 1.0 )
		stepWidth = stepx * ux
		stepHeight = stepy * uy

		#Grid
		gux = ux * stepx
		guy = uy * stepy
		ox = (dx) % gux
		oy = (dy) % guy
		rows = int( h/guy ) + 1
		cols = int( w/gux ) + 1
		offx = self.offsetX
		painter.setPen( AxisGridBackground._gridPen )
		for col in range( cols ): #V lines
			x = col * gux + ox + x0 + offx
			painter.drawLine( x, y0, x, y1 )
		
		# x0 = max( x0, _HEAD_OFFSET )
		offy = self.offsetY
		painter.setPen( AxisGridBackground._gridPen )
		for row in range( rows ): #H lines
			y = row * guy + oy + y0 + offy
			painter.drawLine( x0, y, x1, y )
		
		#Origin
		painter.setPen( AxisGridBackground._originPen )
		originX = 0
		originY = 0
		painter.drawLine( originX, y0, originX, y1 )
		painter.drawLine( x0, originY, x1, originY )

		trans = painter.transform()
		trans.translate( -dx, -dy )
		painter.setTransform( trans )
		#XAxis
		if self.XAxisVisible:
			start = math.floor( vx0/stepx ) * stepx
			end   = math.ceil( vx1/stepx ) * stepx
			count = int( (end-start)/stepx ) + 1
			
			painter.setPen( AxisGridBackground._axisPen )
			subStep = 5
			subPitch = stepWidth/subStep
			for i in range( count ): #V lines
				vx = start + i * stepx
				xx = (vx-vx0) * ux
				painter.drawLine( xx, h-20, xx, h - 1 )
				for j in range( 1, subStep ):
					sxx = xx + j * subPitch
					painter.drawLine( sxx, h-6, sxx, h - 1 )
				markText = '%.2f'%( vx/_PIXEL_PER_UNIT )
				painter.drawText( QRectF( xx + 2, h-20, 100, 100 ), Qt.AlignTop|Qt.AlignLeft, markText )

		#YAxis
		if self.YAxisVisible:
			start = math.floor( vy0/stepy ) * stepy
			end   = math.ceil( vy1/stepy ) * stepy
			count = int( (end-start)/stepy ) + 1

			painter.setPen( AxisGridBackground._axisPen )
			subStep = 5
			subPitch = stepHeight/subStep
			for i in range( count ): #V lines
				vy = start + i * stepy
				yy = (vy-vy0) * uy
				painter.drawLine( 0, yy, 20, yy )
				for j in range( 1, subStep ):
					syy = yy + j * subPitch
					painter.drawLine( 0, syy, 6, syy )
				markText = '%.2f'%( -vy/_PIXEL_PER_UNIT )
				painter.drawText( QRectF( 5, yy + 3, 100, 20 ), Qt.AlignTop|Qt.AlignLeft, markText )
		
		if self.rangeVisible:
			x = self.maxRange + dx
			painter.setPen( AxisGridBackground._rangePen )
			painter.drawLine( x, y0 + dy, x, y1 + dy )

		if self.cursorVisible:
			x = self.cursorPosX + dx
			painter.setPen( self.cursorPen )
			painter.drawLine( x, y0 + dy, x, y1 + dy )

	def setZoom( self, zx, zy ):
		self.zoomX = zx
		self.zoomY = zy
		self.update()

##----------------------------------------------------------------##
class CurveSpanItem( QtWidgets.QGraphicsPathItem ):
	def __init__( self, startVert, *args ):
		super( CurveSpanItem, self ).__init__( *args )
		self.startVert = startVert
		self.setParentItem( startVert.parentCurve )
		applyStyle( 'curve', self )

	def updateShape( self ):
		mode = self.startVert.tweenMode
		if mode == TWEEN_MODE_CONSTANT:
			self.updateConstantCurve()
		if mode == TWEEN_MODE_LINEAR:
			self.updateLinearCurve()
		if mode == TWEEN_MODE_BEZIER:
			self.updateBezierCurve()

	def updateLinearCurve( self ):
		startVert = self.startVert
		endVert = startVert.getNextVert()
		if not endVert: 
			self.hide()
			return
		self.show()
		self.setPos( startVert.pos() )

		path = QtGui.QPainterPath()
		pos1 = self.mapFromScene( endVert.scenePos() )
		path.moveTo( 0, 0 )
		path.lineTo( pos1 )
		self.setPath( path )

	def updateConstantCurve( self ):
		startVert = self.startVert
		endVert = startVert.getNextVert()
		if not endVert: 
			self.hide()
			return
		self.show()
		self.setPos( startVert.pos() )

		path = QtGui.QPainterPath()
		pos1 = self.mapFromScene( endVert.scenePos() )
		path.moveTo( 0, 0 )
		path.lineTo( pos1.x(), 0 )
		path.lineTo( pos1 )
		self.setPath( path )

	def updateBezierCurve( self ):
		startVert = self.startVert
		endVert  = startVert.getNextVert()
		if not endVert: 
			self.hide()
			return
		self.show()

		self.setPos( startVert.pos() )

		path = QtGui.QPainterPath()
		pos1 = self.mapFromScene( endVert.scenePos() )
		tp0  = startVert.getPostBP() # + (0,0)
		preBP = endVert.getPreBP() + pos1
		path.moveTo( 0, 0 )
		path.cubicTo( tp0, preBP, pos1 )
		self.setPath( path )

	def paint( self, painter, option, widget ):
		painter.setRenderHint( QtGui.QPainter.Antialiasing, False )
		applyStyle( 'curve', painter)
		path = self.path()
		painter.drawPath( path )

##----------------------------------------------------------------##
class CurveTangentPointItem( QtWidgets.QGraphicsRectItem ):
	def __init__( self, parent ):
		super( CurveTangentPointItem, self ).__init__( parent = parent )
		self.setZValue( 9 )
		self.setRect( -BP_SIZE/2, -BP_SIZE/2, BP_SIZE, BP_SIZE )
		self.innerRect = QRectF( -BP_INNER_SIZE/2, -BP_INNER_SIZE/2, BP_INNER_SIZE, BP_INNER_SIZE )
		self.setCursor( Qt.PointingHandCursor )
		self.setFlag( self.ItemSendsGeometryChanges, True )
		self.setFlag( self.ItemIsMovable, True )
		self.setFlag( self.ItemIsSelectable, True )

	def itemChange( self, change, value ):
		if change == self.ItemPositionChange or change == self.ItemPositionHasChanged:
			self.parentVert.onTPUpdate( self )
		return super( CurveTangentPointItem, self ).itemChange( change, value )

	def paint( self, painter, option, widget ):
		if self.isSelected():
			applyStyle( 'bp:selected', painter )
		else:
			applyStyle( 'bp', painter )
		painter.drawEllipse( self.innerRect )

##----------------------------------------------------------------##
class CurveVertPointItem( QtWidgets.QGraphicsRectItem ):
	def __init__( self, vertItem ):
		super( CurveVertPointItem, self ).__init__( parent = vertItem.parentCurve )
		self.setZValue( 15 )
		self.setRect( -CV_SIZE/2, -CV_SIZE/2, CV_SIZE, CV_SIZE )
		self.innerRect = QRectF( -CV_INNER_SIZE/2, -CV_INNER_SIZE/2, CV_INNER_SIZE, CV_INNER_SIZE )
		self.setCursor( Qt.PointingHandCursor )
		self.setFlag( self.ItemSendsGeometryChanges, True )
		self.setFlag( self.ItemIsMovable, True )
		self.setFlag( self.ItemIsSelectable, True )
		self.vertItem = vertItem

	def itemChange( self, change, value ):
		if change == self.ItemPositionChange or change == self.ItemPositionHasChanged:
			vert = self.vertItem
			x, y = vert.limitVertPos( self.x(), self.y() )
			self.setFlag( self.ItemSendsGeometryChanges, False)
			self.setPos( x, y )
			self.vertItem.setPos( self.pos() )
			self.setFlag( self.ItemSendsGeometryChanges, True)
		return super( CurveVertPointItem, self ).itemChange( change, value )

	def paint( self, painter, option, widget ):
		if self.isSelected():
			applyStyle( 'cv:selected', painter )
		else:
			applyStyle( 'cv', painter )
		painter.drawRect( self.innerRect )

##----------------------------------------------------------------##
class CurveVertItem( QtWidgets.QGraphicsRectItem ):
	def __init__( self, parent ):
		super( CurveVertItem, self ).__init__( parent = parent )
		self.node = None
		#
		self.index = 0 #update by curve verts sorting
		self.parentCurve = parent
		self.setZValue( 10 )
		self.setRect( -CV_SIZE/2, -CV_SIZE/2, CV_SIZE, CV_SIZE )
		self.setFlag( self.ItemSendsGeometryChanges, True )
		self.updating = False

		self.tweenMode = TWEEN_MODE_LINEAR

		#components
		self.VP     = CurveVertPointItem( self )
		self.span   = CurveSpanItem( self )
		self.preBP  = CurveTangentPointItem( self )
		self.postBP = CurveTangentPointItem( self )

		self.preBP.parentVert  = self
		self.postBP.parentVert = self
		self.VP.parentVert     = self

		self.preBP.hide()
		self.postBP.hide()

		self.preBezierPoint  = ( 0.5, 0 )
		self.postBezierPoint = ( 0.5, 0 )

		self.setParentItem( parent )
		

	def getCurveView( self ):
		return self.parentCurve.getCurveView()

	def limitVertPos( self, x, y ):
		nv = self.getNextVert()
		pv = self.getPrevVert()
		if pv:
			x = max( pv.x(), x )
		else:
			x = max( 0, x )
		if nv:
			x = min( nv.x(), x )
		view = self.getCurveView()
		rx0, rx1 = view.getRangeX()
		x0 = rx0 * _PIXEL_PER_UNIT
		x1 = rx1 * _PIXEL_PER_UNIT
		x = max( min( x, x1 ), x0 )
		return x, y

	def updateZoom( self, zx, zy ):
		trans = QTransform()
		trans.scale( 1.0/zx, 1.0/zy )
		# self.setTransform( trans )
		self.VP.setTransform( trans )
		self.preBP.setTransform( trans )
		self.postBP.setTransform( trans )
		self.updateTPPos()

	def getPostBP( self ):
		return self.postBP.pos()

	def getPreBP( self ):
		return self.preBP.pos()	

	def updateTPPos( self ):
		prev = self.getPrevVert()
		if prev: #update TP pos
			(px0, py0) = prev.postBezierPoint
			(px1, py1) = self.preBezierPoint
			pos0 = prev.pos()
			pos1 = self.pos()
			dx = ( pos1.x() - pos0.x() )
			prev.postBP.setPos(   px0 * dx, - py0 )
			self.preBP .setPos( - px1 * dx, - py1 )

	def itemChange( self, change, value ):		
		if change == self.ItemPositionChange:
			pass
		elif change == self.ItemPositionHasChanged:
			if not self.updating:
				self.updating = True
				self.VP.setPos( self.pos() )
				self.updateTPPos()
				if self.getNextVert():
					self.getNextVert().updateTPPos()
				self.updateSpan()
				self.getCurveView().notifyVertChanged( self )
				self.updating = False
		return QtWidgets.QGraphicsRectItem.itemChange( self, change, value )

	def onTPUpdate( self, tp ):
		if tp == self.postBP:
			nextVert = self.getNextVert()
			if nextVert:
				pos = tp.pos()
				dx = nextVert.pos().x() - self.pos().x()
				if dx == 0:
					(px, py) = self.postBezierPoint
					self.postBezierPoint = ( px, -pos.y() )
				else:
					( bpx, bpy ) = nextVert.preBezierPoint 
					v0 = 0.0
					v1 = (1.0 - bpx)
					v = tp.pos().x() / dx
					corrected = max( 0.0, min( v1, v  ) )
					self.postBezierPoint = ( corrected , -pos.y() )
					if v != corrected:
						tp.setFlag( self.ItemSendsGeometryChanges, False )
						tp.setX( dx*corrected )
						tp.setFlag( self.ItemSendsGeometryChanges, True )
		elif tp == self.preBP:
			prevVert = self.getPrevVert()
			if prevVert:
				pos = tp.pos()
				dx = prevVert.pos().x() - self.pos().x()
				if dx == 0:
					(px, py) = self.preBezierPoint
					self.preBezierPoint = ( px, -pos.y() )
				else:
					( bpx, bpy ) = prevVert.postBezierPoint 
					v0 = 0.0
					v1 = (1.0 - bpx)
					v = tp.pos().x() / dx
					corrected = max( 0.0, min( v1, v ) )
					self.preBezierPoint = ( corrected , -pos.y() )
					if v != corrected:
						tp.setFlag( self.ItemSendsGeometryChanges, False )
						tp.setX( dx * corrected )
						tp.setFlag( self.ItemSendsGeometryChanges, True )
		self.updateSpan()
		self.getCurveView().notifyVertChanged( self, False, True )

	def getIndex( self ):
		return self.index

	def getPrevVert( self ):
		return self.parentCurve.getPrevVert( self )

	def getNextVert( self ):
		return self.parentCurve.getNextVert( self )

	def updateSpan( self, updateNeighbor = True ):
		prevVert = self.getPrevVert()
		nextVert = self.getNextVert()
		if self.tweenMode == TWEEN_MODE_BEZIER:
			self.postBP.show()
			if nextVert:
				nextVert.preBP.show()
		else:
			self.postBP.hide()
			if nextVert:
				nextVert.preBP.hide()

		if updateNeighbor:
			if prevVert: prevVert.updateSpan( False )
			if nextVert: nextVert.updateSpan( False )
		self.span.updateShape()
		bx = ( self.preBP.x(), self.postBP.x(), 0.0 )
		by = ( self.preBP.y(), self.postBP.y(), 0.0 )
		x0 = min( bx )
		y0 = min( by )
		x1 = max( bx )
		y1 = max( by )
		self.setRect( x0,y0,x1-x0,y1-y0 )		

	def paint( self, painter, option, widget ):
		applyStyle( 'bp', painter)
		p0 = QPointF( 0.0, 0.0 )
		if self.preBP.isVisible():
			painter.drawLine( p0, self.preBP.pos() )
		if self.postBP.isVisible():
			painter.drawLine( p0, self.postBP.pos() )

	def setTweenMode( self, mode ):
		if not self.updating:
			self.updating = True
			if mode < 0 or mode > TWEEN_MODE_BEZIER:
				mode = 0
			self.tweenMode = mode
			self.getCurveView().notifyVertTweenModeChanged( self, mode )
			self.updateTPPos()
			nextVert = self.getNextVert()
			if nextVert:
				nextVert.updateTPPos()
			self.updateSpan()
			self.updating = False

	def setParam( self, x,y, tweenMode, preBPX, preBPY, postBPX, postBPY ):
		self.setPos( x * _PIXEL_PER_UNIT, -y * _PIXEL_PER_UNIT )
		self.tweenMode = tweenMode
		#Todo tangent
		self.preBezierPoint  = ( preBPX,  preBPY * _PIXEL_PER_UNIT  )
		self.postBezierPoint = ( postBPX, postBPY * _PIXEL_PER_UNIT )
		self.updateTPPos()
		self.updateSpan()

	def showBP( self ):
		self.preBP.show()
		self.postBP.show()
		prev = self.getPrevVert()
		if prev:
			prev.postBP.show()
		next = self.getNextVert()
		if next:
			next.preBP.show()

	def hideTP( self ):
		self.preBP.hide()
		self.postBP.hide()
		prev = self.getPrevVert()
		if prev:
			prev.postBP.hide()
		next = self.getNextVert()
		if next:
			next.preBP.hide()

	def delete( self, scn ):
		if scn:
			scn.removeItem( self.preBP )
			scn.removeItem( self.postBP )
			scn.removeItem( self.VP )
			scn.removeItem( self )
		self.setParentItem( None )
		self.preBP.setParentItem( None )
		self.postBP.setParentItem( None )
		self.VP.setParentItem( None )

	def setSelected( self, selected ):
		self.VP.setSelected( selected )


##----------------------------------------------------------------##
class CurveItem( QtWidgets.QGraphicsRectItem ):
	def __init__( self, curveNode ):
		super(CurveItem, self).__init__()
		self.node = curveNode
		self.view = None

		self.zx = 1
		self.zy = 1
		self.vertItems = []
		self.nodeToVert = {}
		
	def getVertByNode( self, node ):
		return self.nodeToVert.get( node, None )

	def addVert( self, node ):
		vert = CurveVertItem( self )
		vert.node = node
		self.vertItems.append( vert )
		vert.index = len( self.vertItems ) - 1
		self.nodeToVert[ node ] = vert
		self.sortVerts()
		self.updateSpan()
		vert.updateZoom( self.zx, self.zy )
		return vert

	def removeVert( self, node ):
		vert = self.getVertByNode( node )
		if vert :
			del self.nodeToVert[ node ]
			vert.setParentItem( None )
			vert.node = None
			self.vertItems.remove( vert )

	def getPrevVert( self, vert ):
		index = vert.index
		index1 = index - 1
		if index1 >= 0:
			return self.vertItems[ index1 ]
		return None

	def getNextVert( self, vert ):
		index = vert.index
		index1 = index + 1
		if index1 < len( self.vertItems ):
			return self.vertItems[ index1 ]
		return None

	def clear( self ):
		scn = self.scene()
		for vert in self.vertItems:
			vert.delete( scn )
			vert.node = None
		self.nodeToVert = {}
		self.vertItems = []
		self.updateSpan()

	def sortVerts( self ):
		pass

	def setZoom( self, x, y ):
		self.zx = x
		self.zy = y
		trans = QTransform()
		trans.scale( self.zx, self.zy )
		self.setTransform( trans )
		for vert in self.vertItems:
			vert.updateZoom( self.zx, self.zy )

	def updateSpan( self ):
		pass

	def getCurveView( self ):
		return self.view

##----------------------------------------------------------------##
class CurveView( GLGraphicsView ):
	scrollXChanged     = Signal( float )
	scrollYChanged     = Signal( float )
	zoomXChanged       = Signal( float )
	zoomYChanged       = Signal( float )
	cursorPosXChanged  = Signal( float )
	cursorPosYChanged  = Signal( float )

	vertChanged        = Signal( object, float, float ) #vertNode, x, y
	vertBezierPointChanged = Signal( object, float, float, float, float )
	vertTweenModeChanged = Signal( object, int )
	selectionChanged   = Signal()

	def __init__(self, *args, **kwargs ):
		super(CurveView, self).__init__( *args, **kwargs )
		self.updating = False
		self.updatingSelection = False
		scene = GLGraphicsScene()
		self.setScene( scene )
		
		self.setBackgroundBrush( _DEFAULT_BG )
		self.gridBackground = AxisGridBackground()
		scene.addItem( self.gridBackground )
		scene.sceneRectChanged.connect( self.onRectChanged )

		scene.selectionChanged.connect( self.notifySceneItemSelectionChanged )
		
		self.curveItems = []
		self.nodeToCurve = {}

		#components
		self.cursorItem = TimelineCursorItem()
		self.cursorItem.setLine( 0,-10000, 0, 20000 )
		self.cursorItem.setZValue( 1000 )
		# self.scene().addItem( self.cursorItem )

		self.rebuilding = False
		self.panning = False
		self.scrollX = 0
		self.scrollY = 0
		self.scrollXMin = None
		self.scrollXMax = None

		self.cursorX = 0
		self.cursorY = 0
		
		self.offsetX = 0

		self.zoomX = 1.0
		self.zoomY = 1.0
		self.scene().setSceneRect( QRectF( -10000,-10000, 20000, 20000 ) )
		self.setZoomX( 1 )
		self.setZoomY( 1 )
		self.setCursorVisible( True )

		self.minRangeX = 0
		self.maxRangeX = 1000000
		self.minRangeY = -1000000
		self.maxRangeY = 1000000

	def onRectChanged( self, rect ):
		self.gridBackground.setRect( rect )

	def getRangeX( self ):
		return self.minRangeX, self.maxRangeX

	def getRangeY( self ):
		return self.minRangeY, self.maxRangeY

	def setRangeX( self, x0, x1 ):
		self.minRangeX, self.maxRangeX = x0, x1
		#TODO: update grid

	def setRangeY( self, y0, y1 ):
		self.minRangeY, self.mayRangeY = y0, y1
		#TODO: update grid

	def setAxisVisible( self, xAxis, yAxis ):
		self.gridBackground.XAxisVisible = xAxis
		self.gridBackground.YAxisVisible = yAxis

	def setCursorVisible( self, visible ):
		# self.cursorItem.setVisible( visible )
		self.gridBackground.cursorVisible = visible

	def setScrollXLimit( self, minX, maxX ):
		self.scrollXMin = minX
		self.scrollXMax = maxX

	def setScroll( self, x, y ):
		if not self.scrollXMin is None:
			x = max( self.scrollXMin, x )
		# if self.scrollXMin:
		# 	x = max( self.scrollXMin, x )
		self.scrollX = x
		self.scrollY = y
		self.scrollXChanged.emit( self.scrollX )
		self.scrollYChanged.emit( self.scrollY )
		self.updateTransfrom()

	def setScrollX( self, x ):
		if not self.scrollXMin is None:
			x = max( self.scrollXMin, x )
		self.scrollX = x
		self.scrollXChanged.emit( self.scrollX )
		self.updateTransfrom()

	def setOffset( self, x, y ):
		self.offsetX = x
		self.offsetY = y
		self.updateTransfrom()

	def setCursorX( self, vx ):
		self.cursorX = vx
		# self.cursorItem.setX( self.valueToX( vx ) )
		x = self.valueToX( vx )
		self.gridBackground.setCursorPosX( x )
		self.update()

	def wheelEvent(self, event):
		steps = event.pixelDelta().y() / 120.0;
		zoomRate = 1.1
		delta = event.angleDelta()
		dx = delta.x()
		dy = delta.y()
		if dy>0:
			self.setZoomY( self.zoomY * zoomRate )
		elif dy<0:
			self.setZoomY( self.zoomY / zoomRate )

		if dx>0:
			self.setZoomX( self.zoomX * zoomRate )
		elif dx<0:
			self.setZoomX( self.zoomX / zoomRate )

	def setZoomX( self, zoom ):
		self.zoomXChanged.emit( zoom )
		self.zoomX = zoom
		self.onZoomChanged()

	def setZoomY( self, zoom ):
		self.zoomYChanged.emit( zoom )
		self.zoomY = zoom
		self.onZoomChanged()

	def onZoomChanged( self ):
		for curve in self.curveItems:
			curve.setZoom( self.zoomX, self.zoomY )
		self.gridBackground.setZoom( self.zoomX, self.zoomY )
		self.updateTransfrom()
		# self.cursorItem.setX( self.valueToX( self.cursorX ) )
		self.gridBackground.setCursorPosX( self.valueToX( self.cursorX ) )

	def mouseMoveEvent( self, event ):
		super( CurveView, self ).mouseMoveEvent( event )
		if self.panning:
			p1 = event.pos()
			p0, off0 = self.panning
			dx = p0.x() - p1.x()
			dy = p0.y() - p1.y()
			offX0, offY0 = off0
			offX1 = offX0 + dx
			offY1 = offY0 + dy
			self.setScroll( self.xToValue( offX1 ), self.yToValue( offY1 ) )

	def mousePressEvent( self, event ):
		super( CurveView, self ).mousePressEvent( event )
		if event.button() == Qt.MidButton:
			offX0, offY0 = self.valueToPos( self.scrollX, self.scrollY )
			self.panning = ( event.pos(), ( offX0, offY0 ) )

	def mouseReleaseEvent( self, event ):
		super( CurveView, self ).mouseReleaseEvent( event )
		if event.button() == Qt.MidButton :
			if self.panning:
				self.panning = False

	def updateTransfrom( self ):
		if self.updating : return
		self.updating = True
		trans = QTransform()
		tx = self.valueToX( -self.scrollX ) + self.offsetX
		ty = self.valueToY( -self.scrollY )
		# if ty > 20000:
		# 	raise "wtf"
		trans.translate( tx, ty )
		self.setTransform( trans )
		self.update()
		self.updating = False

	def xToValue( self, x ):
		return  x /( _PIXEL_PER_UNIT * self.zoomX )

	def valueToX( self, v ):
		return v * self.zoomX * _PIXEL_PER_UNIT

	def yToValue( self, y ):
		return  y /( _PIXEL_PER_UNIT * self.zoomY )

	def valueToY( self, v ):
		return v * self.zoomY * _PIXEL_PER_UNIT

	def valueToPos( self, x, y ):
		return ( self.valueToX( x ), self.valueToY( y ) )

	def posToValue( self, xv, yv ):
		return ( self.xToValue( xv ), self.yToValue( yv ) )


	#====Building
	def rebuild( self, fit = True ):
		self.clear()
		self.rebuilding = True
		for curveNode in self.getCurveNodes():
			self.addCurve( curveNode )
		self.rebuilding = False
		if fit:
			self.fitAllCurves( False, True ) #fit y axis only

	def viewportSize( self ):
		view = self.viewport()
		return view.width(), view.height()

	def locatePoint( self, px, py ):
		w, h = self.viewportSize()
		self.setScroll( px - self.xToValue( w )/2, -py - self.yToValue( h )/2 )

	def fitRect( self, x0,y0,x1,y1, fitX = True, fitY = True ):
		w, h = self.viewportSize()
		dx = x1 - x0
		dy = y1 - y0
		marginX = 100
		marginY = 100
		zx = max( w - marginX, 100 ) / (dx * _PIXEL_PER_UNIT*2.0)
		zy = max( h - marginY, 100 ) / (dy * _PIXEL_PER_UNIT*2.0)
		cx = ( x0 + x1 ) / 2.0
		cy = ( y0 + y1 ) / 2.0
		scrX = self.scrollX
		scrY = self.scrollY

		self.updating = True
		if fitX:
			self.setZoomX( zx )
			scrX = cx - self.xToValue( w/2.0 )
		if fitY:
			self.setZoomY( zy )
			scrY = - cy - self.yToValue( h/2.0 )
		self.setScroll( scrX, scrY )
		self.updating = False
		self.updateTransfrom()

	def fitAllCurves( self, fitX = True, fitY = True ):
		return self.fitCurves( self.getCurveNodes(), fitX, fitY )

	def fitCurves( self, curves, fitX = True, fitY = True ):
		x0, y0 = 100000000, 100000000
		x1, y1 = -100000000, -100000000
		for curve in curves:
			cx0, cy0, cx1, cy1 = self.calcCurveAABB( curve )
			x0 = min( cx0, x0 )
			y0 = min( cy0, y0 )
			x1 = max( cx1, x1 )
			y1 = max( cy1, y1 )
		dx = x1 - x0
		dy = y1 - y0
		if dx <=0 or dy <= 0: return
		self.fitRect( x0, y0, x1, y1, fitX, fitY )

	def calcCurveAABB( self, curve ):
		x0, y0 = 100000000, 100000000
		x1, y1 = -100000000, -100000000
		for vert in self.getVertNodes( curve ):
			x, y, tweenMode, preBPX, preBPY, postBPX, postBPY = self.getVertParam( vert )
			x0 = min( x, x0 )
			y0 = min( y, y0 )
			x1 = max( x, x1 )
			y1 = max( y, y1 )
		return x0,y0,x1,y1

	def clear( self ):
		scn = self.scene()
		for curve in self.curveItems:
			curve.clear()
			scn.removeItem( curve )
		self.curveItems = []

	def removeCurve( self, curveNode ):
		curve = self.getCurveByNode( curveNode )
		if curve:
			del self.nodeToCurve[ curveNode ]
			curve.clear()
			curve.node = None
			self.scene().removeItem( curve )
			self.curveItems.remove( curve )

	def addCurve( self, curveNode, **option ):
		curve = CurveItem( curveNode )
		curve.view = self
		self.scene().addItem( curve )
		self.curveItems.append( curve )
		self.nodeToCurve[ curveNode ] = curve

		vertNodes = self.getSortedVertNodes( curveNode )
		if vertNodes:
			for vertNode in vertNodes:
				self.addVert( vertNode )

		curve.setZoom( self.zoomX, self.zoomY )
		self.refreshCurve( curveNode, **option )
		return curve

	def addVert( self, vertNode, **option ):
		curve = self.affirmParentCurve( vertNode )
		if not curve: return None
		vert = curve.addVert( vertNode )
		if vert:
			self.refreshVert( vertNode, **option )			
		return vert

	def removeVert( self, vertNode ):
		curve = self.getParentCurve( vertNode )
		if not curve: return
		curve.removeVert( vertNode )
		if vertNode in self.selection:
			self.selection.remove( vertNode )
		self.refreshCurve( curve )

	def setVertTweenMode( self, vertNode, mode ):
		vertItem = self.getVertByNode( vertNode )
		if not vertItem: return
		vertItem.setTweenMode( mode )
		self.refreshVert( vertNode )

	def refreshVert( self, vertNode, **option ):
		vert = self.getVertByNode( vertNode )
		if vert:
			x, y, tweenMode, preBPX, preBPY, postBPX, postBPY = self.getVertParam( vertNode )
			vert.setParam( x,y, tweenMode, preBPX, preBPY, postBPX, postBPY )
			self.updateVertContent( vert, vertNode, **option )
			if option.get( 'refresh_neighbors', True ):
				pre = vert.getPrevVert()
				if pre:
					self.refreshVert( pre.node, refresh_neighbors = False )
				next = vert.getNextVert()
				if next:
					self.refreshVert( next.node, refresh_neighbors = False )

	def refreshCurve( self, curveNode, **option ):
		curve = self.getCurveByNode( curveNode )
		#TODO: rebuild verts
		if curve:
			self.updateCurveContent( curve, curveNode, **option )

	def getParentCurve( self, vertNode ):
		curveNode = self.getParentCurveNode( vertNode )
		if not curveNode: return None
		return self.getCurveByNode( curveNode )

	def getCurveByNode( self, curveNode ):
		return self.nodeToCurve.get( curveNode, None )

	def getVertByNode( self, vertNode ):
		curve = self.getParentCurve( vertNode )
		if not curve: return None
		return curve.getVertByNode( vertNode )

	def affirmParentCurve( self, vertNode ):
		curveNode = self.getParentCurveNode( vertNode )
		if not curveNode: return None
		curveItem = self.getCurveByNode( curveNode )
		if not curveItem:
			return self.addCurve( curveNode )
		else:
			return curveItem

	#====notify====
	def notifyVertChanged( self, vert, posChanged = True, bezierPointChanged = True ):
		if self.rebuilding: return
		if posChanged:
			self.vertChanged.emit( vert.node, vert.x()/_PIXEL_PER_UNIT, -vert.y()/_PIXEL_PER_UNIT )
			
		if bezierPointChanged:
			( preBPX,  preBPY  ) = vert.preBezierPoint
			( postBPX, postBPY ) = vert.postBezierPoint
			self.vertBezierPointChanged.emit( vert.node, preBPX, preBPY/_PIXEL_PER_UNIT,	postBPX, postBPY/_PIXEL_PER_UNIT )

	def notifyVertTweenModeChanged( self, vert, newMode ):
		if self.rebuilding: return
		self.vertTweenModeChanged.emit( vert.node, newMode )

	# #====Selection====
	def getSelection( self ):
		selection = []
		for item in self.scene().selectedItems():
			if isinstance( item, CurveVertPointItem ):
				selection.append( item.parentVert.node )
		return selection

	def setSelection( self, selection, notify = True ):
		self.updatingSelection = True
		for node in selection:
			vertItem = self.getVertByNode( node )
			if vertItem:
				vertItem.setSelected( True )
		self.update()
		self.updatingSelection = False
		if notify:
			self.notifySceneItemSelectionChanged()

	def notifySceneItemSelectionChanged( self ):
		if self.updatingSelection: return
		self.selectionChanged.emit()

	def getSortedVertNodes( self, curveNode ):
		def _sortVertEntry( m1, m2 ):
			v1, x1 = m1
			v2, x2 = m2
			diff = x1 - x2
			if diff > 0: return 1
			if diff < 0: return -1
			return 0

		verts = self.getVertNodes( curveNode )
		tosort = []
		for vert in verts:
			( x, y, mode, bpx0, bpy0, bpx1, bpy1 ) = self.getVertParam( vert )
			tosort.append( (vert,x) )
		result = []
		for entry in sorted( tosort, key = cmp_to_key(_sortVertEntry) ):
			( vert, x ) = entry
			result.append( vert )
		return result

	#====VIRTUAL FUNCTIONS ========
	def getParentCurveNode( self, vertNode ):
		return None

	def getCurveNodes( self ):
		return []

	def getVertNodes( self, curveNode ):
		return []

	def getVertPara_sort( self, curveNode ):
		#x, y, tweenMode, pre-tangent, post-tangeng
		return ( 0, 0, TWEEN_MODE_BEZIER, 0, 0, 0, 0 )

	def updateCurveContent( self, curve, node, **option ):
		pass

	def updateVertContent( self, vert, vertNode, **option ):
		pass

if __name__ == '__main__':
	from random import random


	# import testView
	##----------------------------------------------------------------##
	class TestCurve(object):
		def __init__( self ):
			self.verts = []

		def getVerts( self ):
			return self.verts

		def randomFill( self, off ):
			for i in range( 0, 4 ):
				vert = TestCurveVert( self )
				vert.x = i+ random()*0.1
				vert.y = (random()-0.5)*100 + off
				self.verts.append( vert )

	class TestCurveVert(object):
		def __init__( self, parent ):
			self.parentCurve = parent
			self.x = 0
			self.y = 1
			self.tweenMode = TWEEN_MODE_BEZIER
			self.preBezierPoint = ( 0.5, -25.0 )
			self.postBezierPoint = ( 0.5, 55.0 )

		def getParam( self ):
			( bpx0, bpy0 ) = self.preBezierPoint
			( bpx1, bpy1 ) = self.postBezierPoint
			return ( self.x, self.y, self.tweenMode, bpx0, bpy0, bpx1, bpy1 )
	
	class TestCurveView( CurveView ):
		"""docstring for TestCurveView"""
		def __init__(self, *args):
			super(TestCurveView, self).__init__( *args )
			self.testCurves = []
			for i in range( 0, 1 ):
				curve = TestCurve()
				curve.randomFill( i * 100 )
				self.testCurves.append( curve )
			self.vertChanged.connect( self.onVertChanged )
			self.selectionChanged.connect( self.noSelectionChanged )

		def getParentCurveNode( self, vertNode ):
			return vertNode.parentCurve

		def getCurveNodes( self ):
			return self.testCurves

		def getVertNodes( self, curveNode ):
			return curveNode.getVerts()

		def getVertParam( self, vertNode ):
			return vertNode.getParam()

		def onVertChanged( self, vert, x, y ):
			print(('vert changed', vert, x, y))

		def noSelectionChanged( self ):
			print((self.getSelection()))


	class CurveWidget( QtWidgets.QWidget ):
		def __init__( self, *args, **kwargs ):
			super( CurveWidget, self ).__init__( *args, **kwargs )		
			layout = QtWidgets.QVBoxLayout( self )
			self.view = TestCurveView()
			self.view.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding )
			layout.addWidget( self.view )
			layout.setSpacing( 0 )
			layout.setContentsMargins( 0 , 0 , 0 , 0 )
			self.view.rebuild()
			self.view.setSelection( [self.view.testCurves[0].verts[0]] )
			self.view.setRangeX( 0, 5 )

		def closeEvent( self, event ):
			self.view.deleteLater()
	
	app = QtWidgets.QApplication( sys.argv )
	styleSheetName = 'gii.qss'
	app.setStyleSheet(
			open( '/Users/tommo/prj/gii/data/theme/' + styleSheetName ).read() 
		)
	frame = CurveWidget()
	frame.resize( 600, 300 )
	print((frame.view.width(), frame.view.height()))
	frame.show()
	frame.raise_()
	
	app.exec_()
