import os
##----------------------------------------------------------------##
from gii.core     import *
from gii.qt.controls.PropertyEditor import PropertyEditor
from gii.qt.controls.Menu import MenuManager
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor
from gii.qt.dialogs   import alertMessage, requestConfirm

from qtpy        import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore import Qt, QEventLoop, QEvent, QObject, Signal, Slot

from gii.SceneEditor  import SceneEditorModule
from util.IDPool  import IDPool

from gii.qt.IconCache         import getIcon
from mock import _MOCK

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
class SerializableEditor( SceneEditorModule ):
	"""docstring for SerializableEditor"""

	name = 'serializable_editor'
	dependency = [ 'mock', 'qt' ]

	def __init__(self):
		self.instances      = []
	
	def onLoad(self):		
		self.idPool = IDPool()
		
	def onStart( self ):
		pass

	def openAsset( self, target ):
		instance = self.findInstances( target )
		if not instance:
			instance = self.createInstance( target )
		else:
			instance.refresh()

	def createInstance( self, target ):
		#todo: pool
		id = self.idPool.request()
		title = target.getNodePath()
		container = self.requestDocumentWindow('SerializableEditor-%d'%id,
				title   = title,
				minSize = (200,100)
		)
		instance = SerializableEditorInstance(id)
		instance.parentModule = self
		instance.createWidget( container )
		instance.setTarget( target )
		self.instances.append( instance )
		container.show()
		return instance

	def findInstances(self, targetNode):
		for ins in self.instances:
			if ins.targetNode == targetNode:
				return ins
		return None

	def removeInstance( self, instance ):
		self.instances.remove( instance )

	def refresh( self, targetNode = None, context = None ):
		for ins in self.instances:
			if not targetNode or ins.hasTarget( targetNode ):
				ins.refresh()

##----------------------------------------------------------------##

class SerializableEditorInstance( object ):
	def __init__(self, id):
		self.id = id
		self.targetNode  = None
		self.targetAsset = None
		self.container = None
		self.body      = None
		self.dataDirty = False

	def createWidget( self, container ):
		self.container = container
		self.container.setCallbackOnClose( self.onClose )
		self.toolbar = self.container.addToolBar()
		self.toolbar.setIconSize( QtCore.QSize( 16, 16 ) )
		self.actionSave   = self.toolbar.addAction( getIcon( 'save' ), 'Save' )
		self.actionLocate = self.toolbar.addAction( getIcon( 'search' ), 'Locate' )
		self.actionSave.setEnabled( False )

		self.actionSave.triggered.connect( self.onActionSave )
		self.actionLocate.triggered.connect( self.onActionLocate )

		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('SerializableEditor.ui')
		)

		self.scroll = scroll = addWidgetWithLayout(
			QtWidgets.QScrollArea( window.containerProperty ),
			window.containerProperty
		)

		scroll.verticalScrollBar().setStyleSheet('width:4px')
		scroll.setWidgetResizable( True )
		self.propertyEditor = PropertyEditor( scroll )
		scroll.setWidget( self.propertyEditor )
		self.propertyEditor.propertyChanged.connect( self.onPropertyChanged )

	def setTarget(self, targetNode):
		self.targetNode = targetNode
		data = _MOCK.loadAsset( targetNode.getPath() )
		if data:
			asset, luaAssetNode = data
			self.targetAsset = asset
			self.propertyEditor.setTarget( asset )
		else:
			self.targetAsset = None
			self.propertyEditor.setTarget( None )

	def refresh( self ):
		self.propertyEditor.refreshAll()

	def hasTarget( self, targetNode ):
		return self.targetNode == targetNode

	def resetData( self ):
		if self.targetAsset and self.targetNode:
			path = self.targetNode.getAbsFilePath()
			_MOCK.deserializeFromFile( self.targetAsset, path )
			self.actionSave.setEnabled( False )
			self.dataDirty = False

	def saveData( self ):
		if self.targetAsset:
			path = self.targetNode.getAbsFilePath()
			_MOCK.serializeToFile( self.targetAsset, path )
			self.actionSave.setEnabled( False )
			self.dataDirty = False

	def onActionSave( self ):
		self.saveData()

	def onActionLocate( self ):
		if self.targetNode:
			browser = app.getModule( 'asset_browser' )
			if browser:
				browser.locateAsset( self.targetNode )

	def onPropertyChanged( self, id, value ):
		self.dataDirty = True
		self.actionSave.setEnabled( True )

	def onClose( self ):
		if self.dataDirty:
			res = requestConfirm( 'data modified!', 'save data before close?' )
			if res == None: #cancel
				return False

			elif res == True:   #save
				self.onActionSave()

			elif res == False: #no save
				self.resetData()
		self.parentModule.removeInstance( self )
		return True
