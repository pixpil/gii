from gii.core.model import *

from .PropertyEditor import FieldEditor, registerSimpleFieldEditorFactory
from gii.SearchView import requestSearchView
from gii.qt.IconCache  import getIcon

from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtCore import Qt

##----------------------------------------------------------------##
class ActionFieldButton( QtWidgets.QToolButton ):
	def sizeHint( self ):
		return QtCore.QSize( 20, 20)

##----------------------------------------------------------------##
class ActionFieldEditor( FieldEditor ):
	def setTarget( self, parent, field ):
		super( ActionFieldEditor, self ).setTarget( parent, field )
		t = field.getType()
		self.actionName    = t.actionName

	def get( self ):
		pass
		
	def set( self, value ):
		pass
		
	def setValue( self, value ):		
		pass

	def initLabel( self, label, container ):
		self.label = label
		self.labelWidget = QtWidgets.QLabel( container )
		self.labelWidget.setText( '' )
		self.labelWidget.setMinimumSize( 50, 16 )
		self.labelWidget.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Expanding
			)
		return self.labelWidget

	def initEditor( self, container ):
		self.button = ActionFieldButton( container )
		self.button.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Expanding
			)
		self.button.setToolButtonStyle( Qt.ToolButtonTextBesideIcon )
		self.button.setText( self.label )
		icon = self.getOption( 'icon', 'play' )
		self.button.setIcon( getIcon(icon) )
		self.button.clicked.connect( self.doAction )
		return self.button

	def doAction( self ):
		self.notifyChanged( True )
		self.notifyObjectChanged()

	def setFocus( self ):
		self.button.setFocus()

registerSimpleFieldEditorFactory( ActionType, ActionFieldEditor )

