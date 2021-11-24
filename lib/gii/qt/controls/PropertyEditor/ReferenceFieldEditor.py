from gii.core import *
from gii.core.model import *
from gii.qt.dialogs import alertMessage

from .PropertyEditor import FieldEditor, registerSimpleFieldEditorFactory
from .SearchFieldEditor import SearchFieldEditorBase

##----------------------------------------------------------------##
class ReferenceFieldEditor( SearchFieldEditorBase ):	
	def getSearchContext( self ):
		return "scene"

	def gotoObject( self ):
		signals.emit( 'selection.hint', self.target )

	def clearObject( self ):
		self.setValue( False )

	def syncSelection( self ):
		sceneGraphEditor = app.getModule( 'scenegraph_editor' )
		if sceneGraphEditor:
			entries = self.enumerateSearch()
			objects = [ entry.getObject() for entry in entries ]
			for entity in sceneGraphEditor.getSelection():
				for obj in objects:
					if obj == entity or obj[ '_entity' ] == entity:
						self.setValue( obj )
						return
		alertMessage( 'No matched object', 'No matched entity/component selected' )

##----------------------------------------------------------------##

registerSimpleFieldEditorFactory( ReferenceType, ReferenceFieldEditor )
