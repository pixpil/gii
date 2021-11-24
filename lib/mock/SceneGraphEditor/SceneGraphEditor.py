from functools import cmp_to_key

import random
import os.path
import json

##----------------------------------------------------------------##
from gii.core        import app, signals, slot, printTraceBack, RemoteCommand
from gii.core.model  import *
from gii.core.AssetUtils import *
from gii.core.mime import *

from gii.qt          import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.dialogs                    import alertMessage, requestConfirm, requestString
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter
from gii.qt.controls.SimpleTitleBar    import SimpleTitleBar
from gii.qt.helpers                    import makeBrush, makeFont, restrainWidgetToScreen

from gii.moai.MOAIRuntime import MOAILuaDelegate
from gii.SceneEditor      import SceneEditorModule

from gii.SearchView       import requestSearchView, registerSearchEnumerator

##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt, QObject
from qtpy.QtGui     import QBrush, QColor, QPen, QIcon, QPalette
from qtpy.QtWidgets import QApplication, QStyle
from qtpy.QtCore    import QEventLoop, QEvent

##----------------------------------------------------------------##
from mock import _MOCK, _MOCK_EDIT, isMockInstance, MOCKPreviewCanvas
##----------------------------------------------------------------##


def getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


_brushAnimatable = makeBrush( color = '#5f3d26' )
_fontAnimatable  = makeFont( bold = True, italic = True )

def makeSceneGraphMimeData( source, objects ):
	ids =[]
	for obj in objects:
		if isMockInstance( obj, 'Entity' ):
			guid = obj['__guid']
			if guid:
				ids.append( guid )
	output = {
		'source': source,
		'ids': ids
	}
	outputData = json.dumps( output ).encode('utf-8')
	data = QtCore.QMimeData()
	data.setData( GII_MIME_ENTITY_REF, outputData )
	return data

##----------------------------------------------------------------##
class SceneGraphEditor( SceneEditorModule ):
	def __init__(self):
		super( SceneGraphEditor, self ).__init__()
		self.sceneDirty       = False
		self.sceneState       = None
		self.activeSceneNode  = None
		self.refreshScheduled = False
		self.previewing       = False
		self.workspaceState   = None
		self.recentScenes     = []

		self.groupSoloVis     = False
		self.groupSoloOpacity = False
		self.groupSoloEdit    = True

		self.lockRootGroup  = False
		self.previousManualRootGroupName   = None
		self.previousRootGroupName = None

	def getName( self ):
		return 'scenegraph_editor'

	def getDependency( self ):
		return [ 'scene_editor', 'mock' ]

	def onRegister( self, name ):
		modulePreview = self.getModule( 'game_preview' )
		modulePreview.registerPreviewCanvas( MOCKPreviewCanvas )

	def onLoad( self ):
		#UI
		self.windowTitle = 'Scenegraph'
		self.container = self.requestDockWindow( 'SceneGraphEditor',
			title     = 'Scenegraph',
			size      = (200,200),
			minSize   = (200,200),
			dock      = 'left'
			)

		#Components
		self.groupManager = GroupManagerWidget()
		self.groupManager.owner = self
		self.groupManager.hide()

		self.headerRootGroup = self.container.addWidget(
			HeaderRootGroupWidget( self.container ),
			expanding = True
		)
		self.headerRootGroup.owner = self

		self.treeFilter = self.container.addWidget(
			GenericTreeFilter(
				self.container
			),
			expanding = False
		)
		self.tree = self.container.addWidget( 
				SceneGraphTreeWidget( 
					self.container,
					sorting  = True,
					editable = True,
					multiple_selection = True,
					drag_mode = 'internal'
				)
			)
		self.treeFilter.setTargetTree( self.tree )
		self.tree.module = self
		self.tool = self.addToolBar( 'scene_graph', self.container.addToolBar() )
		
		self.entityCreatorMenu=self.addMenu( 'main/scene/entity_create',
			dict( label = 'Create Entity' )
		)

		self.componentCreatorMenu=self.addMenu( 'main/scene/component_create',
			dict( label = 'Create Component' )
		)


		#menu
		self.addMenuItem(
			'main/file/open_scene', 
			dict( label = 'Open Scene', shortcut = 'ctrl+shift+o' )
			)

		self.addMenuItem(
			'main/file/open_recent_scene', 
			dict( label = 'Open Recent Scene', shortcut = 'ctrl+alt+o' )
			)

		self.addMenuItem( 'main/file/close_scene', 
			dict( label = 'Close Scene', shortcut = 'Ctrl+W' )
			)
		self.addMenuItem( 'main/scene/save_scene',
			dict( label = 'Save', shortcut = 'Ctrl+S' )
			)
		self.addMenuItem( 'main/scene/locate_scene_asset',
			dict( label = 'Locate Scene Asset' )
			)

		self.addMenu( 'main/scene/----' )
		self.addMenuItem( 'main/scene/toggle_introspector_lock',
			dict( label = 'Toggle Introspector Lock', shortcut = 'Ctrl+I' )
		)

		self.addMenuItem( 'main/scene/lock_scenegroup',
			dict( label = 'Lock Scene Graph', type = 'check' )
		)

		self.addMenu( 'main/scene/----' )
		self.addMenuItem( 'main/scene/reallocate_scene_guid',
			dict( label = 'Reallocate Entity GUIDs' )
			)

		self.addMenu( 'main/scene/----' )
		self.addMenuItem( 'main/scene/change_root_group',    dict( label = 'Change Scene Group', shortcut = 'ctrl+j' ) )
		
		self.addMenuItem( 'main/asset/----' )
		self.addMenuItem( 'main/asset/sync_mock_asset', dict( label = 'Sync MOCK Assets' ) )

		##
		self.addMenu( 'component_context', dict( label = 'Selected Component' ) )
		self.addMenuItem( 'component_context/remove_component', dict( label = 'Remove' ) )
		self.addMenuItem( 'component_context/----' )
		self.addMenuItem( 'component_context/copy_component', 	dict( label = 'Copy' ) )
		self.addMenuItem( 'component_context/paste_component', 	dict( label = 'Paste Component Here' ) )
		self.addMenuItem( 'component_context/----' )
		self.addMenuItem( 'component_context/toggle_bypass',	dict( label = 'Toggle Bypassing Component' ) )
		self.addMenuItem( 'component_context/----' )
		self.addMenuItem( 'component_context/move_component_up', dict( label = 'Move Up' ) )
		self.addMenuItem( 'component_context/move_component_down', dict( label = 'Move Down' ) )
		self.addMenuItem( 'component_context/----' )
		self.addMenuItem( 'component_context/edit_component_alias', dict( label = 'Edit Alias' ) )
		self.addMenuItem( 'component_context/----' )
		self.addMenuItem( 'component_context/show_component_source', dict( label = 'Show Source File' ) )

		self.addMenu( 'main/entity', dict( label = 'Entity' ) )
		
		self.addMenuItem( 'main/entity/add_empty_entity',    dict( label = 'Create Empty', shortcut = 'ctrl+alt+N' ) )
		self.addMenuItem( 'main/entity/add_entity',          dict( label = 'Create',       shortcut = 'ctrl+shift+N' ) )
		
		self.addMenuItem( 'main/entity/----' )
		self.addMenuItem( 'main/entity/load_prefab',         dict( label = 'Load Prefab', shortcut = 'ctrl+alt+shift+N' ) )
		self.addMenuItem( 'main/entity/load_prefab_in_container', dict( label = 'Load Prefab In Container', shortcut = 'ctrl+shift+=' ) )
		
		self.addMenuItem( 'main/entity/----' )
		self.addMenuItem( 'main/entity/remove_entity',       dict( label = 'Remove'  ) )
		self.addMenuItem( 'main/entity/clone_entity',        dict( label = 'Clone',  shortcut = 'ctrl+d' ) )
		
		self.addMenuItem( 'main/entity/----' )
		self.addMenuItem( 'main/entity/add_component',       dict( label = 'Add Component', shortcut = 'ctrl+alt+=' ) )
		self.addMenuItem( 'main/entity/assign_layer',        dict( label = 'Assign Layer', shortcut = 'ctrl+alt+L' ) )
		self.addMenuItem( 'main/entity/toggle_visibility',   dict( label = 'Toggle Visibility' ) )
		self.addMenuItem( 'main/entity/freeze_entity_pivot', dict( label = 'Freeze Pivot' ) )
		self.addMenuItem( 'main/entity/replace_entity_class',dict( label = 'Replace Entity' ) )
		self.addMenuItem( 'main/entity/reset_group_loc',     dict( label = 'Reset Group Location' ) )

		self.addMenuItem( 'main/entity/----' )
		self.addMenuItem( 'main/find/find_entity', dict( label = 'Find In Scene', shortcut = 'ctrl+f' ) )
		self.addMenuItem( 'main/find/find_entity_in_group', dict( label = 'Find In Group', shortcut = 'ctrl+alt+f' ) )
		self.addMenuItem( 'main/find/find_entity_group', dict( label = 'Find Group' ) )
		self.addMenuItem( 'main/find/find_asset_in_entity', dict( label = 'Find Asset In Entity', shortcut = 'ctrl+e' ) )

		#Toolbars
		self.addTool( 'scene_graph/select_scene',    label ='Select Scene', icon = 'settings' )
		self.addTool( 'scene_graph/----'  )
		self.addTool( 'scene_graph/create_group',    label ='+ Group', icon = 'add_folder' )
		self.addTool( 'scene_graph/----'  )
		self.addTool( 'scene_graph/make_proto',    label = 'Convert To Proto', icon = 'proto_make' )
		self.addTool( 'scene_graph/save_prefab',   label = 'Save to Prefab', icon = 'prefab_make' )
		self.addTool( 'scene_graph/----'  )
		self.addTool( 'scene_graph/create_proto_instance',    label = 'Create Proto Instance', icon = 'proto_instantiate' )
		self.addTool( 'scene_graph/create_proto_container',    label = 'Create Proto Container', icon = 'proto_container' )
		self.addTool( 'scene_graph/----'  )
		self.addTool( 'scene_graph/refresh_tree',  label = 'R', icon = 'refresh' )

		self.addTool( 'scene/refresh', label = 'refresh', icon='refresh' )

		#ShortCuts
		self.addShortcut( self.container, 'ctrl+/', 'scene_editor/toggle_entity_visibility' )
		# self.addShortcut( self.container, 'ctrl+alt+/', 'scene_editor/toggle_entity_group_solo' )

		#SIGNALS
		signals.connect( 'moai.clean',        self.onMoaiClean        )

		signals.connect( 'scene.clear',       self.onSceneClear      )
		signals.connect( 'scene.change',      self.onSceneChange     )

		signals.connect( 'selection.changed', self.onSelectionChanged )
		signals.connect( 'selection.hint',    self.onSelectionHint    )

		signals.connect( 'preview.start',     self.onPreviewStart     )
		signals.connect( 'preview.stop' ,     self.onPreviewStop      )

		# signals.connect( 'animator.start',     self.onAnimatorStart     )
		# signals.connect( 'animator.stop' ,     self.onAnimatorStop      )

		signals.connect( 'entity.added',      self.onEntityAdded      )
		signals.connect( 'entity.removed',    self.onEntityRemoved    )
		signals.connect( 'entity.renamed',    self.onEntityRenamed    )
		signals.connect( 'entity.reorder',    self.onEntityReorder    )
		signals.connect( 'entity.modified',    self.onEntityModified    )
		signals.connect( 'entity.visible_changed',    self.onEntityVisibleChanged )
		signals.connect( 'entity.pickable_changed',   self.onEntityPickableChanged )


		signals.connect( 'prefab.unlink',     self.onPrefabUnlink    )
		signals.connect( 'prefab.relink',     self.onPrefabRelink    )
		signals.connect( 'prefab.pull',       self.onPrefabPull      )

		signals.connect( 'proto.unlink',      self.onPrefabUnlink    )
		signals.connect( 'proto.relink',      self.onPrefabRelink    )

		signals.connect( 'app.ready', self.postAppReady )


		signals.connect( 'component.added',   self.onComponentAdded   )
		signals.connect( 'component.removed', self.onComponentRemoved )

		signals.connect( 'project.presave',   self.preProjectSave )

		signals.connect( 'asset.modified', self.onAssetModified )
		signals.connect( 'asset.imported_all', self.postAssetImport )


		registerSearchEnumerator( sceneObjectSearchEnumerator )
		registerSearchEnumerator( entityNameSearchEnumerator )
		registerSearchEnumerator( componentNameSearchEnumerator )
		registerSearchEnumerator( layerNameSearchEnumerator )

		self.delegate = MOAILuaDelegate( self )
		self.delegate.load( getModulePath( 'SceneGraphEditor.lua' ) )

		self.detectedModifiedProto = {}

	def onStart( self ):
		self.refreshCreatorMenu()

	def postAppReady( self ):
		self.openPreviousScene()

	def openPreviousScene( self ):
		previousScene = self.getWorkspaceConfig( 'previous_scene', None )
		if previousScene:
			node = self.getAssetLibrary().getAssetNode( previousScene )
			if node:
				node.edit()

	def confirmStop( self ):
		if self.affirmSceneSaved() == 'cancel': return False
		return True

	def onStop( self ):
		if self.activeSceneNode:
			self.setWorkspaceConfig( 'previous_scene', self.activeSceneNode.getNodePath() )
		else:
			self.setWorkspaceConfig( 'previous_scene', False )

	def onSetFocus( self ):
		self.container.show()
		self.container.raise_()
		self.container.setFocus()

	def getActiveSceneNode( self ):
		return self.activeSceneNode
		
	def getActiveScene( self ):
		return self.delegate.safeCallMethod( 'editor', 'getScene' )

	def getActiveSceneRootGroup( self ):
		scene = self.delegate.safeCallMethod( 'editor', 'getScene' )
		if scene:
			return scene.getRootGroup( scene )
		else:
			return None

	def getRootSceneGroups( self ):
		scene = self.delegate.safeCallMethod( 'editor', 'getScene' )
		if scene:
			groups = scene.getRootGroups( scene )
			return [ g for g in groups.values() ]
		else:
			return []

	def listRootGroupsForSearch( self, typeId, context, option ):
		groups = self.getRootSceneGroups()
		result = []
		for g in groups:
			if g._isDefault:
				name = '<DEFAULT>'
			else:
				name = g.getName( g )
			entry = ( g, name, 'scene_group', 'entity_group' )
			result.append( entry )
		return result

	def getAssetPathsInUse( self ):
		if not self.activeSceneNode:
			return []
		assets = self.delegate.safeCallMethod( 'editor', 'getAssetsInUse' )
		if assets:
			return list(assets.keys())
		else:
			return []

	def getAssetsInUse( self, assetType = None ):
		lib = self.getAssetLibrary()
		result = [ lib.getAssetNode( path ) for path in self.getAssetPathsInUse() ]
		if assetType:
			result1 = []
			for node in result:
				if node:
					if node.getType() == assetType:
						result1.append( node )
			result = result1
		return result

	def onAssetModified( self, node ):
		if node.getType() == 'proto':
			if not self.detectedModifiedProto:
				self.detectedModifiedProto = {}
			self.detectedModifiedProto[ node.getPath() ] = True

	def postAssetImport( self ):
		scene = self.delegate.safeCallMethod( 'editor', 'getScene' )
		if not self.detectedModifiedProto: return
		if not scene: return
		needReload = False
		protoInstances = _MOCK.findProtoInstances( scene )
		for protoPath in self.detectedModifiedProto.keys():
			if needReload: break
			for instance in protoInstances.values():
				if _MOCK.hasProtoHistory( instance, protoPath ):
					needReload = True
					break
		self.detectedModifiedProto = False
		if needReload:
			self.reopenScene()

	def updateButtonPanelGroup( self ):
		scene = self.delegate.safeCallMethod( 'editor', 'getScene' )
		group = scene.getDefaultRootGroup( scene )
		if group._isDefault:
			self.headerRootGroup.setButtonText( '<DEFAULT>' )
		else:
			self.headerRootGroup.setButtonText( group.getName( group ) )

	def changeToPreviousRootGroup( self ):
		targetGroupName = self.workspaceState.get( 'active_root_group', self.previousRootGroupName )
		if self.lockRootGroup and self.previousManualRootGroupName:
			targetGroupName = self.previousManualRootGroupName

		if targetGroupName:
			return self.changeRootGroupByName( targetGroupName )
		else:
			return False

	def changeRootGroup( self, group, manual = False ):
		res = self.delegate.safeCallMethod( 'editor', 'changeRootGroup', group )
		if res and res != 'same' :
			self.previousRootGroupName = group.name
			if manual: self.previousManualRootGroupName = group.name
			self.updateButtonPanelGroup()
			self.onSceneGroupChange()
		return res

	def changeRootGroupByName( self, name, manual = False ):
		group = self.delegate.safeCallMethod( 'editor', 'getRootGroup', name )
		if group:
			return self.changeRootGroup( group, manual )
		else:
			return False

	def setGroupSoloVis( self, soloVis ):
		self.groupSoloVis = soloVis
		self.onSceneGroupChange()

	def setGroupSoloOpacity( self, soloOpacity ):
		self.groupSoloOpacity = soloOpacity
		self.onSceneGroupChange()

	def setGroupSoloEdit( self, soloEdit ):
		self.groupSoloEdit = soloEdit
		self.onSceneGroupChange()
		
	def addRootGroup( self ):
		name = requestString('Create Scene Group:', 'Enter Group Name:' )
		if not name: return False
		scene = self.delegate.safeCallMethod( 'editor', 'getScene' )
		if scene.getRootGroup( scene, name ):
			alertMessage( 'warn', 
				'Duplicated scene group name: %s' % name
			)
			return False

		cmd = self.doCommand(
			'scene_editor/create_root_group', 
			name  = name
		)
		if not cmd: return False
		group = cmd.getResult()
		return group

	def removeRootGroup( self, group ):
		if group._isDefault:
			alertMessage( 'warn', 
				'Can not remove DEFAULT scene group'
			)
			return False
		if self.doCommand(
			'scene_editor/remove_root_group', 
			group = group
		):
			scene = self.delegate.safeCallMethod( 'editor', 'getScene' )
			if scene.getDefaultRootGroup( scene ) == group:
				scene.setDefaultRootGroup( scene )
				self.updateButtonPanelGroup()
				self.onSceneGroupChange()
			return True
		else:
			return False

	def cloneRootGroup( self, group ):
		pass

	def renameRootGroup( self, group ):
		if group._isDefault:
			alertMessage( 'warn', 
				'Can not rename DEFAULT scene group'
			)
			return False
		name0 = group.getName( group )
		name = requestString('Rename Scene Group <%s>' % name0, 'Enter New Name (%s):' % name0 )
		if not name: return False
		if name == name0: return False
		
		scene = self.delegate.safeCallMethod( 'editor', 'getScene' )
		if scene.getRootGroup( scene, name ):
			alertMessage( 'warn', 
				'Duplicated scene group name: %s' % name
			)
			return False

		if self.doCommand(
			'scene_editor/rename_root_group', 
			group = group,
			name  = name
		):
			self.updateButtonPanelGroup()
			self.onSceneGroupChange()
			return True
		else:
			return False

	def listRecentScenes( self, typeId, context, option ):
		entries = []
		lib = self.getAssetLibrary()
		for path in reversed( self.recentScenes ):
			node = lib.getAssetNode( path )
			if node:
				entry = ( node, path, 'scene', 'scene' )
				entries.append( entry )
		return entries

	def locateProto( self, protoNode ):
		if not self.delegate.safeCallMethod( 'editor', 'locateProto', protoNode.getPath() ): return
		if self.getModule('scene_view'):
			self.getModule('scene_view').focusSelection()

	def locateEntityByGUID( self, guid ):
		if not self.delegate.safeCallMethod( 'editor', 'locateEntityByGUID', guid ): return
		if self.getModule('scene_view'):
			self.getModule('scene_view').focusSelection()

	def openSceneByPath( self, path ):
		assetNode = self.getAssetLibrary().getAssetNode( path )
		if assetNode:
			return self.openScene( assetNode )
		return None

	def openScene( self, node ):
		sceneView = self.getModule( 'scene_view' )
		if self.activeSceneNode == node:
			if self.getModule( 'scene_view' ):
				self.getModule( 'scene_view' ).setFocus()

		else:
			if not self.closeScene(): return False
			if sceneView: sceneView.makeCanvasCurrent()
			self.activeSceneNode = node
			signals.emitNow( 'scene.pre_open', node )
			
			if sceneView: sceneView.makeCanvasCurrent()
			scene = self.delegate.safeCallMethod( 'editor', 'openScene', node.getPath() )
			if not scene:
				#todo: raise something
				alertMessage( 'error', 
					'%s\n\nfailed to open scene, see console for detailed information.' % node.getPath() )
				self.activeSceneNode = None
				return False
			
			self.sceneState = 'ok'

			signals.emitNow( 'scene.open', self.activeSceneNode, scene )
			self.setFocus()
			self.loadWorkspaceState( False )
			if sceneView: sceneView.makeCanvasCurrent()
			self.delegate.safeCallMethod( 'editor', 'postOpenScene' )
			toolMgr = self.getModule( 'scene_tool_manager' )
			if toolMgr:
				toolMgr.resetTool()
			self.changeSelection( None )

			if self.changeToPreviousRootGroup() == True:
				pass
			else:
				self.updateButtonPanelGroup()
				self.onSceneGroupChange()
			
			self.setWorkspaceConfig( 'active_scene', self.activeSceneNode.getNodePath() )
			
		return True

	def affirmSceneSaved( self ):
		if self.sceneDirty:
			res = requestConfirm( 'scene modified!', 'save scene before close?' )
			if res == True:   #save
				self.saveScene()
				return True
			elif res == None: #cancel
				return 'cancel'
			elif res == False: #no save
				return False
		else:
			return True

	def closeScene( self ):
		if self.previewing:
			alertMessage( 'Previewing', 'stop prevewing before closing scene' )
			return False

		if not self.activeSceneNode: return True
		if self.affirmSceneSaved() == 'cancel': return False

		path = self.activeSceneNode.getPath()
		try:
			self.recentScenes.remove( path )
		except Exception as e:
			pass
			
		self.saveWorkspaceState()
		
		self.sceneState = None
		self.tree.clear()
		self.getApp().clearCommandStack( 'scene_editor' )
		signals.emitNow( 'scene.close', self.activeSceneNode )
		self.delegate.safeCallMethod( 'editor', 'closeScene' )		
		self.recentScenes.append( path )
		self.markSceneDirty( False )
		self.activeSceneNode = None
		self.workspaceState  = None
		
		return True

	def onSceneClear( self ):
		# self.tree.clear()
		pass

	def findEntityByGUID(self,guid):
		return self.delegate.safeCallMethod('editor','findEntityByGUID',guid)

	def findComByGUID(self,guid):
		return self.delegate.safeCallMethod('editor','findComByGUID',guid)

	def markSceneDirty( self, dirty = True ):
		if not self.previewing:
			if self.activeSceneNode:
				if dirty != self.sceneDirty:
					self.sceneDirty = dirty

	def saveWorkspaceState( self ):
		self.retainWorkspaceState()
		treeFoldState      = self.workspaceState['tree_state']
		containerFoldState = self.workspaceState['container_state']
		entityLockState    = self.workspaceState['entity_lock_state']
		activeRootGroupName = self.workspaceState['active_root_group']
		self.activeSceneNode.setWorkspaceData( 'tree_state', treeFoldState )
		self.activeSceneNode.setWorkspaceData( 'container_state', containerFoldState )
		self.activeSceneNode.setWorkspaceData( 'entity_lock_state', entityLockState )
		self.activeSceneNode.setWorkspaceData( 'active_root_group', activeRootGroupName )

	def loadWorkspaceState( self, restoreState = True ):
		treeFoldState      = self.activeSceneNode.getWorkspaceData( 'tree_state', None )		
		containerFoldState = self.activeSceneNode.getWorkspaceData( 'container_state', None )		
		entityLockState    = self.activeSceneNode.getWorkspaceData( 'entity_lock_state', None )	
		activeRootGroupName = self.activeSceneNode.getWorkspaceData( 'active_root_group', None )

		#Legacy support
		if not treeFoldState:
			treeFoldState      = self.activeSceneNode.getMetaData( 'tree_state', None )		
		if not containerFoldState:
			containerFoldState = self.activeSceneNode.getMetaData( 'container_state', None )		
		if not entityLockState:
			entityLockState    = self.activeSceneNode.getMetaData( 'entity_lock_state', None )	
			
		self.workspaceState = {
			'tree_state'        : treeFoldState,
			'container_state'   : containerFoldState,
			'entity_lock_state' : entityLockState,
			'active_root_group' : activeRootGroupName,
		}		
		if restoreState: self.restoreWorkspaceState()

	def retainWorkspaceState( self ):
		#tree node foldstate
		treeFoldState = None
		if self.workspaceState:
			treeFoldState = self.workspaceState.get( 'tree_state', None )
		if not treeFoldState:
			treeFoldState = {}
			
		for key, value in self.tree.saveFoldState().items():
			treeFoldState[ key ] = value
		#save introspector foldstate
		introspectorFoldState = self.delegate.safeCallMethod( 'editor', 'saveIntrospectorFoldState' )
		entityLockState = self.delegate.safeCallMethod( 'editor', 'saveEntityLockState' )
		scene = self.delegate.safeCallMethod( 'editor', 'getScene' )
		g = scene.getDefaultRootGroup( scene )
		self.workspaceState = {
			'tree_state'        : treeFoldState,
			'container_state'   : introspectorFoldState,
			'entity_lock_state' : entityLockState,
			'active_root_group' : g.name
		}

	def restoreWorkspaceState( self ):
		if not self.workspaceState: return
		treeState = self.workspaceState.get( 'tree_state', None )
		if treeState:
			self.tree.loadFoldState( treeState )	
		
		containerState = self.workspaceState.get( 'container_state', None )
		if containerState:
			self.delegate.safeCallMethod( 'editor', 'loadIntrospectorFoldState', containerState )
		
		lockState = self.workspaceState.get( 'entity_lock_state', None )
		if lockState:
			self.delegate.safeCallMethod( 'editor', 'loadEntityLockState', lockState )


	def onSceneGroupChange( self ):
		scene = self.delegate.safeCallMethod( 'editor', 'getScene' )
		scene.updateSolo( scene, self.groupSoloVis, self.groupSoloOpacity, self.groupSoloEdit )
		signals.emit( 'scene.update' )
		signals.emit( 'entity.gizmo_changed', None )
		sceneView = self.getModule( 'scene_view' )
		if sceneView:
			group = self.getActiveSceneRootGroup()
			if group:
				sceneView.setInfo( 'Group:' + group.name )
			else:
				sceneView.setInfo( '' )

		return self.onSceneChange()

	def onSceneChange( self ):
		self.tree.rebuild()
		self.restoreWorkspaceState()
		self.tree.refreshAllContent()
		self.tree.verticalScrollBar().setValue( 0 )
		
	def saveScene( self ):
		if not self.activeSceneNode: return
		
		if self.sceneState == 'error':
			if not requestConfirm(
				'Warning',
				'There are errors in current scene, saving might cause corruption, confirm?'
			):
				return False

		signals.emitNow( 'scene.save' )
		path = self.activeSceneNode.getAbsFilePath()
		res = self.delegate.safeCallMethod( 'editor', 'saveScene', path )
		signals.emitNow( 'scene.saved' )
		if res:
			self.saveWorkspaceState()
			self.markSceneDirty( False )
			return True
		else:
			return False

	def reopenScene( self ):
		if not self.activeSceneNode: return
		if self.previewing: return
		sceneNode = self.activeSceneNode
		self.closeScene()
		self.openScene( sceneNode )

	def refreshScene( self ):
		if not self.activeSceneNode: return
		if self.previewing: return

		self.refreshScheduled = False
		node = self.activeSceneNode

		if self.sceneState == 'ok':
			self.retainWorkspaceState()
		
		#TODO: confirm scene saving if dirty
		if self.delegate.safeCallMethod( 'editor', 'refreshScene' ):
			self.sceneState = 'ok'
			self.restoreWorkspaceState()
		else:
			alertMessage( 'Warning', 'error while refreshing current scene' )
			self.sceneState = 'error'

		self.refreshCreatorMenu()
		self.onSceneGroupChange()

	def scheduleRefreshScene( self ):
		if not self.activeSceneNode: return
		self.refreshScheduled = True

	def refreshCreatorMenu( self ):
		def addEntityMenuItem( name ):
			if name == '----': 
				self.entityCreatorMenu.addChild( '----' )
				return
			self.entityCreatorMenu.addChild({
					'name'     : 'create_entity_'+name,
					'label'    : name,
					'command'  : 'scene_editor/create_entity',
					'command_args' : dict( name = name )
				})

		def addComponentMenuItem( name ):
			if name == '----': 
				self.componentCreatorMenu.addChild( '----' )
				return
			self.componentCreatorMenu.addChild({
					'name'     : 'create_component_'+name,
					'label'    : name,
					'command'  : 'scene_editor/create_component',
					'command_args' : dict( name = name )
				})

		self.entityCreatorMenu.clear()
		self.componentCreatorMenu.clear()

		registry = _MOCK.getEntityRegistry()
		#entity
		keys = sorted( registry.keys() )
		addEntityMenuItem( 'Entity' )
		addEntityMenuItem( '----' )
		for entityName in sorted( registry.keys() ):
			if entityName!='Entity': addEntityMenuItem( entityName )

		#component
		registry = _MOCK.getComponentRegistry()
		for comName in sorted( registry.keys() ):
			addComponentMenuItem( comName )

	def needUpdate( self ):
		return True
		
	def onUpdate( self ):
		if self.refreshScheduled:
			self.refreshScene()

	def preProjectSave( self, prj ):
		if self.activeSceneNode:
			# _MOCK.game.previewingScene = self.activeSceneNode.getNodePath()
			self.setWorkspaceConfig( 'active_scene', self.activeSceneNode.getNodePath() )

	def getAutoCompletion( self, full = False ):
		scene = self.getActiveScene()
		if not scene: return []
		v = {}
		for ent in scene.entities.keys():
			if ent.FLAG_INTERNAL: continue
			if ent.FLAG_EDITOR_OBJECT: continue
			if full:
				name = ent.getFullName( ent, False )
			else:
				name = ent.getName( ent )
			if len( name ) >= 3:
				v[ name ] = True
		entityNames = list( v.keys() )
		return entityNames

	def onMoaiClean( self ):
		self.tree.clear()

	
	def onTool( self, tool ):
		name = tool.name
		if name == 'refresh_tree':
			self.tree.rebuild()

		elif name == 'refresh':
			self.scheduleRefreshScene()
			
		elif name == 'save_prefab':
			requestSearchView( 
				info    = 'select a perfab node to store',
				context = 'asset',
				type    = 'prefab',
				on_selection = lambda obj: self.createPrefab( obj )				
				)
		
		elif name == 'make_proto':
			self.makeProto()

		elif name == 'create_proto_instance' or name == 'load_prefab':
			requestSearchView( 
				info    = 'select a proto to instantiate',
				context = 'asset',
				type    = 'proto;prefab',
				on_selection = 
					lambda obj: 
						self.doCommand( 'scene_editor/create_proto_instance', proto = obj.getNodePath() )
				)

		elif name == 'create_proto_container':
			requestSearchView( 
				info    = 'select a proto to create contained instance',
				context = 'asset',
				type    = 'proto;prefab',
				on_selection = 
					lambda obj: 
						self.doCommand( 'scene_editor/create_proto_container', proto = obj.getNodePath() )
				)

		elif name == 'select_scene':
			self.doCommand( 'scene_editor/select_scene' )

		elif name == 'create_group':
			self.doCommand( 'scene_editor/entity_group_create' )

		elif name == 'group_entity':
			self.doCommand( 'scene_editor/group_entities' )
			
	def onMenu( self, menu ):
		name = menu.name
		if name == 'close_scene':
			if self.previewing:
				alertMessage( 'Warning', 'Stop previewing before closing scene' )
				return
			self.closeScene()

		elif name == 'open_scene':
			if self.previewing:
				alertMessage( 'Warning', 'Stop previewing before opening scene' )
				return
			requestSearchView( 
				info    = 'select scene to open',
				context = 'asset',
				type    = 'scene',
				on_selection = self.openScene
				)
			
		elif name == 'save_scene':
			if self.previewing:
				alertMessage( 'Warning', 'Stop previewing before saving' )
				return
			self.saveScene()

		elif name == 'open_recent_scene':
			if self.previewing:
				alertMessage( 'Warning', 'Stop previewing before opening scene' )
				return
			requestSearchView(
				info    = 'open recently opened scene',
				context = 'asset',
				type    = 'scene',
				on_selection = self.openScene,
				on_search = self.listRecentScenes,
				sort_method = 'none'
				)

		elif name == 'change_root_group':
			requestSearchView(
				info    = 'change active scene group',
				context = 'scene',
				type    = 'scene',
				on_selection = lambda obj: self.changeRootGroup( obj, manual = True ),
				on_search = self.listRootGroupsForSearch,
				sort_method = 'none'
				)

		elif name == 'sync_mock_asset':
			self.getModule( 'mock' ).syncBuiltinAsset()

		elif name == 'locate_scene_asset':
			if self.activeSceneNode:
				assetBrowser = self.getModule( 'asset_browser' )
				if assetBrowser:
					assetBrowser.locateAsset( self.activeSceneNode )

		elif name == 'add_entity':
			requestSearchView( 
				info    = 'select entity type to create',
				context = 'entity_creation',
				on_selection = lambda obj: 
					self.doCommand( 'scene_editor/create_entity', name = obj )
				)

		elif name == 'add_component':
			requestSearchView( 
				info    = 'select component type to create',
				context = 'component_creation',
				on_selection = lambda obj: 
					self.doCommand( 'scene_editor/create_component', name = obj )
				)

		elif name == 'add_empty_entity':
			self.doCommand( 'scene_editor/create_entity', name = 'Empty' )

		elif name == 'load_prefab':
			requestSearchView( 
				info    = 'select a proto to instantiate',
				context = 'asset',
				type    = 'proto;prefab',
				on_selection = 
					lambda obj: 
						self.doCommand( 'scene_editor/create_proto_instance', proto = obj.getNodePath() )
				)

		elif name == 'load_prefab_in_container':
			requestSearchView( 
				info    = 'select a perfab node to instantiate( PefabContainer )',
				context = 'asset',
				type    = 'prefab;proto',
				on_selection = 
					lambda obj: 
						self.doCommand( 'scene_editor/create_prefab_container', prefab = obj.getNodePath() )
				)

		elif name == 'remove_entity':
			self.doCommand( 'scene_editor/remove_entity' )

		elif name == 'replace_entity_class':
			if self.previewing:
				alertMessage( 'Warning', 'Cannot replace entity class while previewing' )
				return
			requestSearchView( 
				info    = 'select target entity class to replace with',
				on_search    = self.onSearchEntityClass,
				on_selection = 
					lambda clas: 
						self.doCommand( 'scene_editor/replace_entity_class', targetClass = clas )
			)				

		elif name == 'clone_entity':
			self.doCommand( 'scene_editor/clone_entity' )

		elif name == 'find_entity':
			requestSearchView( 
				info    = 'search for entity in current scene',
				context = 'scene',
				type    = 'entity',
				on_selection = lambda x: self.selectEntity( x, focus_tree = True ) ,
				on_test      = self.selectEntity
				)

		
		elif name == 'find_entity_in_group':
			requestSearchView( 
				info    = 'search for entity in current entity group',
				context = 'scene',
				type    = 'entity_in_group',
				on_selection = lambda x: self.selectEntity( x, focus_tree = True ) ,
				on_test      = self.selectEntity
				)

		elif name == 'find_entity_group':
			requestSearchView( 
				info    = 'search for group in current scene',
				context = 'scene',
				type    = 'group',
				on_selection = lambda x: self.selectEntity( x, focus_tree = True ) ,
				on_test      = self.selectEntity
				)

		elif name == 'find_asset_in_entity':
			requestSearchView( 
				info    = 'list all asset used in current Entity',
				on_search    = self.onSearchAssetInEntity,
				on_selection = self.getModule( 'asset_browser' ).locateAsset,
				on_test      = self.getModule( 'asset_browser' ).selectAsset
				)

		elif name == 'create_group':
			self.doCommand( 'scene_editor/entity_group_create' )

		elif name == 'remove_component':
			context = menu.getContext()
			if context:
				self.doCommand( 'scene_editor/remove_component', target = context )

		elif name == 'copy_component':
			context = menu.getContext()
			if context:
				self.onCopyComponent( context )

		elif name == 'paste_component':
			context = menu.getContext()
			if context:
				self.onPasteComponent( context.getEntity( context ), context )

		elif name == 'toggle_bypass':
			context = menu.getContext()
			if context:
				com = context
				bypassed = com[ 'FLAG_BYPASSED' ]
				self.doCommand( 'scene_editor/set_bypassed', target = com, value = not bypassed )

		elif name == 'move_component_up':
			context = menu.getContext()
			if context:
				self.onChangeComponentOrder( context, -1 )

		elif name == 'move_component_down':
			context = menu.getContext()
			if context:
				self.onChangeComponentOrder( context, 1 )

		elif name == 'show_component_source':
			context = menu.getContext()
			if context:
				src = context.getClassSourceFile( context ) or ''
				if src.startswith( '@' ):
					path = src[ 1: ]
					if os.path.exists( path ):
						openFileInOS( path )
					else:
						alertMessage( 'File not found', 'Cannot find source file:' + path )
				else:
					alertMessage( 'Invalid Source Path', 'Unknown source:' + path )

		elif name == 'edit_component_alias':
			context = menu.getContext()
			if context:
				oldAlias = context._alias or ''
				alias = requestString( 'Edit Alias', 'Enter Alias:', oldAlias )
				if alias != None:
					if not alias: alias = False
					self.doCommand( 'scene_editor/rename_component', target = context, alias = alias )

		elif name == 'assign_layer':
			if not self.tree.getSelection(): return
			requestSearchView( 
				info    = 'select layer to assign',
				context = 'scene_layer',
				type    = _MOCK.Entity,
				on_selection = self.assignEntityLayer
				)

		elif name == 'toggle_visibility':
			self.doCommand( 'scene_editor/toggle_entity_visibility' )

		elif name == 'freeze_entity_pivot':
			self.doCommand( 'scene_editor/freeze_entity_pivot' )

		elif name == 'reset_group_loc':
			self.doCommand( 'scene_editor/reset_group_loc' )

		elif name == 'reallocate_scene_guid':
			if requestConfirm( 
				'Reallocating GUID',
				'not UNDOABLE operation, confirm?\n'
				):
				self.doCommand( 'scene_editor/reallocate_scene_guid' )
				self.markSceneDirty()

		elif name == 'toggle_introspector_lock':
			m = self.getModule( 'introspector' )
			locked = None
			for instance in m.instances:
				if instance.locked:
					locked = True
			for instance in m.instances:
				instance.setLocked( not locked )

		elif name == 'lock_scenegroup':
			checked = menu.getValue()
			self.lockRootGroup = checked
			g = self.getActiveSceneRootGroup()
			if g:
				self.previousManualRootGroupName = g.name

	def onSelectionChanged( self, selection, key ):
		if key != 'scene': return
		if self.tree.syncSelection:
			self.tree.blockSignals( True )
			for e in selection:
				if not ( isMockInstance( e, 'EntityGroup' ) or isMockInstance( e, 'Entity' ) ): continue
				rootGroup = e.getRootGroup( e )
				if rootGroup:
					self.changeRootGroup( rootGroup )
					break
			self.tree.selectNode( None )
			for e in selection:
				self.tree.selectNode( e, add = True)				
			self.tree.blockSignals( False )

	def selectEntity( self, target, **option ):
		if option.get( 'focus_tree', False ):
			self.tree.setFocus()
		self.changeSelection( target )

	##----------------------------------------------------------------##
	def renameEntity( self, target, name ):
		self.doCommand( 'scene_editor/rename_entity', target = target, name = name )

	def addEntityNode( self, entity ):
		self.tree.addNode( entity, expanded = False )
		self.tree.setNodeExpanded( entity, False )

	def addEntityGroupNode( self, entity ):
		self.tree.addNode( entity, expanded = True )
		self.tree.setNodeExpanded( entity, True )

	def removeEntityNode( self, entity ):
		self.tree.removeNode( entity )

	def assignEntityLayer( self, layerName ):
		#TODO:command pattern
		if not layerName: return
		self.doCommand( 'scene_editor/assign_layer', target = layerName )

	def onSelectionHint( self, selection ):
		if selection._entity:
			self.changeSelection( selection._entity )			
		else:
			self.changeSelection( selection )

	def onSearchAssetInEntity( self, typeId, context, option ):
		collected = self.delegate.callMethod( 'editor', 'getAssetInSelectedEntity' )
		lib       = self.getAssetLibrary()
		result    = []
		for path in collected.values():
			node = lib.getAssetNode( path )
			if node:
				entry = ( node, path, node.getType(), lib.getAssetIcon( node.getType() ) )
				result.append( entry )
		return result

	def onPreviewStart( self ):
		if not self.activeSceneNode: return
		self.retainWorkspaceState()
		self.delegate.safeCallMethod( 'editor', 'retainScene' )
		self.delegate.safeCallMethod( 'editor', 'startScenePreview' )
		self.previewing = True

	def onPreviewStop( self ):
		if not self.activeSceneNode: return
		self.changeSelection( None )
		self.tree.clear()
		self.delegate.safeCallMethod( 'editor', 'stopScenePreview' )
		self.previewing = False
		if self.delegate.safeCallMethod( 'editor', 'restoreScene' ):
			self.restoreWorkspaceState()

	def onAnimatorStart( self ):
		self.retainWorkspaceState()
		self.delegate.safeCallMethod( 'editor', 'retainScene' )

	def onAnimatorStop( self ):
		self.tree.clear()
		self.delegate.safeCallMethod( 'editor', 'clearScene' )
		if self.delegate.safeCallMethod( 'editor', 'restoreScene' ):
			self.restoreWorkspaceState()

	##----------------------------------------------------------------##
	def updateEntityPriority( self ):
		if not self.activeSceneNode: return
		self.markSceneDirty()

	def onEntityRenamed( self, entity, newname ):
		self.tree.refreshNodeContent( entity )
		self.markSceneDirty()

	def onEntityReorder( self, entity ):
		self.tree.setSortingEnabled( False )
		self.tree.setSortingEnabled( True )
		self.markSceneDirty()

	def onEntityVisibleChanged( self, entity ):
		self.tree.refreshNodeContent( entity )
		self.markSceneDirty()

	def onEntityPickableChanged( self, entity ):
		self.tree.refreshNodeContent( entity )
		self.markSceneDirty()

	def onEntityAdded( self, entity, context = None ):
		if context in ( 'new', 'clone', 'drag', 'instance' ):
			pnode = entity.parent
			if pnode:
				self.tree.setNodeExpanded( pnode, True )
			if context != 'clone':
				self.tree.selectNode( entity )
			if context == 'new':
				self.setFocus()
				self.tree.setFocus()
				self.tree.editNode( entity )
				
		signals.emit( 'scene.update' )
		self.markSceneDirty()

	def onEntityRemoved( self, entity ):
		signals.emit( 'scene.update' )
		self.markSceneDirty()

	def onEntityModified( self, entity, context = None ):
		self.markSceneDirty()

	##----------------------------------------------------------------##
	def onComponentAdded( self, com, entity ):
		signals.emit( 'scene.update' )
		self.markSceneDirty()

	def onComponentRemoved( self, com, entity ):
		signals.emit( 'scene.update' )
		self.markSceneDirty()


	##----------------------------------------------------------------##
	def onPrefabUnlink( self, entity ):
		self.tree.refreshNodeContent( entity, updateChildren = True )

	def onPrefabPull( self, entity ):
		self.markSceneDirty()
		self.tree.selectNode( entity )

	def onPrefabRelink( self, entity ):
		self.tree.refreshNodeContent( entity, updateChildren = True )

	def createPrefab( self, targetPrefab ):
		selection = self.getSelection()
		if not selection: return
		if len( selection ) > 1:
			return alertMessage( 'multiple entities cannot be converted into prefab' )
		target = selection[0]
		if requestConfirm( 'convert prefab', 'Push selected Entity into Prefab?\n' + targetPrefab.getNodePath() ):
			self.doCommand( 'scene_editor/create_prefab', 
				entity = target, 
				prefab = targetPrefab.getNodePath(),
				file   = targetPrefab.getAbsFilePath()
			)

	def makeProto( self ):
		selection = self.getSelection()
		if not selection: return
		if len( selection ) > 1:
			if requestConfirm( 'convert protos', 'Convert multiple Entities into Protos?' ):
				for target in selection:
					self.doCommand( 'scene_editor/make_proto', 
						entity = target
					)
					self.tree.refreshNodeContent( target )

		else:
			target = selection[0]
			if not target: return
			if requestConfirm( 'convert proto', 'Convert this Entity into Proto?' ):
				self.doCommand( 'scene_editor/make_proto', 
					entity = target
				)
				self.tree.refreshNodeContent( target )

	def createProtoInstance( self ):
		pass


	##----------------------------------------------------------------##
	def copyEntityToClipboard( self ):
		entityGroupData = self.delegate.callMethod( 'editor', 'makeSceneSelectionCopyData' )
		if not entityGroupData: 
			alertMessage( 'not implemented', 'failed to copy entities' )
			return False
		clip = QtWidgets.QApplication.clipboard()
		mime = QtCore.QMimeData()
		text = ''
		for s in self.getSelection():
			if text == '':
				text = text + s.name
			else:
				text = text + '\n' + s.name
		mime.setText( text )
		mime.setData( GII_MIME_ENTITY_DATA, entityGroupData.encode('utf-8') )
		if len( self.getSelection() ) == 1:
			ent = self.getSelection()[ 0 ]
			scenePath = self.activeSceneNode.getPath()
			url = self.getApp().makeURL( 'scene', path = scenePath, entity_id = ent.__guid )
			mime.setUrls( [ QtCore.QUrl( url ) ] )
		clip.setMimeData( mime )
		return True

	def cutEntityToClipboard( self ):
		if not self.copyEntityToClipboard():
			return False
		self.doCommand( 'scene_editor/remove_entity' )
		return True

	def pasteEntityFromClipboard( self, pos = 'into' ):
		clip = QtWidgets.QApplication.clipboard()
		mime = clip.mimeData()
		if mime.hasFormat( GII_MIME_ENTITY_DATA ):
			data = mime.data( GII_MIME_ENTITY_DATA )
			self.doCommand( 'scene_editor/paste_entity',
				data = str( data, encoding = 'utf-8' ),
				pos  = pos
			)

	##----------------------------------------------------------------##
	def onCopyComponent( self, targetComponent ):
		componentData = self.delegate.callMethod( 'editor', 'makeComponentCopyData', targetComponent )
		if not componentData: return False
		clip = QtWidgets.QApplication.clipboard()
		mime = QtCore.QMimeData()
		mime.setData( GII_MIME_COMPONENT_DATA, componentData.encode( 'utf-8' ) )
		clip.setMimeData( mime )
		return True

	def onPasteComponent( self, targetEntity, beforeComponent = None ):
		clip = QtWidgets.QApplication.clipboard()
		mime = clip.mimeData()
		if mime.hasFormat( GII_MIME_COMPONENT_DATA ):
			data = mime.data( GII_MIME_COMPONENT_DATA )
			self.doCommand( 'scene_editor/paste_component',
				targetEntity = targetEntity,
				data = str( data, encoding = 'utf-8' ),
				before = beforeComponent
			)
		else:
			alertMessage( 'no data', 'no component data' )

	def onChangeComponentOrder( self, targetComponent, delta ):
		self.doCommand( 'scene_editor/change_component_order',
				target = targetComponent,
				delta  = delta
			)
		

##----------------------------------------------------------------##
class RootGroupTitleButton( QtWidgets.QToolButton ):
	def __init__( self, *args ):
		super( RootGroupTitleButton, self ).__init__( *args )
		self.setFixedHeight( 20 )
		self.setToolButtonStyle( Qt.ToolButtonTextBesideIcon )
		self.setIcon( getIcon( 'entity_group' ) )
		self.setText( '<DEFAULT>' )
		self.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )


class HeaderRootGroupWidget( QtWidgets.QWidget ):
	def __init__( self, *args ):
		super( HeaderRootGroupWidget, self ).__init__( *args )
		self.owner = None
		layout = QtWidgets.QHBoxLayout( self )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		layout.setSpacing( 1 )
		
		self.buttonSoloVis  = QtWidgets.QToolButton( self )
		self.buttonSoloOpacity = QtWidgets.QToolButton( self )
		self.buttonSoloEdit = QtWidgets.QToolButton( self )

		self.buttonSoloVis.setObjectName( 'ButtonSoloVis' )
		self.buttonSoloOpacity.setObjectName( 'ButtonSoloVis' )
		self.buttonSoloEdit.setObjectName( 'ButtonSoloEdit' )

		self.buttonSoloVis.setCheckable( True )
		self.buttonSoloOpacity.setCheckable( True )
		self.buttonSoloEdit.setCheckable( True )
		self.buttonSoloEdit.setChecked( True )
		self.buttonSoloVis.setText( 'Vis' )
		self.buttonSoloOpacity.setText( 'Opac' )
		self.buttonSoloEdit.setText( 'Edit' )
		
		self.buttonPanelGroup =	RootGroupTitleButton( self )
		
		self.label = QtWidgets.QLabel( self )
		self.label.setText( ' Solo:')

		layout.addWidget( self.buttonPanelGroup )
		layout.addWidget( self.label )
		layout.addWidget( self.buttonSoloVis )
		layout.addWidget( self.buttonSoloOpacity )
		layout.addWidget( self.buttonSoloEdit )

		self.buttonSoloVis.clicked.connect( self.onSoloVisChange )
		self.buttonSoloOpacity.clicked.connect( self.onSoloOpacityChange )
		self.buttonSoloEdit.clicked.connect( self.onSoloEditChange )
		self.buttonPanelGroup.clicked.connect( self.onShowPanelGroupManager )
		self.setFixedHeight( 20 )

	def setButtonText( self, text ):
		self.buttonPanelGroup.setText( text )

	def onShowPanelGroupManager( self ):
		pos = self.buttonPanelGroup.mapToGlobal(
			self.buttonPanelGroup.pos()
		)
		self.owner.groupManager.start( pos )

	def onSoloVisChange( self ):
		soloVis = self.buttonSoloVis.isChecked()
		self.owner.setGroupSoloVis( soloVis )

	def onSoloOpacityChange( self ):
		soloOpacity = self.buttonSoloOpacity.isChecked()
		self.owner.setGroupSoloOpacity( soloOpacity )

	def onSoloEditChange( self ):
		soloEdit = self.buttonSoloEdit.isChecked()
		self.owner.setGroupSoloEdit( soloEdit )
	

##----------------------------------------------------------------##
class WindowAutoHideEventFilter( QObject ):
	def eventFilter(self, obj, event):
		e = event.type()		
		if e == QEvent.KeyPress and event.key() == Qt.Key_Escape:
			obj.hide()
		elif e == QEvent.WindowDeactivate:
			obj.hide()

		return QObject.eventFilter( self, obj, event )


##----------------------------------------------------------------##
class SceneGroupListView( GenericTreeWidget ):
	def __init__( self, *args, **option ):
		super( SceneGroupListView, self ).__init__( *args, **option )
		self.setAttribute(Qt.WA_MacShowFocusRect, False)

	def getOwner( self ):
		return self.parent().getOwner()

	def getHeaderInfo( self ):
		return [('Scene Group', 170), ('State',30 ) ]

	def getRootNode( self ):
		return self.getOwner()

	def getNodeParent( self, node ):
		if node == self.getOwner():
			return None
		return self.getOwner()

	def getNodeChildren( self, node ):
		if node == self.getOwner():
			return self.getOwner().getRootSceneGroups()

	def updateItemContent( self, item, node, **option ):
		if node == self.getOwner():
			return
		item.setIcon( 0, getIcon( 'entity_group' ) )
		if node._isDefault:
			item.setText( 0 , '<DEFAULT>' )
		else:
			name = node.getName( node )
			item.setText( 0, name )

	def getItemFlags( self, node ):
		if node == self.getOwner(): return {}
		if node._isDefault:
			return { 'editable' : False }
		else:
			return { 'editable' : True }

	def onItemActivated(self, item, col):
		res = self.getOwner().changeRootGroup( item.node, True )
		if not res: return
		self.parent().close()
		if res == 'same':
			alertMessage( 'Already Openend', 'Scene group already selected' )

##----------------------------------------------------------------##
class GroupManagerWidget( QtWidgets.QWidget ):
	def __init__( self, *args ):
		super( GroupManagerWidget, self ).__init__( *args )
		self.setWindowFlags( Qt.Window | Qt.FramelessWindowHint )
		# self.setWindowModality( Qt.WindowModal )
		layout = QtWidgets.QVBoxLayout( self )
		layout.setContentsMargins( 5 , 5 , 5 , 5 )
		layout.setSpacing( 5 )

		self.owner = False
		self.toolBar = toolBar = QtWidgets.QToolBar( self )
		self.tree = SceneGroupListView( self )
		self.toolBar.setFixedHeight( 20 )
		
		self.actionAdd    = toolBar.addAction( 'Add'    )
		self.actionRemove = toolBar.addAction( 'Remove' )
		self.actionRename = toolBar.addAction( 'Rename' )
		# self.actionClone  = toolBar.addAction( 'Clone'  )

		self.actionAdd.triggered.connect( self.onActionAdd )
		self.actionRemove.triggered.connect( self.onActionRemove )
		self.actionRename.triggered.connect( self.onActionRename )
		# self.actionAdd.triggered.connect( self.onActionClone )
		
		self.actionAdd.setIcon    ( getIcon( 'add' ) )
		self.actionRemove.setIcon ( getIcon( 'remove' ) )
		self.actionRename.setIcon ( getIcon( 'pencil' ) )
		# self.actionClone.setIcon  ( getIcon( 'clone' ) )

		self.titleBar = SimpleTitleBar( self )
		self.titleBar.setTitle( 'Scene Groups' )

		layout.addWidget( self.titleBar )
		layout.addWidget( self.toolBar )
		layout.addWidget( self.tree )

		self.setMinimumSize( 200, 300 )
		self.setMaximumWidth( 250 )



	def getOwner( self ):
		return self.owner

	def start( self, pos = None ):
		if not pos:
			pos    = QtGui.QCursor.pos()		
		self.move( pos )
		restrainWidgetToScreen( self )
		self.tree.rebuild()
		self.show()
		self.raise_()

	def onActionAdd( self ):
		group = self.getOwner().addRootGroup()
		if group:
			self.tree.addNode( group )			
			self.getOwner().changeRootGroup( group )

	def onActionRemove( self ):
		for node in self.tree.getSelection():
			if self.getOwner().removeRootGroup( node ):
				self.tree.rebuild()
			break

	def onActionRename( self ):
		for node in self.tree.getSelection():
			if self.getOwner().renameRootGroup( node ):
				self.tree.refreshNodeContent( node )
			break

	def onActionClone( self ):
		pass

	def event( self, ev ):
		e = ev.type()		
		if e == QEvent.KeyPress and ev.key() == Qt.Key_Escape:
			self.hide()

		elif e == QEvent.WindowDeactivate:
			self.hide()

		return super( GroupManagerWidget, self ).event( ev )


##----------------------------------------------------------------##
def _sortEntity( a, b ):
	return b._priority - a._priority

# _BrushEntityNormal = QtGui.QBrush()
# _BrushEntityLocked = QtGui.QBrush( QColorF( 0.6,0.6,0.6 ) )
# _BrushEntityHidden = QtGui.QBrush( QColorF( 1,1,0 ) )
# _BrushEntityPrefab = QtGui.QBrush( QColorF( .5,.5,1 ) )


class SceneGraphTreeItemDelegate(QtWidgets.QStyledItemDelegate):
	_textBrush      = QBrush( QColor( '#dd5200' ) )
	_textPen        = QPen( QColor( '#dddddd' ) )
	_textPenGroup   = QPen( QColor( '#ada993' ) )
	_backgroundBrushHovered  = QBrush( QColor( '#454768' ) )
	_backgroundBrushSelected = QBrush( QColor( '#515c84' ) )
	
	def paint(self, painter, option, index):
		painter.save()
		index0 = index.sibling( index.row(), 0 )
		utype = index0.data( Qt.UserRole )

		# # set background color
		if option.state & QStyle.State_Selected:
			painter.setPen  ( Qt.NoPen )
			painter.setBrush( SceneGraphTreeItemDelegate._backgroundBrushSelected )
			painter.drawRect(option.rect)
		elif option.state & QStyle.State_MouseOver:
			painter.setPen  ( Qt.NoPen )
			painter.setBrush( SceneGraphTreeItemDelegate._backgroundBrushHovered )
			painter.drawRect(option.rect)

		rect = option.rect
		icon = QIcon( index.data( Qt.DecorationRole ) )
		rect.adjust( 5, 0, 0, 0 )
		if icon and not icon.isNull():
			icon.paint( painter, rect, Qt.AlignLeft )
			rect.adjust( 22, 0, 0, 0 )
		text = index.data(Qt.DisplayRole)
		if utype == 1: #GROUP
			painter.setPen( SceneGraphTreeItemDelegate._textPenGroup )
		else:
			painter.setPen( SceneGraphTreeItemDelegate._textPen )
		painter.drawText( rect, Qt.AlignLeft | Qt.AlignVCenter, text )
		painter.restore()


class ReadonlySceneGraphTreeItemDelegate( SceneGraphTreeItemDelegate ):
	def createEditor( *args ):
		return None

##----------------------------------------------------------------##
class SceneGraphTreeWidget( GenericTreeWidget ):
	def __init__( self, *args, **kwargs ):
		super( SceneGraphTreeWidget, self ).__init__( *args, **kwargs )
		self.syncSelection = True
		self.adjustingRange = False
		self.verticalScrollBar().rangeChanged.connect( self.onScrollRangeChanged )
		self.setIndentation( 13 )

	def getHeaderInfo( self ):
		return [('Entity',240), ('V',27 ), ('L',27 ), ( 'Layer', -1 ) ]

	def getReadonlyItemDelegate( self ):
		return ReadonlySceneGraphTreeItemDelegate( self )

	def getDefaultItemDelegate( self ):
		return SceneGraphTreeItemDelegate( self )

	def getRootNode( self ):
		return self.module.getActiveSceneRootGroup()

	# def mimeData( self, items ):
	# 	#TODO: scene source
	# 	return makeSceneGraphMimeData( 'main', [ item.node for item in items ] )

	def saveFoldState( self ):
		#TODO: other state?
		result = {}
		for node, item in self.nodeDict.items():
			if not item: continue
			guid     = node['__guid']
			expanded = item.isExpanded()
			result[ guid ] = { 'expanded': expanded }
		return result

	def loadFoldState( self, data ):
		for node, item in self.nodeDict.items():
			if not item: continue
			guid  = node['__guid']
			state = data.get( guid )
			if state:
				item.setExpanded( state['expanded'] )

	def saveTreeStates( self ):
		pass

	def loadTreeStates( self ):
		pass

	def getNodeParent( self, node ): # reimplemnt for target node	
		p = node.getParentOrGroup( node )
		if p and not p.FLAG_EDITOR_OBJECT :
			return p
		return None

	def getNodeChildren( self, node ):
		if isMockInstance( node, 'EntityGroup' ):
			output = []
			#groups
			for group in node.childGroups:
				output.append( group )
			#entities
			for ent in node.entities:
				if ( not ent.parent ) and ( not ( ent.FLAG_EDITOR_OBJECT or ent.FLAG_INTERNAL ) ):
					output.append( ent )
			# output = sorted( output, key = cmp_to_key( _sortEntity ) )
			return output

		else: #entity
			output = []
			for ent in node.children:
				if not ( ent.FLAG_EDITOR_OBJECT or ent.FLAG_INTERNAL ):
					output.append( ent )
			# output = sorted( output, key = cmp_to_key( _sortEntity ) )
			return output

	def compareNodes( self, node1, node2 ):
		return node1._priority >= node2._priority

	def createItem( self, node ):
		return SceneGraphTreeItem()

	def updateHeaderItem( self, item, col, info ):
		if info[0] == 'V':
			item.setText( col, '')
			item.setIcon( col, getIcon( 'entity_vis' ) )
		elif info[0] == 'L':
			item.setText( col, '')
			item.setIcon( col, getIcon( 'entity_lock' ) )

	def getEntityType( self, obj ):
		if obj['FLAG_PROTO_SOURCE']:
			protoState = 'proto'
		elif obj['PROTO_INSTANCE_STATE']:
			protoState = 'instance-proto'
		elif obj[ '__prefabId' ]:
			protoState = 'instance-prefab'
		elif obj['__proto_history']:
			protoState = 'instance-sub'
		else:
			protoState = False

		if isMockInstance( obj, 'ProtoContainer' ):
			category = 'container-proto'
		elif isMockInstance( obj, 'PrefabContainer' ):
			category = 'container-prefab'
		elif isMockInstance( obj, 'UIView' ):
			category = 'uiview'
		elif isMockInstance( obj, 'UIWidget' ):
			category = 'uiwidget'
		else:
			category = 'normal'

		return ( category, protoState )


	def updateItemContent( self, item, node, **option ):
		name = None
		item.setData( 0, Qt.UserRole, 0 )

		if isMockInstance( node, 'EntityGroup' ):
			item.setText( 0, node.name or '<unnamed>' )
			item.setIcon( 0, getIcon('entity_group') )
			item.setData( 0, Qt.UserRole, 1 )

		elif isMockInstance( node, 'Entity' ):
			node.forceUpdate( node )
			category, protoState = self.getEntityType( node )
			
			if protoState:
				iconPath = 'entity/%s.%s' % ( category, protoState )
				iconFallback = 'entity/normal.%s' % protoState 
			else:
				iconPath = 'entity/%s' % category
				iconFallback = 'entity/normal'

			item.setIcon( 0, getIcon( iconPath, iconFallback ) )
			item.setText( 0, node.name or '<unnamed>' )
	
			layerName = node.getLayer( node )
			if isinstance( layerName, tuple ):
				item.setText( 3, '????' )
			else:
				item.setText( 3, layerName )

		#update icon
		if node.isVisible( node ):
			item.setIcon( 1, getIcon( 'entity_vis' ) )
		elif node.isLocalVisible( node ):
			item.setIcon( 1, getIcon( 'entity_parent_invis' ) )
		else:
			item.setIcon( 1, getIcon( 'entity_invis' ) )

		if node.isEditLocked( node ):
			if node.isLocalEditLocked( node ):
				item.setIcon( 2, getIcon( 'entity_lock' ) )
			else:
				item.setIcon( 2, getIcon( 'entity_parent_lock' ) )
		else:
			item.setIcon( 2, getIcon( 'entity_nolock' ) )

			
	def onItemSelectionChanged(self):
		if not self.syncSelection: return
		items = self.selectedItems()
		if items:
			selections=[item.node for item in items]
			self.module.changeSelection(selections)
		else:
			self.module.changeSelection(None)

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

		target = self.itemAt( ev.pos() )
		ok = False
		if pos == 'on':
			ok = self.module.doCommand( 'scene_editor/reparent_entity', target = target.node )
		elif pos == 'viewport':
			ok = self.module.doCommand( 'scene_editor/reparent_entity', target = 'root' )
		elif pos == 'above' or pos == 'below':
			ok = self.module.doCommand( 'scene_editor/reparent_entity', target = target.node, mode = 'sibling' )

		if ok:
			super( GenericTreeWidget, self ).dropEvent( ev )
		else:
			ev.setDropAction( Qt.IgnoreAction )

	def onDeletePressed( self ):
		self.syncSelection = False
		item0 = self.currentItem()
		item1 = self.itemBelow( item0 )
		self.module.doCommand( 'scene_editor/remove_entity' )
		if item1:
			self.setFocusedItem( item1 )
		self.syncSelection = True
		self.onItemSelectionChanged()

	def onItemChanged( self, item, col ):
		self.module.renameEntity( item.node, item.text(0) )

	def onClipboardCopy( self ):
		self.module.copyEntityToClipboard()
		return True

	def onClipboardCut( self ):
		self.module.cutEntityToClipboard()
		return True

	def onClipboardPaste( self ):
		self.module.pasteEntityFromClipboard()
		return True

	def onScrollRangeChanged( self, min, max ):
		if self.adjustingRange: return
		self.adjustingRange = True
		if max > min:
			pageStep = self.verticalScrollBar().pageStep()
			self.verticalScrollBar().setRange( min, max + 1 )
		self.adjustingRange = False

	def mousePressEvent( self, ev ):
		if ev.button() == Qt.LeftButton:
			item = self.itemAt( ev.pos() )
			if item:
				col = self.columnAt( ev.pos().x() )
				if col == 1:
					node = self.getNodeByItem( item )
					self.module.doCommand( 'scene_editor/toggle_entity_visibility', target = node )
					self.refreshNodeContent( node, updateChildren = True )
					return
				elif col == 2:
					node = self.getNodeByItem( item )
					self.module.doCommand( 'scene_editor/toggle_entity_lock', target = node )
					self.refreshNodeContent( node, updateChildren = True )
					return
			
		return super( SceneGraphTreeWidget, self ).mousePressEvent( ev )


##----------------------------------------------------------------##
#TODO: allow sort by other column
class SceneGraphTreeItem(QtWidgets.QTreeWidgetItem):
	def __lt__(self, other):
		node0 = self.node
		node1 = hasattr(other, 'node') and other.node or None
		if not node1:
			return True
		if not node0:
			return False
		tree = self.treeWidget()
		order = tree.sortOrder()
	
		group0 = isMockInstance( node0, 'EntityGroup' )
		group1 = isMockInstance( node1, 'EntityGroup' )
		if group0 != group1:
			if order == 0:
				if group0: return True
				if group1: return False
			else:
				if group0: return False
				if group1: return True
		
		proto0 = node0[ 'FLAG_PROTO_SOURCE' ]
		proto1 = node1[ 'FLAG_PROTO_SOURCE' ]
		if proto0 != proto1:
			if order == 0:
				if proto0: return True
				if proto1: return False
			else:
				if proto0: return False
				if proto1: return True

		if isMockInstance( node0, 'UIWidget' ) and isMockInstance( node1, 'UIWidget' ):
			z0 = node0.zorder
			z1 = node1.zorder
			if z0 != z1:
				if order == 0:
					return z0 < z1
				else:
					return z0 > z1
		return super( SceneGraphTreeItem, self ).__lt__( other )

##----------------------------------------------------------------##
SceneGraphEditor().register()

##----------------------------------------------------------------##
def sceneObjectSearchEnumerator( typeId, context, option ):
	if not context in ['scene', 'all']: return None
	modelMgr = ModelManager.get()
	objects = modelMgr.enumerateObjects( typeId, context, option )
	if not objects: return None
	result = []
	for obj in objects:
		name     = modelMgr.getObjectRepr( obj )
		typeName = modelMgr.getObjectTypeRepr( obj )
		entry = ( obj, name, typeName, None )
		result.append( entry )
	return result

def entityNameSearchEnumerator( typeId, context, option ):
	if not context in [ 'entity_creation' ] : return None
	registry = _MOCK.getEntityRegistry()
	result = []
	for name in sorted( registry.keys() ):
		entry = ( name, name, 'Entity', None )
		result.append( entry )
	return result

def componentNameSearchEnumerator( typeId, context, option ):
	if not context in [ 'component_creation' ] : return None
	registry = _MOCK.getComponentRegistry()
	result = []
	for name in sorted( registry.keys() ):
		entry = ( name, name, 'Entity', None )
		result.append( entry )
	return result
		
def layerNameSearchEnumerator( typeId, context, option ):
	if not context in [ 'scene_layer' ] : return None
	layers = _MOCK.game.layers
	result = []
	for name in sorted( [ layer.name for layer in layers.values() ] ):
		if name == '_GII_EDITOR_LAYER': continue
		entry = ( name, name, 'Layer', None )
		result.append( entry )
	return result

##----------------------------------------------------------------##
class RemoteCommandGetSceneAutoCompletion( RemoteCommand ):
	name = 'get_scene_auto_completion'
	def run( self, *args ):
		result = []
		if 'entity_full' in args:
			result += app.getModule( 'scenegraph_editor' ).getAutoCompletion( True )
		elif 'entity' in args:
			result += app.getModule( 'scenegraph_editor' ).getAutoCompletion( False )
		
		if 'scene' in args:
			lib = app.getAssetLibrary()
			scenes = lib.enumerateAsset( 'scene' )
			result += [ node.getPath() for node in scenes ]

		if 'quest' in args:
			result += [ n for n in _MOCK_EDIT.listQuestNodeNames().values() ]

		if result:
			return '\n'.join( result )
		else:
			return None


##----------------------------------------------------------------##
@slot( 'app.open_url' )
def URLSceneHandler( url ):
	if url.get( 'base', None ) != 'scene': return
	data = url['data']
	path = data.get( 'path', None )
	if not path:
		print( 'no scene path' )
		return
	app.getModule( 'asset_browser' ).locateAsset( path )
	app.getModule( 'scenegraph_editor' ).openSceneByPath( path )
	
	#TODO: focus target entity/component
	entityGUID = data.get( 'entity_id', None )
	if entityGUID:
		def callback():
			app.getModule( 'scenegraph_editor' ).locateEntityByGUID( entityGUID )

		app.callLater( 0.2, callback )

	#TODO: camera
	cameraData = data.get( 'camera', None )
	if cameraData:		
		app.getModule( 'scene_view' ).loadCameraState( cameraData )
	


