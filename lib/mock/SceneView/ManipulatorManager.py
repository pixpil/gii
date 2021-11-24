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

from mock import _MOCK, _MOCK_EDIT, isMockInstance


##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


##----------------------------------------------------------------##
class ManipulatorLauncher( SceneTool ):
	name = 'manipulator_launcher'
	shortcut = 'T'
	context = 'scene_view'
	def onStart( self, **context ):
		module = app.getModule( 'manipulator_manager' )
		module.setEditActive( True )

	def onStop( self ):
		module = app.getModule( 'manipulator_manager' )
		module.setEditActive( False )


##----------------------------------------------------------------##
class ManipulatorManager( SceneEditorModule ):
	name = 'manipulator_manager'
	dependency = [ 'mock', 'scene_view' ]

	def onLoad( self ):
		self.toolWindow = self.requestToolWindow( 'ManipulatorManager',
			title     = 'Manipulators',
			size      = (200,180),
			minSize   = (200,180)
		)

		self.tree = self.toolWindow.addWidget( ManipulatorTargetTreeWidget() )

		self.addTool(	'scene_view_tools/----' )
		self.addTool(	'scene_view_tools/tool_manipulator',
			widget = SceneToolButton( 'manipulator_launcher',
				icon = 'tools/manipulator',
				label = 'Manipulator'
			)
		)

		signals.connect( 'selection.changed', self.onSelectionChanged )
		
		self.targetShapeCanvas = None

		
	def setEditActive( self, active ):
		if active:
			self.toolWindow.show()
		else:
			self.toolWindow.hide()


	def onSelectionChanged( self, selection, key ):
		if key == 'scene':
			pass
			# target = self.delegate.callMethod( 'editor', 'findTargetShapeCanvas' )
			# self.setTargetCanvas( target )
	
##----------------------------------------------------------------##
class ManipulatorTargetTreeWidget( GenericTreeWidget ):
	def __init__( self, *args, **options ):
		options[ 'editable' ] = False
		super( ManipulatorTargetTreeWidget, self ).__init__( *args, **options )
		self.setIndentation( 0 )
		self.setAttribute(Qt.WA_MacShowFocusRect, False)

	def getHeaderInfo( self ):
		return [ ('Target',-1) ]

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


