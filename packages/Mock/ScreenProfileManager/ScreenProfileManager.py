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

from mock import  MOCKEditCanvas

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

class ScreenProfileManager( SceneEditorModule ):
	def __init__(self):
		super( ScreenProfileManager, self ).__init__()

	def getName( self ):
		return 'screen_profile_manager'

	def getDependency( self ):
		return [ 'mock' ]

	def onLoad( self ):
		self.configPath = self.getProject().getConfigPath( _DEPLOY_CONFIG_FILE )
		#UI
		self.container = self.requestDocumentWindow( 'ScreenProfileManager',
			title     = 'Screen Profile Manager',
			allowDock = False,
			minSize   = ( 200, 200 ),
			)
		self.window = window = self.container.addWidgetFromFile( _getModulePath('ScreenProfileManager.ui') )

		# self.tree 
		layout = QtWidgets.QVBoxLayout()
		window.containerTree.setLayout( layout )
		layout.setSpacing( 0 )		
		layout.setContentsMargins( 0 , 0 , 0 , 0 )

		self.tree = ScreenProfileTree(
				window.containerTree,
				editable = True,
				multiple_selection = False
			)
		self.tree.manager = self
		layout.addWidget( self.tree )

		screenToolbar = QtWidgets.QToolBar( window.containerTree )
		layout.addWidget( screenToolbar )
		self.targetTool = self.addToolBar( 'screen_profile', screenToolbar )
		self.addTool( 'screen_profile/add_profile',    label = '+', icon = 'add' )
		self.addTool( 'screen_profile/remove_profile', label = '-', icon = 'remove' )

		#target property
		self.propertyEditor = addWidgetWithLayout(
			PropertyEditor( window.containerProperty )
		)

		#menu
		self.addMenuItem( 'main/file/screen_profile_manager', 
			dict( label = 'Screen Profile Manager' )
			)
		# self.addTool( 
		# 	'asset/show_screen_profile_manager',
		# 	label = 'Screen Profile Manager',			
		# 	on_click = lambda item: self.setFocus()
		# 	)

		self.canvas = addWidgetWithLayout(
			MOCKEditCanvas( window.containerPreview )
		)
		self.canvas.loadScript( _getModulePath('ScreenProfileManager.lua') )

		self.propertyEditor .propertyChanged .connect( self.onPropertyChanged )


	def onSetFocus( self ):
		self.container.show()
		self.container.raise_()
		self.tree.rebuild()

	def getScreenProfiles( self ):
		return self.canvas.callMethod( 'manager', 'getProfiles' )

	def renameProfile( self, profile, name ):
		profile.name = name
		self.propertyEditor.refresh()

	def onMenu( self, node ):
		name = node.name
		if name == 'screen_profile_manager':
			self.onSetFocus()

	def onTool( self, tool ):
		name = tool.name
		if name == 'add_profile':
			p = self.canvas.callMethod( 'manager', 'addProfile' )
			self.tree.addNode( p )
			self.tree.editNode( p )
		elif name == 'remove_profile':
			for target in self.tree.getSelection():
				self.canvas.callMethod( 'manager', 'removeProfile', target )
				self.tree.removeNode( target )
				return

	def onPropertyChanged( self, obj, id, value ):
		for target in self.tree.getSelection():
			self.tree.refreshNodeContent( target )


ScreenProfileManager().register()

##----------------------------------------------------------------##
class ScreenProfileTree( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Name',150), ('Resolution', 200), ('DPI',30), ('Orientation',-1) ]

	def getRootNode( self ):
		return self.manager

	def getNodeParent( self, node ):
		if node == self.manager: return None
		return self.manager

	def getNodeChildren( self, node ):
		if node == self.manager:
			return [ node for node in list(self.manager.getScreenProfiles().values()) ]
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		if node == self.manager: return
		item.setText( 0, node.name )
		item.setText( 1, node.getDimString( node ) )
		item.setText( 2, str( int(node.dpi) ) )
		item.setText( 3, node.orientation )

	def onItemChanged( self, item, col ):
		target = item.node
		self.manager.renameDeployTarget( target, item.text(0) )

	def onItemSelectionChanged( self ):
		selection = self.getSelection()
		if selection:
			for node in selection:
				self.manager.propertyEditor.setTarget( node )
		else:
			self.manager.propertyEditor.clear()

	def onItemChanged( self, item, col ):
		node = self.getNodeByItem( item )
		if node:
			self.manager.renameProfile( node, item.text( 0 ) )
