import subprocess
import os.path
import shutil
import time
import json

from gii.core         import *
from gii.qt           import *
from gii.qt.IconCache                  import getIcon
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor
from gii.qt.dialogs   import requestString, alertMessage, requestColor, requestProperty
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget
from gii.qt.controls.GenericListWidget import GenericListWidget

from gii.SceneEditor import SceneEditorModule, SceneTool, SceneToolMeta, SceneToolButton
from gii.SearchView  import requestSearchView

from mock import  MOCKEditCanvas

from qtpy  import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt

from mock import _MOCK, isMockInstance

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
class SceneToolPaintCanvasPen( SceneTool ):
	name = 'paintcanvas_pen'
	def onStart( self, **context ):
		app.getModule( 'paintcanvas_editor' ).changeTool( 'pen' )

##----------------------------------------------------------------##
class SceneToolPaintCanvasEraser( SceneTool ):
	name = 'paintcanvas_eraser'
	def onStart( self, **context ):
		app.getModule( 'paintcanvas_editor' ).changeTool( 'eraser' )

##----------------------------------------------------------------##
class PaintCanvasEditor( SceneEditorModule ):
	name       = 'paintcanvas_editor'
	dependency = [ 'mock' ]

	def onLoad( self ):
		self.viewSelectedOnly = True

		self.container = self.requestDockWindow(
				title = 'PaintCanvas'
			)
		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('PaintCanvasEditor.ui')
		)

		self.canvas = MOCKEditCanvas( window.containerPreview )
		self.canvas.loadScript( 
				_getModulePath('PaintCanvasEditor.lua'),
				{
					'_module': self
				}
			)		
		self.canvas.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding )


		self.toolbarMain = QtWidgets.QToolBar( window.containerBottom )
		self.toolbarMain.setOrientation( Qt.Horizontal )


		layoutPreview = QtWidgets.QVBoxLayout( window.containerPreview )
		layoutPreview.setSpacing( 0 )
		layoutPreview.setContentsMargins( 0 , 0 , 0 , 0 )
		layoutPreview.addWidget( self.canvas )


		layoutBottom = QtWidgets.QVBoxLayout( window.containerBottom )
		layoutBottom.setSpacing( 0 )
		layoutBottom.setContentsMargins( 0 , 0 , 0 , 0 )

		layoutBottom.addWidget( self.toolbarMain )

		self.addToolBar( 'paintcanvas_main', self.toolbarMain )
		self.addTool( 'paintcanvas_main/find_paintcanvas', icon = 'find', label = 'Find PaintCanvas' ) 
		self.addTool( 'paintcanvas_main/----' ) 
		self.addTool( 'paintcanvas_main/tool_pen', 
			widget = SceneToolButton( 'paintcanvas_pen',
				icon = 'paintcanvas/pen',
				label = 'Pen'
			)
		)
		self.addTool( 'paintcanvas_main/tool_eraser', 
			widget = SceneToolButton( 'paintcanvas_eraser',
				icon = 'paintcanvas/eraser',
				label = 'Eraser'
			)
		)
		self.addTool( 'paintcanvas_main/----' )
		self.addTool( 'paintcanvas_main/tool_clear',    label = 'Clear', icon = 'paintcanvas/clear' )

		signals.connect( 'selection.changed', self.onSceneSelectionChanged )

		self.targetPaintCanvas = None

	def onStart( self ):
		self.container.show()
		# self.container.setEnabled( False )
		self.setEditActive( False )
		
	def onStop( self ):
		pass

	def onSetFocus( self ):
		self.getModule( 'scene_editor' ).setFocus()
		self.container.show()
		self.container.setFocus()

	def onSceneSelectionChanged( self, selection, key ):
		if key != 'scene': return
		#find animator component
		target = self.canvas.callMethod( 'editor', 'findTargetPaintCanvas' )
		self.setTargetPaintCanvas( target )

	def setEditActive( self, active ):
		self.enableTool( 'paintcanvas_main/tool_pen', active )
		self.enableTool( 'paintcanvas_main/tool_eraser', active )
		self.enableTool( 'paintcanvas_main/tool_clear', active )

	def setTargetPaintCanvas( self, paintCanvas ):
		self.canvas.callMethod( 'editor', 'setTargetPaintCanvas', paintCanvas )
		self.targetPaintCanvas = paintCanvas
		if paintCanvas:
			self.setEditActive( True )
		else:
			self.setEditActive( False )

	def renameLayer( self, layer, name ):
		layer.name = name

	def changeTool( self, toolId ):
		self.canvas.callMethod( 'editor', 'changeTool', toolId )
		if toolId == 'terrain':
			currentBrush = self.canvas.callMethod( 'editor', 'getTerrainBrush' )
			
	def selectPaintCanvasEntity( self, com ):
		entity = com._entity
		if not entity: return
		self.changeSelection( entity )

	def onTool( self, tool ):
		name = tool.name
		if   name == 'find_paintcanvas':
			requestSearchView( 
				context   = 'scene',
				type      = _MOCK.PaintCanvas,
				on_selection = self.selectPaintCanvasEntity
			)

		elif name == 'tool_clear':
			self.canvas.callMethod( 'editor', 'clearCanvas' )



