import random
import os
import shutil
import os.path

from functools import cmp_to_key

from gii.core         import *
from gii.qt.dialogs   import requestString, alertMessage, requestConfirm
from gii.qt.helpers   import setClipboardText
from gii.SearchView   import requestSearchView, registerSearchEnumerator

from gii.SceneEditor  import SceneEditorModule

from gii.FileWatcher  import FileWatch

from qtpy            import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore     import Qt

from .AssetBrowserWidgets import *

from util import TagMatch
from gii.qt.helpers import repolishWidget

from util.SearchFilter import *
import re

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


##----------------------------------------------------------------##
class AssetBrowser( SceneEditorModule ):
	name       = 'asset_browser'
	dependency = ['qt', 'scene_editor','asset_support', 'file_watcher']

	def onLoad( self ):
		self.activeInstance = None
		self.instances = {}

		self.assetFilterViewModes = {}
		self.assetFilterRootGroup = SearchFilterGroup()
		self.assetFilterRootGroup.setName( '__root__' )

		#create menu
		signals.connect( 'module.loaded',        self.onModuleLoaded )		
		signals.connect( 'app.ready',            self.postAppReady )		

		self.creatorMenu = self.addMenu(
			'asset_create_context',
			{ 'label':'Create' }
		)

		self.findMenu( 'main/asset' ).addChild([
			'----',
			dict( name = 'open_asset', label = 'Open Asset', shortcut = 'ctrl+O' ),
			dict( name = 'create_asset', label = 'Create' ),
			dict( name = 'create_folder', label = 'Create Folder' ),
			'----',
			dict( name = 'refresh_remote', label = 'Refresh Remote Files' ),
			'----',
			dict( name = 'new_asset_search', label = 'New Asset Search' ),
		], self )

		self.findMenu( 'main/find' ).addChild([
			dict( name = 'find_asset', label = 'Find Asset', shortcut = 'ctrl+T' ),
			dict( name = 'find_asset_folder', label = 'Find Folder', shortcut = 'ctrl+alt+T' ),
			# dict( name = 'find_entity_for_asset', label = 'Find Entity Using Asset', shortcut = 'ctrl+shift+T' ),
		], self )
		

		self.assetContextMenu=self.addMenu('asset_context')
		self.assetContextMenu.addChild([
				{'name':'show_in_browser', 'label':'Show File'},
				{'name':'open_in_system', 'label':'Open In System'},
				{'name':'copy_node_path', 'label':'Copy Asset Path'},
				'----',
				{'name':'clone', 'label':'Clone'},
				'----',
				{'name':'reimport', 'label':'Reimport'},
				'----',
				{'name':'show_meta_data', 'label':'Show Meta Data File'},
				'----',
				{'name':'check_asset_remote', 'label':'Check Remote File'},
				'----',
				{'name':'deploy_set', 'label':'Set Deploy'},
				{'name':'deploy_unset', 'label':'Unset Deploy'},
				{'name':'deploy_disallow', 'label':'Disallow Deploy'},
				'----',
				{'name':'refresh_thumbnail', 'label':'Refresh Thumbnail'},
			])

		signals.connect( 'selection.changed', self.onSelectionChanged )

		
		self.browserInstance = self.createInstance( 'main' )
		self.activeInstance  = self.browserInstance
		self.currentContextSource = False
		self.newCreateNodePath = None
		self.loadConfig()

	def onStart( self ):		
		signals.connect( 'asset.index.pre_save', self.preAssetIndexSave )
		signals.connect( 'asset.index.save', self.onAssetIndexSave )
		self.assetFileWatch = AssetFileWatch()
		self.assetFileWatch.register()
		
		for instance in self.instances.values():
			instance.onStart()

	def postAppReady( self ):
		for instance in self.instances.values():
			instance.rebuildItemView()

	def onStop( self ):
		self.saveConfig()

	def onSelectionChanged( self, selection, context ):
		if context != 'asset': return
		pass
		
	def loadConfig( self ):
		#load filter
		filterData = self.getConfig( 'filters', None )
		if filterData:
			self.assetFilterRootGroup.load( filterData )
		self.assetFilterViewModes = self.getWorkspaceConfig( 'filter_view_modes', {} )

		#load instances
		instanceConfigs = self.getWorkspaceConfig( 'instances', {} )
		for key, config in instanceConfigs.items():
			mode = config.get( 'mode', 'search' )
			instance = self.requestInstance( key, mode = mode )
			instance.loadConfig( config )

	def saveFilterConfig( self ):
		filterData = self.assetFilterRootGroup.save()
		self.setConfig( 'filters', filterData )
		self.setWorkspaceConfig( 'filter_view_modes', self.assetFilterViewModes )

	def saveConfig( self ):
		#save filter
		self.saveFilterConfig()

		#save instances
		instanceConfigs = {}
		for key, instance in self.instances.items():
			config = instance.saveConfig()
			instanceConfigs[ key ] = config
		self.setWorkspaceConfig( 'instances', instanceConfigs )

		for instance in self.instances.values():
			instance.onStop()

	def onSetFocus( self ):
		self.getMainWindow().raise_()
		self.browserInstance.setFocus()

	def onUnload( self ):
		#persist expand state
		# self.treeFolder.saveTreeStates()
		pass

	def onModuleLoaded( self ):				
		for creator in self.getAssetLibrary().assetCreators:
			self.loadAssetCreator(creator)

	def loadAssetCreator( self, creator ):
		label     = creator.getLabel()
		assetType = creator.getAssetType()		

		def creatorFunc( value = None ):
			self.createAsset( creator )

		#insert into create menu
		self.creatorMenu.addChild({
				'name'     : 'create_'+assetType,
				'label'    : label,
				'on_click' : creatorFunc
			})

	#
	def requestInstance( self, key, **options ):
		if key == 'main':
			options[ 'main' ] = True
		
		instance = self.getInstance( key )
		if instance: return instance

		instance = AssetBrowserInstance( key, **options )
		instance.module = self
		self.instances[ key ] = instance
		instance.onLoad()
		return instance

	def getInstance( self, key ):
		return self.instances.get( key, None )

	def getMainInstance( self ):
		return self.browserInstance

	def getActiveInstance( self ):
		return self.activeInstance

	def setActiveInstance( self, instance ):
		if self.activeInstance == instance: return
		prevInstance = self.activeInstance
		self.activeInstance = instance
		if prevInstance:
			prevInstance.clearSelection()

	def getItemSelection( self ):
		return self.getActiveInstance().getItemSelection()

	def createInstance( self, key = None, **options ):
		if not key:
			key = generateGUID()
		if self.getInstance( key ):
			raise Exception( 'duplicated instance key: %s' % str(key) )

		return self.requestInstance( key, **options )

	def removeInstance( self, instance ):
		key = instance.instanceId
		assert key != 'main'
		instance.onStop()
		del self.instances[ key ]

	#asset operation
	def locateAsset( self, asset, focus = True, **options ):
		if isinstance( asset, str ): #path
			asset = self.getAssetLibrary().getAssetNode( asset )
		if not asset: return
		self.browserInstance.locateAsset( asset, focus, **options )

	def selectAsset( self, asset, **options ):
		if not asset: return
		self.browserInstance.selectAsset( asset, **options )
		
	def openAsset( self, asset, **option ):
		if isinstance( asset, str ): #path
			asset = self.getAssetLibrary().getAssetNode( asset )
		if not asset: return
		if option.get('select', True ):
			self.selectAsset( asset )
		asset.edit()

	def createAsset( self, creator, instance = None ):
		if isinstance( creator, str ):
			creator = self.getAssetLibrary().getAssetCreator( creator )

		label       = creator.getLabel()
		assetType   = creator.getAssetType()		

		instance = instance or self.browserInstance
		if instance.currentFolders:
			contextNode = instance.currentFolders[0]
		else:
			contextNode = None

		if not isinstance( contextNode, AssetNode ):
			contextNode = app.getAssetLibrary().getRootNode()

		instance.setFocus()
		name = requestString('Create Asset <%s>' % assetType, 'Enter asset name: <%s>' % assetType )
		if not name: return

		try:
			finalPath = creator.createAsset( name, contextNode, assetType )
			self.newCreateNodePath = finalPath
		except Exception as e:
			logging.exception( e )
			alertMessage( 'Asset Creation Error', repr(e) )

	def createRemoteFile( self, instance = None ):
		name = requestString( 'Add Remote File', 'Target Filename:' )
		if not name: return
		instance = instance or self.browserInstance
		if instance.currentFolders:
			contextNode = instance.currentFolders[0]
		else:
			contextNode = None
		if not isinstance( contextNode, AssetNode ):
			contextNode = app.getAssetLibrary().getRootNode()
		remoteFilePath = app.getAssetLibrary().createRemoteFile( contextNode, name )
		if remoteFilePath:
			AssetUtils.showFileInBrowser( remoteFilePath )

	def checkRemoteFile( self, instance = None ):
		instance = instance or self.browserInstance
		for n in instance.getItemSelection():
			if isinstance( n, AssetNode ):
				app.getAssetLibrary().scanSingleRemoteFile( n )
		print( 'remote file checked.' )

	def showRemoteFile( self, instance = None ):
		instance = instance or self.browserInstance
		for n in instance.getItemSelection():
			if isinstance( n, AssetNode ):
				remoteNode = n.getRemoteFileNode()
				if remoteNode:
					AssetUtils.showFileInBrowser( remoteNode.getAbsRuleFilePath() )

	#search
	def createAssetSearch( self, **options ):
		instance = self.createInstance( mode = 'search' )
		instance.onStart()
		instance.setFocus()
		

	def getFilterRootGroup( self ):
		return self.assetFilterRootGroup

	def setFilterViewMode( self, assetFilter, mode ):
		if assetFilter.getRoot() == self.getFilterRootGroup():
			self.assetFilterViewModes[ assetFilter.getId() ] = mode
	#menu
	def popupAssetContextMenu( self, node, instance = None, fromTree = False ):
		self.currentContextSource   = fromTree and 'tree' or 'item'
		self.currentContextInstance = instance
		if node:
			self.currentContextTargetNode = node
			deployState = node.deployState
			self.enableMenu( 'asset_context/open_in_system',  True )
			self.enableMenu( 'asset_context/copy_node_path',  True )
			self.enableMenu( 'asset_context/deploy_set',      deployState != True )
			self.enableMenu( 'asset_context/deploy_unset',    deployState != None )
			self.enableMenu( 'asset_context/deploy_disallow', deployState != False )
			self.enableMenu( 'asset_context/refresh_thumbnail', True )
			self.enableMenu( 'asset_context/check_asset_remote',    node.isRemoteFile() )
			self.findMenu('asset_context').popUp()
		else:
			self.enableMenu( 'asset_context/open_in_system', False )
			self.enableMenu( 'asset_context/copy_node_path', False )
			self.enableMenu( 'asset_context/deploy_set',     False )
			self.enableMenu( 'asset_context/deploy_unset',   False )
			self.enableMenu( 'asset_context/deploy_disallow',False )
			self.enableMenu( 'asset_context/refresh_thumbnail',False )
			self.enableMenu( 'asset_context/check_asset_remote',   False )
			self.findMenu('asset_context').popUp()

	def onMenu(self, menuNode):
		name = menuNode.name

		if name in ('deploy_set', 'deploy_disallow', 'deploy_unset'):
			if name   == 'deploy_set':      newstate = True
			elif name == 'deploy_disallow': newstate = False
			elif name == 'deploy_unset':    newstate = None
			s = self.currentContextInstance.getItemSelection()
			for n in s:
				if isinstance(n,AssetNode):
					n.setDeployState(newstate)

		elif name == 'check_asset_remote':
			self.checkRemoteFile( self.currentContextInstance )

		elif name == 'refresh_remote':
			app.getAssetLibrary().scanRemoteFiles()
			alertMessage( 'OK', 'Remote files refreshed', 'info' )
					
		elif name == 'reimport':
			if self.currentContextSource == 'tree':
				targetNode = self.currentContextTargetNode
				if targetNode:
					targets = [ targetNode ]
				else:
					targets = []
			else:
				targets = self.currentContextInstance.getItemSelection()
			for targetNode in targets:
				if isinstance( targetNode, AssetNode ):
					targetNode.markModified()
			app.getAssetLibrary().importModifiedAssets()

		elif name == 'clone':
			pass

		elif name == 'remove':
			pass

		elif name == 'show_in_browser':
			n = self.currentContextTargetNode
			if isinstance( n, AssetNode ):
				n.showInBrowser()

		elif name == 'show_meta_data':
			n = self.currentContextTargetNode
			if isinstance( n, AssetNode ):
				path = n.getMetaDataFilePath()
				if path and os.path.exists( path ):
					AssetUtils.showFileInBrowser(path)
				else:
					if requestConfirm( 'No Metadata', 'Create an empty file?' ):
						if not n.metadata:
							n.setMetaData( 'key', 'value' )
						n.metaDataDirty = True
						n.saveMetaDataTable()
						AssetUtils.showFileInBrowser(path)

		elif name == 'open_in_system':
			for n in self.currentContextInstance.getItemSelection():
				if isinstance( n, AssetNode ):
					n.openInSystem()
					break

		elif name == 'copy_node_path':
			text = ''
			for n in self.currentContextInstance.getItemSelection():
				if text: text += '\n'
				text += n.getNodePath()
			setClipboardText( text )

		elif name == 'refresh_thumbnail':
			text = ''
			for n in self.currentContextInstance.getItemSelection():
				n.clearThumbnails()
				for instance in self.instances.values():
					view = instance.getCurrentView()
					view.refreshNodeContent( n )

		elif name == 'create_asset':
			requestSearchView( 
				info    = 'select asset type to create',
				context = 'asset_creator',
				type    = 'scene',
				on_selection = self.createAsset
			)

		elif name == 'create_folder':
			self.createAsset( 'folder' )

		elif name == 'find_asset':
			requestSearchView( 
				info    = 'search for asset',
				context = 'asset',
				on_test      = self.selectAsset,
				on_selection = self.selectAsset
				)

		elif name == 'find_asset_folder':
			requestSearchView( 
				info    = 'search for asset',
				context = 'asset_folder',
				on_test      = self.selectAsset,
				on_selection = self.selectAsset
				)

		elif name == 'open_asset':
			requestSearchView( 
				info    = 'open asset',
				context = 'asset',
				on_test      = self.selectAsset,
				on_selection = self.openAsset
				)

		elif name == 'new_asset_search':
			self.createAssetSearch()

	def preAssetIndexSave( self ):
		self.assetFileWatch.stop()

	def onAssetIndexSave( self ):
		self.assetFileWatch.start()



##----------------------------------------------------------------##
class AssetBrowserInstance( object ):
	def __init__( self, instanceId, **kwargs ):
		super(AssetBrowserInstance, self).__init__()
		self.module = None
		self.main = kwargs.get( 'main', False )
		self.instanceId = instanceId
		self.windowId = 'AssetBrowser-%s' % self.instanceId
		self.mode = ( self.main and 'browse' ) or kwargs.get( 'mode', 'search' )
		self.windowTitle = ''
		
		self.assetFilter       = SearchFilter()
		self.filtering         = False
		self.initialSelection  = None
		self.updatingSelection = False


	def setTitle( self, title ):
		self.windowTitle = title
		prefix = self.mode == 'search' and 'Asset Search' or 'Assets'
		if title:
			self.window.setWindowTitle( '%s< %s >' % ( prefix, title ) )
		else:
			self.window.setWindowTitle( '%s' % prefix )

	def isMain( self ):
		return self.main

	def isActiveInstance( self ):
		return self.module.getActiveInstance() == self

	def isSearch( self ):
		return self.mode == 'search'

	def onLoad( self ):
		self.viewMode = 'icon'
		self.assetSource = 'all'

		self.currentFolders = []

		self.browseHistory = []
		self.historyCursor = 0
		self.updatingHistory = False

		self.thumbnailSize = ( 80, 80 )
		dock = 'bottom'
		if self.isSearch():
			dock = 'float'

		self.window = self.module.requestDockWindow(
				self.windowId,
				title   = 'Assets',
				dock    = dock,
				minSize = (200,200)
			)
		self.window.setCallbackOnClose( self.onClose )
		self.window.hide()
		ui = self.window.addWidgetFromFile(
			_getModulePath('AssetBrowser.ui')
		)

		self.splitter = ui.splitter
		
		#Tree folder
		self.treeFolderFilter = AssetFolderTreeFilter(
				self.window
			)
		self.treeFolder  = 	AssetFolderTreeView(
			sorting   = True,
			multiple_selection = True,
			drag_mode = 'all',
			folder_only = True
		)

		self.treeFolderFilter.setTargetTree( self.treeFolder )
		self.treeFolder.owner = self
		self.treeFolder.setContextMenuPolicy( QtCore.Qt.CustomContextMenu)
		self.treeFolder.customContextMenuRequested.connect( self.onTreeViewContextMenu)

		#Tree filter
		self.treeFilterFilter = AssetFolderTreeFilter(
				self.window
			)
		self.treeFilter  = 	AssetFilterTreeView(
			sorting   = True,
			multiple_selection = False
			# drag_mode = 'internal',
		)
		
		self.treeFilterFilter.setTargetTree( self.treeFilter )
		self.treeFilter.owner = self

		##
		self.iconList       = AssetBrowserIconListWidget()
		self.detailList     = AssetBrowserDetailListWidget()
		self.assetFilterWidget  = AssetBrowserTagFilterWidget()
		self.statusBar      = AssetBrowserStatusBar()
		self.navigator      = AssetBrowserNavigator()

		folderToolbar  = QtWidgets.QToolBar()
		contentToolbar = QtWidgets.QToolBar()

		self.detailList .owner = self
		self.iconList   .owner = self
		self.assetFilterWidget.owner = self
		self.statusBar  .owner = self
		self.navigator  .owner = self

		self.iconList.setContextMenuPolicy( QtCore.Qt.CustomContextMenu)
		self.iconList.customContextMenuRequested.connect( self.onItemContextMenu )
		self.detailList.setContextMenuPolicy( QtCore.Qt.CustomContextMenu)
		self.detailList.customContextMenuRequested.connect( self.onItemContextMenu )

		##
		self.detailListFilter = GenericTreeFilter( self.window )
		self.detailListFilter.setFoldButtonsVisible( False )
		self.detailListFilter.setTargetTree( self.detailList )

		self.iconListFilter = GenericListFilter( self.window )
		self.iconListFilter.setTargetList( self.iconList )

		self.detailListFilter.filterChanged.connect( self.iconListFilter.setFilter )
		self.iconListFilter.filterChanged.connect( self.detailListFilter.setFilter )

		layoutLeft = QtWidgets.QVBoxLayout( ui.containerTree )
		layoutLeft.setSpacing( 0 )
		layoutLeft.setContentsMargins( 0 , 0 , 0 , 0 )
		
		layoutLeft.addWidget( folderToolbar )
		layoutLeft.addWidget( self.treeFolderFilter )
		layoutLeft.addWidget( self.treeFolder )

		layoutLeft.addWidget( self.treeFilterFilter )
		layoutLeft.addWidget( self.treeFilter )
		
		layoutRight = QtWidgets.QVBoxLayout( ui.containerRight )
		layoutRight.setSpacing( 0 )
		layoutRight.setContentsMargins( 0 , 0 , 0 , 0 )

		layoutRight.addWidget( contentToolbar )
		layoutRight.addWidget( self.detailListFilter )
		layoutRight.addWidget( self.iconListFilter )
		layoutRight.addWidget( self.assetFilterWidget )
		layoutRight.addWidget( self.iconList )
		layoutRight.addWidget( self.detailList )
		layoutRight.addWidget( self.statusBar )

		##Tool bar
		self.folderToolBar  = self.module.addToolBar( None, folderToolbar, owner = self )
		self.contentToolBar = self.module.addToolBar( None, contentToolbar, owner = self )

		self.contentToolBar.addTools([
			dict( name = 'detail_view', label = 'List View', type = 'check', icon = 'list',   group='view_mode' ),
			dict( name = 'icon_view',   label = 'Icon View', type = 'check', icon = 'grid-2', group='view_mode' ),
		])
		self.setViewMode( 'icon' )

		if self.isSearch():
			#search mode
			self.treeFolder.hide()
			self.treeFolderFilter.hide()

			self.folderToolBar.addTools([
				dict( name = 'create_filter', label = 'Add Filter', icon = 'add' ),
				dict( name = 'create_filter_group', label = 'Add Filter Group', icon = 'add_folder' ),
			])

			self.contentToolBar.addTools([
				'----',
				dict( name = 'locate_asset', label = 'Locate Asset', icon = 'search' ),
				'----',
				dict( name = 'asset_in_scene', label = 'Assets In Current Scene Only', type = 'check' ),
			])

		else:
			#browse mode
			self.treeFilter.hide()
			self.treeFilterFilter.hide()

			self.folderToolBar.addTools([
				dict( name = 'navigator', widget = self.navigator ),
			])
			self.contentToolBar.addTools([
				'----',
				dict( name = 'create_folder', label = 'Create Folder', icon = 'add_folder' ),
				dict( name = 'create_asset', label = 'Create Asset', icon = 'add_file' ),
				'----',
				dict( name = 'create_remote_file', label = 'Create Remote Asset', icon = 'add_remote' ),
				dict( name = 'show_remote_file', label = 'Show Remote Rule', icon = 'show_remote' ),
				dict( name = 'check_remote_file', label = 'Check Remote Asset', icon = 'check_remote' ),
				'----',
			])

		self.setTitle( '' )
		self.setAssetFilter( None )
		

	def onStart( self ):
		assetLib = self.module.getAssetLibrary()

		self.treeFolder.rebuild()
		self.treeFilter.rebuild()

		signals.connect( 'asset.register',   self.onAssetRegister )
		signals.connect( 'asset.unregister', self.onAssetUnregister )
		signals.connect( 'asset.moved',      self.onAssetMoved )
		signals.connect( 'asset.modified',   self.onAssetModified )
		signals.connect( 'asset.deploy.changed', self.onAssetDeployChanged )
		signals.connect( 'scene.change',     self.onSceneChange )


		if self.isSearch():
			#search mode
			self.treeFolder.hide()
			self.treeFolderFilter.hide()
			self.treeFilter.selectNode( self.assetFilter )

		else:
			#browse mode
			self.treeFilter.hide()
			self.treeFilterFilter.hide()
			if self.initialSelection:
				nodes = [ assetLib.getAssetNode( path ) for path in self.initialSelection ]
				self.treeFolder.selectNode( nodes )

		self.assetFilterWidget.rebuild()
		
	def onStop( self ):
		if self.isMain():
			self.treeFolder.saveTreeStates()

	def saveConfig( self ):
		sizes = self.splitter.sizes()
		if not self.assetFilter:
			filterData = False
		else:
			if self.assetFilter.getRoot() == self.getFilterRootGroup():
				filterData = self.assetFilter.getId()
			else:
				filterData = self.assetFilter.save()
		config = {
			'mode' : self.mode,
			'current_selection' : [ node.getPath() for node in self.currentFolders ],
			'splitter_sizes'    : sizes,
			'current_filter'    : filterData
		}
		return config

	def loadConfig( self, config ):
		assetLib = self.module.getAssetLibrary()
		if not self.isSearch():
			self.initialSelection = config.get( 'current_selection', None )

		splitterSizes    = config.get( 'splitter_sizes', None )
		if splitterSizes:
			if splitterSizes[0] == 0:
				splitterSizes[0] = 80
			self.splitter.setSizes( splitterSizes )

		filterData = config.get( 'current_filter', None )
		if filterData:
			if isinstance( filterData, str ): #ref
				node = self.getFilterRootGroup().findChild( filterData )
				self.assetFilter = node
			else:
				self.assetFilter.load( filterData )

	#View control
	def setAssetSource( self, source ):
		if self.assetSource == source: return
		self.assetSource = source
		self.rebuildItemView( True )

	def setViewMode( self, mode, changeToolState = True, rebuildView = True ):
		prevSelection = self.getItemSelection()
		self.viewMode = mode
		if mode == 'icon':
			self.detailList.hide()
			self.detailListFilter.hide()
			self.detailListFilter.setEnabled( False )
			self.iconList.show()
			self.iconListFilter.show()
			self.iconListFilter.setEnabled( True )

			if changeToolState: self.contentToolBar.getTool( 'icon_view' ).setValue( True )
			if rebuildView:
				self.rebuildItemView( True )

		else: #if mode == 'detail'

			self.iconList.hide()
			self.iconListFilter.hide()
			self.iconListFilter.setEnabled( False )
			self.detailList.show()
			self.detailListFilter.show()
			self.detailListFilter.setEnabled( True )

			if changeToolState: self.contentToolBar.getTool( 'detail_view' ).setValue( True )
			if rebuildView:
				self.rebuildItemView( True )

		if prevSelection:
			for node in prevSelection:
				self.getCurrentView().selectNode( node, add = True, goto = False )
			self.getCurrentView().gotoNode( prevSelection[0] )

		if self.isSearch():
			self.module.setFilterViewMode( self.assetFilter, self.viewMode )

		else:
			for folder in self.getCurrentFolders():
				folder.setWorkspaceData( 'browser_view_mode', self.viewMode )
				break

	def getCurrentView( self ):
		if self.viewMode == 'icon':
			return self.iconList
		else: #if mode == 'detail'
			return self.detailList

	def setFocus( self ):
		self.window.show()
		self.window.setFocus()
		self.window.raise_()
		self.getCurrentView().setFocus()

	#
	def onItemContextMenu( self, point ):
		item = self.getCurrentView().itemAt(point)
		if item:
			node = item.node
		else:
			node = None
		self.module.popupAssetContextMenu( node, self )

	def onTreeViewContextMenu( self, point ):
		item = self.treeFolder.itemAt(point)
		if item:
			node = item.node
		else:
			node = None
		self.module.popupAssetContextMenu( node, self, True )

	def removeItemFromView( self, node ):
		self.getCurrentView().removeNode( node )

	def getItemSelection( self ):
		return self.getCurrentView().getSelection()

	def getFolderSelection( self ):
		return self.treeFolder.getSelection()

	def rebuildItemView( self, retainSelection = False ):
		if not self.module.ready: return
		if self.viewMode == 'icon':
			self.iconList.rebuild()
		else: #if mode == 'detail'
			self.detailList.rebuild()
		self.iconListFilter  .refresh()
		self.detailListFilter.refresh()

	def onTreeSelectionChanged( self ):
		folders = []
		for anode in self.getFolderSelection():
			# assert anode.isType( 'folder' )
			folders.append( anode )
		self.pushHistory()
		self.currentFolders = folders
		if folders:
			folderNode = folders[0]
			viewMode = folderNode.getWorkspaceData( 'browser_view_mode', 'icon' )
			self.setViewMode( viewMode, True, False )
		self.rebuildItemView()
		self.updateStatusBar()

	def onTreeRequestDelete( self ):
		if requestConfirm( 'delete asset package/folder', 'Confirm to delete asset(s)?' ):
			for node in self.getFolderSelection():
				node.deleteFile()

	def onListRequestDelete( self ):
		if requestConfirm( 'delete asset package/folder', 'Confirm to delete asset(s)?' ):
			for node in self.getItemSelection():
				node.deleteFile()
			
	def onListSelectionChanged( self ):
		if not self.updatingSelection:
			self.module.setActiveInstance( self )
		self.updatingSelection = True
		selection = self.getItemSelection()
		self.updatingSelection = False
		if self.isActiveInstance():
			self.updatePreview()
			self.updateStatusBar()
			self.module.changeAssetSelection( selection )

	def clearSelection( self ):
		self.updatingSelection = True
		self.getCurrentView().selectNode( None )
		self.updatingSelection = False


	def onActivateNode( self, node, src ):
		if src == 'tree': #direct open
			if node.isVirtual():
				node = node.findNonVirtualParent()
				self.openAsset( node, select = False )
			if node.isType( 'folder' ):
				node.openInSystem()
			else:
				self.openAsset( node, select = False )

		else:
			if self.isSearch():
				self.openAsset( node, select = False )
			else:
				if node.isGroupType( 'folder', 'package' ):
					self.selectAsset( node, enter_folder = True )
				else:
					self.openAsset( node, select = False )

	#status bar/ tags
	def editAssetTags( self ):
		target = None
		itemSelection = self.getItemSelection()
		if itemSelection:
			target = itemSelection[0]
		else:
			folders = self.getCurrentFolders()
			if folders:
				target = folders[0]
		if not target: return
		text = requestString( 
			'Tags', 
			'Enter Tags:',
			target.getTagString()
		)
		if text != None:
			target.setTagString( text )
			self.updateStatusBar()

	def updateStatusBarForAsset( self, asset, forFolder = False ):
		if forFolder:
			self.statusBar.setText( '[' + asset.getNodePath() + ']' )
		else:
			self.statusBar.setText( asset.getNodePath() )
		inherited = asset.getInheritedTagString()
		if inherited:
			self.statusBar.setTags( 
				'%s ( %s )' % ( asset.getTagString(), inherited )
				)
		else:
			self.statusBar.setTags( asset.getTagString() )

	def updateStatusBar( self ):
		self.statusBar.show()
		selection = self.getItemSelection()
		count = len( selection )
		if count == 1:
			node = selection[0]
			self.updateStatusBarForAsset( node )
			return
		elif count > 1:
			self.statusBar.setText( '%d asset selected' % count )
			return
		else:
			folders = self.getCurrentFolders()
			countFolder = len( folders )
			if countFolder == 1:
				folder = folders[0]
				self.updateStatusBarForAsset( folder, True )
				return
			elif countFolder > 1:
				self.statusBar.setText( '%d folders/packages selected' % countFolder )
				return
		self.statusBar.setText( 'no selection' )
		self.statusBar.hide()

	def updatePreview( self ):
		selection = self.getItemSelection()
		previewer = app.getModule( 'asset_previewer' )
		if previewer:
			previewer.setTarget( selection )
	
	#browsing support
	def pushHistory( self ):
		if self.updatingHistory: return
		currentSelection = self.getFolderSelection()
		if not currentSelection: return
		count = self.historyCursor
		if count > 0 and currentSelection == self.browseHistory[ count - 1 ]: return
		self.browseHistory = self.browseHistory[ 0: count ]
		self.browseHistory.append( currentSelection )
		self.historyCursor = count + 1

	def clearHistory( self ):
		self.browseHistory = []
		self.historyCursor = 0

	def forwardHistory( self ):
		count = len( self.browseHistory )
		if self.historyCursor >= count: return
		self.updatingHistory = True
		self.historyCursor = min( self.historyCursor + 1, count )
		selection = self.browseHistory[ self.historyCursor - 1 ]
		for asset in selection:
			self.selectAsset( asset, update_history = False, enter_folder = True )
		self.updatingHistory = False

	def backwardHistory( self ):
		if self.historyCursor <= 1: return #no more history
		self.historyCursor = max( self.historyCursor - 1, 0 )
		self.updatingHistory = True
		selection = self.browseHistory[ self.historyCursor - 1 ]
		for asset in selection:
			self.selectAsset( asset, update_history = False, goto = True, enter_folder = True )
		self.updatingHistory = False

	def goUpperLevel( self ):
		for folder in self.currentFolders:
			self.selectAsset( folder, goto = True )
			return

	#commands
	def locateAsset( self, asset, focus = True, **options ):
		if isinstance( asset, str ): #path
			asset = self.getAssetLibrary().getAssetNode( asset )
		if not asset: return
		if focus: self.setFocus()
		# self.getCurrentView().setFocus( Qt.MouseFocusReason)
		self.selectAsset( asset, goto = True )

	def selectAsset( self, asset, **options ):
		if not asset: return
		#find parent package/folder
		if options.get( 'enter_folder', False ):
			folder = asset
		else:
			folder = asset.getParent()
		while folder:
			if folder.getGroupType() in [ 'folder', 'package' ]: break
			folder = folder.getParent()
		self.treeFolder.selectNode( folder )
		if options.get( 'update_history', True ):
			self.pushHistory()

		itemView = self.getCurrentView()
		itemView.selectNode( asset )
		if options.get( 'goto', False ):
			self.treeFolder.scrollToNode( folder )
			itemView.scrollToNode( asset )
			self.setFocus()
			itemView.setFocus()

	def openAsset( self, asset, **option ):
		return self.module.openAsset( asset, **option )

	def getCurrentFolders( self ):
		return self.currentFolders

	def getAssetsInList( self ):
		assetFilter = self.assetFilter
		if not assetFilter: return
		assetFilter.updateRule()

		if self.isSearch(): #search for all assets:
			assetLib = self.module.getAssetLibrary()
			assets = []
			if not assetFilter.hasItem():
				pass
			else:
				if self.assetSource == 'scene':
					sceneGraphEditor = app.getModule( 'scenegraph_editor' )
					if sceneGraphEditor:
						sourceAssets = sceneGraphEditor.getAssetsInUse()
					else:
						sourceAssets = []
				else:
					sourceAssets = assetLib.getAllAssets()

				includeDeprecated = False
				for assetNode in sourceAssets:
					if not assetNode: continue
					if assetNode.hasTag( 'deprecated' ) and ( not includeDeprecated ): continue
					info = assetNode.buildSearchInfo( uppercase = True )
					if assetFilter.evaluate( info ):
						assets.append( assetNode )

		else: #filter current folder
			assets = []
			filtering = assetFilter.compiledRule
			for folder in self.currentFolders:
				for assetNode in folder.getChildren():
					if filtering:
						info = assetNode.buildSearchInfo( uppercase = True )
						if ( not assetFilter.evaluate( info ) ):
							continue
					assets.append( assetNode )

		def _sortFunc( x, y ):
			t1 = x.getType()
			t2 = y.getType()
			if t1 == 'folder' and t2 != 'folder': return -1
			if t2 == 'folder' and t1 != 'folder': return 1
			return x.getName() < y.getName()

		return sorted( assets, key = cmp_to_key( _sortFunc ) )

	def getAssetThumbnailIcon( self, assetNode, size ):
		thumbnailPath = assetNode.requestThumbnail( size )
		if thumbnailPath:
			icon = QtGui.QIcon( QtGui.QPixmap( thumbnailPath ) )
			return icon
		else:
			return None

	def onSceneChange( self ):
		if self.assetSource == 'scene':
			self.rebuildItemView()

	def onAssetRegister( self, node ):
		pnode = node.getParent()
		if node.isGroupType( 'folder', 'package' ):
			if pnode:
				self.treeFolder.addNode( node )

		if pnode in self.currentFolders:
			self.rebuildItemView()
			if node.getPath() == self.module.newCreateNodePath:
				self.module.newCreateNodePath = None
				self.selectAsset( node, enter_folder = True )

	def onAssetUnregister( self, node ):
		pnode=node.getParent()
		if pnode:
			self.treeFolder.removeNode(node)
		if pnode in self.currentFolders:
			self.removeItemFromView( node )

	def onAssetMoved( self, node ):
		pass

	def onAssetModified( self, node ):
		self.treeFolder.refreshNodeContent( node )
		# self.getCurrentView().refreshNodeContent( node )

	def onAssetDeployChanged( self, node ):
		self.treeFolder.updateItem( node, 
				basic            = False,
				deploy           = True, 
				updateChildren   = True,
				updateDependency = True
			)
		app.getAssetLibrary().saveAssetTable()
	
	def updateTagFilter( self ):
		prevFiltering = self.filtering
		self.assetFilter.updateRule()
		self.filtering = self.assetFilter.isFiltering()
		if self.filtering != prevFiltering:
			self.getCurrentView().setProperty( 'filtered', self.filtering )
			repolishWidget( self.getCurrentView() )
		self.rebuildItemView()

	def createAsset( self, creator ):
		self.module.createAsset( creator, self )

	def createRemoteFile( self ):
		self.module.createRemoteFile( self )

	def checkRemoteFile( self ):
		self.module.checkRemoteFile( self )

	def showRemoteFile( self ):
		self.module.showRemoteFile( self )

	def pasteLocalFiles( self, paths ):
		folders =  self.getFolderSelection()
		if len( folders ) != 1: return
		folder = folders[0]
		if folder.isType( 'folder' ) and ( not folder.isVirtual() ):
			targetRootPath = folder.getAbsFilePath()
			for path in paths:
				if path.endswith('/'):
					path = path[:-1]
				if not path: continue
				targetPath = targetRootPath + '/' + os.path.basename( path )
				print(( path, targetPath ))
				if os.path.isfile( path ):
					shutil.copy2( str(path), str(targetPath) )
				elif os.path.isdir( path ):
					shutil.copytree( str(path), str(targetPath) )

	#tool
	def onTool( self, tool ):
		name = tool.name
		if name == 'icon_view':
			self.setViewMode( 'icon', False )
		elif name == 'detail_view':
			self.setViewMode( 'detail', False )

		#content toolbar
		elif name == 'create_asset':
			requestSearchView( 
				info    = 'select asset type to create',
				context = 'asset_creator',
				type    = 'scene',
				on_selection = self.createAsset
			)

		elif name == 'create_folder':
			self.createAsset( 'folder' )

		elif name == 'create_remote_file':
			self.createRemoteFile()

		elif name == 'check_remote_file':
			self.checkRemoteFile()

		elif name == 'show_remote_file':
			self.showRemoteFile()

		elif name == 'locate_asset':
			for node in self.getItemSelection():
				self.module.locateAsset( node, goto = True )
				break

		elif name == 'asset_in_scene':
			self.setAssetSource( bool(tool.getValue()) and 'scene' or 'all' )

		elif name in ( 'create_filter', 'create_filter_group' ):
			node = self.treeFilter.getFirstSelection()
			if not node:
				contextGroup = self.getFilterRootGroup()
			elif isinstance( node, SearchFilterGroup ):
				contextGroup = node
			else:
				contextGroup = node.getParent()
			if name == 'create_filter':
				node = SearchFilter()
				node.setName ( 'filter' )
			else:
				node = SearchFilterGroup()
				node.setName ( 'group' )

			contextGroup.addChild( node )

			self.treeFilter.addNode( node )
			self.treeFilter.editNode( node )
			self.treeFilter.selectNode( node )

	def onClose( self ):
		if not self.isMain():
			self.module.removeInstance( self )
		return True

		#asset fitler
	def getFilterRootGroup( self ):
		return self.module.getFilterRootGroup()

	def	setAssetFilter( self, f ):
		if isinstance( f, SearchFilterGroup ):
			return

		elif isinstance( f, SearchFilter ):
			self.assetFilter = f
			self.assetFilterWidget.setTargetFilter( self.assetFilter )
			self.module.saveFilterConfig()
			viewMode = self.module.assetFilterViewModes.get( self.assetFilter.getId(), 'icon' )
			self.setViewMode( viewMode )

		else:
			self.assetFilter = SearchFilter()
			self.assetFilterWidget.setTargetFilter( self.assetFilter )

	def renameFilter( self, node, name ):
		node.setName( name )
		self.module.saveFilterConfig()

	def onAsseotFilterRequestDelete( self, node ):
		if requestConfirm( 'Confirm Deletion', 'Delete this filter (group)?' ):
			node.remove()
		self.setAssetFilter( None )
		self.module.saveFilterConfig()
		self.assetFilterWidget.rebuild()
		self.treeFilter.rebuild()


##----------------------------------------------------------------##
class AssetFileWatch( FileWatch ):
	metaPattern = re.compile( '^.*/\.assetmeta/.*\.meta$')
	reportFolderPattern = re.compile( '^.*/\.report$')
	metaFolderPattern = re.compile( '^.*/\.assetmeta$')
	def getPath( self ):
		return app.getProject().getAssetPath()

	def onFileMoved(self, path, newpath):
		if AssetFileWatch.reportFolderPattern.match( path ): return #ignore report folder
		if AssetFileWatch.metaFolderPattern.match( path ): return #ignore meta folder
		if AssetFileWatch.metaPattern.match( path ):
			logging.info('file: meta moved: %s -> %s' % (path, newpath) )
			app.getAssetLibrary().onMetaChanged( path )
			app.getAssetLibrary().onMetaChanged( newpath )
		else:
			logging.info('file: asset moved: %s -> %s' % (path, newpath) )
			return app.getAssetLibrary().onFileMoved( path, newpath )
		
	def onFileCreated(self, path):
		if AssetFileWatch.reportFolderPattern.match( path ): return #ignore report folder
		if AssetFileWatch.metaFolderPattern.match( path ): return #ignore meta folder
		if AssetFileWatch.metaPattern.match( path ):
			logging.info('file: meta created:' + path)
			app.getAssetLibrary().onMetaChanged( path )
		else:
			logging.info('asset created:' + path)
			return app.getAssetLibrary().onFileCreated( path )
		
	def onFileModified(self, path):
		if AssetFileWatch.reportFolderPattern.match( path ): return #ignore report folder
		if AssetFileWatch.metaFolderPattern.match( path ): return #ignore meta folder
		if AssetFileWatch.metaPattern.match( path ):
			logging.info('file: meta modified:' + path)
			return app.getAssetLibrary().onMetaChanged( path )
		else:
			logging.info('file: asset modified:' + path)
			return app.getAssetLibrary().onFileModified( path )
		
	def onFileDeleted(self, path):
		if AssetFileWatch.reportFolderPattern.match( path ): return #ignore report folder
		if AssetFileWatch.metaFolderPattern.match( path ): return #ignore meta folder
		if AssetFileWatch.metaPattern.match( path ):
			logging.info('file: meta deleted:' + path)
			return app.getAssetLibrary().onMetaChanged( path )
		else:
			logging.info('file: asset deleted:' + path)
			return app.getAssetLibrary().onFileDeleted( path )
		
	def getIgnorePatterns( self ):
		patterns = FileWatch.getIgnorePatterns( self ) or []
		patterns += [ '*/_gii' ]
		return patterns


##----------------------------------------------------------------##
@slot( 'app.open_url' )
def URLSceneHandler( url ):
	if url.get( 'base', None ) != 'asset': return
	data = url['data']
	path = data.get( 'path', None )
	if not path:
		print( 'no asset path' )
		return
	app.getModule( 'asset_browser' ).locateAsset( path )

