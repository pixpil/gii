from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtCore import Qt, Signal

##----------------------------------------------------------------##
class FieldEditorLabel( QtWidgets.QLabel ):
	def __init__(self, *arg):
		super(FieldEditorLabel, self).__init__( *arg )
		self.setMinimumSize( 50, 16 )
		self.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Fixed
			)
		self.fieldEditor = None

	def setEditor( self, fieldEditor ):
		self.fieldEditor = fieldEditor

	def mousePressEvent(self, event):
		button=event.button()		
		if button == Qt.RightButton:
			if self.fieldEditor:
				self.fieldEditor.notifyContextMenuRequested()

##----------------------------------------------------------------##
class FieldEditorLineEdit(QtWidgets.QLineEdit):
	def __init__(self, *arg):
		super(FieldEditorLineEdit, self).__init__( *arg )
		self.acceptPress = False

	def focusOutEvent( self, ev ):
		self.acceptPress = False
		return super( FieldEditorLineEdit, self ).focusOutEvent( ev )

	def mousePressEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			if not self.acceptPress:
				self.acceptPress = True
				self.selectAll()
				return
		return super( FieldEditorLineEdit, self ).mousePressEvent( ev )
	
##----------------------------------------------------------------##
class FieldEditorSpinBox(QtWidgets.QSpinBox):
	def __init__(self, *arg ):
		super(FieldEditorSpinBox, self).__init__( *arg )
		# self.setButtonSymbols( QtWidgets.QAbstractSpinBox.NoButtons )
		self.ignoreWheelEvent = False
		self.setFocusPolicy( Qt.StrongFocus )
		self.setLineEdit( FieldEditorLineEdit( self ) )

	def focusInEvent( self, ev ):
		super(FieldEditorSpinBox, self).focusInEvent( ev )
		self.selectAll()
		self.setFocusPolicy( Qt.WheelFocus )

	def focusOutEvent( self, ev ):
		super(FieldEditorSpinBox, self).focusOutEvent( ev )
		self.setFocusPolicy( Qt.StrongFocus )

	def setWheelEventConfig( self, wheelEventConfig ):
		self.ignoreWheelEvent = wheelEventConfig

	def wheelEvent( self, ev ):
		if self.hasFocus() and not self.ignoreWheelEvent:
			super(FieldEditorSpinBox, self).wheelEvent( ev )
		else:
			ev.ignore()

##----------------------------------------------------------------##
class FieldEditorDoubleSpinBox(QtWidgets.QDoubleSpinBox):
	def __init__(self, *arg):
		super(FieldEditorDoubleSpinBox, self).__init__( *arg )
		# self.setButtonSymbols( QtWidgets.QAbstractSpinBox.NoButtons )
		self.setFocusPolicy( Qt.StrongFocus )
		self.setLineEdit( FieldEditorLineEdit( self ) )
		self.ignoreWheelEvent = False

	def focusInEvent( self, ev ):
		super(FieldEditorDoubleSpinBox, self).focusInEvent( ev )
		self.selectAll()
		self.setFocusPolicy( Qt.WheelFocus )

	def focusOutEvent( self, ev ):
		super(FieldEditorDoubleSpinBox, self).focusOutEvent( ev )
		self.setFocusPolicy( Qt.StrongFocus )

	def setWheelEventConfig( self, wheelEventConfig ):
		self.ignoreWheelEvent = wheelEventConfig
		
	def wheelEvent( self, ev ):
		if self.hasFocus() and not self.ignoreWheelEvent:
			super(FieldEditorDoubleSpinBox, self).wheelEvent( ev )
		else:
			ev.ignore()

##----------------------------------------------------------------##
class DraggableLabel( FieldEditorLabel ):
	dragged = QtCore.Signal( int )

	def __init__( self, *args ):
		super( DraggableLabel, self ).__init__( *args )
		self.dragging = False
		self.x0 = 0
		self.setCursor( Qt.PointingHandCursor )

	def mousePressEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			self.dragging = True
			self.grabMouse()
			self.x0 = ev.x()
		elif ev.button() == Qt.RightButton:
			if self.fieldEditor:
				self.fieldEditor.notifyContextMenuRequested()

	def mouseReleaseEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			if self.dragging:
				self.dragging = False
				self.releaseMouse()

	def mouseMoveEvent( self, ev ):
		if self.dragging:
			delta = ev.x() - self.x0
			self.x0 = ev.x()
			self.dragged.emit( delta )

##----------------------------------------------------------------##
class FieldEditorSlider(QtWidgets.QSlider):
	def focusInEvent( self, ev ):
		super(FieldEditorSlider, self).focusInEvent( ev )
		self.setFocusPolicy( Qt.WheelFocus )

	def focusOutEvent( self, ev ):
		super(FieldEditorSlider, self).focusOutEvent( ev )
		self.setFocusPolicy( Qt.StrongFocus )

	def wheelEvent( self, ev ):
		if self.hasFocus():
			super(FieldEditorSlider, self).wheelEvent( ev )
		else:
			ev.ignore()

# ##----------------------------------------------------------------##
class FieldEditorSliderBox(QtWidgets.QWidget):
	valueChanged = QtCore.Signal( float )

	def __init__( self, *args ):
		super( FieldEditorSliderBox, self ).__init__( *args )
		layout = QtWidgets.QHBoxLayout()
		self.setLayout( layout )
		self.text   = FieldEditorLineEdit( self )
		self.text.setText( '0' )
		self.slider = FieldEditorSlider( self )
		self.slider.setOrientation( Qt.Horizontal )		
		layout.setSpacing(5)
		layout.setContentsMargins(0,0,0,0)
		layout.addWidget( self.text )
		layout.addWidget( self.slider )
		layout.setStretchFactor( self.text, 1 )
		layout.setStretchFactor( self.slider, 2 )
		self.slider.valueChanged.connect( self.onSliderChanged )
		self.numberType = int
		self.text.editingFinished.connect( self.onTextEditingFinished )
		self.refreshing = False
		self._value = 0.0
		self.minValue = 0
		self.maxValue = 100
		self.updateSliderStep()

	def setReadOnly( self, readonly = True ):
		self.text.setReadOnly( readonly )
		self.slider.setEnabled( not readonly )

	def setNumberType( self, t ):
		self.numberType = t

	def onSliderChanged( self, v ):
		if self.refreshing: return
		self.setValue( v*self.sliderUnit + self.minValue )

	def setRange( self, minv, maxv ):		
		self.minValue = minv or 0
		self.maxValue = maxv or 100
		self.updateSliderStep()

	def updateSliderStep( self ):
		diff = self.maxValue - self.minValue
		if diff==0: diff = 1
		w = self.slider.width()
		self.slider.setMinimum( 0 )
		self.slider.setMaximum( w )
		self.sliderUnit = diff / float( w )
		self.refreshing = True
		self.slider.setValue( int( (self._value - self.minValue)/self.sliderUnit ) )
		self.refreshing = False

	def setValue( self, v ):
		if not v: v = 0
		if self.numberType == int:
			v = int( v )
		self._value = v
		self.valueChanged.emit( self._value )
		self.refreshing = True
		self.slider.setValue( int( (v - self.minValue)/self.sliderUnit ) )
		if self.numberType == int:
			self.text.setText( '%d' % v )
		else:
			self.text.setText( '%.2f' % v )
		self.refreshing = False

	def value( self ):
		return self._value

	def onTextEditingFinished( self ):
		try:
			t = self.text.text()
			if self.numberType == int:
				value = int( t )
			else:
				value = float( t )
		except:
			value = 0
		self.setValue( value )

	def resizeEvent( self, ev ):
		self.updateSliderStep()		

