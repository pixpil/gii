import random
##----------------------------------------------------------------##
from gii.core        import app, signals, LuaCall
from gii.qt          import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget
from gii.qt.controls.CategoryList      import CategoryList

from gii.moai.MOAIRuntime import MOAILuaDelegate, createLuaTableFrom
from gii.SceneEditor      import SceneEditorModule, getSceneSelectionManager, SceneTool
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor

##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt, Signal

##----------------------------------------------------------------##
from mock import _MOCK, _MOCK_EDIT, isMockInstance
##----------------------------------------------------------------##

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
class ComponentPreviewManager( SceneEditorModule ):
	name = 'component_preview_manager'
	dependency = [ 'scene_view', 'mock' ]
	def onLoad( self ):
		self.mainToolBar = self.addToolBar( 'component_preview', 
			self.getMainWindow().requestToolBar( 'component_preview' )
			)

		self.addTool( 'component_preview/toggle_component_preview',
			label = 'Component Preview',
			icon = 'component_preview',
			type = 'check'
		)

		self.addTool( 'component_preview/toggle_component_child_preview',
			label = 'Preview Children',
			icon = 'component_preview_children',
			type = 'check'
		)

		self.addTool( 'component_preview/toggle_component_preview_autostop',
			label = 'Auto Stop',
			icon = 'component_preview_autostop',
			type = 'check'
		)

		self.addTool( 'component_preview/component_preview_reset',
			label = 'Reset',
			icon = 'component_preview_reset'
		)

		self.addTool( 'component_preview/component_preview_clear',
			label = 'Clear',
			icon = 'component_preview_clear'
		)
		signals.connect( 'scene.open', self.onSceneOpen )
		signals.connect( 'selection.changed', self.onSceneSelectionChanged )
		self.previewEnabled = True
		self.preivewChildren = True
		self.autostop = True

	def onStart( self ):
		self.updateTimer = self.getMainWindow().startTimer( 60, self.onUpdateTimer )
		self.updateTimer.stop()

		signals.connect( 'app.activate',   self.onAppActivate )
		signals.connect( 'app.deactivate', self.onAppDeactivate )


	def onAppReady( self ):
		self.previewManager = _MOCK_EDIT.getComponentPreviewManager()
		self.moduleSceneView = self.getModule( 'scene_view')
		self.moaiRuntime     = app.affirmModule( 'moai' )

		self.setToolValue( 'component_preview/toggle_component_preview', True )
		self.setToolValue( 'component_preview/toggle_component_child_preview', True )
		self.setToolValue( 'component_preview/toggle_component_preview_autostop', True )

	def onAppActivate(self):
		self.updateSessionState()
		# if self.waitActivate:
		# 	self.waitActivate=False
		# 	self.getRuntime().resume()

	def onAppDeactivate(self):
		self.updateTimer.stop()
		# if self.getWorkspaceConfig('pause_on_leave',False):
		# 	self.waitActivate=True
		# 	self.getRuntime().pause()

	def clearSessions( self ):
		LuaCall( self.previewManager, 'clearSessions' )

	def resetSessions( self ):
		LuaCall( self.previewManager, 'resetSessions' )

	def updateSessionState( self ):
		self.moduleSceneView.makeCanvasCurrent()
		LuaCall( self.previewManager, 'buildForMainSceneView' )
		if LuaCall( self.previewManager, 'hasSession' ):
			self.updateTimer.start()
		else:
			self.updateTimer.stop()

	def updateOptions( self ):
		self.previewEnabled  = bool(self.getToolValue( 'component_preview/toggle_component_preview' ) )
		self.preivewChildren = bool(self.getToolValue( 'component_preview/toggle_component_child_preview' ) )
		self.autostop        = bool(self.getToolValue( 'component_preview/toggle_component_preview_autostop' ) )
		options = {
			'enabled' : self.previewEnabled,
			'previewChildren' : self.preivewChildren,
			'autostop' : self.autostop
		}
		LuaCall( self.previewManager, 'setOptions', createLuaTableFrom( options ) )
		self.updateSessionState()

	def onUpdateTimer( self ):
		self.moduleSceneView.makeCanvasCurrent()
		LuaCall( self.previewManager, 'updateSessions' )
		self.moaiRuntime.stepSim( 1.0/60.0 )
		self.moduleSceneView.scheduleUpdate()
		
	def onSceneOpen( self, scene, reason ):
		pass

	def onSceneSelectionChanged( self, selection, key ):
		if key != 'scene': return
		self.updateSessionState()

	def onTool( self, tool ):
		name = tool.name
		if name == 'toggle_component_preview':
			self.updateOptions()

		elif name == 'toggle_component_child_preview':
			self.updateOptions()

		elif name == 'toggle_component_preview_autostop':
			self.updateOptions()

		elif name == 'component_preview_reset':
			self.resetSessions()

		elif name == 'component_preview_clear':
			self.clearSessions()
