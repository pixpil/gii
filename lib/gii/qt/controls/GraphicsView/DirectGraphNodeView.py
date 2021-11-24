# -*- coding: utf-8 -*-
import sys
import math

from qtpy import QtWidgets, QtGui, QtCore, QtOpenGL, uic
from qtpy.QtCore import Qt, QObject, QEvent, Signal
from qtpy.QtCore import QPoint, QRect, QSize
from qtpy.QtCore import QPointF, QRectF, QSizeF
from qtpy.QtGui import QColor

from .GraphicsViewHelper import *

##----------------------------------------------------------------##
_GraphNodeZValue = 10
class GraphNodeItem( QtWidgets.QGraphicsRectItem ):
	_pen = QtGui.QPen( QColor( '#a4a4a4' ) )
	_brush = makeBrush( color = '#676767' )
	def __init__( self ):
		super( GraphNodeItem, self ).__init__()
		self.inPortDict = {}
		self.outPortDict = {}
		self.inPorts  = []
		self.outPorts = []
		self.header = self.createHeader()
		self.header.setParentItem( self )
		self.setCacheMode( QtWidgets.QGraphicsItem.ItemCoordinateCache )
		self.setRect( 0, 0, 100, 120 )
		self.setFlag( self.ItemIsSelectable, True )
		self.setFlag( self.ItemIsMovable, True )
		self.setFlag( self.ItemSendsGeometryChanges, True )
		self.setAcceptHoverEvents( True )
		self.setCursor( Qt.PointingHandCursor )
		self.buildPorts()
		self.setZValue( _GraphNodeZValue )
		self.updateShape()

	def createHeader( self ):
		return GraphNodeHeaderItem()

	def getHeader( self ):
		return self.header

	def getInPort( self, id ):
		return self.inPortDict.get( id, None )

	def getOutPort( self, id ):
		return self.outPortDict.get( id, None )

	def addInPort( self, key, port ):
		port.dir = -1
		port.setParentItem( self )
		port.key = key
		self.inPortDict[ key ] = port
		self.inPorts.append( port )

	def addOutPort( self, key, port ):
		port.dir = 1
		port.setParentItem( self )
		port.key = key
		self.outPortDict[ key ] = port
		self.outPorts.append( port )

	def buildPorts( self ):
		#input
		for i in range( 4 ):
			port = GraphNodePortItem()
			self.addInPort( 'p%d'%i, port )
		#output
		for i in range( 2 ):
			port = GraphNodePortItem()
			self.addOutPort( 'p%d'%i, port )

	def updateShape( self ):
		h = self.rect().height()
		row = max( len(self.inPorts), len(self.outPorts) )
		rowSize = 20
		headerSize = 20
		headerMargin = 10
		footerMargin = 10
		minHeight = 20
		nodeWidth = 120
		totalHeight = max( row * rowSize, minHeight ) + headerMargin + headerSize + footerMargin
		y0 = headerMargin + headerSize
		self.setRect( 0,0, nodeWidth, totalHeight )

		for i, port in enumerate( self.inPorts ):
			port.setPos( 1, y0 + i*rowSize + rowSize/2 )

		for i, port in enumerate( self.outPorts ):
			port.setPos( nodeWidth - 1, y0 + i*rowSize + rowSize/2 )

		self.header.updateShape()

	def delete( self ):
		for port in self.inPorts:
			port.clearConnections()
		for port in self.outPorts:
			port.clearConnections()
		if self.parentItem():
			self.parentItem().removeItem( self )
		else:
			self.scene().removeItem( self )

	def itemChange( self, change, value ):
		if change == self.ItemPositionChange or change == self.ItemPositionHasChanged:
			for port in self.inPorts:
				port.updateConnections()
			for port in self.outPorts:
				port.updateConnections()

		return QtWidgets.QGraphicsRectItem.itemChange( self, change, value )

	def mousePressEvent( self, ev ):
		global _GraphNodeZValue 
		_GraphNodeZValue += 0.000001 #shitty reordering
		self.setZValue( _GraphNodeZValue )
		return super( GraphNodeItem, self ).mousePressEvent( ev )

	def paint( self, painter, option, widget ):
		rect = self.rect()
		painter.setPen( GraphNodeItem._pen )
		painter.setBrush( GraphNodeItem._brush )
		painter.drawRoundedRect( rect, 3,3 )


##----------------------------------------------------------------##
class GraphNodeConnectionItem( QtWidgets.QGraphicsPathItem ):
	_pen                  = makePen( color = '#ffffff', width = 1 )
	_brush_arrow          = makeBrush( color = '#ffffff' )
	_pen_selected         = makePen( color = '#ff4700', width = 2 )
	_brush_arrow_selected = makeBrush( color = '#ff4700' )
	_polyTri = QtGui.QPolygonF([
			QPointF(  0,   0 ),
			QPointF( -12, -6 ),
			QPointF( -12,  6 ),
			])
	def __init__( self, srcPort, dstPort ):
		super( GraphNodeConnectionItem, self ).__init__()
		self.useCurve = True
		self.srcPort = None
		self.dstPort = None
		self.setSrcPort( srcPort )
		self.setDstPort( dstPort )
		self.setZValue( -1 )
		self.updatePath()
		self.setPen( GraphNodeConnectionItem._pen )
		self.setCursor( Qt.PointingHandCursor )
		self.setAcceptHoverEvents( True )
		self.selected = False

	def setSrcPort( self, port ):
		if self.srcPort:
			self.srcPort.update()
			if self in self.srcPort.connections:
				del self.srcPort.connections[ self ]
		self.srcPort = port
		if port:
			port.connections[ self ] = True
			port.update()
		self.updatePath()

	def setDstPort( self, port ):
		if self.srcPort == port: return False
		if self.dstPort:
			self.dstPort.update()
			if self in self.dstPort.connections:
				del self.dstPort.connections[ self ]
		self.dstPort = port
		if port:
			port.connections[ self ] = True
			port.update()
		self.updatePath()
		return True

	def delete( self ):
		if self.srcPort:
			del self.srcPort.connections[ self ]

		if self.dstPort:
			del self.dstPort.connections[ self ]

		self.scene().removeItem( self )


	def updatePath( self ):
		if not ( self.srcPort and self.dstPort ):
			path = QtGui.QPainterPath() #empty
			self.setPath( path )
			return

		pos0 = self.srcPort.scenePos()
		pos1 = self.dstPort.scenePos()
		n0 = self.srcPort.CPNormal()
		n1 = self.dstPort.CPNormal()
		self.setPos( pos0 )
		pos1 = self.mapFromScene( pos1 )
		path = QtGui.QPainterPath()
		path.moveTo( 0, 0 )		
		dx = pos1.x()

		if self.useCurve:
			diff = max( abs(dx) * 0.7, 30 )
			cpos0 = n0 * diff
			cpos1 = pos1 + n1 * diff
			path.cubicTo( cpos0, cpos1, pos1 )
		else:
			diff = dx / 4
			cpos0 = n0 * diff
			cpos1 = pos1 + n1 * diff
			path.lineTo( cpos0 )
			path.lineTo( cpos1 )
			path.lineTo( pos1 )				

		self.setPath( path )
		self.pathLength = path.length()
		self.arrowPercent = path.percentAtLength( self.pathLength - 8 )

	def paint( self, painter, option, widget ):
		if self.selected:
			self.setPen( GraphNodeConnectionItem._pen_selected )
		else:
			self.setPen( GraphNodeConnectionItem._pen )

		super( GraphNodeConnectionItem, self ).paint( painter, option, widget )
		#draw arrow
		path = self.path()
		midDir   = path.angleAtPercent( self.arrowPercent )
		midPoint = path.pointAtPercent( self.arrowPercent )
		trans = QTransform()
		trans.translate( midPoint.x(), midPoint.y() )
		trans.rotate( -midDir )
		painter.setTransform( trans, True )
		if self.selected:
			painter.setBrush( GraphNodeConnectionItem._brush_arrow_selected )
		else:
			painter.setBrush( GraphNodeConnectionItem._brush_arrow )
		painter.drawPolygon( GraphNodeConnectionItem._polyTri )

	def mousePressEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			self.selected = True
			self.update()
		return super( GraphNodeConnectionItem, self ).mousePressEvent( ev )

	def mouseReleaseEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			self.selected = False
			self.update()
		return super( GraphNodeConnectionItem, self ).mouseReleaseEvent( ev )
