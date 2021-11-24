import random
import logging
import os.path

##----------------------------------------------------------------##
from gii.core        import app, signals, JSONHelper
from gii.qt          import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter
from gii.qt.controls.GraphicsView.YEdGraphView import YEdGraphView
from gii.qt.dialogs   import requestString, alertMessage, requestConfirm
from gii.moai.MOAIRuntime import MOAILuaDelegate
from gii.SceneEditor      import SceneEditorModule, getSceneSelectionManager
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor

##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt

##----------------------------------------------------------------##
from gii.SearchView       import requestSearchView, registerSearchEnumerator

from util.YEd import *

##----------------------------------------------------------------##
from mock import _MOCK, isMockInstance
##----------------------------------------------------------------##


_GII_PORTAL_DATA_NAME = 'portal_data.json'
_GII_PORTAL_DATA_EXPORT_NAME = 'portal_data'

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

# ##----------------------------------------------------------------##
# def getScenePortalPriority( sceneNode, default = 0 ):
# 	n = sceneNode
# 	while n:
# 		p = n.getMetaData( 'scene_portal_priority', None )
# 		if p: return p
# 		n = n.getParent()
# 	return default

##----------------------------------------------------------------##
class ScenePortalGraphView( YEdGraphView ):
	def onNodeDClicked( self, item ):
		node = item.node
		fullname = node.getFullLabel()
		if node.isGroup():
			app.getModule( 'scene_portal_manager' ).locatePortalGroup( fullname )
		else:		
			app.getModule( 'scene_portal_manager' ).locatePortal( fullname )

##----------------------------------------------------------------##
class ScenePortalManager( SceneEditorModule ):
	name = 'scene_portal_manager'
	dependency = [ 'mock' ]

	def onLoad( self ):
		#UI
		self.container = self.requestDockWindow( 'ScenePortalManager',
			title     = 'Scene Portals',
			size      = (120,120),
			minSize   = (120,120),
			dock      = 'left',
			toolWindow =  False
		)

		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('container.ui')
		)

		#Components
		leftLayout = QtWidgets.QVBoxLayout( window.containerLeft )
		leftLayout.setSpacing( 0 )
		leftLayout.setContentsMargins( 0 , 0 , 0 , 0 )

		rightLayout = QtWidgets.QVBoxLayout( window.containerRight )
		rightLayout.setSpacing( 0 )
		rightLayout.setContentsMargins( 0 , 0 , 0 , 0 )

		self.treeGraphsFilter = GenericTreeFilter( window.containerRight )
		self.treeGraphsFilter.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
		self.treeGraphs = ScenePortalGraphListWidget( window.containerLeft )
		self.treeGraphsFilter.setTargetTree( self.treeGraphs )
		self.treeGraphs.setIndentation( 0 )
		self.toolbarGraph = QtWidgets.QToolBar( window.containerLeft )
		self.toolbarGraph.setOrientation( Qt.Horizontal )
		self.toolbarGraph.setMaximumHeight( 32 )

		self.graphView = ScenePortalGraphView( 
			parent = window.containerRight,
			use_gl = False,
			antialias = True
		)

		leftLayout.addWidget( self.toolbarGraph )
		leftLayout.addWidget( self.treeGraphsFilter )
		leftLayout.addWidget( self.treeGraphs )

		rightLayout.addWidget( self.graphView )

		self.addToolBar( 'scene_portal_graph', self.toolbarGraph )
		self.addTool( 'scene_portal_graph/refresh', label = 'Refresh', icon = 'refresh' )
		self.addTool( 'scene_portal_graph/----' )
		self.addTool( 'scene_portal_graph/add_graph',      label = 'Add', icon = 'add' )
		self.addTool( 'scene_portal_graph/remove_graph',   label = 'Remove', icon = 'remove' )

		self.addMenuItem(
			'main/scene/rebuild_portal_registry', 
			dict( label = 'Rebuild Portal Data' )
		)

		self.addMenuItem(
			'main/scene/portal_jump', 
			dict( label = 'Portal Jump', shortcut = 'Ctrl+Alt+J' )
		)

		
		signals.connect( 'selection.changed', self.onSelectionChanged )
		signals.connect( 'scene.change',      self.onSceneChange     )

		self.portalRegistry = None
		self.showAllScenePortals = False
		self.updatingSelection = False

	def onStart( self ):
		signals.connect( 'asset.register',   self.onAssetRegister )
		signals.connect( 'asset.unregister', self.onAssetUnregister )
		signals.connect( 'asset.modified',   self.onAssetModified )
		self.loadRegistry()

	def onAppReady( self ):
		self.treeGraphs.rebuild()

	def onStop( self ):
		self.saveRegistry()

	def clearRegistry( self ):
		self.portalRegistry = {}

	def loadRegistry( self ):
		self.portalRegistry = JSONHelper.tryLoadJSON(
			self.getProject().getGameConfigPath( _GII_PORTAL_DATA_NAME ),
			'portal data'
		)
		if not self.portalRegistry:
			self.portalRegistry = {}
			self.scanPortals()

	def saveRegistry( self ):
		JSONHelper.trySaveJSON(
			self.portalRegistry, 
			self.getProject().getGameConfigPath( _GII_PORTAL_DATA_NAME ),
			'portal data' 
		)
		reg = _MOCK.getScenePortalRegistry()
		reg.markDirty( reg )

	def scanPortals( self ):
		assetLib = self.getAssetLibrary()
		for assetNode in assetLib.iterAssets():
			if assetNode.getType() == 'scene':
				self.processScenePortal( assetNode )
		self.saveRegistry()

	def clearScenePortal( self, scenePath ):
		registry = self.portalRegistry
		toRemove = []
		for key, entry in list(registry.items()):
			if entry[ 'scene' ] == scenePath: toRemove.append( key )
		for key in toRemove:
			del registry[ key ]

	def processScenePortal( self, sceneNode ):
		if sceneNode.getType() != 'scene': return
		self.clearScenePortal( sceneNode.getPath()  )
		if sceneNode.hasTag( 'deprecated' ): return
		registry = self.portalRegistry
		sceneFilePath = sceneNode.getFilePath()
		if os.path.isfile( sceneFilePath ):
			sceneData = JSONHelper.tryLoadJSON( sceneFilePath )
		elif os.path.isdir( sceneFilePath ):
			sceneData = JSONHelper.tryLoadJSON( sceneFilePath + '/scene_index.json' )

		configData = sceneData and sceneData.get( 'config', None )
		if not configData: return
		managerData = configData.get( 'managers', None )
		if not managerData: return
		scenePortalData = managerData.get( 'ScenePortalManager', None )
		if not scenePortalData: return
		scenePath = sceneNode.getPath()
		prior = sceneNode.getInheritedMetaData( 'scene_portal_priority', 0 )
		for portalData in scenePortalData.get( 'portals', [] ):
			name      = portalData[ 'name' ]
			fullname  = portalData[ 'fullname' ]
			prevEntry = registry.get( fullname, None )
			if prevEntry:
				prevScene = prevEntry[ 'scene' ]
				if prevScene != scenePath:
					prior0 = prevEntry[ 'priority' ]
					if prior < prior0:
						logging.info( 'ignore duplicated portal(low priority): %s @ %s' % ( fullname,  scenePath ) )
						continue
					elif prior == prior0:
						#TODO: warn about duplicated portal
						logging.warning( 
							'duplicated portal ID: %s, found in %s and %s' % ( fullname, scenePath, prevScene ) )
						continue
			newEntry = {
				'fullname' : fullname,
				'name'     : name,
				'scene'    : scenePath,
				'data'     : portalData,
				'priority' : prior
			}
			registry[ fullname ] = newEntry
			logging.info( 'add portal: %s @ %s' % ( fullname,  scenePath ) )

	def locatePortalGroup( self, groupName ):
		registry = _MOCK.getScenePortalRegistry()
		scenePath = registry.getPortalGroupDefaultScene( registry, groupName )
		if not scenePath:
			alertMessage( 'No scene for portal group', 'No default scene found for group:' + groupName )
			return False

		node = self.getAssetLibrary().getAssetNode( scenePath )
		if not node:
			alertMessage( 'No scene found', 'Target scene not found:' + scenePath )
			return False

		node.edit()

	def locatePortal( self, portalInfo, select = False ):
		if self.updatingSelection: return
		if isinstance( portalInfo, str ): #ID?
			registry = _MOCK.getScenePortalRegistry()
			portalInfo = registry.getPortalInfo( registry, portalInfo )
		if not portalInfo:
			return False
		scenePath = portalInfo.scene
		sceneNode = self.getAssetLibrary().getAssetNode( scenePath )
		if sceneNode:
			guid = portalInfo.data.guid
			editor = self.getModule( 'scenegraph_editor' )
			if editor.getActiveSceneNode() == sceneNode:
				editor.locateEntityByGUID( guid )
			else:
				# if editor.getActiveSceneNode() and ( not requestConfirm( 'Changing Scene', 'opening another scene, proceed?' ) ):
				# 	return
				callLocating = signals.callOnce( 'scene.change', lambda: editor.locateEntityByGUID( guid ) )
				if not editor.openScene( sceneNode ):
					signals.dropCall( callLocating )

	def setCurrentGraph( self, graphNode ):
		self.currentGraphNode = graphNode
		if graphNode:
			parser = YEdGraphMLParser()
			assetPath = graphNode.path
			assetNode = self.getAssetLibrary().getAssetNode( assetPath )
			g = parser.parse( assetNode.getAbsFilePath() )
			if g:
				self.graphView.loadGraph( g )
				self.graphView.fitAll()
			else:
				self.graphView.clear()

	def locateGraph( self, graph ):
		self.getModule( 'asset_browser' ).locateAsset( graph.path )

	def getPortalList( self ):
		if self.showAllScenePortals:
			registry = _MOCK.getScenePortalRegistry()
			return [ info for info in list(registry.portals.values()) ]
		else:
			return self.getCurrentScenePortals()

	def getCurrentScenePortals( self ):
		registry = _MOCK.getScenePortalRegistry()
		editor = self.getModule( 'scenegraph_editor' )
		sceneNode = editor.getActiveSceneNode()
		if not sceneNode: return []
		result = []
		for info in list(registry.portals.values()):
			if info.scene == sceneNode.getPath():
				result.append( info )
		return result

	def onSelectionChanged( self, selection, key ):
		#TODO
		pass

	def onSceneChange( self ):
		pass

	def onAssetRegister( self, assetNode ):
		if assetNode.getType() == 'scene':
			self.processScenePortal( assetNode )
			self.saveRegistry()

	def onAssetUnregister( self, assetNode ):
		if assetNode.getType() == 'scene':
			self.clearScenePortal( assetNode.getPath() )
			self.saveRegistry()

	def onAssetModified( self, assetNode ):
		if assetNode.getType() == 'scene':
			self.processScenePortal( assetNode )
			self.saveRegistry()

	def enumerateSelectableGraphs( self, typeId, context, option ):
		result = []
		registry = _MOCK.getScenePortalRegistry()
		for asset in self.getAssetLibrary().iterAssets():
			if asset.getType() != 'scene_portal_graph': continue
			path = asset.getPath()
			if registry.hasGraph( registry, path ): continue
			entry = ( asset, path, 'portal_graph', 'portal_graph' )
			result.append( entry )
		return result

	def promptProtalJump( self ):
		entries = [ ( portal.id, portal.id, 'portal', 'portal' ) for portal in self.getCurrentScenePortals() ]
		def _locateConnectedPortal( id ):
			if not self.locateConnectedPortal( id ):
				alertMessage( 'No connection', 'No connected portal found' )
		def _locatePortal( selections ):
			pass
	
		requestSearchView( 
			info         = 'select portal to jump',
			selections   = entries,
			on_selection = _locateConnectedPortal,
			on_change    = _locatePortal
		)

	def locateConnectedPortal( self, portalId ):
		registry = _MOCK.getScenePortalRegistry()
		targetId = registry.findConnectedPortal( registry, portalId )
		if targetId:
			self.locatePortal( targetId )
			return True
		return False

	def addGraph( self, assetNode ):
		registry = _MOCK.getScenePortalRegistry()
		graphNode = registry.addGraph( registry, assetNode.getPath() )
		self.treeGraphs.addNode( graphNode )

	def removeGraph( self, graphNode ):
		registry = _MOCK.getScenePortalRegistry()
		registry.removeGraph( registry, graphNode.getPath( graphNode ) )
		self.treeGraphs.removeNode( graphNode )

	def onTool( self, tool ):
		name = tool.name
		if name == 'add_graph':
			requestSearchView( 
				info    = 'select portal graph to add',
				context = 'portal_graph',
				on_search = self.enumerateSelectableGraphs,
				on_selection = self.addGraph
			)

		elif name == 'remove_graph':
			for node in self.treeGraphs.getSelection():
				self.removeGraph( node )

		elif name == 'refresh':
			self.treeGraphs.rebuild()

	def onMenu( self, menu ):
		if menu.name == 'rebuild_portal_registry':
			self.clearRegistry()
			self.scanPortals()
			print('done')
		elif menu.name == 'portal_jump':
			self.promptProtalJump()

##----------------------------------------------------------------##
class ScenePortalGraphListWidget( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Graph Path',-1) ]

	def getRootNode( self ):
		return _MOCK.getScenePortalRegistry()

	def getNodeParent( self, node ):
		if node == self.getRootNode(): return None
		return self.getRootNode()

	def getNodeChildren( self, node ):
		if node == self.getRootNode():
			return [ graph for graph in list(node.graphs.values()) ]
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		if node == self.getRootNode(): return
		item.setIcon( 0, getIcon( 'portal_graph' ) )
		path = node.path
		name = os.path.basename( path )
		if name.endswith( '.portal.graphml' ):
			shortName = name[:-15]
		else:
			shortName, ext = os.path.splitext( name )
		item.setText( 0, shortName )

	def onItemSelectionChanged( self ):
		for node in self.getSelection():
			app.getModule( 'scene_portal_manager' ).setCurrentGraph( node )
			break

	def onItemActivated( self, item, col ):
		node = item.node
		app.getModule( 'scene_portal_manager' ).locateGraph( node )


##----------------------------------------------------------------##
def ScenePortalSearchEnumerator( typeId, context, option ):
	if not context in [ 'scene_portal' ] : return None
	game = _MOCK.game
	#TODO
	return []
	