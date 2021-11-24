import subprocess
import os.path
import shutil
import time
import json

from gii.core         import *
from gii.qt           import *
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor
from gii.qt.dialogs   import *
from gii.qt.IconCache import getIcon

from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter
from gii.qt.controls.PropertyEditor      import PropertyEditor

from gii.SceneEditor  import SceneEditorModule

from mock import  MOCKEditCanvas

from qtpy  import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt

from gii.SearchView   import requestSearchView, registerSearchEnumerator

##----------------------------------------------------------------##
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

class TextureManager( SceneEditorModule ):
	"""docstring for MockStyleSheetEditor"""
	def __init__(self):
		super(TextureManager, self).__init__()
	
	def getName(self):
		return 'mock.texture_manager'

	def getDependency(self):
		return [ 'qt', 'moai', 'texture_library' ]

	def onLoad(self):
		self.container = self.requestDocumentWindow( 'MockTextureManager',
				title       = 'TextureManager',
				size        = (500,300),
				minSize     = (500,300),
				# allowDock = False
			)
		self.toolbar = self.addToolBar( 'texture_manager', self.container.addToolBar() )

		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('TextureManager.ui')
		)
		
		self.tree = addWidgetWithLayout(
			TextureTreeWidget( 
				window.containerTree,
				drag_mode = 'internal',
				editable  = True,
				multiple_selection = True,
				expanded = False
			)
		)
		self.tree.module = self
		
		self.treeFilter = GenericTreeFilter( window.containerTree )
		window.containerTree.layout().insertWidget( 0, self.treeFilter )
		self.treeFilter.setTargetTree( self.tree )

		self.propEditor = addWidgetWithLayout(
			PropertyEditor( window.containerProp)
		)

		self.canvas = addWidgetWithLayout(
			MOCKEditCanvas( window.containerPreview )
		)
		self.canvas.loadScript( _getModulePath('TextureManager.lua') )

		self.addMenuItem( 'main/asset/----' )
		self.addMenuItem(
				'main/asset/texture_manager',
				{
					'label': 'Texture Manager',
					'on_click': lambda menu: self.setFocus()
				}
			)


		self.addTool(	'texture_manager/rebuild',   label = 'Rebuild', icon  = 'refresh' )
		self.addTool( 'texture_manager/----' )
		self.addTool(	'texture_manager/add_group',   label = 'Add Group', icon  = 'add' )
		self.addTool(	'texture_manager/remove_group',label = 'Remove Group', icon  = 'remove' )
		self.addTool( 'texture_manager/----' )
		self.addTool(	'texture_manager/assign_group',   label = 'Assign Group', icon  = 'in' )
		self.addTool( 'texture_manager/----' )
		self.addTool(	'texture_manager/assign_processor',   label = 'Assign Processor', icon  = 'compose' )
		self.addTool(	'texture_manager/clear_processor',   label = 'Clear Processor', icon  = 'remove' )
		self.addTool( 'texture_manager/----' )
		self.addTool(	'texture_manager/apply',     label = 'Apply Changes' )

		self.addShortcut( self.container, '=',  self.regroupTo )
		self.addShortcut( self.container, '-',  self.regroup, 'default' )

		self.propEditor.propertyChanged. connect( self.onPropertyChanged )
		
		registerSearchEnumerator( textureGroupSearchEnumerator )

	def onStart( self ):
		#test data
		lib = self.getModule('texture_library').getLibrary()
		self.canvas.callMethod( 'preview', 'setLibrary', lib )
		self.tree.rebuild()
		
		signals.connect( 'texture.add', self.onTextureAdd )
		signals.connect( 'texture.remove', self.onTextureRemove )


	def onSetFocus( self ):
		self.container.show()
		self.container.raise_()

	def onAssetRegister(self, node):
		if not node.isType( 'texture' ) : return
		# self.tree.addNode( node )		

	def onAssetUnregister(self, node):
		if not node.isType( 'texture' ) : return
		# self.tree.removeNode( node )

	def onPropertyChanged( self, obj, id, value ):
		if id in ( 'name', 'processor' ) :
			self.tree.refreshNodeContent( obj )
		obj.onFieldChanged( obj, id )	

	def onTool( self, tool ):
		name = tool.name
		if name == 'add_group':
			g = self.canvas.callMethod( 'preview', 'addGroup' )
			self.tree.addNode( g )
			self.tree.editNode( g )
			self.tree.selectNode( g )

		elif name == 'remove_group':
			self.removeSelectedGroup()

		elif name == 'assign_group':
			self.regroupTo()

		elif name == 'assign_processor':
			requestSearchView( 
				info    = 'select processor to assign',
				context = 'asset',
				type    = 'texture_processor',
				on_selection = self.assignProcessor
			)

		elif name == 'clear_processor':
			self.assignProcessor( None )
			
		elif name == 'rebuild':	
			texLib = self.getModule( 'texture_library' )
			assetLib = self.getAssetLibrary()
			for node in self.tree.getSelection():
				clasName = node.getClassName( node )
				if clasName == 'TextureGroup':
					texLib.scheduleUpdateGroup( node, 'file' )
					# for tex in node.textures.values():
					# 	assetNode = assetLib.getAssetNode( tex.path )
					# 	assetNode.markModified()
					# 	assetLib.scheduleScanProject()						
				else:
					texLib.scheduleUpdateTexture( node, True )
					# assetNode = assetLib.getAssetNode( node.path )
					# assetNode.markModified()
					# assetLib.scheduleScanProject()
		elif name == 'apply':
			texLib = self.getModule( 'texture_library' )
			texLib.scheduleUpdate()

	def onTextureAdd( self, texNode ):
		self.tree.addNode( texNode )

	def onTextureRemove( self, texNode ):
		self.tree.removeNode( texNode )

	def regroupTo( self ):
		requestSearchView( 
				info    = 'select texture group to assign',
				context = 'texture_group',				
				on_selection = self.regroup
			)

	def assignProcessor( self, assetNode ):
		path = assetNode and assetNode.getNodePath() or False
		for node in self.tree.getSelection():
			node.processor = path
			self.tree.refreshNodeContent( node )
			if node == self.propEditor.getTarget():
				self.propEditor.refreshAll()

	def getLibrary( self ):
		return self.canvas.callMethod( 'preview', 'getLibrary' )

	def getTextureGroups( self ):
		lib = self.getLibrary()
		return [ group for group in lib.groups.values() ]

	def changeSelection( self ):
		selection = self.tree.getSelection()
		self.canvas.callMethod( 'preview', 'changeSelection', selection )
		if len( selection ) == 1:
			self.propEditor.setTarget( selection[0] )
		else:
			self.propEditor.setTarget( None )

	def renameGroup( self, group, newName ):
		group.name = newName

	def removeSelectedGroup( self ):
		for node in self.tree.getSelection():
			clasName = node.getClassName( node )
			if clasName == 'TextureGroup':				
				if node.default: continue
				#remove groupp, put texutres to default
				self.canvas.callMethod( 'preview', 'removeGroup', node )
				defaultGroup = self.getLibrary().defaultGroup
				self.tree.removeNode( node )
				self.tree.refreshNode( defaultGroup )
			else:
				#move selected texture to default
				self.canvas.callMethod( 'preview', 'moveTextureToDefaultGroup', node )
				self.tree.refreshNode( node )

	def regroup( self, group, refreshTree = True ):
		if group == 'default':
			group = self.getLibrary().defaultGroup

		for node in self.tree.getSelection():
			clasName = node.getClassName( node )
			if clasName == 'TextureGroup':	continue
			self.canvas.callMethod( 'preview', 'regroup', node, group )

		if refreshTree:
			self.tree.rebuild()

##----------------------------------------------------------------##
class TextureTreeWidget( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Name', 200), ('folder', 80), ('processor', -1) ]

	def getRootNode( self ):
		return self.module.getLibrary()

	def saveTreeStates( self ):
		pass

	def loadTreeStates( self ):
		pass

	def getNodeParent( self, node ): # reimplemnt for target node	
		if node == self.getRootNode(): return None
		return node.parent
		
	def getNodeChildren( self, node ):
		if node == self.getRootNode(): #lib
			return [ group for group in node.groups.values() ]
		elif node.getClassName( node ) == 'TextureGroup': #group
			return [ item for item in node.textures.values() ]
		else: #texture
			return []

	def updateItemContent( self, item, node, **option ):
		if node == self.getRootNode(): return		
		clasName = node.getClassName( node )

		if clasName == 'TextureGroup':
			if node.default:
				item.setIcon( 0, getIcon('folder_cyan') )
			else:
				item.setIcon( 0, getIcon('folder') )
			item.setText( 0, node.name )			
			item.setExpanded( node.expanded )
		else:
			path = node.path
			if node.isPrebuiltAtlas( node ):
				item.setIcon( 0, getIcon('cell') )
			else:
				item.setIcon( 0, getIcon('texture') )
			item.setText( 0, os.path.basename( path ) )
			item.setText( 1, os.path.dirname( path ) )

		if node.processor:
			processorName, ext = os.path.splitext( os.path.basename( node.processor ) )
			item.setText( 2, processorName )
		else:
			item.setText( 2, '' )

	def getItemFlags( self, node ):
		clasName = node.getClassName( node )
		if clasName == 'TextureGroup':
			return dict( editable = not node.default, draggable = False, droppable = True )
		else:
			return dict( editable = False, draggable = True, droppable = False )

	def onDropEvent( self, targetNode, pos, ev ):
		if pos == 'viewport': return
		#regroup
		clasName = targetNode.getClassName( targetNode )
		if clasName == 'TextureGroup':
			self.module.regroup( targetNode, False )
		else:
			self.module.regroup( targetNode.parent, False )

	def onItemExpanded( self, item ):
		node = item.node
		if node.getClassName( node ) == 'TextureGroup':
			node.expanded = True

	def onItemCollapsed( self, item ):
		node = item.node
		if node.getClassName( node ) == 'TextureGroup':
			node.expanded = False

	def onItemChanged( self, item, col ):
		node = item.node
		self.module.renameGroup( node, item.text(0) )

	def onItemSelectionChanged(self):
		self.module.changeSelection()

	def onItemActivated( self, item, col ):
		node = item.node
		if node.getClassName( node ) == 'TextureGroup': return
		path = node['path']
		self.module.getModule('asset_browser').locateAsset( path )


##----------------------------------------------------------------##
def textureGroupSearchEnumerator( typeId, context, option ):
	if not context in [ 'texture_group' ] : return None
	result = []
	for group in app.getModule('mock.texture_manager').getTextureGroups():		
		entry = ( group, group.name, 'texture_group', 'folder' )
		result.append( entry )
	return result


##----------------------------------------------------------------##
TextureManager().register()
