# -*- coding: utf-8 -*-
from .GraphNodeItemBase import *

##----------------------------------------------------------------##
class DialogueNodeItem( QtWidgets.QGraphicsRectItem ):
	_pen   = makePen( color = '#808080', )
	_brush = makeBrush( color = '#1a1a1a' )

	def paint( self, painter, option, widget ):
		painter.setPen( DialogueNodeItem._pen )
		painter.setBrush( DialogueNodeItem._brush )
		rect = self.rect()
		painter.drawRoundedRect( rect, 10, 10 )
		trect = rect.adjusted( 2,2, -2,-2 )
		painter.drawText( trect, Qt.AlignLeft|Qt.AlignVCenter, 'Hello, long time no see' )

##----------------------------------------------------------------##
class GraphNodeGroupItem( GraphNodeItemBase, QtWidgets.QGraphicsRectItem ):
	_pen   = makePen( color = '#808080', style = Qt.DashLine )
	_brush = makeBrush( color = '#1a1a1a' )
	def __init__( self ):
		super(GraphNodeGroupItem, self).__init__()
		self.title = 'Group'
		self.setRect( 0,0, 400, 400 )
		self.setFlag( self.ItemIsSelectable, True )
		self.setFlag( self.ItemIsMovable, True )
		self.setFlag( self.ItemSendsGeometryChanges, True )
		self.setFlag( self.ItemClipsChildrenToShape, True )
		self.setZValue( -100 )

	def isGroup( self ):
		return True

	def getTitle( self ):
		return self.title

	def setTitle( self, title ):
		self.title = title

	def paint( self, painter, option, widget ):
		painter.setPen( GraphNodeGroupItem._pen )
		painter.setBrush( GraphNodeGroupItem._brush )
		rect = self.rect()
		painter.drawRoundedRect( rect, 10, 10 )
		trect = rect.adjusted( 10, 10, -4, -4 )
		painter.drawText( trect, Qt.AlignLeft|Qt.AlignTop, self.getTitle() )


class GraphNodePortItem( GraphNodeItemBase, QtWidgets.QGraphicsRectItem ):
	_pen = makePen( color = '#a4a4a4' )
	_brush = makeBrush( color = '#000000' )
	_pen_text = makePen( color = '#ffffff' )

	_pen_hover = makePen( color = '#ffffff' )
	_brush_hover = makeBrush( color = '#000000' )

	_pen_fill = Qt.NoPen
	_brush_fill = makeBrush( color = '#ffffff' )

	def __init__( self ):
		super( GraphNodePortItem, self ).__init__()
		size = 16
		self.dir = -1
		self.setRect( -size/2, -size/2, size, size )
		self.setCursor( Qt.PointingHandCursor )
		self.connections = {}
		self._pen = GraphNodePortItem._pen
		self._brush = GraphNodePortItem._brush
		self.setAcceptHoverEvents( True )

	def getText( self ):
		return '>'
	
	def clearConnections( self ):
		for conn in self.connections:
			if conn.srcPort == self:
				conn.setSrcPort( None )
			if conn.dstPort == self:
				conn.setDstPort( None )

	def updateConnections( self ):
		for conn in self.connections:
			conn.updatePath()

	def hasConnection( self ):
		if self.connections:
			return True
		else:
			return False

	def hoverEnterEvent( self, event ):
		self._pen = GraphNodePortItem._pen_hover
		self._brush = GraphNodePortItem._brush_hover
		self.update()
		return super( GraphNodePortItem, self ).hoverEnterEvent( event )

	def hoverLeaveEvent( self, event ):
		self._pen = GraphNodePortItem._pen
		self._brush = GraphNodePortItem._brush
		self.update()
		return super( GraphNodePortItem, self ).hoverLeaveEvent( event )

	def paint( self, painter, option, widget ):
		painter.setPen( self._pen )
		painter.setBrush( self._brush )
		rect = self.rect()
		painter.drawEllipse( rect.adjusted(  2,2,-2,-2 ) )
		if self.hasConnection():
			painter.setPen( GraphNodePortItem._pen_fill )
			painter.setBrush( GraphNodePortItem._brush_fill )
			painter.drawEllipse( -3,-3,6,6 )
		text = self.getText()
		painter.setPen( GraphNodePortItem._pen_text )
		if self.dir == -1: #in
			trect = QRect( rect.right() + 2, rect.top(), 100, 20 )
			painter.drawText( trect, Qt.AlignLeft|Qt.AlignVCenter, text )
		elif self.dir == 1: #out
			trect = QRect( rect.left() - 2 -100, rect.top(), 100, 20 )
			painter.drawText( trect, Qt.AlignRight|Qt.AlignVCenter, text )


	def CPNormal( self ):
		p0 = self.scenePos()
		if self.dir == -1: #in node
			return QPointF( -1, 0 )
		elif self.dir == 1: #out node
			return QPointF( 1, 0 )
		else:
			raise Exception( 'invalid port dir: %d' % self.dir )


##----------------------------------------------------------------##
class GraphNodeHeaderItem( GraphNodeItemBase, QtWidgets.QGraphicsRectItem ):
	_pen = Qt.NoPen
	_textPen = makePen( color = '#777' )
	_brush = makeBrush( color = '#444' )
	def __init__( self ):
		super( GraphNodeHeaderItem, self ).__init__()
		self.headerText = ':: Dialogue'
		self.headerHeight = 20
		self.setCursor( Qt.PointingHandCursor )


	def setText( self, t ):
		self.headerText = t

	def getText( self ):
		return self.headerText

	def updateShape( self ):
		rect = self.parentItem().rect()
		rect.setHeight( self.headerHeight )
		rect.adjust( 1,1,-1,0)
		self.setRect( rect )

	def paint( self, painter, option, widget ):
		painter.setPen( Qt.NoPen )
		painter.setBrush( GraphNodeHeaderItem._brush )
		rect = self.rect()
		painter.drawRect( rect )
		trect = rect.adjusted( 4, 2, 0, 0 )
		painter.setPen( GraphNodeHeaderItem._textPen )
		painter.drawText( trect, Qt.AlignLeft|Qt.AlignVCenter, self.getText() )


##----------------------------------------------------------------##
_GraphNodeZValue = 10
class GraphNodeItem( QtWidgets.QGraphicsRectItem ):
	_pen = QtGui.QPen( QColor( '#a4a4a4' ) )
	_brush = makeBrush( color = '#676767', alpha = 0.8 )
	def __init__( self ):
		super( GraphNodeItem, self ).__init__()
		self.inPortDict = {}
		self.outPortDict = {}
		self.inPorts  = []
		self.outPorts = []
		self.header = self.createHeader()
		self.header.setParentItem( self )
		self.setCacheMode( QtWidgets.QGraphicsItem.ItemCoordinateCache )
		self.setRect( 0, 0, 300, 120 )
		self.setFlag( self.ItemIsSelectable, True )
		self.setFlag( self.ItemIsMovable, True )
		self.setFlag( self.ItemSendsGeometryChanges, True )
		self.setAcceptHoverEvents( True )
		self.setCursor( Qt.PointingHandCursor )
		self.buildPorts()
		self.setZValue( _GraphNodeZValue )
		self.updateShape()
		self.textItem = QtWidgets.QGraphicsTextItem()
		self.textItem.setParentItem( self )
		self.textItem.setPlainText( 'Hello, World' )
		self.textItem.setDefaultTextColor( QColor('#fff') )
		self.textItem.setPos( 10, 25 )
		self.textItem.setTextInteractionFlags( Qt.TextEditorInteraction )
		self.textItem.setTextWidth( 280 )

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
		for i in range( 1 ):
			port = GraphNodePortItem()
			self.addInPort( 'p%d'%i, port )
		#output
		for i in range( 3 ):
			port = GraphNodePortItem()
			self.addOutPort( 'p%d'%i, port )

	def updateShape( self ):
		h = self.rect().height()
		row = max( len(self.inPorts), len(self.outPorts) )
		rowSize = 20
		headerSize = 20
		headerMargin = 5
		contentSize = 18
		footerMargin = 5
		minHeight = 20
		nodeWidth = 180
		totalHeight = max( row * rowSize, minHeight ) + headerMargin + contentSize + headerSize + footerMargin
		y0 = headerMargin + contentSize + headerSize
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

if __name__ == '__main__':
	from . import TestGraphView
	