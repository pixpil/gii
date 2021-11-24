import sys
import os

from qtpy import QtWidgets, QtGui, QtCore, QtOpenGL, uic

from gii.qt.controls.GraphicsView.GraphNodeView import *

##----------------------------------------------------------------##
class TestGraph():
	pass

class TestGraphItem():
	pass

class TestGraphItemConnection():
	pass

##----------------------------------------------------------------##
class TestGraphNodeViewWidget( GraphNodeViewWidget ):
	def __init__(self, *args, **kwargs ):
		super(TestGraphNodeViewWidget, self).__init__( *args, **kwargs )
		self.buildTestData()

	def buildTestData( self ):
		group = GraphNodeGroupItem()
		self.scene.addItem( group )

		node1 = GraphNodeItem()
		node2 = GraphNodeItem()
		node3 = GraphNodeItem()
		node4 = GraphNodeItem()
		node5 = GraphNodeItem()

		node1.setPos( 200, 100 )
		
		self.scene.addItem( node1 )
		self.scene.addItem( node2 )
		self.scene.addItem( node3 )
		self.scene.addItem( node4 )
		self.scene.addItem( node5 )

		conn = GraphNodeConnectionItem( node1.getOutPort( 'p1' ), node2.getInPort( 'p0' ) )
		self.scene.addItem( conn )
		conn = GraphNodeConnectionItem( node2.getOutPort( 'p1' ), node3.getInPort( 'p0' ) )
		self.scene.addItem( conn )
		
		
##----------------------------------------------------------------##
app = QtWidgets.QApplication( sys.argv )
styleSheetName = 'gii.qss'
app.setStyleSheet(
		open( '/Users/tommo/prj/gii/data/theme/' + styleSheetName ).read() 
	)

g = TestGraphNodeViewWidget()
g.resize( 600, 300 )
g.show()
g.raise_()
# Graph.setZoom( 10 )
# Graph.selectTrack( dataset[1] )

app.exec_()
