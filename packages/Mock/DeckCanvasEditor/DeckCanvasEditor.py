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
from gii.moai.MOAIRuntime import MOAILuaDelegate

from qtpy  import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt

from mock import _MOCK, isMockInstance

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
class SceneToolDeckCanvasPen( SceneTool ):
	name = 'deckcanvas_pen'
	context = 'scene_view'
	shortcut = 'Y'

	def onStart( self, **context ):
		module = app.getModule( 'deckcanvas_editor' )
		module.showToolWindow()
		module.startPenTool()
		# app.getModule( 'scene_view' ).canvas.setCursorByName( 'pen' )

	def onStop( self ):
		module = app.getModule( 'deckcanvas_editor' )
		module.hideToolWindow()

		
##----------------------------------------------------------------##
class DeckCanvasEditor( SceneEditorModule ):
	name       = 'deckcanvas_editor'
	dependency = [ 'mock' ]

	def onLoad( self ):
		self.mainToolBar = self.addToolBar( 'deckcanvas_tools', 
			self.getMainWindow().requestToolBar( 'deckcanvas_tools' )
			)
		
		self.addTool( 'deckcanvas_tools/tool_pen',
			widget = SceneToolButton(
				'deckcanvas_pen',
				label = 'Deck Canvas Editor',
				icon = 'deckcanvas/pen'
			)
		)

		self.addTool( 'deckcanvas_tools/toggle_item_bounds_visible',
			label = 'Toggle Item Bounds',
			icon = 'deckcanvas/layer',
			type = 'check'
		)

		self.findTool( 'deckcanvas_tools/toggle_item_bounds_visible' ).setValue( True )

		self.delegate = MOAILuaDelegate( self )
		self.delegate.load( _getModulePath( 'DeckCanvasEditor.lua' ) )
		signals.connect( 'selection.changed', self.onSelectionChanged )

		self.toolWindow = self.requestToolWindow( 'DeckCanvasEditor',
			title     = 'DeckCanvas',
			size      = (120,40),
			minSize   = (120,40)
		)

		self.targetCanvas = None

	def onStart( self ):
		self.setEditActive( True )

	def onSetFocus( self ):
		self.getModule( 'scene_editor' ).setFocus()
		self.container.show()
		self.container.setFocus()

	def updateSelection( self ):
		target = self.delegate.callMethod( 'editor', 'findTargetDeckCanvas' )
		self.setTargetCanvas( target )

	def onSelectionChanged( self, selection, key ):
		if key == 'scene':
			self.updateSelection()

		elif key == 'asset':
			decks = []
			for node in selection:
				if node.getType().startswith( 'deck2d.' ):
					decks.append( node.getNodePath() )

			self.delegate.callMethod( 
				'editor',
				'changeDeckSelection',
				decks
			)

	def setEditActive( self, active ):
		self.enableTool( 'deckcanvas_tools/tool_pen',  active )

	def setTargetCanvas( self, canvas ):
		self.delegate.callMethod( 'editor', 'setTargetCanvas', canvas )
		self.targetCanvas = canvas
		# if not self.targetCanvas:
		# 	self.setEditActive( False )
		# 	return
		# self.setEditActive( True )

	def showToolWindow( self ):
		# self.toolWindow.show()
		self.getModule( 'scene_view' ).setFocus()

	def hideToolWindow( self ):
		# self.toolWindow.hide()
		pass

	def startPenTool( self ):
		self.delegate.callMethod( 'editor', 'startPenTool' )

	def onTool( self, tool ):
		name = tool.name
		if name == 'toggle_item_bounds_visible':
			_MOCK.setDeckCanvasItemBoundsVisible( bool(tool.getValue()) )
			signals.emit( 'scene.update' )
