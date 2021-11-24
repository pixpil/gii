from gii.core import  *
from gii.SceneEditor.Introspector   import CommonObjectEditor, registerObjectEditor
from gii.qt.controls.PropertyEditor import PropertyEditor

from qtpy import QtWidgets, QtGui, QtCore, uic
from qtpy.QtCore import Qt
from qtpy.QtCore import QEventLoop, QEvent, QObject


from mock import _MOCK, isMockInstance, getMockClassName


##----------------------------------------------------------------##
def getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path
		
class GlobalObjectEditor( CommonObjectEditor ): #a generic property grid 	
	def setTarget( self, target ):
		super( GlobalObjectEditor, self ).setTarget( target )
		if target.type == 'object':
			self.getIntrospector().addObjectEditor( target.object )
		
	def onPropertyChanged( self, obj, id, value ):
		if id == 'name':
			signals.emit( 'global_object.renamed', obj, value )

registerObjectEditor( _MOCK.GlobalObjectNode, GlobalObjectEditor )