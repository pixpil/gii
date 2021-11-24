import sys
import math

from qtpy import QtWidgets, QtGui, QtCore, QtOpenGL, uic
from qtpy.QtCore import Qt, QObject, QEvent, Signal
from qtpy.QtCore import QPoint, QRect, QSize
from qtpy.QtCore import QPointF, QRectF, QSizeF
from qtpy.QtGui import QColor, QTransform, qRgb
from qtpy.QtWidgets import QStyle, QMessageBox


class SimpleTitleBar( QtWidgets.QFrame ):
	def __init__( self, *args ):
		super( SimpleTitleBar, self ).__init__( *args )
		# self.setObjectName( 'SimpleTitleBar' )
		self.pressedPos = None
		self.setMinimumSize( 10, 10 )
		self.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
		layout = QtWidgets.QHBoxLayout( self )
		self.label = QtWidgets.QLabel( self )
		self.label.setText( 'Label' )
		layout.addWidget( self.label )
		layout.setSpacing( 0 )
		layout.setContentsMargins( 2 , 2 , 2 , 2 )

	def setTitle( self, text ):
		self.label.setText( text )

	def title( self ):
		return self.label.text()

	def mousePressEvent( self, ev ):
		if ev.buttons() & Qt.LeftButton:
			self.pressedPos = ev.pos()

	def mouseMoveEvent( self, ev ):
		if ev.buttons() & Qt.LeftButton:
			diff = ev.pos() - self.pressedPos
			parent = self.parent()
			if parent:
				parent.move( parent.pos() + diff )

######TEST
if __name__ == '__main__':
	import sys
	app = QtWidgets.QApplication( sys.argv )
	styleSheetName = 'gii.qss'
	app.setStyleSheet(
			open( '/Users/tommo/prj/gii/data/theme/' + styleSheetName ).read() 
		)

	class TestFrame( QtWidgets.QFrame ):
		def __init__(self, *args):
			super(TestFrame, self).__init__( *args )
			self.setMinimumSize( 500, 300 )
			layout = QtWidgets.QVBoxLayout( self )
			layout.setSpacing( 0 )
			layout.setContentsMargins( 0 , 0 , 0 , 0 )

			self.titleBar = SimpleTitleBar( self )
			layout.addWidget( self.titleBar )

			layout.addStretch()

	widget = TestFrame()
	widget.show()
	widget.raise_()

	app.exec_()

