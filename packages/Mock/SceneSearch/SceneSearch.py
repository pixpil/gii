import random
import os
import shutil
import os.path

from gii.core         import *
from gii.qt.dialogs   import requestString, alertMessage, requestConfirm
from gii.qt.helpers   import setClipboardText
from gii.SearchView   import requestSearchView, registerSearchEnumerator

from gii.SceneEditor  import SceneEditorModule

from gii.FileWatcher  import FileWatch

from qtpy            import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore     import Qt
from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter
from gii.qt.controls.GenericListWidget import GenericListWidget, GenericListFilter
from gii.qt.controls.ElidedLabel       import ElidedLabel
from gii.qt.controls.SearchFilterWidget import SearchFilterWidget


from util import TagMatch
from gii.qt.helpers import repolishWidget

from util.SearchFilter import *

from mock import _MOCK, _MOCK_EDIT, isMockInstance, getMockClassName

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
def _toUpper( v, convert ):
	if not convert: return v
	if isinstance( v, list ):
		return [ item.upper() for item in v ]
	else:
		return v.upper()

def buildEntitySearchInfo( entity, **options ):
	info = {}
	uppercase =  options.get( 'uppercase', True )
	def _toUpper( v, convert ):
		if not convert: return v
		if isinstance( v, str ):
			v = v.split( ',' )
		if isinstance( v, list ):
			return [ item.upper() for item in v ]
		else:
			return ''
	# info[ 'tag'  ] = _toUpper( entity.getTagCache() , uppercase )
	info[ 'type' ] = _toUpper( entity.getClassName( entity ) , uppercase )
	info[ 'name' ] = _toUpper( entity.getName( entity ) , uppercase )
	info[ 'components' ] = _toUpper( entity.getComponentInfo( entity ) , uppercase )
	return info

##----------------------------------------------------------------##
class SceneSearch( SceneEditorModule ):
	name = 'scene_search'
	dependency = [ 'scenegraph_editor' ]

	def onLoad( self ):
		self.updateScheduled = False

		self.searchFilterRootGroup = SearchFilterGroup()
		self.searchFilterRootGroup.setName( '__root__' )

		self.searchFilter = SearchFilter()
		self.filtering = False
		self.initialSelection = None

		self.currentFolders = []

		self.updatingSelection = False

		self.window = self.requestDockWindow(
				'SceneSearch',
				title   = 'Scene Search',
				dock    = 'bottom',
				minSize = (200,200)
			)
		self.window.hide()
		ui = self.window.addWidgetFromFile(
			_getModulePath('SceneSearch.ui')
		)

		self.splitter = ui.splitter
		
		#Tree filter
		self.treeSearchFilter = GenericTreeFilter( self.window )
		self.treeSearch  = 	SceneSearchTreeWidget(
			sorting   = True,
			multiple_selection = False
			# drag_mode = 'internal',
		)
		
		self.treeSearchFilter.setTargetTree( self.treeSearch )
		self.treeSearch.owner = self

		##
		self.detailList          = SceneSearchDetailListWidget()
		self.searchFilterWidget  = SceneSearchTagFilterWidget()
		self.statusBar           = SceneSearchStatusBar()

		filterToolbar  = QtWidgets.QToolBar()
		contentToolbar = QtWidgets.QToolBar()

		self.detailList .owner = self
		self.searchFilterWidget.owner = self
		self.statusBar  .owner = self

		self.detailList.setContextMenuPolicy( QtCore.Qt.CustomContextMenu)
		self.detailList.customContextMenuRequested.connect( self.onItemContextMenu )

		##
		self.detailListFilter = GenericTreeFilter( self.window )
		self.detailListFilter.setFoldButtonsVisible( False )
		self.detailListFilter.setTargetTree( self.detailList )

		layoutLeft = QtWidgets.QVBoxLayout( ui.containerTree )
		layoutLeft.setSpacing( 0 )
		layoutLeft.setContentsMargins( 0 , 0 , 0 , 0 )
		
		layoutLeft.addWidget( filterToolbar )
		layoutLeft.addWidget( self.treeSearchFilter )
		layoutLeft.addWidget( self.treeSearch )
		
		layoutRight = QtWidgets.QVBoxLayout( ui.containerRight )
		layoutRight.setSpacing( 0 )
		layoutRight.setContentsMargins( 0 , 0 , 0 , 0 )

		layoutRight.addWidget( contentToolbar )
		layoutRight.addWidget( self.detailListFilter )
		layoutRight.addWidget( self.searchFilterWidget )
		layoutRight.addWidget( self.detailList )
		layoutRight.addWidget( self.statusBar )

		##Tool bar
		self.filterToolBar  = self.addToolBar( None, filterToolbar, owner = self )
		self.contentToolBar = self.addToolBar( None, contentToolbar, owner = self )

		self.filterToolBar.addTools([
			dict( name = 'create_filter', label = 'Add Filter', icon = 'add' ),
			dict( name = 'create_filter_group', label = 'Add Filter Group', icon = 'add_folder' ),
		])

		self.contentToolBar.addTools([
			dict( name = 'locate_entity', label = 'Locate Entity', icon = 'search' ),
		])

		signals.connect( 'selection.changed', self.onSelectionChanged )
		signals.connect( 'scene.change',      self.onSceneChange     )
		signals.connect( 'scene.update',      self.onSceneUpdate     )

		signals.connect( 'entity.added',              self.onEntityAdded      )
		signals.connect( 'entity.removed',            self.onEntityRemoved    )
		signals.connect( 'component.added',           self.onComponentAdded    )
		signals.connect( 'component.removed',         self.onComponentRemoved    )
		signals.connect( 'entity.renamed',            self.onEntityModified )
		signals.connect( 'entity.modified',           self.onEntityModified )
		signals.connect( 'entity.visible_changed',    self.onEntityModified )
		signals.connect( 'entity.pickable_changed',   self.onEntityModified )

		self.setSearchFilter( None )
		self.window.show()
		self.loadConfig()
		

	def onStart( self ):
		self.treeSearch.rebuild()
		#search mode
		self.treeSearch.selectNode( self.searchFilter )
		self.searchFilterWidget.rebuild()

	def onStop( self ):
		self.saveConfig()

	def saveConfig( self ):
		self.saveFilterConfig()
		self.setWorkspaceConfig( 'splitter_sizes', self.splitter.sizes() )

	def loadConfig( self ):
		filterData = self.getConfig( 'filters', None )
		if filterData:
			self.getFilterRootGroup().load( filterData )
		splitterSizes = self.getWorkspaceConfig( 'splitter_sizes', None )
		if splitterSizes:
			if splitterSizes[0] == 0:
				splitterSizes[0] = 80
			self.splitter.setSizes( splitterSizes )
	
	def saveFilterConfig( self ):
		filterData = self.getFilterRootGroup().save()
		self.setConfig( 'filters', filterData )

	def setFocus( self ):
		self.window.raise_()
		self.detailList.setFocus()

	def onSceneChange( self ):
		self.scheduleRebuildItemView()

	def onSceneUpdate( self ):
		if self.updateScheduled:
			self.updateScheduled = False
			self.rebuildItemView()

	def onEntityModified( self, entity, *args ):
		self.detailList.refreshNodeContent( entity )

	def onEntityAdded( self, entity, context = None ):
		self.scheduleRebuildItemView()

	def onEntityRemoved( self, entity ):
		self.scheduleRebuildItemView()

	def onComponentAdded( self, com, entity ):
		self.scheduleRebuildItemView()

	def onComponentRemoved( self, com, entity ):
		self.scheduleRebuildItemView()

	def onSelectionChanged( self, selection, context ):
		if context != 'scene': return
		if self.updatingSelection: return
		self.updatingSelection = True
		self.detailList.selectNode( selection )
		self.updatingSelection = False
	
	def onItemContextMenu( self, point ):
		pass

	def getItemSelection( self ):
		return self.detailList.getSelection()

	def scheduleRebuildItemView( self ):
		self.updateScheduled = True

	def rebuildItemView( self ):
		self.updatingSelection = True
		self.detailList.rebuild()
		self.detailListFilter.refresh()
		#sync selection
		self.detailList.selectNode( self.getSelection() )
		self.updatingSelection = False

	def onListSelectionChanged( self ):
		if self.updatingSelection: return
		self.updatingSelection = True
		selection = self.getItemSelection()
		self.updatingSelection = False
		self.updateStatusBar()
		self.changeSelection( selection )

	def clearSelection( self ):
		if self.updatingSelection: return
		self.updatingSelection = True
		self.detailList.selectNode( None )
		self.updatingSelection = False

	def onActivateNode( self, node, src ):
		self.doCommand( 'scene_editor/focus_selection' )

	def updateStatusBar( self ):
		self.statusBar.hide()
		# self.statusBar.setText( 'no selection' )

	def getEntityInList( self ):
		searchFilter = self.searchFilter
		searchFilter.updateRule()
		game = _MOCK.game
		scene = game.getMainScene( game )
		result = []
		for entity in scene.entities.keys():
			if entity.FLAG_EDITOR_OBJECT: continue
			if entity.FLAG_INTERNAL: continue
			info = buildEntitySearchInfo( entity )
			if searchFilter.evaluate( info ):
				result.append( entity )
		return result

	def locateEntity( self, entity, **args ):
		pass
	
	def updateTagFilter( self ):
		prevFiltering = self.filtering
		self.searchFilter.updateRule()
		self.filtering = self.searchFilter.isFiltering()
		if self.filtering != prevFiltering:
			self.detailList.setProperty( 'filtered', self.filtering )
			repolishWidget( self.detailList )
		self.rebuildItemView()

	#tool
	def onTool( self, tool ):
		name = tool.name
		if name == 'locate_entity':
			self.doCommand( 'scene_editor/focus_selection' )

		elif name in ( 'create_filter', 'create_filter_group' ):
			node = self.treeSearch.getFirstSelection()
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

			self.treeSearch.addNode( node )
			self.treeSearch.editNode( node )
			self.treeSearch.selectNode( node )

	def getFilterRootGroup( self ):
		return self.searchFilterRootGroup

	def	setSearchFilter( self, f ):
		if isinstance( f, SearchFilterGroup ):
			return

		elif isinstance( f, SearchFilter ):
			self.searchFilter = f
			self.searchFilterWidget.setTargetFilter( self.searchFilter )
			self.rebuildItemView()

		else:
			self.searchFilter = SearchFilter()
			self.searchFilterWidget.setTargetFilter( self.searchFilter )

	def renameFilter( self, node, name ):
		node.setName( name )
		self.saveFilterConfig()

	def onFilterRequestDelete( self, node ):
		if requestConfirm( 'Confirm Deletion', 'Delete this filter (group)?' ):
			node.remove()
		self.setSearchFilter( None )
		self.saveFilterConfig()
		self.searchFilterWidget.rebuild()
		self.treeSearch.rebuild()


##----------------------------------------------------------------##
def makeSceneObjectMimeData( entities ):
	#TODO
	data = None
	# assetList = []
	# urlList   = []
	
	# for entity in entities:
	# 	entityList.append( entity.getPath() )
	# 	if not entity.isVirtual():
	# 		urlList.append( QtCore.QUrl.fromLocalFile( entity.getAbsFilePath() ) )
	# assetListData = json.dumps( assetList ).encode('utf-8')
	
	# text = '\n'.join( assetList )

	# data = QtCore.QMimeData()
	# data.setData( GII_MIME_ASSET_LIST, assetListData )
	# if urlList:
	# 	data.setUrls( urlList )
	# data.setText( text )
	return data



##----------------------------------------------------------------##
#TODO: allow sort by other column
class SceneSearchDetailListItem(QtWidgets.QTreeWidgetItem):
	def __lt__(self, other):
		node0 = self.node
		node1 = hasattr(other, 'node') and other.node or None
		if not node1:
			return True
		tree = self.treeWidget()
		# t0 = node0.getType()
		# t1 = node1.getType()
		# if t1!=t0:			
		# 	if tree.sortOrder() == 0:
		# 		if t0 == 'folder': return True
		# 		if t1 == 'folder': return False
		# 	else:
		# 		if t0 == 'folder': return False
		# 		if t1 == 'folder': return True
		return super( SceneSearchDetailListItem, self ).__lt__( other )

##----------------------------------------------------------------##
class SceneSearchDetailListWidget( GenericTreeWidget ):
	def __init__( self, *args, **option ):
		option[ 'drag_mode' ] = 'all'
		option[ 'multiple_selection' ] = True
		super( SceneSearchDetailListWidget, self ).__init__( *args, **option )
		self.setObjectName( 'SceneSearchDetailList' )
		self.setIndentation( 0 )

	def getHeaderInfo( self ):
		return [('Name',350), ('Group', 80 ), ('Type', 80), ('V',27 ), ('L',27 ), ( 'Layer', 80 ), ( 'Com', -1 ) ]

	def getRootNode( self ):
		return self.owner

	def getNodeParent( self, node ): # reimplemnt for target node	
		if node == self.owner: return None
		return self.owner

	def getNodeChildren( self, node ):
		if node == self.owner:
			return self.owner.getEntityInList()
		else:
			return []

	def createItem( self, node ):
		return SceneSearchDetailListItem()
	
	def updateHeaderItem( self, item, col, info ):
		if info[0] == 'V':
			item.setText( col, '')
			item.setIcon( col, getIcon( 'entity_vis' ) )
		elif info[0] == 'L':
			item.setText( col, '')
			item.setIcon( col, getIcon( 'entity_lock' ) )

	def updateItemContent( self, item, node, **option ):
		if node == self.owner: return 
		# name = node.getName( node )
		# item.setText( 0, name or '<unknown>' )
		# item.setIcon( 0, getIcon( 'entity' ) )
		node.forceUpdate( node )
		if node['FLAG_PROTO_SOURCE']:
			item.setIcon( 0, getIcon('proto') )
		elif node['PROTO_INSTANCE_STATE']:
			item.setIcon( 0, getIcon('instance') )
		elif node['__proto_history']:
			item.setIcon( 0, getIcon('instance-sub') )
		elif node[ '__prefabId' ]:
			item.setIcon( 0, getIcon('instance-prefab') )
		elif isMockInstance( node, 'ProtoContainer' ):
			item.setIcon( 0, getIcon('instance-container') )
		elif isMockInstance( node, 'PrefabContainer' ):
			item.setIcon( 0, getIcon('instance-prefab-container') )
		else:
			item.setIcon( 0, getIcon('obj') )
		item.setText( 0, node.getFullName( node ) or '<unnamed>' )

		item.setText( 1, node.getRootGroupName( node ) )

		item.setText( 2, getMockClassName( node ) )

		#update icon
		if node.isVisible( node ):
			item.setIcon( 3, getIcon( 'entity_vis' ) )
		elif node.isLocalVisible( node ):
			item.setIcon( 3, getIcon( 'entity_parent_invis' ) )
		else:
			item.setIcon( 3, getIcon( 'entity_invis' ) )

		if node.isEditLocked( node ):
			if node.isLocalEditLocked( node ):
				item.setIcon( 4, getIcon( 'entity_lock' ) )
			else:
				item.setIcon( 4, getIcon( 'entity_parent_lock' ) )
		else:
			item.setIcon( 4, getIcon( 'entity_nolock' ) )


		layerName = node.getLayer( node )
		if isinstance( layerName, tuple ):
			item.setText( 5, '????' )
		else:
			item.setText( 5, layerName )

		item.setText( 6, node.getComponentInfo( node ) or '' )

		#TODO: component brief

	def mousePressEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			item = self.itemAt( ev.pos() )
			if item:
				col = self.columnAt( ev.pos().x() )
				if col == 3:
					node = self.getNodeByItem( item )
					self.owner.doCommand( 'scene_editor/toggle_entity_visibility', target = node )
					self.refreshNodeContent( node, updateChildren = True )
					return
				elif col == 4:
					node = self.getNodeByItem( item )
					self.owner.doCommand( 'scene_editor/toggle_entity_lock', target = node )
					self.refreshNodeContent( node, updateChildren = True )
					return
			
		return super( SceneSearchDetailListWidget, self ).mousePressEvent( ev )

	def mimeData( self, items ):
		return makeSceneObjectMimeData( [ item.node for item in items ])
		
	def onItemSelectionChanged(self):
		self.owner.onListSelectionChanged()

	def onItemActivated( self, item, col ):
		node = item.node
		self.owner.onActivateNode( node, 'list' )

	def onClipboardCopy( self ):
		clip = QtWidgets.QApplication.clipboard()
		clip.setMimeData( makeSceneObjectMimeData( self.getSelection() ) )
		return True

##----------------------------------------------------------------##
class SceneSearchTagFilterWidget( SearchFilterWidget ):
	def __init__( self, *args, **kwargs ):
		super( SceneSearchTagFilterWidget, self ).__init__( *args, **kwargs )
		self.filterChanged.connect( self.onFilterChanged )
	
	def onFilterChanged( self ):
		self.owner.updateTagFilter()


##----------------------------------------------------------------##
class SceneSearchStatusBar( QtWidgets.QFrame ):
	def __init__( self, *args, **kwargs ):
		super( SceneSearchStatusBar, self ).__init__( *args, **kwargs )
		layout = QtWidgets.QVBoxLayout( self )
		layout.setSpacing( 1 )
		layout.setContentsMargins( 1 , 1 , 1 , 1 )

		self.textStatus = ElidedLabel( self )
		self.textStatus.setMinimumHeight( 15 )
		layout.addWidget( self.textStatus )

	def setText( self, text ):
		self.textStatus.setText( text )

##----------------------------------------------------------------##
class SceneSearchTreeFilter( GenericTreeFilter ):
	pass

##----------------------------------------------------------------##
#TODO: allow sort by other column
class SceneSearchTreeItem(QtWidgets.QTreeWidgetItem):
	def __lt__(self, other):
		node0 = self.node
		node1 = hasattr(other, 'node') and other.node or None
		if not node1:
			return True
		tree = self.treeWidget()

		t0 = node0.getType()
		t1 = node1.getType()
		if t1!=t0:			
			if tree.sortOrder() == 0:
				if t0 == 'group': return True
				if t1 == 'group': return False
			else:
				if t0 == 'group': return False
				if t1 == 'group': return True
		return super( SceneSearchTreeItem, self ).__lt__( other )
		# return node0.getName().lower()<node1.getName().lower()

##----------------------------------------------------------------##
class SceneSearchTreeWidget( GenericTreeWidget ):
	def __init__( self, *args, **option ):
		option[ 'show_root' ] = False
		option[ 'editable'  ] = True

		super( SceneSearchTreeWidget, self ).__init__( *args, **option )
		self.setHeaderHidden( True )

	def saveTreeStates( self ):
		pass

	def loadTreeStates( self ):
		pass
		
	def getRootNode( self ):
		return self.owner.getFilterRootGroup()

	def getNodeParent( self, node ): # reimplemnt for target node
		return node.getParent()

	def getNodeChildren( self, node ):
		result = []
		for node in node.getChildren():
			result.append( node )
		return result

	def createItem( self, node ):
		return SceneSearchTreeItem()

	def updateItemContent( self, item, node, **option ):
		t = node.getType()
		item.setText( 0, node.getName() )
		if t == 'group':
			item.setIcon(0, getIcon( 'folder-tag' ) )
		else:
			item.setIcon(0, getIcon( 'asset-filter' ) )

	def getHeaderInfo( self ):
		return [ ('Name',120) ]

	def onClicked(self, item, col):
		pass

	def onItemSelectionChanged(self):
		for f in self.getSelection():
			self.owner.setSearchFilter( f )

	def onItemChanged( self, item, col ):
		node = self.getNodeByItem( item )
		self.owner.renameFilter( node, item.text( 0 ) )
		
	def onDeletePressed( self ):
		for f in self.getSelection():
			self.owner.onFilterRequestDelete( f )
		
		