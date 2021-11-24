import subprocess
import os.path
import shutil
import time
import json

from gii.core         import *
from gii.qt           import *
from gii.qt.IconCache                  import getIcon
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor
from gii.qt.dialogs   import requestString, alertMessage, requestColor, requestProperty, requestConfirm
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget
from gii.qt.controls.GenericListWidget import GenericListWidget

from gii.SceneEditor import SceneEditorModule, SceneTool, SceneToolMeta, SceneToolButton
from gii.SearchView  import requestSearchView

from mock import  MOCKEditCanvas
from gii.moai.MOAIRuntime import MOAILuaDelegate

from qtpy  import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt

from mock import _MOCK, isMockInstance


##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


##----------------------------------------------------------------##
class ShapeCanvasEditorTool( SceneTool ):
	name = 'shape_canvas_editor'
	def onStart( self, **context ):
		module = app.getModule( 'shape_canvas_editor' )
		module.showToolWindow()

	def onStop( self ):
		module = app.getModule( 'shape_canvas_editor' )
		module.hideToolWindow()


##----------------------------------------------------------------##
class ShapeCanvasEditor( SceneEditorModule ):
	name = 'shape_canvas_editor'
	dependency = [ 'mock' ]

	def onLoad( self ):
		self.toolWindow = self.requestToolWindow( 'ShapeCanvasEditor',
			title     = 'Shape Canvas',
			size      = (200,180),
			minSize   = (200,180)
		)

		self.targetShapeCanvas = None

		# self.delegate = MOAILuaDelegate( self )
		# self.delegate.load( _getModulePath( 'ShapeCanvasEditor.lua' ) )
		signals.connect( 'selection.changed', self.onSelectionChanged )

		self.mainToolBar = self.addToolBar( 'shape_canvas_tools_top', 
			self.getMainWindow().requestToolBar( 'shape_canvas_tools_top' )
		)
		
		self.addTool( 'shape_canvas_tools_top/shape_editor',
			widget = SceneToolButton(
				'shape_canvas_editor',
				label = 'Shape Canvas Editor',
				icon = 'tools/shape'
			)
		)

		toolbar = self.toolWindow.addToolBar()
		self.addToolBar( 'shape_canvas_editor', toolbar  )

		self.addTool( 'shape_canvas_editor/add_point',  label = 'Add Point',   icon = 'tools/shape_point' )
		self.addTool( 'shape_canvas_editor/add_rect',   label = 'Add Rect',    icon = 'tools/shape_rect' )
		self.addTool( 'shape_canvas_editor/add_circle', label = 'Add Circle',  icon = 'tools/shape_circle' )
		self.addTool( 'shape_canvas_editor/add_poly',   label = 'Add Polygon', icon = 'tools/shape_polygon' )
		self.addTool( 'shape_canvas_editor/----' )
		self.addTool( 'shape_canvas_editor/remove',     label = 'Remove',      icon = 'remove' )
		self.addTool( 'shape_canvas_editor/----' )
		self.addTool( 'shape_canvas_editor/clear',      label = 'Clear',       icon = 'clear' )

		self.tree = self.toolWindow.addWidget( ShapeItemTreeWidget() )
		

	def showToolWindow( self ):
		self.toolWindow.show()

	def hideToolWindow( self ):
		self.toolWindow.hide()

	def onSelectionChanged( self, selection, key ):
		if key == 'scene':
			pass
			# target = self.delegate.callMethod( 'editor', 'findTargetShapeCanvas' )
			# self.setTargetCanvas( target )
	
	def onTool( self, tool ):
		id = tool.getName()
		if id == 'remove':
			pass
			#app.doCommand( 'scene_editor/shape_canvas_remove' )
			
		elif id == 'clear':
			if requestConfirm( 'Clear shape canvas', 'Confirm to delete all shapes?' ):
				app.doCommand( 'scene_editor/shape_canvas_clear' )

		elif id == 'add_point':
			app.doCommand( 'scene_editor/shape_canvas_clear' )

		elif id == 'add_rect':
			pass

		elif id == 'add_circle':
			pass
			
		elif id == 'add_poly':
			pass

##----------------------------------------------------------------##
class ShapeItemTreeWidget( GenericTreeWidget ):
	def __init__( self, *args, **options ):
		options[ 'editable' ] = True
		super( ShapeItemTreeWidget, self ).__init__( *args, **options )
		self.setIndentation( 0 )
		self.setAttribute(Qt.WA_MacShowFocusRect, False)

	def getHeaderInfo( self ):
		return [ ('Shape',-1) ]

	def getRootNode( self ):
		return self

	def getNodeParent( self, node ): # reimplemnt for target node	
		if node == self:
			return None
		return self

	def getNodeChildren( self, node ):
		if node == self:
			target = self.parent().target
			if target:
				return [ cv for cv in list(self.target.variables.values()) ]
			else:
				return []
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		if node == self: return
		stype = node.getClassName( node )
		
		item.setText( 0, node.name )
		item.setIcon( 0, node.getIcon( node ) )
		item.setText( 1, node.getTypeName( node ) )
		
	def onItemChanged( self, item, col ):
		node = self.getNodeByItem( item )
		if col == 0:
			node.name = item.text( 0 )
		self.refreshNode( node )


