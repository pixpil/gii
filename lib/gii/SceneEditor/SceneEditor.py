import os
import logging

from gii.core        import app, signals, EditorCommandStack, RemoteCommand
from gii.core.selection import SelectionManager, getSelectionManager

from gii.qt.controls.Window import MainWindow
from gii.qt.controls.Menu   import MenuManager
from gii.qt  import TopEditorModule, SubEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget
##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt, QObject
from qtpy.QtGui    import QKeyEvent
##----------------------------------------------------------------##

from gii.moai.MOAIRuntime import MOAILuaDelegate


##----------------------------------------------------------------##
class SceneEditorModule( SubEditorModule ):
	def getParentModuleId( self ):
		return 'scene_editor'

	def getSceneEditor( self ):
		return self.getParentModule()

	def getSceneToolManager( self ):
		return self.getModule( 'scene_tool_manager' )

	def changeSceneTool( self, toolId ):
		self.getSceneToolManager().changeTool( toolId )


	def getSelectionManager( self ):
		return self.getParentModule().sceneSelectionManager
	
	def getSelection( self ):
		return self.getSelectionManager().getSelection()

	def changeSelection( self, selection ):
		self.getSelectionManager().changeSelection( selection )


	def getAssetSelectionManager( self ):
		return self.getParentModule().assetSelectionManager

	def getAssetSelection( self ):
		return self.getAssetSelectionManager().getSelection()

	def changeAssetSelection( self, selection ):
		self.getAssetSelectionManager().changeSelection( selection )


##----------------------------------------------------------------##
class SceneEditor( TopEditorModule ):
	name       = 'scene_editor'
	dependency = ['qt']

	def getWindowTitle( self ):
		return 'Scene Editor'

	def onSetupMainWindow( self, window ):
		self.mainToolBar = self.addToolBar( 'scene', self.mainWindow.requestToolBar( 'main' ) )		
		window.setMenuWidget( self.getQtSupport().getSharedMenubar() )
		#menu
		self.addMenu( 'main/scene', dict( label = 'Scene' ) )
		window.hide()

	def onLoad( self ):
		self.sceneSelectionManager = SelectionManager( 'scene' )
		self.assetSelectionManager = SelectionManager( 'asset' )
		signals.connect( 'app.start', self.postStart )
		return True

	def postStart( self ):
		self.mainWindow.show()
		
	def onMenu(self, node):
		name = node.name
		if name == 'open_scene':
			#TODO
			pass

	def onTool( self, tool ):
		name = tool.name
		if name == 'run':
			from gii.core.tools import RunHost
			RunHost.run( 'main' )
			
		elif name == 'deploy':
			deployManager = self.getModule('deploy_manager')
			if deployManager:
				deployManager.setFocus()

##----------------------------------------------------------------##
def getSceneSelectionManager():
	return app.getModule('scene_editor').sceneSelectionManager

##----------------------------------------------------------------##
class RemoteCommandRunGame( RemoteCommand ):
	name = 'run_game'
	def run( self, target = None, *args ):
		from gii.core.tools import RunHost
		RunHost.run( 'main' )

