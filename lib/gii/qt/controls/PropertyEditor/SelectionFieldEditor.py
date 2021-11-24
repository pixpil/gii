from gii.core.model import *

from .PropertyEditor import FieldEditor, FieldEditorFactory, registerFieldEditorFactory
from gii.SearchView import requestSearchView

from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtCore import Qt

from .EnumFieldEditor import EnumFieldEditor

##----------------------------------------------------------------##
class SelectionFieldEditor( EnumFieldEditor ):
	def setTarget( self, parent, field ):
		super( EnumFieldEditor, self ).setTarget( parent, field )
		self.selectionFunc = field.getOption( 'selection' )

	def get( self ):
		#TODO
		pass

	def set( self, value ):		
		self.value = value
		if value is None:
			self.button.setText('')
			return
		selections = self.selectionFunc( self.getTarget() ) #find selection name
		if selections:
			for item in list(selections.values()):
				itemName, itemValue = item[1], item[2]
				if value == itemValue:
					self.button.setText( itemName )
					return
		self.button.setText('<???>')

	def openSearchView( self ):
		requestSearchView( 
			context      = 'scene',
			type         = None,
			multiple_selection = False,
			on_selection = self.onSearchSelection,
			on_cancel    = self.onSearchCancel,
			on_search    = self.onSearch,
			initial      = self.value
			)

	def onSearch( self, typeId, context, option ):
		selections = self.selectionFunc( self.getTarget() )
		entries = []
		if selections:
			for item in list(selections.values()):
				itemName, itemValue = item[1], item[2]
				entry = ( itemValue, itemName, '', None )
				entries.append( entry )			
		return entries


##----------------------------------------------------------------##
class SelectionFieldEditorFactory( FieldEditorFactory ):
	def getPriority( self ):
		return 10

	def build( self, parentEditor, field, context = None ):
		selection = field.getOption( 'selection', None )
		if selection:
			editor = SelectionFieldEditor( parentEditor, field )
			return editor
		return None

registerFieldEditorFactory( SelectionFieldEditorFactory() )
