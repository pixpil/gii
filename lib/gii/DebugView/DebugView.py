import os
import logging

from gii.core        import app, signals, EditorCommandStack, RemoteCommand
from gii.core.selection import SelectionManager

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
class DebugViewModule( SubEditorModule ):
	def getParentModuleId( self ):
		return 'debug_view'

##----------------------------------------------------------------##
class DebugView( TopEditorModule ):
	name       = 'debug_view'
	dependency = ['qt']

	def getSelectionGroup( self ):
		return 'debug'

	def getWindowTitle( self ):
		return 'Debug View'
	
	def onSetupMainWindow( self, window ):
		self.mainToolBar = self.addToolBar( 'debug', self.mainWindow.requestToolBar( 'main' ) )		
		#window.setMenuWidget( self.getQtSupport().getSharedMenubar() )
		#MainTool 
		# self.addTool( 'scene/run',    label = 'Run' )
		# self.addTool( 'scene/deploy', label = 'Deploy' )
		#menu
		# self.addMenu( 'main/debug', dict( label = 'Debug' ) )

	def onLoad( self ):
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
