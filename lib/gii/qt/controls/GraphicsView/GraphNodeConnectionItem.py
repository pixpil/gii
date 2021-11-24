from .GraphNodeItem import *

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
		self.arrowPercent = 0.5

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
			diff = dx > 0 and max( dx * 0.7, 30 ) or 100
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


##----------------------------------------------------------------##
class GraphNodeLineConnectionItem( GraphNodeConnectionItem):
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
		path.lineTo( pos1 )
		
		self.setPath( path )
		self.pathLength = path.length()
		self.arrowPercent = path.percentAtLength( self.pathLength - 8 )

##----------------------------------------------------------------##
class GraphNodeCurveConnectionItem( GraphNodeConnectionItem):
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
		diff = max( dx * 0.7, 30 )
		cpos0 = n0 * diff
		cpos1 = pos1 + n1 * diff
		path.cubicTo( cpos0, cpos1, pos1 )

		self.setPath( path )
		self.pathLength = path.length()
		self.arrowPercent = path.percentAtLength( self.pathLength - 8 )

##----------------------------------------------------------------##
class GraphNodePolyLineConnectionItem( GraphNodeConnectionItem):
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
		diff = max( dx * 0.5, 30 )
		cpos0 = n0 * diff
		cpos1 = pos1 + n1 * diff
		path.lineTo( cpos0 )
		path.lineTo( cpos1 )
		path.lineTo( pos1 )				

		self.setPath( path )
		self.pathLength = path.length()
		self.arrowPercent = path.percentAtLength( self.pathLength - 8 )


if __name__ == '__main__':
	from . import TestGraphView
	