import random
##----------------------------------------------------------------##
from gii.core        import app, signals
from gii.qt          import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter
from gii.moai.MOAIRuntime import MOAILuaDelegate
from gii.SceneEditor      import SceneEditorModule, getSceneSelectionManager
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor

##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt

##----------------------------------------------------------------##
from gii.SearchView       import requestSearchView, registerSearchEnumerator

##----------------------------------------------------------------##
from mock import _MOCK, isMockInstance
##----------------------------------------------------------------##


##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

def _fixDuplicatedName( names, name, id = None ):
	if id:
		testName = name + '_%d' % id
	else:
		id = 0
		testName = name
	#find duplicated name
	if testName in names:
		return _fixDuplicatedName( names, name, id + 1)
	else:
		return testName

##----------------------------------------------------------------##
class GlobalObjectManager( SceneEditorModule ):
	def __init__(self):
		super( GlobalObjectManager, self ).__init__()
		self.refreshScheduled = False

	def getName( self ):
		return 'global_object_manager'

	def getDependency( self ):
		return [ 'scene_editor', 'mock' ]

	def onLoad( self ):
		#UI
		self.window = self.requestDockWindow( 'GlobalObjectManager',
			title     = 'Global Objects',
			size      = (120,120),
			minSize   = (120,120),
			dock      = 'left'
			)

		#Components
		self.treeFilter = self.window.addWidget(
			GenericTreeFilter(), expanding = False
		)
		self.tree = self.window.addWidget( 
				GlobalObjectTreeWidget( 
					multiple_selection = True,
					editable           = True,
					drag_mode          = 'internal'
				)
			)
		self.treeFilter.setTargetTree( self.tree )

		self.tool = self.addToolBar( 'global_object_manager', self.window.addToolBar() )
		self.delegate = MOAILuaDelegate( self )
		self.delegate.load( _getModulePath( 'GlobalObjectManager.lua' ) )

		# self.creatorMenu=self.addMenu(
		# 	'global_object_create',
		# 	{ 'label':'Create Global Object' }
		# 	)

		self.addTool( 'global_object_manager/add',    label = 'Add', icon = 'add' )
		self.addTool( 'global_object_manager/remove', label = 'Remove', icon = 'remove' )
		self.addTool( 'global_object_manager/clone',  label = 'Clone', icon = 'clone' )
		self.addTool( 'global_object_manager/add_group',    label = 'Add Group', icon = 'add_folder' )
		self.addTool( 'global_object_manager/----' )
		self.addTool( 'global_object_manager/refresh',    label = 'Refresh', icon = 'refresh' )
		
		# self.addMenuItem( 'main/find/find_global_object', 
		# 	dict( label = 'Find In Global Objects', shortcut = 'ctrl+alt+f' ) )

		#SIGNALS
		signals.connect( 'moai.clean', self.onMoaiClean )

		signals.connect( 'global_object.added',   self.onObjectAdded )
		signals.connect( 'global_object.removed', self.onObjectRemoved )
		signals.connect( 'global_object.renamed', self.onObjectRenamed )

		if self.getModule('introspector'):
			from . import GlobalObjectNodeEditor

		registerSearchEnumerator( globalObjectNameSearchEnumerator )
		registerSearchEnumerator( globalObjectSearchEnumerator )

	def onAppReady( self ):
		self.tree.rebuild()
		self.tree.setColumnWidth( 0, 150 )

	def onMoaiClean( self ):
		self.tree.clear()

	def onTool( self, tool ):
		name = tool.name
		if name == 'add':
			requestSearchView( 
				info    = 'select global object class to create',
				context = 'global_object_class',
				on_selection = lambda objName: self.createGlobalObject( objName )				
				)

		if name == 'add_group':
			group = self.delegate.safeCall( 'addGroup' )
			self.tree.addNode( group )
			self.tree.editNode( group )
			self.tree.selectNode( group )

		elif name == 'remove':
			for node in self.tree.getSelection():
				self.doCommand( 'scene_editor/remove_global_object', target = node )
				self.tree.removeNode( node )

		elif name == 'refresh':
			self.scheduleRefreshObject()

	def onMenu( self, menu ):
		if menu.name == 'find_global_object':
			requestSearchView( 
				info    = 'search for global object',
				context = 'global_object',				
				on_selection = lambda node: self.selectObject( node, True )
				)

	def needUpdate( self ):
		return True
		
	def onUpdate( self ):
		if self.refreshScheduled :
			self.refreshScheduled = False
			self.delegate.safeCall( 'reloadObjects' )
			self.tree.rebuild()

	def scheduleRefreshObject( self ):
		self.refreshScheduled = True

	def selectObject( self, target, updateTree = False ):
		self.changeSelection( target )
		if updateTree:
			self.tree.blockSignals( True )
			self.tree.selectNode( None )
			if isinstance( target, list ):
				for e in target:
					self.tree.selectNode( e, add = True)
			else:
				self.tree.selectNode( target )
			self.tree.blockSignals( False )

	def renameObject( self, obj, name ):
		obj.setName( obj, name )

	def createGlobalObject( self, objName ):
		self.doCommand( 'scene_editor/create_global_object', name = objName )

	def reparentObject( self, sources, target ):
		if self.doCommand( 'scene_editor/reparent_global_object', 
			sources = sources,
			target = target ):
			return True

	def onObjectAdded( self, node, reason = 'new' ):
		self.tree.addNode( node )
		if reason == 'new':
			self.tree.editNode( node )
			self.tree.selectNode( node )

	def onObjectRemoved( self, node ):
		self.tree.removeNode( node )

	def onObjectRenamed( self, node, name ):
		self.tree.refreshNodeContent( node )

	
##----------------------------------------------------------------##
class GlobalObjectTreeWidget( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Name',200), ('Type', 80), ('',-1) ]

	def getRootNode( self ):
		return _MOCK.game.globalObjectLibrary.root

	def saveTreeStates( self ):
		for node, item in list(self.nodeDict.items()):
			node.__folded = item.isExpanded()

	def loadTreeStates( self ):
		for node, item in list(self.nodeDict.items()):
			folded = node.__folded or False
			item.setExpanded( not folded )

	def getNodeParent( self, node ): # reimplemnt for target node	
		return node.parent

	def getNodeChildren( self, node ):
		if node.type == 'group':
			return [ k for k in list(node.children.values()) ]
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		name = None
		if node.type == 'group':
			item.setIcon( 0, getIcon('folder') )
			item.setText( 0, node.name )
		else:
			item.setIcon( 0, getIcon('text') )
			item.setText( 0, node.name )
			item.setText( 1, node.objectType or '???' )
			#TODO: type
		
	def onItemSelectionChanged(self):
		selections = self.getSelection()
		app.getModule('global_object_manager').selectObject( selections )

	def onItemChanged( self, item, col ):
		obj = self.getNodeByItem( item )
		app.getModule('global_object_manager').renameObject( obj, item.text(0) )

	def dropEvent( self, ev ):		
		p = self.dropIndicatorPosition()
		pos = False
		if p == QtWidgets.QAbstractItemView.OnItem: #reparent
			pos = 'on'
		elif p == QtWidgets.QAbstractItemView.AboveItem:
			pos = 'above'
		elif p == QtWidgets.QAbstractItemView.BelowItem:
			pos = 'below'
		else:
			pos = 'viewport'
		
		if pos == 'above' or pos =='below':
			#TODO: reorder
			ev.setDropAction( Qt.IgnoreAction )
			return

		targetItem = self.itemAt( ev.pos() )
		
		if pos == 'on':
			targetObject = targetItem.node
		else:
			targetObject = 'root'
		
		if app.getModule('global_object_manager').reparentObject( self.getSelection(), targetObject ):
			ev.acceptProposedAction()
			self.rebuild()
		else:
			ev.setDropAction( Qt.IgnoreAction )

##----------------------------------------------------------------##
GlobalObjectManager().register()

##----------------------------------------------------------------##
		
def globalObjectNameSearchEnumerator( typeId, context, option ):
	if not context in [ 'global_object_class' ] : return None
	registry = _MOCK.getGlobalObjectClassRegistry()
	result = []
	for name in list(registry.keys()):
		entry = ( name, name, 'GlobalObjectCls', None )
		result.append( entry )
	return result

def globalObjectSearchEnumerator( typeId, context, option ):
	if not context in [ 'global_object' ] : return None
	game = _MOCK.game
	lib = game.getGlobalObjectLibrary( game )
	nodeList = lib.getNodeList( lib )
	result = []
	for node in list(nodeList.values()) :
		entry = ( node, node.fullName, 'GlobalObject', None )
		result.append( entry )
	return result
