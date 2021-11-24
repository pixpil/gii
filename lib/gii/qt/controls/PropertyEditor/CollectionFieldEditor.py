from gii.core.model import *

from .PropertyEditor import FieldEditor, registerFieldEditorFactory, FieldEditorFactory
from gii.SearchView import requestSearchView

from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtCore import Qt

##----------------------------------------------------------------##
class CollectionFieldButton( QtWidgets.QToolButton ):
	def sizeHint( self ):
		return QtCore.QSize( 20, 20)

##----------------------------------------------------------------##
class CollectionFieldEditor( FieldEditor ):
	def setTarget( self, parent, field ):
		super( CollectionFieldEditor, self ).setTarget( parent, field )
		t = field.getType()
		self.targetType    = t.itemType
		self.targetContext = None  #TODO
		self.value = None
		self.selectionFunc = field.getOption( 'selection', None )

	def get( self ):
		#TODO
		pass
		
	def set( self, value ):
		self.value = value
		if value:
			self.button.setText( '[...]' )
		else:
			self.button.setText( '[]' )
		
	def setValue( self, value ):		
		self.set( value )
		self.notifyChanged( value )

	def initEditor( self, container ):
		self.button = CollectionFieldButton( container )
		self.button.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Expanding
			)
		self.button.setText( '[]' )
		if self.getOption( 'readonly', False ):
			self.button.setEnabled( False )
		self.button.clicked.connect( self.openSearchView )
		return self.button

	def openSearchView( self ):
		if self.selectionFunc:
			requestSearchView( 
				context      = 'scene',
				type         = self.targetType,
				multiple_selection = True,
				on_selection = self.onSearchSelection,
				on_cancel    = self.onSearchCancel,
				on_search    = self.onSearch,
				initial      = self.value
				)
		else:
			requestSearchView( 
				context      = 'scene',
				type         = self.targetType,
				multiple_selection = True,
				on_selection = self.onSearchSelection,
				on_cancel    = self.onSearchCancel,
				initial      = self.value
				)

	def onSearchSelection( self, value ):
		self.setValue( value )
		self.setFocus()

	def onSearchCancel( self ):
		self.setFocus()

	def onSearch( self, typeId, context, option ):
		selections = self.selectionFunc( self.getTarget() )
		entries = []
		if selections:
			for item in list(selections.values()):
				itemName, itemValue = item[1], item[2]
				entry = ( itemValue, itemName, '', None )
				entries.append( entry )			
		return entries

	def setFocus( self ):
		self.button.setFocus()

##----------------------------------------------------------------##
class CollectionFieldEditorFactory( FieldEditorFactory ):
	def getPriority( self ):
		return 100

	def build( self, parentEditor, field, context = None ):
		dataType  = field._type
		while dataType:
			if dataType == CollectionType:
				
				return CollectionFieldEditor( parentEditor, field )
			dataType = getSuperType( dataType )
		return None

registerFieldEditorFactory( CollectionFieldEditorFactory() )

# registerSimpleFieldEditorFactory( CollectionType, CollectionFieldEditor )

