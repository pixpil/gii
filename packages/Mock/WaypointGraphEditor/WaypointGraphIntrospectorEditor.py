from gii.core import  *
from gii.SceneEditor.Introspector   import CommonObjectEditor, registerObjectEditor
from gii.qt.controls.GenericListWidget import GenericListWidget
from gii.qt.controls.PropertyEditor import PropertyEditor

from qtpy import QtWidgets, QtGui, QtCore, uic
from qtpy.QtCore import Qt
from qtpy.QtCore import QEventLoop, QEvent, QObject


from mock import _MOCK, isMockInstance, getMockClassName
from mock.SceneGraphEditor.EntityEditor import ComponentEditor, registerMOCKObjectEditor


##----------------------------------------------------------------##
def getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


##----------------------------------------------------------------##
class WaypointEditorWidget( QtWidgets.QWidget ):
	def __init__( self, **args ):
		super( WaypointEditorWidget, self ).__init__( **args )

class WaypointListWidget( GenericListWidget ):
	def getNodes( self ):
		return self.parentEditor.getWaypoints()

	def updateItemContent( self, item, node, **options ):
		item.setText( repr(node) )


##----------------------------------------------------------------##
class WaypointGraphInspectorEditor( ComponentEditor ): #a generic property grid 	
	def initWidget( self, container, objectContainer ):
		grid = super( WaypointGraphInspectorEditor, self ).initWidget( container, objectContainer )
		self.waypointList = WaypointListWidget()
		self.waypointList.parentEditor = self
		return [ grid, self.waypointList ]

	def setTarget( self, target ):
		super( WaypointGraphInspectorEditor, self ).setTarget( target )
		self.waypointList.rebuild()

	def getWaypoints( self ):
		return []

##----------------------------------------------------------------##
registerMOCKObjectEditor( 'WaypointGraph', WaypointGraphInspectorEditor )

