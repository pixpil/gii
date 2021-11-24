import sys
from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtCore import Qt, QRect, QSize, QPoint, Signal
from qtpy.QtWidgets import QApplication, QCompleter, QLineEdit
from qtpy.QtGui import QColor


class BitMaskPanel( QtWidgets.QWidget ):
	valueChanged = Signal( int )
	def __init__( self, *args ):
		super(BitMaskPanel, self).__init__( *args )
		self._bitSize = 16
		self._value = 0
		self._gridSize = 20
		self._readonly = False
		self.setCursor( Qt.PointingHandCursor )
		self.setMouseTracking( True )

	def gridSize( self ):
		return self._gridSize

	def setGridSize( self, size ):
		self._gridSize = size
		self.update()

	def setBitSize( self, size ):
		self._bitSize = size
		self.update()

	def bitSize( self ):
		return self._bitSize

	def sizeHint( self ):
		colCount = 8
		rowCount = int( self._bitSize / colCount )
		gs = self._gridSize
		return QSize( colCount*gs + 1, rowCount*gs + 1 )

	def minimumSizeHint( self ):
		return self.sizeHint()

	def paintEvent( self, ev ):
		painter = QtGui.QPainter()
		painter.begin( self )



		rect = self.rect()
		gs = self._gridSize
		brushT = QColor( '#4E7641' )
		brushF = Qt.black
		penG   = Qt.darkGray
		penT   = Qt.white
		penF   = Qt.darkGray
		value  = int( self._value )
		tflag = Qt.AlignCenter | Qt.AlignVCenter
		for i in range( self._bitSize ):
			col = i % 8
			row = int( i/8 )
			x0 = gs * col
			y0 = gs * row
			gridRect = QRect( x0, y0, gs, gs )
			bit = bool( value & ( 1 << i ) )
			if bit:
				painter.setBrush( brushT )
				painter.setPen( penG )
			else:
				painter.setBrush( brushF )
				painter.setPen( penG )

			painter.drawRect( gridRect )
			if bit:
				painter.setPen( penT )
			else:
				painter.setPen( penF )
			painter.drawText(
				gridRect, tflag, '%d' % i
				)
		painter.end()

	def mousePressEvent( self, ev ):
		if self._readonly : return
		if ev.button() != Qt.LeftButton: return
		pos = ev.pos()
		gs = self._gridSize
		xx = int( pos.x()/gs )
		yy = int( pos.y()/gs )
		if xx > 8: return
		bitPos = yy * 8 + xx
		if bitPos > self._bitSize: return
		mask = 1 << bitPos
		if self._value & mask: #erase
			self._value &= ~mask
		else:#add
			self._value |= mask
		self.update()
		self.valueChanged.emit( self._value )

	def isReadonly( self ):
		return self._readonly
	
	def setReadOnly( self, value ):
		self._readonly = value
		self.update()

class NoScrollSpin( QtWidgets.QSpinBox ):
	def wheelEvent( self, ev ):
		pass
		
class BitMaskEdit( QtWidgets.QWidget ):
	valueChanged = Signal( int )
	def __init__( self, *args ):
		super( BitMaskEdit, self ).__init__( *args )
		layout = QtWidgets.QVBoxLayout( self )
		self.bitMaskPanel = BitMaskPanel( self )
		self.spin = NoScrollSpin( self )
		self.spin.setFocusPolicy( Qt.TabFocus )
		self.spin.setButtonSymbols( QtWidgets.QAbstractSpinBox.NoButtons )
		self.spin.setMinimum( 0 )
		self.spin.setMaximum( 65535 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		layout.setSpacing( 1 )
		layout.addWidget( self.spin )
		layout.addWidget( self.bitMaskPanel )

		self.bitMaskPanel.valueChanged.connect( self.spin.setValue )
		self.spin.valueChanged.connect( self.onSpinChanged )
		self.setValue( 0 )

	def setBitSize( self, size ):
		size = max( min( size, 64 ), 0 )
		self.spin.setMaximum( (1 << size) - 1 )
		self.bitMaskPanel.setBitSize( size )

	def bitSize( self ):
		return self.bitMaskPanel.bitSize()

	def value( self ):
		return self.spin.value()

	def setValue( self, v ):
		try:
			self.spin.setValue( v )
		except Exception as e:
			pass

	def onSpinChanged( self, v ):
		self.bitMaskPanel._value = v
		self.bitMaskPanel.update()
		self.valueChanged.emit( v )

	def setReadOnly( self, readOnly ):
		self.spin.setReadOnly( readOnly )
		self.bitMaskPanel.setReadOnly( readOnly )


if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication( sys.argv )
	styleSheetName = 'gii.qss'
	app.setStyleSheet(
			open( '/Users/tommo/prj/gii/data/theme/' + styleSheetName ).read() 
		)
	edit = BitMaskEdit()
	edit.show()
	# edit.setReadOnly( True )
	edit.raise_()
	sys.exit(app.exec_())
