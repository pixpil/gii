import random
##----------------------------------------------------------------##
from gii.core        import app, signals
from gii.qt          import QtEditorModule

from gii.qt.IconCache                  import getIcon

from gii.qt.controls.GenericTreeWidget import GenericTreeWidget
from gii.qt.controls.PropertyEditor  import PropertyEditor

from gii.moai.MOAIRuntime import MOAILuaDelegate
from gii.SceneEditor      import SceneEditorModule
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor

from gii.SearchView       import requestSearchView, registerSearchEnumerator

import datetime

##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt

##----------------------------------------------------------------##
from mock import _MOCK, isMockInstance
##----------------------------------------------------------------##



_DEPLOY_CONFIG_FILE = 'deploy.json'
##----------------------------------------------------------------##

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
class DeployManager( SceneEditorModule ):
	def __init__(self):
		super( DeployManager, self ).__init__()

	def getName( self ):
		return 'deploy_manager'

	def getDependency( self ):
		return [ 'mock' ]

	def onLoad( self ):
		self.configPath = self.getProject().getConfigPath( _DEPLOY_CONFIG_FILE )
		self.activeDeployConfigName = self.getWorkspaceConfig( 'active_deploy_config', 'osx' )
		self.selectActiveDeployConfig( self.activeDeployConfigName )
		#UI
		self.container = self.requestDockWindow( 'DeployManager',
			title     = 'Deployment Manager',
			dock      = 'left',
			minSize   = ( 300, 300 ),
			maxSize   = ( 300, 300 ),
			toolWindow = False
			)

		#Components
		self.window = self.container.addWidgetFromFile( _getModulePath('DeployManager.ui') )

		self.delegate = MOAILuaDelegate( self )
		self.delegate.load( _getModulePath( 'DeployManager.lua' ) )

		#scene tree
		layout = QtWidgets.QVBoxLayout()
		self.window.containerSceneTree.setLayout( layout )
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )

		self.treeScene = DeploySceneTree( 
			self.window.containerSceneTree,
			editable = True,
			sorting  = False,
			multiple_selection = False
			)
		self.treeScene.manager = self
		layout.addWidget( self.treeScene )

		sceneToolbar = QtWidgets.QToolBar( self.window.containerSceneTree )
		layout.addWidget( sceneToolbar )
		self.sceneTool = self.addToolBar( 'deploy_scene', sceneToolbar )
		self.addTool( 'deploy_scene/add_scene',         label = 'add'     ,icon = 'add'    )
		self.addTool( 'deploy_scene/remove_scene',      label = 'remove'  ,icon = 'remove' )
		self.addTool( 'deploy_scene/move_up_scene',     label = 'up'      ,icon = 'arrow-up'     )
		self.addTool( 'deploy_scene/move_down_scene',   label = 'down'    ,icon = 'arrow-down'   )
		self.addTool( 'deploy_scene/----' )
		self.addTool( 'deploy_scene/edit_scene',   label = 'change target scene' ,icon = 'pencil'   )
		self.addTool( 'deploy_scene/----' )
		self.addTool( 'deploy_scene/set_entry_scene',   label = 'set as entry' ,icon = 'flag'   )

		#deploy target tree
		layout = QtWidgets.QVBoxLayout()
		self.window.containerTargetTree.setLayout( layout )
		layout.setSpacing( 0 )		
		layout.setContentsMargins( 0 , 0 , 0 , 0 )

		self.treeTarget = DeployTargetTree( 
			self.window.containerTargetTree,
			editable = True,
			multiple_selection = False
			)
		self.treeTarget.manager = self
		layout.addWidget( self.treeTarget )

		targetToolbar = QtWidgets.QToolBar( self.window.containerTargetTree )
		layout.addWidget( targetToolbar )
		self.targetTool = self.addToolBar( 'deploy_target', targetToolbar )
		self.addTool( 'deploy_target/add_target',    label = '+' )
		self.addTool( 'deploy_target/remove_target', label = '-' )

		#target property
		self.propertyTarget = addWidgetWithLayout(
			PropertyEditor( self.window.containerTargetProp )
		)

		#menu
		self.addMenuItem( 'main/file/----' )
		self.addMenuItem( 'main/file/deploy_manager', 
			dict( label = 'Deploy Manager', shortcut = 'F11' )
			)

		self.addMenuItem( 'main/file/deploy_build', 
			dict( label = 'Deploy Build', shortcut = 'Ctrl+F11' )
			)
		
		self.menuBuildTargets = self.addMenu( 'main/file/deploy_build_targets', 
			dict( label = 'Deploy Build Target', shortcut = 'Ctrl+F11' )
			)
		
		# self.container.show()
		self.window.buttonOK.clicked.connect( self.onButtonOK )

		#other
		registerSearchEnumerator( deployTargetSearchEnumerator )

		signals.connect( 'project.pre_deploy', self.preDeploy )
		signals.connect( 'project.deploy', self.onDeploy )
		signals.connect( 'project.post_deploy', self.postDeploy )


	def onStart( self ):
		#load config
		self.loadConfig()
		#fill trees
		self.treeTarget.rebuild()
		self.treeScene.rebuild()
		self.container.hide()

	def onStop( self ):
		self.saveConfig()

	def onAppReady( self ):
		for config in self.getProject().getDeployConfigs():
			if not config.checkSupported(): continue
			name = config.getName()
			node = self.menuBuildTargets.addChild( {
				'name' : 'choose_deploy_target_'+name,
				'label': name,
				'type' : 'check',
				'group': 'group_deploy_target'
				}
			)
			node.deployConfigName = name
			if name == self.activeDeployConfigName:
				node.setValue( True )

	def selectActiveDeployConfig( self, name ):
		self.activeDeployConfigName = name
		self.setWorkspaceConfig( 'active_deploy_config', self.activeDeployConfigName )
		if self.activeDeployConfigName == name: return
		menuNode = self.menuBuildTargets.findChild( 'choose_deploy_target_'+name )
		if menuNode:
			menuNode.setValue( True )


	def loadConfig( self ):
		self.delegate.safeCall( 'loadDeployManagerConfig', self.configPath )

	def saveConfig( self ):
		self.delegate.safeCall( 'saveDeployManagerConfig', self.configPath )		

	def getDeployTargetTypes( self ):
		registry = self.delegate.safeCall( 'getDeployTargetTypeRegistry' )
		return [ name for name in list(registry.keys()) ]

	def getDeployTargets( self ):
		targets =  self.delegate.safeCallMethod( 'config', 'getTargets' )
		return [ obj for obj in list(targets.values()) ]

	def addDeployTarget( self, targetType ):
		target = self.delegate.safeCallMethod( 'config', 'addDeployTarget', targetType )
		self.treeTarget.addNode( target )
		self.treeTarget.editNode( target )

	def changeDeployScene( self, targetScene ):
		for sceneEntry in self.treeScene.getSelection():
			self.delegate.safeCallMethod( 'config', 'changeTargetScene', sceneEntry, targetScene.getPath() )
			self.treeScene.refreshNode( sceneEntry )
			return

	def renameDeployTarget( self, target, name ):
		target.name = name #avoid duplicated name

	def addDeployScene( self, sceneNode ):
		if not sceneNode: return
		entry = self.delegate.safeCallMethod( 'config', 'addDeployScene', sceneNode.getNodePath() )
		self.treeScene.addNode( entry )
		self.treeScene.editNode( entry )

	def renameDeployScene( self, entry, alias ):
		entry.alias = alias #TODO: avoid duplicated name

	def getDeployScenes( self ):
		scenes =  self.delegate.safeCallMethod( 'config', 'getScenes' )
		return [ obj for obj in list(scenes.values()) ]

	def updateGameConfig( self ):
		self.delegate.safeCallMethod( 'config', 'updateGameConfig' )

	def preDeploy( self, context ):
		self.updateGameConfig()

	def onDeploy( self, context ):
		pass

	def postDeploy( self, context ):
		pass

	def onTool( self, tool ):
		name = tool.name
		if name == 'add_target':
			requestSearchView( 
				info    = 'select deploy target type',
				context = 'deploy_target_type',
				on_selection = self.addDeployTarget
				)

		elif name == 'remove_target':
			for target in self.treeTarget.getSelection():
				self.treeTarget.removeNode( target )
				self.delegate.safeCallMethod( 'config', 'removeDeployTarget', target )

		elif name == 'add_scene':
			requestSearchView( 
				info    = 'select scene to deploy',
				context = 'asset',
				type    = 'scene',
				on_selection = self.addDeployScene
				)

		elif name == 'edit_scene':
			requestSearchView( 
				info    = 'select new target scene ',
				context = 'asset',
				type    = 'scene',
				on_selection = self.changeDeployScene
				)

		elif name == 'remove_scene':
			for entry in self.treeScene.getSelection():	
				self.delegate.safeCallMethod( 'config', 'removeDeployScene', entry )
				self.treeScene.removeNode( entry )
			self.treeScene.refreshAllContent()

		elif name == 'set_entry_scene':
			for entry in self.treeScene.getSelection():
				self.delegate.safeCallMethod( 'config', 'setEntryScene', entry )
				break
			self.treeScene.refreshAllContent()

		elif name == 'move_up_scene':
			for target in self.treeScene.getSelection():
				self.delegate.safeCallMethod( 'config', 'moveSceneUp', target )
				self.treeScene.rebuild()
				self.treeScene.selectNode( target )
				break

		elif name == 'move_down_scene':
			for target in self.treeScene.getSelection():
				self.delegate.safeCallMethod( 'config', 'moveSceneDown', target )
				self.treeScene.rebuild()
				self.treeScene.selectNode( target )
				break

	def onMenu( self, node ):
		name = node.name
		if name == 'deploy_manager' :
			self.onSetFocus()

		elif name == 'deploy_build':
			config = app.getProject().getDeployConfig( self.activeDeployConfigName )
			if config:
				config.execute()

		else:
			if name.startswith( 'choose_deploy_target_' ):
				self.selectActiveDeployConfig( node.deployConfigName )

	def onSetFocus( self ):
		self.container.show()
		self.container.raise_()
	
	def onButtonOK( self ):
		self.saveConfig()
		self.container.hide()

DeployManager().register()

##----------------------------------------------------------------##
def deployTargetSearchEnumerator( typeId, context, option ):
		if not context in [ 'deploy_target_type' ] : return
		result = []
		mgr = app.getModule( 'deploy_manager' )
		for name in mgr.getDeployTargetTypes():
			entry = ( name, name, 'Deploy Target', None )
			result.append( entry )
		return result
##----------------------------------------------------------------##

_BrushEntryScene = QtGui.QBrush( QColorF( 0,0,1 ) )
_BrushDefault    = QtGui.QBrush()

class DeploySceneTree( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Name',250),  ('Path', 250), ('ID', 30) ]

	def getRootNode( self ):
		return self.manager

	def getNodeParent( self, node ):
		if node == self.manager: return None
		return self.manager

	def getNodeChildren( self, node ):
		if node == self.manager:
			return self.manager.getDeployScenes()
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		if node == self.manager: return
		#TODO:icon
		item.setText( 0, node.alias )
		item.setText( 1, node.path )
		item.setText( 2, str(node.id) )
		if node.entry:
			item.setIcon(0, getIcon( 'scene' ) )
		else:
			item.setIcon(0, getIcon( 'obj' ) )

	def onItemChanged( self, item, col ):
		entry = item.node
		self.manager.renameDeployScene( entry, item.text(0) )

##----------------------------------------------------------------##
class DeployTargetTree( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Name',150), ('Type', 30), ('State',30), ('Last Build',-1) ]

	def getRootNode( self ):
		return self.manager

	def getNodeParent( self, node ):
		if node == self.manager: return None
		return self.manager

	def getNodeChildren( self, node ):
		if node == self.manager:
			return self.manager.getDeployTargets()
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		if node == self.manager: return
		#TODO:icon
		item.setText( 0, node.name )
		item.setText( 1, node.getType( node ) )
		item.setText( 2, node.state )
		# item.setText( 3, node.getLastBuild() )

	def onItemChanged( self, item, col ):
		target = item.node
		self.manager.renameDeployTarget( target, item.text(0) )

	def onItemSelectionChanged( self ):
		selection = self.getSelection()
		if selection:
			for node in selection:
				self.manager.propertyTarget.setTarget( node )
		else:
			self.manager.propertyTarget.clear()
