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
class ColorGradingEditor( SceneEditorModule ):
	name       = 'color_grading_editor'
	dependency = [ 'mock' ]

	def onLoad( self ):
		self.container = self.requestDockWindow(
				title = 'Color Grading'
			)
		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('ColorGradingEditor.ui')
		)
		self.toolbarMain = QtWidgets.QToolBar( window.containerList )
		self.toolbarMain.setOrientation( Qt.Horizontal )
		self.toolbarMain.setMaximumHeight( 32 )

		self.tree = ColorGradingConfigTreeWidget( parent = window.containerList )

		listLayout = QtWidgets.QVBoxLayout( window.containerList )
		listLayout.setSpacing( 0 )
		listLayout.setContentsMargins( 0 , 0 , 0 , 0 )

		listLayout.addWidget( self.toolbarMain )
		listLayout.addWidget( self.tree )

		self.addToolBar( 'color_grading', self.toolbarMain )
		self.addTool( 'color_grading/find_context',   label = 'Find', icon = 'find' )
		self.addTool( 'color_grading/----' )
		self.addTool( 'color_grading/save',           label = 'Save',   icon = 'save' )
		self.addTool( 'color_grading/reset',          label = 'Reset',  icon = 'reset' )
		self.addTool( 'color_grading/----' )
		self.addTool( 'color_grading/add_item',       label = 'Add',    icon = 'add' )
		self.addTool( 'color_grading/remove_item',    label = 'Remove', icon = 'remove' )
		self.addTool( 'color_grading/move_up',        label = 'Up',     icon = 'arrow-up' )
		self.addTool( 'color_grading/move_down',      label = 'Down',   icon = 'arrow-down' )



##----------------------------------------------------------------##
class ColorGradingConfigTreeWidget( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Entries',-1) ]

	def getRootNode( self ):
		return self

	def saveTreeStates( self ):
		pass

	def loadTreeStates( self ):
		pass
	
	def getNodeParent( self, node ): # reimplemnt for target node	
		if node == self:
			return None
		return self

	def getNodeChildren( self, node ):
		if node == self:
			return self.parentModule.getLayers()
		return[]

	def updateItemContent( self, item, node, **option ):
		if node == self: return
		item.setText( 0, node.name )


	# def onItemChanged( self, item, col ):
	# 	self.parentModule.renameLayer( item.node, item.text( col ) )

	# def onItemSelectionChanged( self ):
	# 	self.parentModule.onLayerSelectionChanged( self.getSelection() )

	# def onDClicked( self, item, col ):
	# 	if col != 0:
	# 		self.parentModule.editLayerProperty( item.node )

