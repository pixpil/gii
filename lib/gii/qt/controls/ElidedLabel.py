from qtpy            import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore     import Qt

class ElidedLabel( QtWidgets.QLabel ):
	def __init__( self, *args, **kwargs ):
		super( ElidedLabel, self ).__init__( *args, **kwargs )
		self._elideMode = Qt.ElideLeft

	def elideMode( self ):
		return self._elideMode

	def setElideMode( self, mode ):
		self._elideMode = mode

	def paintEvent( self, event ):
		painter = QtGui.QPainter( self )
		metrics = QtGui.QFontMetrics( self.font() )
		elided  = metrics.elidedText( self.text(), self._elideMode, self.width() )
		painter.drawText( self.rect(), self.alignment(), elided )

	def minimumSizeHint( self ):
		return QtWidgets.QWidget.minimumSizeHint( self )
