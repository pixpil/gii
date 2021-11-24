from .PropertyEditor import FieldEditor, registerSimpleFieldEditorFactory
from .FieldEditorControls import *

from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtCore import Qt

##----------------------------------------------------------------##
class VecEditorWidget( QtWidgets.QWidget ):
	def __init__( self, dim, parent ):
		super(VecEditorWidget, self).__init__( parent )
		self.dim = dim
		layout = QtWidgets.QHBoxLayout( self )
		layout.setSpacing(0)
		layout.setContentsMargins(0,0,0,0)		

		self.fields = fields = []
		for i in range( dim ):
			field = FieldEditorDoubleSpinBox( self )
			field.setSizePolicy(
				QtWidgets.QSizePolicy.Expanding,
				QtWidgets.QSizePolicy.Expanding
				)
			field.setMinimumWidth( 40 )
			layout.addWidget( field )
			fields.append( field )

		self.setLayout( layout )

	def getValue( self ):
		return tuple( field.value() for field in self.fields  )

	def setValue( self, value ):
		if value:
			for i, v in enumerate( value ):
				if i >= self.dim: break
				self.fields[i].setValue( v )
		else:
			for field in self.fields:
				field.setValue( 0 )
		
	def setRange( self, min, max ):
		for field in  self.fields:
			field.setRange( min, max )

	def setSingleStep( self, step ):
		for field in  self.fields:
			field.setSingleStep( step )

	def setReadOnly( self, readonly ):
		for field in self.fields:
			field.setReadOnly( readonly )

		
##----------------------------------------------------------------##
class GenericVecFieldEdtior( FieldEditor ):
	def getDimension( self ):
		return 2

	def get( self ):
		return self.editor.getValue()

	def set( self, value ):
		self.editor.setValue( value )

	def onValueChanged( self, v ):
		return self.notifyChanged( self.get() )

	def setReadonly( self, readonly ):
		self.editor.setReadOnly( readonly )

	def initEditor( self, container )	:
		self.editor = VecEditorWidget( self.getDimension(), container )
		# self.editor.setMinimumSize( 50, 16 )
		minValue = self.getOption( 'min', -16777215.0 )
		maxValue = self.getOption( 'max',  16777215.0 )

		for field in  self.editor.fields:
			field.valueChanged.connect( self.onValueChanged )
			field.setRange( minValue, maxValue	)
			field.setSingleStep( self.getOption( 'step', 1 ) )
			field.setDecimals( self.getOption( 'decimals', 4 ) )

		return self.editor

##----------------------------------------------------------------##
class Vec2FieldEdtior( GenericVecFieldEdtior ):
	def getDimension( self ):
		return 2

registerSimpleFieldEditorFactory( 'vec2', Vec2FieldEdtior )

##----------------------------------------------------------------##
class Vec3FieldEdtior( GenericVecFieldEdtior ):
	def getDimension( self ):
		return 3

registerSimpleFieldEditorFactory( 'vec3', Vec3FieldEdtior )

##----------------------------------------------------------------##
class Vec4FieldEdtior( GenericVecFieldEdtior ):
	def getDimension( self ):
		return 4

registerSimpleFieldEditorFactory( 'vec4', Vec4FieldEdtior )
