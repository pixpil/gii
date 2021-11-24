import sys
from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtCore import Qt, QRect, QSize, QPoint, Signal
from qtpy.QtWidgets import QApplication, QLineEdit
from qtpy.QtGui import QColor
import math

class DirectionEditPanel( QtWidgets.QWidget ):
	valueChanged = Signal( int )
	def __init__( self, *args ):
		super(DirectionEditPanel, self).__init__( *args )
		self._value = 0
		self._readonly = False
		self.setCursor( Qt.PointingHandCursor )
		self.setMouseTracking( True )
		self.dragging = False
		self._topAngle = None
		self._ccw      = True
		self._wrapMode = 0 #0 for -180~180; 1 for 0~360
		self._range    = ( 0, 360 )

	def setTopAngle( self, angle ):
		self._topAngle = angle

	def topAngle( self ):
		return self._topAngle

	def setCCW( self, ccw = True ):
		self._ccw = ccw

	def isCCW( self ):
		return self._ccw

	def setRange( self, r0, r1 ):
		self._range = ( r0, r1 )

	def range( self ):
		return self._range

	def wrapMode( self ):
		return self._wrapMode

	def setWrapMode( self, mode ):
		self._wrapMode = mode
	
	def minimumSizeHint( self ):
		return QSize( 50, 50 )

	def convertAngle( self, a ):
		if self._ccw:
			a = -a
			originTop = 90
			if self._topAngle:
				a += ( originTop - self._topAngle )
		else:
			originTop = -90
			if self._topAngle:
				a -= ( originTop - self._topAngle )

		a = a % 360.0
		if self._wrapMode == 0:
			if a > 180:
				a = a - 360
		return a

	def unconvertAngle( self, a ):
		if self._ccw:
			a = -a
			originTop = 90
			if self._topAngle:
				a -= ( originTop - self._topAngle )
		else:
			originTop = -90
			if self._topAngle:
				a += ( originTop - self._topAngle )

		a = a % 360.0
		if self._wrapMode == 0:
			if a > 180:
				a = a - 360
		return a

	def paintEvent( self, ev ):
		painter = QtGui.QPainter()
		# painter.setRenderHint( QtGui.QPainter.HighQualityAntialiasing, False )
		painter.begin( self )
		painter.setRenderHint( QtGui.QPainter.Antialiasing, True )
		rect = self.rect()
		brushT = QColor( '#795122' )
		brushF = QColor( '#222' )
		penG   = QColor( '#444' )
		penT   = Qt.white
		penF   = Qt.darkGray
		value  = self.convertAngle( self._value )
		painter.setPen( penG )
		painter.setBrush( brushF )
		h = rect.height()
		x,y = rect.x(),rect.y()
		painter.drawEllipse(x,y,h,h)
		painter.setPen( penT )
		dx = math.cos( value/180.0*3.14159265355 ) * ( h/2 - 2 )
		dy = math.sin( value/180.0*3.14159265355 ) * ( h/2 - 2 )
		cx, cy = x+h/2, y+h/2
		painter.drawEllipse( cx-2, cy-2, 4,4 )
		painter.drawLine( cx, cy, cx + dx, cy + dy )
		painter.end()

	def mousePressEvent( self, ev ):
		if self._readonly : return
		if ev.button() != Qt.LeftButton: return
		self.onDrag( ev )
		self.dragging = True

	def onDrag( self, ev ):
		pos = ev.pos()
		cx, cy = self.height()/2, self.height()/2
		dx, dy = pos.x() - cx, pos.y() - cy
		a = math.atan2( dy, dx )/3.14159265355*180.0
		a = self.unconvertAngle( a )
		if ev.modifiers() & QtCore.Qt.ControlModifier:
			a = math.floor( a/45.0 ) * 45.0
		self._value = a
		self.update()
		self.valueChanged.emit( self._value )

	def mouseMoveEvent( self, ev ):
		if self._readonly: return
		if self.dragging:
			self.onDrag( ev )

	def mouseReleaseEvent( self, ev ):
		if ev.button() != Qt.LeftButton: return
		self.dragging = False

	def isReadonly( self ):
		return self._readonly
	
	def setReadOnly( self, value ):
		self._readonly = value
		self.update()

class NoScrollSpin( QtWidgets.QDoubleSpinBox ):
	def wheelEvent( self, ev ):
		pass
		
class DirectionEdit( QtWidgets.QWidget ):
	valueChanged = Signal( int )
	def __init__( self, *args ):
		super( DirectionEdit, self ).__init__( *args )
		layout = QtWidgets.QHBoxLayout( self )
		self.directionEditPanel = DirectionEditPanel( self )
		self.spin = NoScrollSpin( self )
		self.spin.setFocusPolicy( Qt.TabFocus )
		# self.spin.setButtonSymbols( QtWidgets.QAbstractSpinBox.NoButtons )
		self.spin.setMinimum( -360 )
		self.spin.setMaximum( 360 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		layout.setSpacing( 1 )
		layout.addWidget( self.directionEditPanel )
		layout.addWidget( self.spin )

		self.directionEditPanel.valueChanged.connect( self.spin.setValue )
		self.spin.valueChanged.connect( self.onSpinChanged )
		self.setValue( 0 )

	def setTopAngle( self, angle ):
		self.directionEditPanel.setTopAngle( angle )

	def setCCW( self, ccw = True ):
		self.directionEditPanel.setCCW( ccw )

	def setWrapMode( self, mode ):
		self.directionEditPanel.setWrapMode( mode )

	def value( self ):
		return self.spin.value()

	def setValue( self, v ):
		self.spin.setValue( v )

	def onSpinChanged( self, v ):
		self.directionEditPanel._value = v
		self.directionEditPanel.update()
		v = v % 360.0
		if self.directionEditPanel._wrapMode == 0:
			if v > 180:
				v = v - 360
		self.spin.setValue( v )
		self.valueChanged.emit( v )

	def setReadOnly( self, readOnly ):
		self.spin.setReadOnly( readOnly )
		self.directionEditPanel.setReadOnly( readOnly )


if __name__ == "__main__":
	import sys
	app = QtWidgets.QApplication( sys.argv )
	styleSheetName = 'gii.qss'
	app.setStyleSheet(
			open( '/Users/tommo/prj/gii/data/theme/' + styleSheetName ).read() 
		)
	edit = DirectionEdit()
	edit.show()
	# edit.setReadOnly( True )
	edit.raise_()
	sys.exit(app.exec_())
