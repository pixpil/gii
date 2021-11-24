from functools import cmp_to_key

from qtpy import QtWidgets, QtGui, QtCore, QtOpenGL, uic
from qtpy.QtCore import Qt, QObject, QEvent, Signal
from qtpy.QtCore import QPoint, QRect, QSize
from qtpy.QtCore import QPointF, QRectF, QSizeF
from qtpy.QtGui import QColor, QTransform
from qtpy.QtWidgets import QStyle

import time

from .GraphicsViewHelper import *
from .TimelineViewCommon import *
from .CurveView import CurveView
from .CurveView import \
	TWEEN_MODE_CONSTANT,\
	TWEEN_MODE_LINEAR,\
	TWEEN_MODE_BEZIER,\
	TANGENT_MODE_AUTO,\
	TANGENT_MODE_SPLIT,\
	TANGENT_MODE_SMOOTH

import sys
import math

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

TimelineForm,BaseClass = uic.loadUiType( _getModulePath('timeline2.ui') )

##----------------------------------------------------------------##

_MARKER_SIZE = 20
_RULER_SIZE = 25
_TRACK_SIZE = 17
_TRACK_MARGIN = 2
_PIXEL_PER_SECOND = 100.0 #basic scale
_HEAD_OFFSET = 30

##----------------------------------------------------------------##
_DEFAULT_BG = makeBrush( color = '#222' )

##----------------------------------------------------------------##
##styles:  ID                     Pen           Brush          Text
makeStyle( 'black',              '#000000',    '#000000'              )
makeStyle( 'default',            '#000000',    '#ff0ecf'              )
makeStyle( 'key',                '#000000',    ('#a0a0a0',0.8)        )
makeStyle( 'key:hover',          '#c2c2c2',    '#a0a0a0'              )
makeStyle( 'key:selected',       '#000000',    ('#5c83ff',0.8)        )

makeStyle( 'eventkey',                '#737373',    ('#5b5c63',0.8), '#c2c2c2' )
makeStyle( 'eventkey:hover',          '#737373',    '#75777f', '#dddddd' )
makeStyle( 'eventkey:selected',       '#5c7340',    ('#5c83ff',0.8), '#ffffff' )

makeStyle( 'key-span',           '#000',       '#303459'    ,'#c2c2c2' )
makeStyle( 'key-span:selected',  '#ffffff',    '#303459'               )
makeStyle( 'track',                None,       dict( color = '#444', alpha = 0.2 ) )
makeStyle( 'track:selected',       None,       dict( color = '#4e536e', alpha = 0.4 ) )
makeStyle( 'selection',          dict( color = '#ffa000', alpha = 0.5 ), dict( color = '#ffa000', alpha = 0.2 ) )


##----------------------------------------------------------------##
class TimelineSubView( GLGraphicsView ):
	zoomChanged       = Signal( float )
	scrollPosChanged  = Signal( float )
	cursorPosChanged  = Signal( float )
	def __init__( self, *args, **kwargs ):
		super(TimelineSubView, self).__init__( *args, **kwargs )
		self.zoom = 1.0
		self.scrollPos = 0.0
		self.cursorPos = 0.0
		self.updating = False
		self.maxRange = 1000000
		self.minRange = 0.0

	def setRange( self, t0, t1 ):
		self.minRange = t0
		self.maxRange = t1

	def getRange( self ):
		return self.minRange, self.maxRange

	def timeToPos( self, t ):
		return t * self.zoom * _PIXEL_PER_SECOND + _HEAD_OFFSET

	def posToTime( self, p ):
		return ( p - _HEAD_OFFSET ) / ( self.zoom * _PIXEL_PER_SECOND )

	def timeLengthToWidth( self, l ):
		return l * self.zoom * _PIXEL_PER_SECOND

	def widthToTimeLength( self, w ):
		return w / ( self.zoom * _PIXEL_PER_SECOND )

	def setZoom( self, zoom, update = True ):
		self.zoom = zoom
		if self.updating: return
		self.updating = True
		self.onZoomChanged( zoom )
		self.zoomChanged.emit( zoom )
		self.updating = False

	def onZoomChanged( self, zoom ):
		pass

	def setScrollPos( self, scrollPos, update = True ):
		self.scrollPos = max( scrollPos, 0.0 )
		if self.updating: return
		self.updating = True
		self.onScrollPosChanged( scrollPos )
		self.scrollPosChanged.emit( scrollPos )
		self.updating = False

	def onScrollPosChanged( self, scrollPos ):
		pass

	def setCursorPos( self, cursorPos, update = True ):
		cursorPos0 = self.cursorPos
		cursorPos = min( max( cursorPos, self.minRange ), self.maxRange )
		if cursorPos0 == cursorPos: return
		self.cursorPos = cursorPos
		if self.updating: return
		self.updating = True
		self.onCursorPosChanged( cursorPos )
		self.cursorPosChanged.emit( cursorPos )
		self.updating = False

	def getCursorPos( self ):
		return self.cursorPos

	def getScrollPos( self ):
		return self.scrollPos

	def onCursorPosChanged( self, cursorPos ):
		pass

	def setCursorVisible( self, visible ):
		pass



##----------------------------------------------------------------##
class TimelineMarkerItem( QtWidgets.QGraphicsRectItem ):
	_polyMarker2 = QtGui.QPolygonF([
		QPointF(   0, 0  ),
		QPointF(   8, 0  ),
		QPointF(   0, 8 ),
	])
	_polyMarker = QtGui.QPolygonF([
			QPointF( -0, 0 ),
			QPointF( 5, 5 ),
			QPointF( 0, 10 ),
			QPointF( -5, 5 ),
		])
	_pen_head = makePen( color = '#7569d0' )
	_pen_head_selected = makePen( color = '#4cb3ff', width = 2 )
	_pen_head_hover = makePen( color = '#ff95f5' )
	
	_pen_text = makePen( color = '#595d95' )
	_pen_text_hover = makePen( color = '#d9e2f4' )
	
	def __init__( self ):
		super(TimelineMarkerItem, self).__init__()
		self.setCursor( Qt.PointingHandCursor)

		self.setFlag( self.ItemSendsGeometryChanges, True )
		# self.setFlag( self.ItemIsMovable, True )
		self.setFlag( self.ItemIsSelectable, True )

		self.setAcceptHoverEvents( True )
		self.setRect( -5, 0, 15, 10 )
		self.penHead = TimelineMarkerItem._pen_head
		self.penLine = makePen( color = '#7569d0' )
		self.penText = makePen( color = '#676baa' )
		self.timePos = 0
		self.timeLength = 0
		self.text = 'marker'
		self.lineItems = []
		self.dragging = False
		self.selected = False
		self.node     = None

	def getText( self ):
		return self.text

	def setText( self, text ):
		self.text = text

	def getTimelineView( self ):
		return self.parentItem().view.getTimelineView()

	def setTimePos( self, timePos, notify = True ):
		view = self.getTimelineView()
		t0, t1 = view.getRange()
		timePos = max( min( timePos, t1 ), t0 )
		self.timePos = timePos
		self.updateShape()
		if notify:
			self.getTimelineView().notifyMarkerChanged( self.node, self.timePos )
	
	def updateShape( self ):
		self.parentItem().updateMarkerPos( self )
		for lineItem in self.lineItems:
			lineItem.updateShape()

	def hoverEnterEvent( self, event ):
		if self.selected: return
		self.penHead = TimelineMarkerItem._pen_head_hover
		self.penText = TimelineMarkerItem._pen_text_hover
		self.update()

	def hoverLeaveEvent( self, event ):
		if self.selected: return
		self.penHead = TimelineMarkerItem._pen_head
		self.penText = TimelineMarkerItem._pen_text
		self.update()

	def paint( self, painter, option, widget ):
		rect = self.rect()
		painter.setPen( self.penHead )
		painter.setBrush( self.brush() )
		painter.drawPolygon( TimelineMarkerItem._polyMarker )
		painter.setPen( self.penLine )
		painter.drawLine( 0,10, 0, 200 )
		painter.setPen( self.penText )
		painter.drawText( 10, 10 , self.getText() )

	def setSelected( self, selected, notifyParent = True ):
		super( TimelineMarkerItem, self ).setSelected( selected )
		self.selected = selected
		if selected:
			self.penHead= TimelineMarkerItem._pen_head_selected
		else:
			self.penHead= TimelineMarkerItem._pen_head
		self.update()

	# def itemChange( self, change, value ):
	# 	if change == self.ItemPositionChange:
	# 		pass
	# 	elif change == self.ItemPositionHasChanged:
	# 		self.setFlag( self.ItemSendsGeometryChanges, False )
	# 		self.setX( max( self.x(), 0 ) )
	# 		self.setFlag( self.ItemSendsGeometryChanges, True )
	# 	return super( TimelineMarkerItem, self ).itemChange( change, value )

	def mousePressEvent( self, event ):
		if event.button() == Qt.LeftButton:
			self.getTimelineView().onMarkerClicked( self )
			self.dragging = ( event.scenePos().x(), self.timePos )

	def mouseReleaseEvent( self, event ):
		if event.button() == Qt.LeftButton:
			self.dragging = False

	def mouseMoveEvent( self, event ):
		if not self.dragging: return
		x0, t0 = self.dragging
		x1 = event.scenePos().x()
		delta = x1 - x0
		t1 = max( self.parentItem().widthToTimeLength( delta ) + t0, 0.0 )
		self.setTimePos( t1 )

	def delete( self ):
		self.node = None
		scn = self.scene()
		scn.removeItem( self )
		self.setParentItem( None )
		for line in self.lineItems:
			line.delete()
		self.lineItems = []

##----------------------------------------------------------------##
class TimelineMarkerSlotItem( QtWidgets.QGraphicsRectItem ):
	def __init__( self ):
		super(TimelineMarkerSlotItem, self).__init__()
		self.setRect( 0,0,10000, _MARKER_SIZE )
		self.brushPlain = makeBrush( color = '#252525' )
		self.brushSlot = makeBrush( color = '#111' )
		self.markers = []
		self.view = None

	def timeToPos( self, t ):
		return self.view.timeToPos( t )

	def posToTime( self, t ):
		return self.view.posToTime( t )

	def timeLengthToWidth( self, l ):
		return self.view.timeLengthToWidth( l )

	def widthToTimeLength( self, w ):
		return self.view.widthToTimeLength( w )

	def findMarker( self, id ):
		for m in self.markers:
			if m.getId() == id: return m
		return None

	def addMarker( self ):
		marker = TimelineMarkerItem()
		marker.setParentItem( self )
		self.markers.append( marker )
		self.updateMarkerPos( marker )
		return marker

	def removeMarker( self, markerItem ):
		self.markers.remove( markerItem )
		markerItem.delete()

	def clearMarkers( self ):
		for marker in self.markers:
			marker.delete()
		self.markers = []

	def updateMarkerPos( self, marker ):
		scroll = self.view.scrollPos
		mp = marker.timePos - scroll
		x = self.timeToPos( mp )
		marker.prepareGeometryChange()
		marker.setPos( x, 5 )

	def updateAllMarkerPos( self ):
		for marker in self.markers:
			self.updateMarkerPos( marker )

	def paint( self, painter, option, widget ):
		rect = self.rect()
		painter.setPen( Qt.NoPen )
		painter.setBrush( self.brushPlain )
		painter.drawRect( rect )
		painter.setBrush( self.brushSlot )
		painter.drawRect( rect.adjusted( 0,4,0,-3 ) )

##----------------------------------------------------------------##
class TimelineRulerItem( QtWidgets.QGraphicsRectItem ):
	_pen_top  = makePen( color = '#4a4a4a', width = 1 )
	_gridPenV  = makePen( color = '#777', width = 1 )
	_gridPenV2 = makePen( color = '#444', width = 1 )
	_gridPenH  = makePen( color = '#555', width = 1 )
	_cursorPen = makePen( color = '#a3ff00', width = 1 )
	_cursorTextPen = makePen( color = '#89ae3f', width = 1 )
	_cursorBrush = makeBrush( color = '#a3ff00' )
	_bgBrush   = makeBrush( color = '#222' )
	_bgActiveBrush  = makeBrush( color = '#c8ff00', alpha = 0.1 )
	_bgEditingBrush = makeBrush( color = '#232e35' )
	_bgRangeBrush   = makeBrush( color = '#353535', alpha = 1 )
	
	_polyCursor = QtGui.QPolygonF([
		QPointF(   0, 0  ),
		QPointF(   -5, -10  ),
		QPointF(   5, -10 ),
	])

	def __init__( self ):
		super( TimelineRulerItem, self ).__init__()
		self.setCursor( Qt.PointingHandCursor)
		self.step = 1
		self.view = None		
		self.setRect( 0,_MARKER_SIZE,10000,_RULER_SIZE )
		self.cursorVisible = True
		self.dragging = False
		self.range = ( 0, 10000 )

	def setRange( self, t0, t1 ):
		self.range = ( t0, t1 )
		self.update()

	def mousePressEvent( self, event ):
		if event.button() == Qt.LeftButton:
			if not self.view.draggable: return
			self.dragging = True
			x = event.scenePos().x()
			self.view.setCursorPos( self.view.posToTime( x ) + self.view.scrollPos )

	def mouseReleaseEvent( self, event ):
		if event.button() == Qt.LeftButton:
			self.dragging = False

	def mouseMoveEvent( self, event ):
		if not self.dragging: return
		x = event.scenePos().x()
		self.view.setCursorPos( self.view.posToTime( x ) + self.view.scrollPos )

	def formatter( self, pos ):
		return '%.1f' % pos

	def paint( self, painter, option, widget ):
		formatter = self.formatter
		# painter.setRenderHint( QtGui.QPainter.Antialiasing, False )
		rect      = painter.viewport()
		transform = painter.transform()
		x = -transform.dx()
		y = -transform.dy()
		w = rect.width()
		h = rect.height()

		painter.setPen( Qt.NoPen )
		painter.setBrush( TimelineRulerItem._bgBrush )
		painter.drawRect( rect )

		#units
		u = self.view.zoom * _PIXEL_PER_SECOND
		t0 = self.view.scrollPos
		dt = w / u
		t1 = t0 + dt

		step = self.step * max( 1, math.floor( 100/u ) )

		start = math.floor( t0/step ) * step
		end   = math.ceil( t1/step + 1 ) * step
		count = int( ( end - start ) / step )
		sw = step * u
		ox = t0 * u
		r0, r1 =  self.range

		#range
		t = 0
		xx  = (t-t0) * u + _HEAD_OFFSET

		painter.setPen( Qt.NoPen )
		painter.setBrush( TimelineRulerItem._bgRangeBrush )
		painter.drawRect( xx, 0, r1 * u, h )

		#baselines
		painter.setPen( TimelineRulerItem._gridPenH )
		painter.drawLine( 0,h-1,w,h-1 ) #topline
		painter.setPen( TimelineRulerItem._gridPenV )
		
		subStep = 5
		subPitchT = float(step)/float(subStep)
		subPitch = sw/subStep
		for i in range( count ): #V lines
			t = start + i * step
			if t > r1:
				painter.setPen( TimelineRulerItem._gridPenV2 )
			xx = (t-t0) * u + _HEAD_OFFSET
			painter.drawLine( xx, h-_RULER_SIZE, xx, h - 2 )
			markText = '%.1f'%( t )
			painter.drawText( QRectF( xx + 4, h-_RULER_SIZE+4, 100, 100 ), Qt.AlignTop|Qt.AlignLeft, markText )
			for j in range( 1, subStep ):
				subt = t + j * subPitchT
				if subt > r1:
					painter.setPen( TimelineRulerItem._gridPenV2 )
				sxx = xx + j * subPitch
				painter.drawLine( sxx, h-5, sxx, h - 2 )
			
		
		painter.setPen( TimelineRulerItem._pen_top )
		painter.drawLine( 0, h-_RULER_SIZE, w, h-_RULER_SIZE ) #topline

		#draw cursor
		if self.cursorVisible:
			painter.setPen( TimelineRulerItem._cursorPen )
			painter.setBrush( TimelineRulerItem._cursorBrush )
			cx = float( self.view.cursorPos - t0 ) * u + _HEAD_OFFSET
			painter.translate( cx - .5, h )
			painter.drawPolygon( TimelineRulerItem._polyCursor )
			painter.setPen( TimelineRulerItem._cursorTextPen )
			cursorText = '%.2f' % ( self.view.cursorPos )
			painter.drawText( 10, -4 , cursorText )


##-------------------------------------- --------------------------##
class TimelineRulerView( TimelineSubView ):
	_BG = makeBrush( color = '#222' )
	def __init__( self, *args, **kwargs ):
		super( TimelineRulerView, self ).__init__( *args, **kwargs )
		self.setScene( GLGraphicsScene( self ) )
		self.scene().setBackgroundBrush( TimelineRulerView._BG );
		self.scene().setSceneRect( QRectF( 0,0, 10000, 10000 ) )
		self.markerSlot = TimelineMarkerSlotItem()
		self.markerSlot.view = self

		self.ruler = TimelineRulerItem()
		self.ruler.view = self

		self.scene().addItem( self.ruler )
		self.scene().addItem( self.markerSlot )
		self.dragging = False
		self.draggable = True
		self.timelineView = None
		self.setRange( 0, 10000 )

		self.nodeToMarker = {}

	def getTimelineView( self ):
		return self.timelineView

	def getVisibleRange( self ):
		#TODO
		return 0, 10

	def setRange( self, t0, t1 ):
		super( TimelineRulerView, self ).setRange( t0, t1 )
		self.ruler.setRange( t0, t1 )

	def clear( self ):
		self.markerSlot.clearMarkers()

	def setCursorDraggable( self, draggable ):
		self.draggable = draggable

	def setCursorVisible( self, visible ):
		self.ruler.cursorVisible = visible
		self.update()

	def wheelEvent(self, event):
		steps = event.pixelDelta().y() / 120.0;
		dx = 0
		dy = 0
		zoomRate = 1.1
		delta = event.angleDelta()
		dx = delta.x()
		dy = delta.y()
		if dy > 0:
			self.setZoom( self.zoom * zoomRate )
		elif dy < 0 :
			self.setZoom( self.zoom / zoomRate )

	def onZoomChanged( self, zoom ):
		self.markerSlot.updateAllMarkerPos()
		self.update()

	def onScrollPosChanged( self, p ):
		self.markerSlot.updateAllMarkerPos()
		self.update()

	def onCursorPosChanged( self, pos ):
		self.update()

	def setDraggable( self, draggable ):
		self.draggable = draggable

	def addMarker( self, node ):
		markerItem = self.markerSlot.addMarker()
		self.nodeToMarker[ node ] = markerItem
		markerItem.node = node
		return markerItem

	def removeMarker( self, node ):
		item = self.nodeToMarker.get( node, None )
		if not item: return False
		if self.getTimelineView().onMarkerRemoving( node ) == False: return False
		self.markerSlot.removeMarker( item )
		del self.nodeToMarker[ node ]
		return True

	def keyPressEvent( self, event ):
		pass

##----------------------------------------------------------------##
class TimelineKeyItem( StyledItemMixin, QtWidgets.QGraphicsRectItem ):
	_polyMark = QtGui.QPolygonF([
			QPointF( -0, 0 ),
			QPointF( 5, 5 ),
			QPointF( 0, 10 ),
			QPointF( -5, 5 ),
		]).translated( -0.5, (_TRACK_SIZE - 10 )/2 + 1 )

	def __init__( self, *args, **kwargs ):
		super( TimelineKeyItem, self ).__init__( *args, **kwargs )
		#
		self.setRect( -10, 0, 20, _TRACK_SIZE)
		self.setZValue( 10 )
		self.setCursor( Qt.PointingHandCursor )
		
		self.setFlag( self.ItemSendsGeometryChanges, True )
		# self.setFlag( self.ItemIsMovable, True )
		self.setFlag( self.ItemIsSelectable, True )
		self.setAcceptHoverEvents( True )

		self.node = None

		self.dragging = False
		self.draggingSpan = None
		self.setItemType( 'key' )
		self.setItemState( 'normal' )
		self.timePos    = 0
		self.timeLength = 0
		self.updatingPos = False

		self.resizable = False
		self.selected = False
		self.text = None

	def setText( self, text ):
		self.text = text

	def getText( self ):
		return self.text

	def setResizable( self, resizable = True ):
		self.resizable = resizable

	def isResizable( self ):
		return self.resizable

	def onPaint( self, painter, option, widget ):
		painter.setRenderHint( QtGui.QPainter.Antialiasing, True )
		rect = self.rect()
		painter.drawPolygon( TimelineKeyItem._polyMark )

	def itemChange( self, change, value ):
		if change == self.ItemPositionChange:
			self.updateKey()
			if not self.updatingPos:
				self.updatingPos = True
				self.setTimePos( self.posToTime( value.x() ) )
				value.setX( self.timeToPos( self.timePos ) )
				self.updatingPos = False
		return QtWidgets.QGraphicsRectItem.itemChange( self, change, value )

	def delete( self ):
		scn = self.scene()
		scn.removeItem( self )

	def updateKey( self ):
		pass

	def hoverEnterEvent( self, event ):
		if self.selected: return
		self.setItemState( 'hover' )
		self.update()

	def hoverLeaveEvent( self, event ):
		if self.selected: return
		self.setItemState( 'normal' )
		self.update()

	def hoverMoveEvent( self, event ):
		if self.resizable:
			x = event.pos().x()
			width = self.rect().width()
			left = self.rect().left()
			right = self.rect().right()
			sizeHandle = max( 2, min( 12, width/5 ) )
			if x < (left+sizeHandle):
				self.mouseOp = 'left-size'
				self.setCursor( Qt.SizeHorCursor )
				return
			elif x > (right-sizeHandle):
				self.mouseOp = 'right-size'
				self.setCursor( Qt.SizeHorCursor )
				return
		self.mouseOp = 'move'
		self.setCursor( Qt.PointingHandCursor )

	def moveIntoNextEmptySpan( self, pos = None ):
		if pos == None:
			pos = self.timePos
		span = self.track.findNextEmptySpan( pos, self.timeLength, self )
		if span:
			s0, s1 = span
			self.setTimePos( s0 )
			return True
		else:
			return False

	def fitIntoNextEmptySpan( self, pos = None ):
		if pos == None:
			pos = self.timePos
		spans = self.track.findEmptySpansAfter( pos )
		if spans:
			s0, s1 = spans[0]
			self.setTimePos( s0 )
			if self.isResizable():
				l = s1 - s0
				if self.timeLength > l:
					self.setTimeLength( s1-s0 )
			return s0, s1
		return None
	

	def setSelected( self, selected, notifyParent = False ):
		super( TimelineKeyItem, self ).setSelected( selected )
		self.selected = selected
		if selected:
			self.setItemState( 'selected' )
		else:
			self.setItemState( 'normal' )
		if notifyParent:
			self.getTimelineView().selectKey( self.node, True )

	def mousePressEvent( self, event ):
		if event.button() == Qt.LeftButton:
			x0 = self.pos().x()
			mx0 = event.scenePos().x()
			t0 = self.getTimePos()
			l0 = self.getTimeLength()
			self.dragging = ( x0, mx0, t0, l0 )
			self.draggingSpan = None
			self.track.sortKeys() #prepare for drag
			if event.modifiers() == Qt.ShiftModifier:
				if self.selected:
					self.getTimelineView().deselectKey( self.node )
				else:
					self.getTimelineView().selectKey( self.node, True )
			else:
				self.getTimelineView().selectKey( self.node, False )

	def mouseMoveEvent( self, event ):
		if self.dragging:
			x0, mx0, t0, l0 = self.dragging
			mx1 = max( event.scenePos().x(), _HEAD_OFFSET )
			delta = mx1 - mx0
			self.prepareGeometryChange()
			op = self.mouseOp

			if op == 'move':
				t1 = self.posToTime( x0 + delta )
				if self.resizable:
					span = self.track.findEmptySpan( t1, self.timeLength, self ) or self.draggingSpan
					if span:
						self.draggingSpan = span
						s0, s1 = span
						t1 = max(t1,s0)
						if s1 != None: t1 = min( t1, s1 - self.timeLength )
						self.setTimePos( t1 )
				else:
					self.setTimePos( t1 )

			elif op == 'left-size':
				t2 = self.getEndTimePos()
				t1 = min( self.posToTime( x0 + delta ), t2 )
				span = self.track.findEmptySpan( t1, self.timeLength, self ) or self.draggingSpan
				if span:
					self.draggingSpan = span
					s0, s1 = span
					t1 = max(t1,s0)
					if s1 != None: 
						t2 = min( t2, s1 )
					self.setTimePos( t1 )
					self.setTimeLength( t2 - t1 )

			elif op == 'right-size':
				span = self.track.findEmptySpan( t0, self.timeLength, self ) or self.draggingSpan
				if span:
					self.draggingSpan = span
					s0, s1 = span
					deltaTime = self.widthToTimeLength( delta )
					l1 = l0 + deltaTime
					t2 = t0 + l1
					if s1 != None: t2 = min( t2, s1 )
					self.setTimeLength( t2 - t0 )

	# def mouseReleaseEvent( self, event ):
	# 	if event.button() == Qt.LeftButton:
	# 		self.dragging = False

	def timeToPos( self, t ):
		return self.track.timeToPos( t )

	def posToTime( self, t ):
		return self.track.posToTime( t )

	def timeLengthToWidth( self, l ):
		return self.track.timeLengthToWidth( l )

	def widthToTimeLength( self, w ):
		return self.track.widthToTimeLength( w )

	def updateShape( self ):
		self.setTimePos( self.timePos, False )

	def setTimePos( self, tpos, notify = True ):
		tpos = max( 0, tpos )
		t0 ,t1 = self.getTimelineView().getRange()
		tpos = max( min( tpos, t1 ), t0 )
		self.timePos = tpos
		if notify:
			self.getTimelineView().notifyKeyChanged( self.node, self.timePos, self.timeLength )
		x = self.timeToPos( self.timePos )
		self.setZValue( tpos*0.0001 )
		if not self.updatingPos:
			self.updatingPos = True
			self.setX( x )
			self.updatingPos = False

	def getTimePos( self ):
		return self.timePos

	def getEndTimePos( self ):
		return self.timePos + self.timeLength

	def setTimeLength( self, l, notify = True ):
		self.timeLength = max( l, 0 )
		if notify:
			self.getTimelineView().notifyKeyChanged( self.node, self.timePos, self.timeLength )

	def getTimeLength( self ):
		return self.timeLength


	def getTimelineView( self ):
		return self.track.getTimelineView()


class TimelineAtomicKeyItem(TimelineKeyItem):
	def setResizable( self, resizable = True ):
		#do nothing
		return
		
class TimelineEventKeyItem( TimelineKeyItem ):
	"""docstring for TimelineEventKeyItem"""
	def __init__(self, *args, **kwargs ):
		super(TimelineEventKeyItem, self).__init__( *args, **kwargs )
		self.setItemType( 'eventkey' )
		self.resizable = True
	
	def updateShape( self ):
		self.setTimePos( self.timePos, False )
		self.updateWidth()

	def setTimeLength( self, l ):
		super( TimelineEventKeyItem, self ).setTimeLength( l )
		self.updateWidth()
	
	def updateWidth( self ):
		spanHeight = _TRACK_SIZE - 0
		width = max( self.timeLengthToWidth( self.timeLength ), 0 )
		self.setRect( -5, (_TRACK_SIZE - spanHeight)/2 + 1, width + 10, spanHeight )

	def onPaint( self, painter, option, widget ):
		painter.setRenderHint( QtGui.QPainter.Antialiasing, False )
		rect = self.rect().adjusted( 6, 0, -6, 0 )
		painter.drawRect( rect )
		x0 = rect.left()
		x1 = rect.right()
		y0 = rect.top()
		y1 = rect.bottom()
		w = x1 - x0
		painter.setPen( QColor( 0,0,0,50 ) )
		painter.drawLine( x0-1,y0,x0-1,y1 )
		painter.drawLine( x1+1,y0,x1+1,y1 )
		if w > 10:
			text = self.getText()
			if text:
				painter.drawStyledText( rect.adjusted( 4, 2, -4, 0 ), Qt.AlignVCenter | Qt.AlignLeft, self.getText() )



##----------------------------------------------------------------##
def _KeyCmp( k1, k2 ):
	t1 = k1.timePos
	t2 = k2.timePos
	if t1 < t2 : return -1
	if t1 > t2 : return 1
	return 0

##----------------------------------------------------------------##
class TimelineTrackItem( StyledItemMixin, QtWidgets.QGraphicsRectItem ):
	def __init__( self ):
		super(TimelineTrackItem, self).__init__()
		self.trackType  = 'normal' # group / object / property
		self.index = 0
		self.keys = []
		self.zoom = 1
		self.setItemType( 'track' )
		self.setItemState( 'normal' )
		self.node = None
		self.allowOverlap = False

	def addKey( self, keyNode, **options ):
		for key in self.keys:
			if key.node == keyNode:
				return key
		keyItem = self.createKey()
		keyItem.node  = keyNode
		keyItem.track = self
		self.keys.append( keyItem )
		keyItem.updateShape()
		return keyItem

	def createKey( self, **options ):
		return TimelineKeyItem( self )
		
	def removeKey( self, keyNode, notify = True ):
		key = self.getKeyByNode( keyNode )
		assert key, 'attempt to remove key not in this timeline'
		if notify:
			if self.getTimelineView().onKeyRemoving( keyNode ) == False: return
		key.setParentItem( None )
		self.keys.remove( key )
		key.delete()

	def sortKeys( self ):
		self.keys = sorted( self.keys, key = cmp_to_key( _KeyCmp ) )

	def getKeyByNode( self, keyNode ):
		for key in self.keys:
			if key.node == keyNode:
				return key
		return None

	def clear( self ):
		keys = self.keys[:]
		for keyItem in keys:
			keyItem.setParentItem( None )
			keyItem.delete()
		self.keys = ()

	def setZoom( self, zoom ):
		self.zoom = zoom
		for keyItem in self.keys:
			keyItem.updateShape()

	def timeToPos( self, t ):
		return self.view.timeToPos( t )

	def posToTime( self, p ):
		return self.view.posToTime( p )

	def timeLengthToWidth( self, l ):
		return self.view.timeLengthToWidth( l )

	def widthToTimeLength( self, w ):
		return self.view.widthToTimeLength( w )

	def onKeyUpdate( self, key ):
		self.view.onKeyUpdate( self, key )

	def setSelected( self, selected = True ):
		super( TimelineTrackItem, self ).setSelected( selected )
		self.selected = selected
		if selected:
			self.setItemState( 'selected' )
		else:
			self.setItemState( 'normal' )
		self.update()

	def onPaint( self, painter, option, widget ):
		rect = self.rect()
		painter.drawRect( rect )

	def getTimelineView( self ):
		return self.view.getTimelineView()

	def mousePressEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			self.getTimelineView().onTrackClicked( self, ev.pos() )

	def findEmptySpan( self, pos, length, ignoreKey = None ):
		#assume key is sorted
		#assume keys dont overlap
		x0 = 0
		x1 = None
		if not self.allowOverlap:
			for key in self.keys:
				if key is ignoreKey: continue
				l = key.getTimePos()
				r = key.getEndTimePos()
				if l > pos:
					x1 = l
					if x1 - x0 < length: return None
					break
				if r > pos: return None #inside span
				x0 = r
		view = self.getTimelineView()
		t0, t1 = view.getRange() 
		if not x1: x1 = t1
		return ( x0, x1 )

	def findNextEmptySpan( self, pos, length, ignoreKey = None ):
		for span in self.findEmptySpansAfter( pos ):
			s0, s1 = span
			l = s1 - s0
			if l >=length :
				return span
		return None

	def findPreviousEmptySpan( self, pos, length, ignoreKey = None ):
		for span in self.findEmptySpansBefore( pos ):
			s0, s1 = span
			l = s1 - s0
			if l >= length :
				return span
		return None

	def findEmptySpans( self, ignoreKey = None ):
		spans = []
		x0 = 0
		x1 = None
		for key in self.keys:
			if key == ignoreKey: continue
			x = key.getTimePos() 
			if x > x0:
				spans.append( (x0, x) )
			x0 = x + key.getTimeLength()
		return spans

	def findEmptySpansAfter( self, pos, ignoreKey = None ):
		spans = []
		x0 = pos
		for key in self.keys:
			if key == ignoreKey: continue
			x = key.getTimePos() 
			if x > x0:
				spans.append( (x0, x) )
			x0 = x + key.getTimeLength()

		view = self.getTimelineView()
		t0, t1 = view.getRange() 
		if t1 > x0:
			spans.append( (x0, t1) )

		return spans

	def findEmptySpansBefore( self, pos, ignoreKey = None ):
		spans = []
		x1 = pos
		for key in reversed( self.keys ):
			if key == ignoreKey: continue
			x = key.getTimePos() 
			l = key.getTimeLength()
			if ( x + l ) < x1:
				spans.append( ( x + l, x1 ) )
			x1 = x
		view = self.getTimelineView()
		t0, t1 = view.getRange() 
		if x1 > t0:
			spans.append( (t0, x1) )
		return spans


##----------------------------------------------------------------##
class TimelineEventTrackItem( TimelineTrackItem ):
	def createKey( self, **options ):
		return TimelineEventKeyItem( self )

##----------------------------------------------------------------##
class SelectionRegionItem( StyledItemMixin, QtWidgets.QGraphicsRectItem ):
	def __init__( self, *args, **kwargs ):
		super( SelectionRegionItem, self ).__init__( *args, **kwargs )
		self.setItemType( 'selection' )

	def onPaint( self, painter, option, widget ):
		rect = self.rect()
		painter.drawRect( rect )

##----------------------------------------------------------------##
class TimelineTrackView( TimelineSubView ):
	scrollYChanged   = Signal( float )
	def __init__( self, *args, **kwargs ):
		super( TimelineTrackView, self ).__init__( *args, **kwargs )
		self.gridSize  = 100
		self.scrollPos = 0.0
		self.cursorPos = 0.0
		self.scrollY   = 0.0
		self.scrollYRange = 200.0
		self.zoom      = 1
		self.panning   = False
		self.updating  = False
		
		self.selecting = False
		self.selectingItems = []

		scene = GLGraphicsScene( self )
		scene.setBackgroundBrush( _DEFAULT_BG );
		# scene.setItemIndexMethod( GLGraphicsScene.NoIndex )
		self.setScene( scene )
		scene.sceneRectChanged.connect( self.onRectChanged )

		self.trackItems = []
		
		#grid
		self.gridBackground = GridBackground()
		self.gridBackground.setGridSize( self.gridSize, _TRACK_SIZE + _TRACK_MARGIN )
		self.gridBackground.setAxisVisible( True, True )
		self.gridBackground.setCursorVisible( True )
		self.gridBackground.setOffset( _HEAD_OFFSET, -1 )
		scene.addItem( self.gridBackground )

		scene.setSceneRect( QRectF( 0,0, 10000, 10000 ) )

		self.selectionRegion = SelectionRegionItem()
		self.selectionRegion.setZValue( 9999 )
		self.selectionRegion.setVisible( False )
		scene.addItem( self.selectionRegion )

		#components
		self.cursorItem = TimelineCursorItem()
		self.cursorItem.setLine( 0,0, 0, 20000 )
		self.cursorItem.setZValue( 1000 )
		# scene.addItem( self.cursorItem )

		self.markerLines = []


	def clear( self ):
		scn = self.scene()
		for trackItem in self.trackItems:
			trackItem.clear()
			trackItem.setParentItem( None )
			scn.removeItem( trackItem )
		self.trackItems = []
		for markerLine in self.markerLines:
			scn.removeItem( markerLine )
			markerLine.setParentItem( None )
		self.markerLines = []

	def setCursorVisible( self, visible ):
		self.cursorItem.setVisible( visible )

	def addTrackItem( self, trackItem, **option ):
		trackItem.view = self
		trackItem.setRect( 0,-1, 100000, _TRACK_SIZE + 2 )
		self.scene().addItem( trackItem )
		self.trackItems.append( trackItem )
		trackItem.index = len( self.trackItems )
		trackItem.setPos( 0, ( trackItem.index - 1 ) * ( _TRACK_SIZE + _TRACK_MARGIN ) )
		return trackItem

	def removeTrackItem( self, track ):
		self.trackItems.remove( track )
		track.setParentItem( None )
		track.node = None
		track.scene().removeItem( track )

	def addMarkerLine( self, marker ):
		lineItem = TimelineMarkerLineItem()
		lineItem.setMarker( marker )
		lineItem.view = self
		self.markerLines.append( lineItem )
		self.scene().addItem( lineItem )
		self.updateMarkerPos( lineItem )
		return lineItem

	def removeMarkerLine( self, marker ):
		for line in self.markerLines:
			if line.parentMarker == marker:
				self.markerLines.remove( line )
				line.setParentItem( None )
				self.scene().removeItem( line )
				break

	def setScrollY( self, y, update = True ):
		self.scrollY = max( min( y, 0.0 ), -self.scrollYRange )
		if self.updating: return
		self.updating = True
		self.scrollYChanged.emit( self.scrollY )
		if update:
			self.updateTransfrom()
		self.updating = False

	def getScrollY( self ):
		return self.scrollY

	def setScrollYRange( self, maxRange ):
		self.scrollYRange = maxRange

	def onCursorPosChanged( self, pos ):
		x = self.timeToPos( self.cursorPos )
		# self.cursorItem.setX( x )
		self.gridBackground.setCursorPos( x )

	def onScrollPosChanged( self, p ):
		self.updateTransfrom()

	def updateMarkerPos( self, mline ):
		x = self.timeToPos( mline.getTimePos() )
		mline.setPos( x, 0 )

	def onZoomChanged( self, zoom ):
		self.updateTransfrom()
		for track in self.trackItems:
			track.setZoom( self.zoom )
		self.gridBackground.setGridWidth( self.gridSize * zoom )
		x = self.timeToPos( self.cursorPos )
		# self.cursorItem.setX( self.timeToPos( self.cursorPos ) )
		self.gridBackground.setCursorPos( x )
		for mline in self.markerLines:
			self.updateMarkerPos( mline )

	def updateTransfrom( self ):
		trans = QTransform()
		sx = - self.timeToPos( self.scrollPos ) + _HEAD_OFFSET
		trans.translate( sx, self.scrollY )
		self.setTransform( trans )
		# self.update()

	def startSelectionRegion( self, pos ):
		self.selecting = True
		self.selectionRegion.setPos( pos )
		self.selectionRegion.setRect( 0,0,0,0 )
		self.selectionRegion.setVisible( True )
		self.resizeSelectionRegion( pos )
		# for keyNode in self.selection:
		# 	key = self.getKeyByNode( keyNode )
		# 	key.setSelected( False, False )

	def resizeSelectionRegion( self, pos1 ):
		pos = self.selectionRegion.pos()
		w, h = pos1.x()-pos.x(), pos1.y()-pos.y()
		self.selectionRegion.setRect( 0,0, w, h )
		itemsInRegion = self.scene().items( pos.x(), pos.y(), w, h )
		for item in self.selectingItems:
			item.setSelected( False, False )

		self.selectingItems = []
		for item in itemsInRegion:
			if isinstance( item, TimelineKeyItem ):
				self.selectingItems.append( item )
				item.setSelected( True, False )

	def stopSelectionRegion( self ):
		self.selectionRegion.setRect( 0,0,0,0 )
		self.selectionRegion.setVisible( False )
		selection = []
		for key in self.selectingItems:
			selection.append( key.node )
		self.timelineView.updateSelection( selection )

	def mouseMoveEvent( self, event ):
		super( TimelineTrackView, self ).mouseMoveEvent( event )
		if self.panning:
			p1 = event.pos()
			p0, sp0, sy0 = self.panning
			dx = p1.x() - p0.x()
			dy = p1.y() - p0.y()
			sp1 = sp0 - dx
			sy1 = sy0 + dy
			self.setScrollPos( self.posToTime( sp1 ), True )
			self.setScrollY( sy1, False )
			self.updateTransfrom()
		elif self.selecting:
			self.resizeSelectionRegion( self.mapToScene( event.pos() ) )

	def mousePressEvent( self, event ):
		super( TimelineTrackView, self ).mousePressEvent( event )
		if event.button() == Qt.MidButton:
			self.panning = ( event.pos(), self.timeToPos( self.scrollPos ), self.scrollY )
		elif event.button() == Qt.LeftButton and event.modifiers() == Qt.ShiftModifier:
			self.startSelectionRegion( self.mapToScene( event.pos() ) )
			self.selecting = True

	def mouseReleaseEvent( self, event ):
		super( TimelineTrackView, self ).mouseReleaseEvent( event )
		if event.button() == Qt.MidButton :
			if self.panning:
				self.panning = False
		if event.button() == Qt.LeftButton:
			if self.selecting:
				self.stopSelectionRegion()
				self.selecting = False

	def wheelEvent(self, event):
		steps = event.pixelDelta().y() / 120.0;
		dx = 0
		dy = 0
		zoomRate = 1.1
		delta = event.angleDelta()
		dx = delta.x()
		dy = delta.y()
		if dy > 0:
			self.setZoom( self.zoom * zoomRate )
		elif dy < 0:
			self.setZoom( self.zoom / zoomRate )

	# def keyPressEvent( self, event ):
	# 	key = event.key()
	# 	modifiers = event.modifiers()
	# 	if key in ( Qt.Key_Delete, Qt.Key_Backspace ):
	# 		self.timelineView.deleteSelection()

	def onRectChanged( self, rect ):
		self.gridBackground.setRect( rect )

	def getTimelineView( self ):
		return self.timelineView

	def setCursorVisible( self, visible ):
		self.gridBackground.setCursorVisible( visible )

##----------------------------------------------------------------##
class TimelineCurveView( CurveView ):
	def __init__( self, *args, **kwargs ):
		super( TimelineCurveView, self ).__init__( *args, **kwargs )
		self.timelineView = None
		self.vertChanged.connect( self.onVertChanged )
		self.vertBezierPointChanged.connect( self.onVertBezierPointChanged )
		self.vertTweenModeChanged.connect( self.onVertTweenModeChanged )

	def getTimelineView( self ):
		return self.timelineView

	def getParentCurveNode( self, vertNode ):
		return self.timelineView.getParentTrackNode( vertNode )

	def getCurveNodes( self ):
		return self.timelineView.getActiveCurveNodes()

	def getVertNodes( self, curveNode ):
		return self.timelineView.getCurveVertNodes( curveNode )

	def getVertParam( self, curveNode ):
		return self.timelineView.getCurveVertParam( curveNode )

	def onVertChanged( self, vertNode, x, y ):
		self.timelineView.notifyKeyChanged( vertNode, x, None )
		self.timelineView.notifyKeyCurveValueChanged( vertNode, y )
		self.timelineView.refreshKey( vertNode )

	def onVertTweenModeChanged( self, vertNode, mode ):
		self.timelineView.notifyKeyTweenModeChanged( vertNode, mode )

	def onVertBezierPointChanged( self, vertNode, bpx0, bpy0, bpx1, bpy1 ):
		self.timelineView.notifyKeyBezierPointChanged( vertNode, bpx0, bpy0, bpx1, bpy1 )

##----------------------------------------------------------------##	
class TimelineView( QtWidgets.QWidget ):
	keySelectionChanged    = Signal()
	trackSelectionChanged  = Signal()
	markerSelectionChanged = Signal()
	markerChanged          = Signal( object, float )
	keyChanged             = Signal( object, float, float )
	keyCurveValueChanged   = Signal( object, float )
	keyTweenModeChanged    = Signal( object, int )
	keyBezierPointChanged  = Signal( object, float, float, float, float )
	cursorPosChanged       = Signal( float )
	zoomChanged            = Signal( float )

	def __init__( self, *args, **kwargs ):
		super( TimelineView, self ).__init__( *args, **kwargs )
		#start up
		self.rebuilding   = False
		self.updating     = False
		self.shiftMode    = False
		self.switchingMode = False
		self.activeView = 'dopesheet'

		self.selection       = []
		self.trackSelection  = []
		self.markerSelection = []

		self.activeCurveNodes = []

		self.refreshingKey = False

		self.initData()
		self.initUI()
		self.setEnabled( True )


	def initData( self ):
		self.tracks       = []
		self.nodeToTrack  = {}
		self.nodeToMarker = {}

	def initUI( self ):
		self.setObjectName( 'Timeline' )
		self.ui = TimelineForm()
		self.ui.setupUi( self )
		
		self.trackView  = TimelineTrackView( parent = self )
		self.trackView.timelineView = self

		self.rulerView  = TimelineRulerView( parent = self )
		self.rulerView.timelineView = self

		self.curveView  = TimelineCurveView( parent = self )
		self.curveView.timelineView = self

		self.curveView.setAxisVisible( False, True )
		self.curveView.setOffset( _HEAD_OFFSET, 0 )
		self.curveView.setScrollXLimit( 0, None )

		self.ui.containerRuler.setFixedHeight( _RULER_SIZE + _MARKER_SIZE )
		
		trackLayout = QtWidgets.QVBoxLayout( self.ui.containerTrack )
		trackLayout.setSpacing( 0)
		trackLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		trackLayout.addWidget( self.trackView )

		curveLayout = QtWidgets.QVBoxLayout( self.ui.containerCurve )
		curveLayout.setSpacing( 0)
		curveLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		curveLayout.addWidget( self.curveView )

		rulerLayout = QtWidgets.QVBoxLayout( self.ui.containerRuler )
		rulerLayout.setSpacing( 0)
		rulerLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		rulerLayout.addWidget( self.rulerView )

		# self.rulerView.cursorPosChanged
		self.trackView.zoomChanged.connect( self.onZoomChanged )
		self.rulerView.zoomChanged.connect( self.onZoomChanged )
		self.curveView.zoomXChanged.connect( self.onZoomChanged )

		self.trackView.scrollPosChanged.connect( self.onScrollPosChanged )
		self.rulerView.scrollPosChanged.connect( self.onScrollPosChanged )
		self.curveView.scrollXChanged.connect( self.onScrollPosChanged )

		self.trackView.cursorPosChanged.connect( self.onCursorPosChanged )
		self.rulerView.cursorPosChanged.connect( self.onCursorPosChanged )

		self.curveView.selectionChanged.connect( self.onCurveSelectionChanged )

		self.tabViewSwitch = QtWidgets.QTabBar()
		bottomLayout = QtWidgets.QHBoxLayout( self.ui.containerBottom )
		bottomLayout.addWidget( self.tabViewSwitch )
		bottomLayout.setSpacing( 3 )
		bottomLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		self.tabViewSwitch.addTab( 'Dope Sheet')
		
		if self.hasCurveView():
			self.tabViewSwitch.addTab( 'Curve View' )

		self.tabViewSwitch.currentChanged.connect( self.onTabChanged )
		self.tabViewSwitch.setShape( QtWidgets.QTabBar.RoundedSouth )
		self.tabViewSwitch.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)

		
		self.toolbarEdit = QtWidgets.QToolBar()
		self.toolbarEdit.setObjectName( 'TimelineToolBarEdit')
		bottomLayout.addWidget( self.toolbarEdit )
		self.toolbarEdit.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
		self.toolbarEdit.setIconSize( QtCore.QSize( 16, 16 ) )
		#key tool
		self.toolbarEdit.addSeparator()

		self.spinboxClipLength = QtWidgets.QDoubleSpinBox()
		self.spinboxClipLength.setFixedWidth( 80 )
		self.spinboxClipLength.setValue( 2.5 )
		self.spinboxClipLength.valueChanged.connect( self.changeClipRange )
		self.spinboxClipLength.setRange( 0, 10000 )
		self.spinboxClipLength.setDecimals( 3 )
		self.spinboxClipLength.setSingleStep( 0.1 )

		# self.spinboxClipLength.setText( '25:00' )
		# self.toolbarEdit.addWidget( QtWidgets.QLabel( 'L' ) )
		self.toolbarEdit.addWidget( self.spinboxClipLength )

		self.toolbarEdit.addSeparator()
		self.toolbuttonAddKey    = self.addEditToolButton(
			'add_key',    '+', 'Add Key(s)'
			)
		self.toolbuttonRemoveKey = self.addEditToolButton(
			'remove_key', '-', 'Remove Key(s)'
			)
		self.toolbuttonCloneKey  = self.addEditToolButton(
			'clone_key',  'C', 'Clone Key(s)'
			)		
		
		self.toolbarEdit.addSeparator()

		self.toolbuttonAddMarker    = self.addEditToolButton(
			'add_marker',    '+M', 'Add Marker'
			)

		if self.hasCurveView():
			#curve tool
			self.toolbarEdit.addSeparator()

			self.toolbuttonCurveModeLinear   = self.addEditToolButton(
				'curve_mode_linear',   'L', 'Linear Interpolation Mode'
				)
			self.toolbuttonCurveModeConstant = self.addEditToolButton(
				'curve_mode_constant', 'K', 'Constant Interpolation Mode'
				)
			self.toolbuttonCurveModeBezier   = self.addEditToolButton(
				'curve_mode_bezier',   'B', 'Uniform Besizer Interpolation Mode'
				)
			self.toolbuttonCurveModeBezierS  = self.addEditToolButton(
				'curve_mode_bezier_s', 'b', 'Splitted Besizer Interpolation Mode'
				)
			
		#init
		self.setScrollPos( 0 )
		self.setCursorPos( 0 )
		self.setZoom( 1.0 )
		# self.trackView.cursorPosChanged.connect(  )

		self.trackSelection = []

		self.actionDeleteSelection = QtWidgets.QAction( self )
		self.actionDeleteSelection.setShortcuts( 
			[ QtGui.QKeySequence('Delete'), QtGui.QKeySequence('Backspace') ] )
		self.actionDeleteSelection.setShortcutContext( Qt.WidgetWithChildrenShortcut )
		self.actionDeleteSelection.triggered.connect( self.deleteSelection )
		self.addAction( self.actionDeleteSelection )


	def addEditToolButton( self, id, label, tooltip = None ):
		tooltip = tooltip or label
		action = self.toolbarEdit.addAction( label )
		action.triggered.connect( lambda x: self.onEditTool( id ) )
		action.setToolTip( tooltip )
		return action

	def onTabChanged( self, idx ):
		self.ui.containerContents.setCurrentIndex( idx )
		self.switchingMode = True
		
		if idx == 1:
			self.activeView = 'curve'
			self.toolbuttonCurveModeLinear.setEnabled( True )
			self.toolbuttonCurveModeConstant.setEnabled( True )
			self.toolbuttonCurveModeBezier.setEnabled( True )
			self.toolbuttonCurveModeBezierS.setEnabled( True )
			selection = self.getSelection()
			self.curveView.rebuild()
			self.curveView.setSelection( selection, False )
		else:
			self.activeView = 'dopesheet'
			self.toolbuttonCurveModeLinear.setEnabled( False )
			self.toolbuttonCurveModeConstant.setEnabled( False )
			self.toolbuttonCurveModeBezier.setEnabled( False )
			self.toolbuttonCurveModeBezierS.setEnabled( False )
		self.switchingMode = False

	def getCurrentEditMode( self ):
		if self.ui.containerContents.currentIndex() == 0:
			return 'dope'
		else:
			return 'curve'

	def getRulerHeight( self ):
		return _RULER_SIZE + _MARKER_SIZE

	def getBottomToolHeight( self ):
		return self.toolbarEdit.height()
		
	def getZoom( self ):
		return self.rulerView.getZoom()

	def getScrollPos( self ):
		return self.rulerView.getScrollPos()

	def getCursorPos( self ):
		return self.rulerView.getCursorPos()

	def setZoom( self, zoom ):
		self.rulerView.setZoom( zoom )

	def setScrollPos( self, pos ):
		self.rulerView.setScrollPos( pos )

	def setTrackViewScrollRange( self, maxRange ):
		self.trackView.setScrollYRange( maxRange )

	def setTrackViewScroll( self, y ):
		self.trackView.setScrollY( y )

	def getTrackViewScroll( self, y ):
		return self.trackView.getScrollY( y )

	def setCursorPos( self, pos, focus = False ):
		self.rulerView.setCursorPos( pos )
		if focus:
			self.focusTimeline( pos )

	def setRange( self, t0, t1 ):
		self.rulerView.setRange( t0, t1 )
		self.curveView.setRangeX( t0, t1 )
		self.spinboxClipLength.setValue( t1 )

	def getRange( self ):
		return self.rulerView.getRange()

	def focusTimeline( self, pos ):
		#TODO:center
		leftEnd, rightEnd = self.rulerView.getVisibleRange()
		self.setScrollPos( max(pos, 0 ) )

	def posToTime( self, x ):
		zoom = self.getZoom()
		pos  = self.getScrollPos()
		return x/zoom + pos

	def timeToPos( self, pos ):
		zoom = self.getZoom()
		pos0 = self.getScrollPos()
		return ( pos - pos0 ) * zoom

	def timeLengthToWidth( self, length ):
		zoom = self.getZoom()
		return zoom * length

	def widthToTimeLength( self, w ):
		zoom = self.getZoom()
		return w/zoom

	def setShiftMode( self, enabled = True ):
		self.shiftMode = enabled
		
	def rebuild( self ):
		self.clear()
		self.setUpdatesEnabled( False )
		self.rebuilding = True
		t0, t1 = self.getClipRange() 
		self.setRange( t0, t1 )
		for markerNode in self.getMarkerNodes():
			self.addMarker( markerNode )
		for trackNode in self.getTrackNodes():
			self.addTrack( trackNode )
		self.updateTrackLayout()
		self.curveView.rebuild()
		self.rebuilding = False
		self.setUpdatesEnabled( True )

	def clear( self ):
		self.setUpdatesEnabled( False )
		self.trackView.clear()
		self.rulerView.clear()
		self.tracks = []
		self.nodeToTrack = {}
		self.updateTrackLayout()
		self.setUpdatesEnabled( True )

	def updateTrackLayout( self ):
		y = 0
		for track in self.tracks:
			node = track.node
			vis = self.isTrackVisible( node )
			if vis:
				y = self.getTrackPos( node )
				track.setY( y )
				y += _TRACK_SIZE + _TRACK_MARGIN
			track.setVisible( vis or False )
		
	def getTrackByNode( self, trackNode ):
		return self.nodeToTrack.get( trackNode, None )

	def getKeyByNode( self, keyNode ):
		track = self.getParentTrack( keyNode )
		return track and track.getKeyByNode( keyNode ) or None

	def getMarkerByNode( self, markerNode ):
		return self.nodeToMarker.get( markerNode, None )

	def createTrackItem( self, node ):
		return TimelineTrackItem()

	def addTrack( self, node, **option ):
		trackItem = self.nodeToTrack.get( node, None )
		if trackItem: return trackItem
		trackItem = self.createTrackItem( node )
		trackItem =  self.trackView.addTrackItem( trackItem, **option )
		trackItem.node = node
		self.nodeToTrack[ node ] = trackItem
		self.tracks.append( trackItem )

		#add keys
		keyNodes = self.getKeyNodes( node )
		if keyNodes:
			for keyNode in keyNodes:
				self.addKey( keyNode, **option )

		self.refreshTrack( node, **option )
		self.updateTrackLayout()
		
		return trackItem

	def removeTrack( self, trackNode ):
		trackItem = self.getTrackByNode( trackNode )
		if not trackItem: return
		i = self.tracks.index( trackItem ) #excpetion catch?
		del self.tracks[i]
		del self.nodeToTrack[ trackItem.node ]
		trackItem.node = None
		trackItem.clear()
		self.trackView.removeTrackItem( trackItem )
		self.updateTrackLayout()

	def addKey( self, keyNode, **option ):
		trackItem = self.affirmParentTrack( keyNode )
		if not trackItem: return None
		key = trackItem.addKey( keyNode, **option )
		if key:
			self.refreshKey( keyNode, **option )
		if self.getCurrentEditMode() == 'curve':
			self.curveView.rebuild( False )
		return key

	def removeKey( self, keyNode, removingChildKey = False ):
		track = self.getParentTrack( keyNode )
		if not track: return
		childKeyNodes = self.getChildKeyNodes( keyNode )
		for childKeyNode in childKeyNodes:
			self.removeKey( childKeyNode, True, )

		track.removeKey( keyNode, not removingChildKey )
		if keyNode in self.selection:
			self.selection.remove( keyNode )

		if not removingChildKey:
			if self.getCurrentEditMode() == 'curve':
				self.curveView.rebuild()
			self.updateSelection( self.selection )

	def getParentTrack( self, keyNode ):
		trackNode = self.getParentTrackNode( keyNode )
		if not trackNode: return None
		return self.getTrackByNode( trackNode )

	def affirmParentTrack( self, keyNode ):
		trackNode = self.getParentTrackNode( keyNode )
		if not trackNode: return None
		trackItem = self.getTrackByNode( trackNode )
		if not trackItem:
			return self.addTrack( trackNode )
		else:
			return trackItem

	def setTrackSelection( self, tracks ):
		prev = self.trackSelection
		if prev:
			for trackNode in prev:
				trackItem = self.getTrackByNode( trackNode )
				if trackItem:
					trackItem.setSelected( False )
		if tracks:
			for trackNode in tracks:
				trackItem = self.getTrackByNode( trackNode )
				if trackItem:
					trackItem.setSelected( True )
		self.trackSelection = tracks
		if self.activeView == 'curve':
			self.curveView.rebuild()

	def getTrackSelection( self ):
		return self.trackSelection

	def setCursorDraggable( self, draggable = True ):
		self.rulerView.setCursorDraggable( draggable )

	def onCursorPosChanged( self, pos ):
		if self.updating: return
		self.updating = True
		self.trackView.setUpdatesEnabled( False )
		self.rulerView.setCursorPos( pos )
		self.trackView.setCursorPos( pos )
		self.curveView.setCursorX( pos )
		self.cursorPosChanged.emit( pos )
		self.trackView.setUpdatesEnabled( True )
		self.updating = False

	def onScrollPosChanged( self, pos ):
		if self.updating: return
		self.updating = True
		self.rulerView.setScrollPos( pos )
		self.trackView.setScrollPos( pos )
		self.curveView.setScrollX( pos )
		self.updating = False

	def onZoomChanged( self, zoom ):
		if self.updating: return
		self.updating = True
		#sync widget zoom
		self.rulerView.setZoom( zoom )
		self.trackView.setZoom( zoom )
		self.curveView.setZoomX( zoom )
		self.zoomChanged.emit( zoom )
		self.updating = False
	
	def refreshKey( self, keyNode, **option ):
		refreshingKey = self.refreshingKey
		self.refreshingKey = True
		key = self.getKeyByNode( keyNode )
		if key:
			pos, length, resizable = self.getKeyParam( keyNode )
			key.setTimePos( pos )
			key.setTimeLength( length )
			key.setResizable( resizable )
			self.updateKeyContent( key, keyNode, **option )
		
		if self.getCurrentEditMode() == 'curve':
			self.curveView.refreshVert( keyNode )
		
		for childKey in self.getChildKeyNodes( keyNode ):
			self.refreshKey( childKey )
			
		self.refreshingKey = refreshingKey

	def refreshMarker( self, markerNode, **option ):
		marker = self.getMarkerByNode( markerNode )
		if marker:
			pos = self.getMarkerParam( markerNode )
			marker.setTimePos( pos )
			self.updateMarkerContent( marker, markerNode, **option )
			marker.update()

	def refreshTrack( self, trackNode, **option ):
		track = self.getTrackByNode( trackNode )
		if track:
			self.updateTrackContent( track, trackNode, **option )

	def notifyKeyBezierPointChanged( self, keyNode, bpx0, bpy0, bpx1, bpy1):
		self.keyBezierPointChanged.emit( keyNode, bpx0, bpy0, bpx1, bpy1 )

	def notifyKeyTweenModeChanged( self, keyNode, mode ):
		self.keyTweenModeChanged.emit( keyNode, mode )

	def notifyKeyCurveValueChanged( self, keyNode, value ):
		self.keyCurveValueChanged.emit( keyNode, value )

	def notifyKeyChanged( self, keyNode, pos, length = None ):
		if self.refreshingKey: return
		if not length:
			_pos, length, resizable = self.getKeyParam( keyNode )
		self.keyChanged.emit( keyNode, pos, length )
		self.refreshKey( keyNode )

	def notifyMarkerChanged( self, markerNode, pos ):
		self.markerChanged.emit( markerNode, pos )

	def selectMarker( self, markerNode, additive = False ):
		if not markerNode and not self.markerSelection: return
		self.selectKey( None )
		if additive:
			if not markerNode in self.markerSelection:
				self.markerSelection.append( markerNode )
			markerItem = self.getMarkerByNode(markerNode)
			markerItem.setSelected( True, False )

		else:
			for prevKey in self.markerSelection:				
				markerItem = self.getMarkerByNode( prevKey )
				if markerItem:
					markerItem.setSelected( False, False )

			self.markerSelection = []
			if markerNode:
				self.markerSelection.append( markerNode )
				markerItem = self.getMarkerByNode( markerNode )
				markerItem.setSelected( True, False )
		self.markerSelectionChanged.emit()
		self.update()
		self.onMarkerSelectionChanged( self.markerSelection )

	def deselectKey( self, keyNode ):
		if not keyNode in self.selection:
			return
		self.selection.remove( keyNode )
		keyItem = self.getKeyByNode(keyNode)
		keyItem.setSelected( False, False )

	def selectKey( self, keyNode, additive = False ):
		if not keyNode and not self.selection: return
		self.selectMarker( None )
		if additive:
			if not keyNode in self.selection:
				self.selection.append( keyNode )
			keyItem = self.getKeyByNode(keyNode)
			keyItem.setSelected( True, False )

		else:
			for prevKey in self.selection:				
				keyItem = self.getKeyByNode( prevKey )
				if keyItem:
					keyItem.setSelected( False, False )

			self.selection = []
			if keyNode:
				self.selection.append( keyNode )
				keyItem = self.getKeyByNode( keyNode )
				keyItem.setSelected( True, False )
		self.keySelectionChanged.emit()
		self.update()
		self.updateSelection( self.selection )

	def clearSelection( self ):
		self.selectKey( None )

	def updateSelection( self, selection, notify = True ):
		if not self.switchingMode:
			self.curveView.setSelection( selection, False )
		self.selection = selection
		self.onSelectionChanged( self.selection )

	def getSelection( self ):
		return self.selection

	def deleteSelection( self ):
		oldSelection = self.selection [:]
		for keyNode in oldSelection:
			self.removeKey( keyNode )
		markerSelection = self.markerSelection [:]
		for markerNode in markerSelection:
			self.removeMarker( markerNode )

	def addMarker( self, node ):
		markerItem = self.rulerView.addMarker( node )
		markerLine = self.trackView.addMarkerLine( markerItem )
		markerItem.node = node
		self.nodeToMarker[ node ] = markerItem
		self.refreshMarker( node )
		return markerItem

	def removeMarker( self, node ):
		item = self.nodeToMarker.get( node, None )
		if not item: return
		if self.rulerView.removeMarker( node ):
			self.trackView.removeMarkerLine( item )
			del self.nodeToMarker[ node ]

	##curve view related
	def getActiveCurveNodes( self ):
		result = []
		for trackNode in self.trackSelection:
			if self.isCurveTrack( trackNode ):
				result.append( trackNode )
		return result

	def getCurveVertNodes( self, curveNode ):
		nodes = self.getKeyNodes( curveNode )
		return nodes

	def getCurveVertParam( self, vertNode ):
		mode = self.getKeyTweenMode( vertNode )
		( pos, length, resizable ) = self.getKeyParam( vertNode )
		value = self.getKeyCurveValue( vertNode )
		( preBPX, preBPY, postBPX, postBPY ) = self.getKeyBezierPoints( vertNode )
		return ( pos, value, mode, preBPX, preBPY, postBPX, postBPY )

	def onCurveSelectionChanged( self ):
		if self.switchingMode: return
		if self.getCurrentEditMode() != 'curve' : return
		selection = self.curveView.getSelection()
		self.selectKey( None )
		for key in selection:
			self.selectKey( key, True )

	#####
	#VIRUTAL data model functions
	#####
	def hasCurveView( self ):
		return True

	def getRulerParam( self ):
		return {}

	def formatPos( self, pos ):
		return '%.1f' % pos

	def updateTrackContent( self, track, node, **option ):
		pass

	def updateKeyContent( self, key, keyNode, **option ):
		pass

	def updateMarkerContent( self, marker, markerNode, **option ):
		pass

	def getKeyText( self, key ):
		return 'Event'

	def getMarkerText( self, marker ):
		return 'Marker'

	def createTrack( self, node ):
		return TimelineTrackItem()

	def getTrackNodes( self ):
		return []

	def getMarkerNodes( self ):
		return []

	def getKeyNodes( self, trackNode ):
		return []

	def getParentKeyNode( self, keyNode ):
		return None

	def getChildKeyNodes( self, keyNode ):
		return []

	def getKeyParam( self, keyNode ):
		return ( 0, 10, True )

	def getKeyCurveValue( self, keyNode ):
		return 0

	def getKeyBezierPoints( self, keyNode ):
		return ( 0.5, 0.0, 0.5, 0.0 )

	def getKeyTweenMode( self, keyNode ):
		return TWEEN_MODE_LINEAR

	def getMarkerParam( self, markerNode ):
		return 0
	
	def getParentTrackNode( self, keyNode ):
		return None

	def getTrackPos( self, trackNode ):
		return 0

	def isTrackVisible( self, trackNode ):
		return 0

	def isCurveTrack( self, trackNode ):
		return False

	def onSelectionChanged( self, selection ):
		pass

	def onMarkerSelectionChanged( self, selection ):
		pass

	def onKeyRemoving( self, keyNode ):
		return True

	def onMarkerRemoving( self, markerNode ):
		return True

	def onClipRangeChanging( self, t0, t1 ):
		return True

	def setTrackSelected( self, trackNode ):
		pass

	def getSelectedTrack( self ):
		pass
	
	def getClipRange( self ):
		return 0, 30

	#######
	#Interaction
	#######
	def changeClipRange( self, value ):
		if self.onClipRangeChanging( 0, value ):
			self.rulerView.setRange( 0, value )
		t0, t1 = self.getClipRange()
		self.curveView.setRangeX( t0, t1 )
		self.spinboxClipLength.setValue( t1 )

	def onTrackClicked( self, track, pos ):
		pass

	def onKeyClicked( self, key, pos ):
		self.selectKey( key.node )

	def onMarkerClicked( self, marker ):
		self.selectMarker( marker.node )

	def setEnabled( self, enabled ):
		super( TimelineView, self ).setEnabled( enabled )
		self.trackView.setCursorVisible( enabled )
		self.rulerView.setCursorVisible( enabled )
		self.curveView.setCursorVisible( enabled )

	def changeSelectionTweenMode( self, mode ):
		if self.activeView != 'curve' : return
		for key in self.curveView.getSelection():
			self.curveView.setVertTweenMode( key, mode )

	def onEditTool( self, toolName ):
		if toolName == 'curve_mode_linear':
			self.changeSelectionTweenMode( TWEEN_MODE_LINEAR )

		elif toolName == 'curve_mode_constant':
			self.changeSelectionTweenMode( TWEEN_MODE_CONSTANT )

		elif toolName == 'curve_mode_bezier':
			self.changeSelectionTweenMode( TWEEN_MODE_BEZIER )
			#TODO

		elif toolName == 'curve_mode_bezier_s':
			self.changeSelectionTweenMode( TWEEN_MODE_BEZIER )
			#TODO

	# def closeEvent( self, ev ):
	# 	self.trackView.deleteLater()
	# 	self.rulerView.deleteLater()
		
	# def __del__( self ):
	# 	self.deleteLater()

##----------------------------------------------------------------##
if __name__ == '__main__':
	from . import testView
