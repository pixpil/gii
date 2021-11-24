import random
##----------------------------------------------------------------##
from gii.core        import app, signals
from gii.qt          import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget
from gii.qt.controls.GenericListWidget import GenericListWidget
from gii.qt.controls.CategoryList      import CategoryList

from gii.moai.MOAIRuntime import MOAILuaDelegate
from gii.SceneEditor      import SceneEditorModule, getSceneSelectionManager
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor

##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt, Signal

##----------------------------------------------------------------##
from mock import _MOCK, isMockInstance
##----------------------------------------------------------------##

from .SceneTool import *

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

def _fixDuplicatedName( names, name, id = None ):
	if id:
		testName = name + '_%d' % id
	else:
		id = 0
		testName = name
	#find duplicated name
	if testName in names:
		return _fixDuplicatedName( names, name, id + 1)
	else:
		return testName


##----------------------------------------------------------------##
class SceneToolBox( SceneEditorModule ):
	name = 'scene_tool_box'
	dependency = [ 'scene_tool_manager' ]
	
	def onLoad( self ):
		self.window = self.requestDockWindow( 'SceneToolBox',
			title     = 'Tools',
			size      = (120,120),
			minSize   = (120,120),
			dock      = 'bottom'
		)
		ui = self.window.addWidgetFromFile(
			_getModulePath('SceneToolBox.ui')
		)
		self.window.setStayOnTop( True )
		self.window.show()
		self.window.setObjectName( 'SceneToolBox' )

		self.treeCategory = SceneToolCategoryTreeWidget( 
					multiple_selection = False,
					editable           = False,
					drag_mode          = 'internal'
				)
		treeLayout = QtWidgets.QVBoxLayout( ui.containerTree )
		treeLayout.addWidget( self.treeCategory )
		treeLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		treeLayout.setSpacing( 0 )
		self.treeCategory.parentModule = self

		self.listTools = SceneToolListWidget()
		listLayout = QtWidgets.QVBoxLayout( ui.containerList )
		listLayout.addWidget( self.listTools )
		listLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		listLayout.setSpacing( 0 )
		self.listTools.parentModule = self
		self.listTools.setIconSize( QtCore.QSize( 64, 64 ) )
		# self.listTools.setGridSize( QtCore.QSize( 80, 6464 ) )

		self.currentCategory = None
		self.currentTool     = None
		self.refreshingTools = False
		
		signals.connect( 'tool.change',  self.onSceneToolChanged )
		signals.connect( 'tool_category.update',  self.onSceneToolCategoryUpdate )

	def onStart( self ):
		self.treeCategory.rebuild()

	def onCategorySelectionChanged( self ):
		for category in self.treeCategory.getSelection():
			self.currentCategory = category
			self.rebuildListTools()
			return
		self.currentCategory = None
		self.rebuildListTools()

	def rebuildListTools( self ):
		self.refreshingTools = True
		self.listTools.rebuild()
		activeTool = self.getSceneToolManager().getActiveTool()
		if activeTool and self.listTools.hasNode( activeTool ):
			self.listTools.selectNode( activeTool, goto = True )
		self.refreshingTools = False

	def getToolsInCurrentCategory( self ):
		category = self.currentCategory
		if category:
			return category.getToolList()
		else:
			return []

	def setActiveTool( self, tool ):
		if self.refreshingTools: return
		if not tool: return
		self.currentTool = tool
		self.getSceneToolManager().setActiveTool( tool )

	def onSceneToolChanged( self, tool ):
		if tool == self.currentTool: return
		category = tool.getCategory()
		if not self.treeCategory.hasNode( category ): return
		self.treeCategory.selectNode( category )
		if not self.listTools.hasNode( tool ):
			self.listTools.selectNode( None )
		else:
			self.listTools.selectNode( tool, goto = True )

	def onSceneToolCategoryUpdate( self, category ):
		if category == self.currentCategory:
			self.rebuildListTools()

##----------------------------------------------------------------##
class SceneToolCategoryTreeItemDelegate( QtWidgets.QStyledItemDelegate ):
	def sizeHint( self, option, index ):
		return QtCore.QSize( 10, 24 )

##----------------------------------------------------------------##
class SceneToolCategoryTreeWidget( GenericTreeWidget ):
	def __init__( self, *arg, **kwargs ):
		super( SceneToolCategoryTreeWidget, self ).__init__( *arg, **kwargs )
		self.headerItem().setHidden( True )
		self.setAttribute(Qt.WA_MacShowFocusRect, False)
		self.setItemDelegate( SceneToolCategoryTreeItemDelegate() )


	def getHeaderInfo( self ):
		return [ ('Name',100) ]

	def getRootNode( self ):
		return app.getModule( 'scene_tool_manager' ).getRootCategory()


	def getNodeParent( self, node ): # reimplemnt for target node	
		return node.getParent()

	def getNodeChildren( self, node ):
		return node.getChildren()
		
	def updateItemContent( self, item, node, **option ):
		iconName = node.getIcon()
		item.setIcon( 0, getIcon( iconName ) )
		item.setText( 0, node.getName() )
		
	def onItemSelectionChanged(self):
		selections = self.getSelection()
		self.parentModule.onCategorySelectionChanged()


##----------------------------------------------------------------##
class SceneToolListWidget( GenericListWidget ):
	def __init__( self, *args, **option ):
		super( SceneToolListWidget, self ).__init__( *args )		
		self.setAttribute(Qt.WA_MacShowFocusRect, False)
		self.setWrapping( True )
		self.setResizeMode( QtWidgets.QListView.Adjust  )

	def getItemFlags( self, node ):
		return {}

	def getDefaultOptions( self ):
		return None

	def getNodes( self ):
		return self.parentModule.getToolsInCurrentCategory()

	def updateItemContent( self, item, node, **option ):
		item.setText( node.getName() )
		item.setIcon( getIcon( node.getIcon() ) )

	def onItemSelectionChanged(self):
		node = self.getFirstSelection()
		self.parentModule.setActiveTool( node )
