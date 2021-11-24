import logging

from .PropertyEditor import FieldEditor, registerSimpleFieldEditorFactory
from .FieldEditorControls import *

from gii.qt.controls.BitMaskEdit import BitMaskEdit
from gii.qt.controls.DirectionEdit import DirectionEdit

from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtCore import Qt

import re

##----------------------------------------------------------------##
class StringFieldEditor( FieldEditor ):
	def get( self ):
		return self.lineEdit.text()

	def set( self, value ):
		if type( value ) in ( str, str ):
			self.lineEdit.setText( value or '' )
		else:
			self.lineEdit.setText( '' )

	def initEditor( self, container ):
		self.lineEdit = FieldEditorLineEdit( container )
		self.lineEdit.setMinimumSize( 50, 16 )
		self.lineEdit.textEdited.connect( self.notifyChanged )
		return self.lineEdit

	def setReadonly( self, readonly ):
		self.lineEdit.setReadOnly( readonly )


##----------------------------------------------------------------##
class NumberFieldEditor( FieldEditor ):
	def get( self ):
		return self.control.value()

	def set( self, value ):
		if value is None: return
		self.control.setValue( value )

	def setReadonly( self, readonly ):
		self.control.setReadOnly( readonly )
		self.labelWidget.setEnabled( not readonly )

	def setWheelEventConfig( self, wheelEventConfig ):
		self.control.setWheelEventConfig( wheelEventConfig )

	def initEditor( self, container ):
		self.step = self.getOption( 'step', 1 )
		widget = self.getOption( 'widget', 'spin' )
		if widget == 'slider':
			self.control = self.initSlider( container )
		elif widget == 'direction':
			self.control = self.initDirectionEdit( container )
		elif widget in [ 'bitmask', 'bitmask32' ] :
			self.control = self.initBitMask( container, 32 )
		elif widget == 'bitmask16' :
			self.control = self.initBitMask( container, 16 )
		elif widget == 'bitmask8' :
			self.control = self.initBitMask( container, 8 )
		else: #if widget == 'spin'
			self.control = self.initSpinBox( container )
		return self.control

	def initLabel( self, label, container ):
		self.labelWidget = DraggableLabel( container )
		self.labelWidget.setText( label )
		self.labelWidget.setEditor( self )
		self.labelWidget.dragged.connect( self.onDragAdjust )
		return self.labelWidget

	def initSpinBox( self, container ):
		spinBox = None
		if self.getFieldType() == int:
			spinBox = FieldEditorSpinBox( container )
			step = int(self.step)
			if step <= 0: step = 1
			spinBox.setSingleStep( step )
		else:
			spinBox = FieldEditorDoubleSpinBox( container )
			spinBox.setDecimals( self.getOption( 'decimals', 4 )	)
			spinBox.setSingleStep( self.step	)
		#common part
		spinBox.setMinimumSize( 50, 16 )
		spinBox.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Expanding
			)
		#options
		minValue = self.getOption( 'min', -16777215.0 )
		maxValue = self.getOption( 'max',  16777215.0 )
		spinBox.setRange( minValue, maxValue	)
		spinBox.valueChanged.connect( self.notifyChanged )
		return spinBox

	def initBitMask( self, container, bitSize ):
		edit = BitMaskEdit( container )
		edit.setBitSize( bitSize )
		edit.valueChanged.connect( self.notifyChanged )
		return edit

	def initDirectionEdit( self, container ):
		edit = DirectionEdit( container )
		edit.setCCW( True )
		edit.setWrapMode( 0 )
		edit.setTopAngle( 90 )

		# edit.setCCW( self.getOption('rotation_mode','CCW') == 'CCW' )
		# edit.setWrapMode( self.getOption( 'wrap_mode', '180' ) == '180' and 0 or 1 )
		# edit.setTopAngle( self.getOption( 'top_angle', 90 ) )
		edit.valueChanged.connect( self.notifyChanged )
		return edit

	def initSlider( self, container ):
		sliderBox = FieldEditorSliderBox( container )
		sliderBox.setMinimumSize( 50, 16 )
		if not self.getOption( 'min' ) and not self.getOption( 'max' ):
			logging.warn( 'no range specified for slider field: %s' % self.field )
		minValue = self.getOption( 'min', 0.0 )
		maxValue = self.getOption( 'max', 100.0 )
		sliderBox.setRange( minValue, maxValue )
		sliderBox.setNumberType( self.getFieldType() )
		sliderBox.valueChanged.connect( self.notifyChanged )
		return sliderBox

	def onDragAdjust( self, delta ):
		v = self.get()
		self.set( v + delta * self.step )


##----------------------------------------------------------------##
class BoolFieldEditor( FieldEditor ):
	def get( self ):
		return self.checkBox.isChecked()

	def set( self, value ):		
		self.checkBox.setChecked( bool(value) )

	def setReadonly( self, readonly ):
		self.checkBox.setEnabled( not readonly )

	def onStateChanged( self, state ):
		return self.notifyChanged( bool( self.get() ) )

	def initEditor( self, container ):
		self.checkBox = QtWidgets.QCheckBox( container )
		self.checkBox.stateChanged.connect( self.onStateChanged )
		return self.checkBox


##----------------------------------------------------------------##

registerSimpleFieldEditorFactory( str,     StringFieldEditor )
registerSimpleFieldEditorFactory( str, StringFieldEditor )
registerSimpleFieldEditorFactory( int,     NumberFieldEditor )
registerSimpleFieldEditorFactory( float,   NumberFieldEditor )
registerSimpleFieldEditorFactory( bool,    BoolFieldEditor )

