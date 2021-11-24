import random
import ujson as json
import os.path

##----------------------------------------------------------------##
from gii.core         import *
from gii.qt          import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter
from gii.SceneEditor      import SceneEditorModule, getSceneSelectionManager
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor
from gii.qt.dialogs   import requestString, alertMessage, requestConfirm

##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt

##----------------------------------------------------------------##
from gii.SearchView       import requestSearchView, registerSearchEnumerator
from gii.SceneEditor  import SceneEditorModule

from mock.asset.LocalePackAsset import LocalePackBuilder, LocalePackAssetManager

##----------------------------------------------------------------##
from mock import _MOCK, isMockInstance

from .LocalePackRepository import createLocalePackRepository

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


##----------------------------------------------------------------##		
class LocalePackManager( SceneEditorModule ):
	name = 'locale_pack_manager'
	dependency = [ 'mock' ]

	def onLoad( self ):
		userSettings = app.getProject().getUserSetting( 'locale_manager', {} )
		self._isAdmin = userSettings.get( 'is_admin' )

		self.currentPackEntry = None
		self.windowTitle = 'Locale Pack Manager'
		self.container = self.requestDocumentWindow( 'localepackmanager',
				title       = 'Locale Packs',
				size        = (500,300),
				minSize     = (500,300)
				# allowDock = False
			)

		self.tool = self.addToolBar( 'locale_pack_manager', self.container.addToolBar() )
		self.addTool( 'locale_pack_manager/refresh',   label = 'Refresh', icon = 'refresh' )
		self.addTool( 'locale_pack_manager/----' )
		self.addTool( 'locale_pack_manager/locate',   label = 'Locate', icon = 'search' )

		if self._isAdmin:
			self.addTool( 'locale_pack_manager/----' )
			self.addTool( 'locale_pack_manager/build_source',   label = 'Build Source' )
			#self.addTool( 'locale_pack_manager/update_remote',   label = 'Update Remote' )
			self.addTool( 'locale_pack_manager/----' )
			self.addTool( 'locale_pack_manager/sync_external',   label = 'Sync External' )
		
		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('window.ui')
		)

		treePacksFilter = addWidgetWithLayout( GenericTreeFilter( window.containerLeft ) )
		self.treePacks = treePacks= addWidgetWithLayout( LocalePackTreeWidget( window.containerLeft ) )
		self.treePacks.module = self
		treePacks.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding )
		treePacksFilter.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
		treePacksFilter.setTargetTree( self.treePacks )

		treeItemsFilter = addWidgetWithLayout( GenericTreeFilter( window.containerRight ) )
		self.treeItems = treeItems = addWidgetWithLayout( LocalePackItemTreeWidget( window.containerRight ) )
		self.treeItems.module = self
		treeItems.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding )
		treeItemsFilter.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
		treeItemsFilter.setTargetTree( self.treeItems )

		self.addMenuItem( 'main/asset/----' )
		self.addMenuItem(
				'main/asset/locale_pack_manager',
				{
					'label': 'Locale Pack Manager',
					'on_click': lambda menu: self.setFocus()
				}
			)

		self.mockLocaleManager = None

	def onAppReady( self ):
		self.mockLocaleManager = _MOCK.getGlobalManager( 'LocaleManager' )
		self.scanPacks()
		self.treePacks.rebuild()
		signals.connect( 'asset.register',   self.onAssetRegister )
		signals.connect( 'asset.unregister', self.onAssetUnregister )

	def onSetFocus( self ):
		self.container.show()
		self.container.raise_()

	def onAssetRegister( self, node ):
		if node.getType() == 'locale_pack':
			self.scanPacks()

	def onAssetUnregister( self, node ):
		if node.getType() == 'locale_pack':
			self.scanPacks()

	def scanPacks( self ):
		manager = self.mockLocaleManager
		assetLib = AssetLibrary.get()
		manager.scanPacks( manager )
		self.treePacks.rebuild()

	def locatePack( self, packAssetNode ):
		self.setFocus()
		manager = self.mockLocaleManager
		entry = LuaCall( manager, 'findLocalePackEntry', packAssetNode.getPath() )
		self.treePacks.selectNode( entry )

	def getLocalePackEntries( self ):
		manager = self.mockLocaleManager
		return [ entry for entry in list(manager[ 'localePackEntries' ].values()) ]

	def getPackItems( self ):
		entry = self.currentPackEntry
		if not entry: return []
		pack = entry.getPack( entry )
		if not pack: return []
		return [
			item for item in list(pack[ 'items' ].values())
		]

	def selectPack( self, packEntry ):
		self.currentPackEntry = packEntry
		self.treeItems.rebuild()

	def addPackItem( self, assetPath ):
		entry = self.currentPackEntry
		if not entry: 
			alertMessage( 'No locale pack', 'No Locale Pack selected.' )
			return
		pack = entry.getPack( entry )
		if pack:
			if not pack.getAssetItem( pack, assetPath ):
				item = pack.addAssetItem( pack, assetPath )
				self.savePackConfig()
				return item
		return None

	def renamePackItem( self, item, name ):
		item.setName( item, name )
		self.savePackConfig()

	def requestDeleteItems( self ):
		if not self.currentPackEntry: return
		deleted = False
		for item in self.treeItems.getSelection():
			pack = item.parentPack
			LuaCall( pack, 'removeItem', item )
			deleted = True
		if deleted:
			self.treeItems.rebuild()
			self.savePackConfig()

	def savePackConfig( self ):
		entry = self.currentPackEntry
		if entry:
			pack = LuaCall( entry, 'getPack' )
			LuaCall( pack, 'affirmGUID' )
			LuaCall( pack, 'saveConfigToFile' )

	def buildSource( self, packPath ):
		builder = LocalePackBuilder( packPath )
		builder.buildSource()
		return True

	def updateRemote( self, packPath ):
		repo = createLocalePackRepository( packPath )
		if repo:
			if repo.update():
				packNode = AssetLibrary.get().getAssetNode( packPath )
				packNode.markModified()
				app.getAssetLibrary().importModifiedAssets()

	def syncExternal( self, packPath ):
		packNode = AssetLibrary.get().getAssetNode( packPath )
		manager = packNode.getManager()
		if isinstance( packNode.getManager(), LocalePackAssetManager ):
			manager.syncExternal( packNode )

	def onTool( self, tool ):
		name = tool.name
		if name == 'locate':
			if self.treeItems.getSelection():
				for item in self.treeItems.getSelection():
					path = item.path
					app.getModule( 'asset_browser' ).locateAsset( path, goto = True )
					break
			else:
				packEntry = self.currentPackEntry
				if packEntry:
					app.getModule( 'asset_browser' ).locateAsset( packEntry.path, goto = True )

		elif name == 'refresh':
			self.scanPacks()
			self.treePacks.rebuild()

		elif name == 'build_source':
			entry = self.currentPackEntry
			if not entry:
				alertMessage( 'No locale pack', 'No Locale Pack selected.' )
				return
			self.buildSource( entry.path )

		elif name == 'sync_external':
			entry = self.currentPackEntry
			if not entry:
				alertMessage( 'No locale pack', 'No Locale Pack selected.' )
				return
			self.syncExternal( entry.path )

		elif name == 'update_remote':
			entry = self.currentPackEntry
			if not entry:
				alertMessage( 'No locale pack', 'No Locale Pack selected.' )
				return
			self.updateRemote( entry.path )

##----------------------------------------------------------------##
class LocalePackTreeWidget( GenericTreeWidget ):
	def __init__( self, *args, **option ):
		super( LocalePackTreeWidget, self ).__init__( *args, **option )
		self.setTextElideMode( Qt.ElideLeft )

	def getDefaultOptions( self ):
		return dict(
			multiple_selection = False,
			editable  = True,
			show_root = False
		)

	def getHeaderInfo( self ):
		return [ ('Pack', -1) ]

	def getRootNode( self ):
		return self.module

	def getNodeChildren( self, node ):
		if node == self.module:
			return [ entry for entry in self.module.getLocalePackEntries() ]
		else:
			return []

	def getNodeParent( self, node ):
		if node == self.module :return None
		return self.module

	def updateItemContent( self, item, node, **option ):
		if node == self.module: return
		path = node.getPath( node )
		p, ext = os.path.splitext( path )
		item.setText( 0, p )
		item.setIcon( 0, getIcon( 'locale_pack' ) )

	def onItemSelectionChanged( self ):
		if self.getSelection():
			self.module.selectPack( self.getSelection()[ 0 ] )
		else:
			self.module.selectPack( None )

	def onItemActivated( self, item, col ):
		node = self.getNodeByItem( item )
		path = node.getAssetPath( node ) 
		app.getModule( 'asset_browser' ).locateAsset( path, goto = True )

	def focusInEvent( self, event ):
		self.module.treeItems.selectNode( None )

##----------------------------------------------------------------##
class LocalePackItemTreeWidget( GenericTreeWidget ):
	def __init__( self, *args ):
		super( LocalePackItemTreeWidget, self ).__init__( *args )
		self.setTextElideMode( Qt.ElideLeft )
		self.setAcceptDrops( True )

	def getDefaultOptions( self ):
		return dict(
			multiple_selection = True,
			editable  = True,
			show_root = False,
			drag_mode = 'drop'
		)

	def getHeaderInfo( self ):
		return [ ('Name', 140), ('asset', 250), ( 'valid', 50 ) ]

	def getRootNode( self ):
		return self.module

	def getNodeChildren( self, node ):
		if node == self.module:
			return self.module.getPackItems()
		else:
			return []

	def getNodeParent( self, node ):
		if node == self.module :return None
		return self.module

	def updateItemContent( self, item, node, **option ):
		if node == self.module: return
		item.setIcon( 0, getIcon( 'default_item' ) )
		item.setText( 0, node.getName( node ) )
		assetLib = AssetLibrary.get()
		assetPath = node.getAssetPath( node )
		assetNode = assetLib.getAssetNode( assetPath )
		item.setText( 1, assetPath )
		if assetNode:
			iconName = assetLib.getAssetIcon( assetNode.getType() ) or 'normal' 
			item.setIcon( 1, getIcon( iconName, 'normal' ) )
		else:
			item.setIcon( 1, getIcon( 'missing' ) )

	def mimeTypes( self ):
		return [ GII_MIME_ASSET_LIST ]

	def onItemActivated( self, item, col ):
		print( 'activate?' )
		node = self.getNodeByItem( item )
		path = node.getAssetPath( node ) 
		app.getModule( 'asset_browser' ).locateAsset( path, goto = True )

	def onDropEvent( self, targetNode, pos, event ):
		mimeData = event.mimeData()
		if mimeData.hasFormat( GII_MIME_ASSET_LIST ):
			raw = str( mimeData.data( GII_MIME_ASSET_LIST ), 'utf-8' )
			assetList = json.loads( raw )
			if not self.module.currentPackEntry:
				alertMessage( 'No locale pack', 'No Locale Pack selected.' )
			else:
				assetLib = AssetLibrary.get()
				for path in assetList:
					packItem = self.module.addPackItem( path )
					if packItem:
						self.addNode( packItem )
			event.accept()

	def onItemChanged( self, item, col ):
		node = self.getNodeByItem( item )
		if col == 0:
			self.module.renamePackItem( node, item.text( 0 ) )	

	def onDeletePressed( self ):
		self.module.requestDeleteItems()
