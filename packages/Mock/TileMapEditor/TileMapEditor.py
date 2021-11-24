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
class SceneToolTilemapPen( SceneTool ):
	name = 'tilemap_pen'
	def onStart( self, **context ):
		app.getModule( 'tilemap_editor' ).changeTool( 'pen' )


##----------------------------------------------------------------##
# class SceneToolTilemapFlipX( SceneTool ):
# 	name = 'tilemap_flipx'
# 	def onStart( self, **context ):
# 		app.getModule( 'tilemap_editor' ).changeTool( 'flip_x' )

##----------------------------------------------------------------##
class SceneToolTilemapEraser( SceneTool ):
	name = 'tilemap_eraser'
	def onStart( self, **context ):
		app.getModule( 'tilemap_editor' ).changeTool( 'eraser' )

##----------------------------------------------------------------##
class SceneToolTilemapFill( SceneTool ):
	name = 'tilemap_fill'
	def onStart( self, **context ):
		app.getModule( 'tilemap_editor' ).changeTool( 'fill' )

##----------------------------------------------------------------##
class SceneToolTilemapTerrain( SceneTool ):
	name = 'tilemap_terrain'
	def onStart( self, **context ):
		app.getModule( 'tilemap_editor' ).changeTool( 'terrain' )

##----------------------------------------------------------------##
class TileMapEditor( SceneEditorModule ):
	name       = 'tilemap_editor'
	dependency = [ 'mock' ]

	def onLoad( self ):
		self.viewSelectedOnly = True

		self.container = self.requestDockWindow(
				title = 'Tilemap'
			)
		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('TileMapEditor.ui')
		)

		self.canvas = MOCKEditCanvas( window.containerCanvas )
		self.canvas.loadScript( 
				_getModulePath('TileMapEditor.lua'),
				{
					'_module': self
				}
			)		

		self.toolbarLayers = QtWidgets.QToolBar( window.containerLayers )
		self.toolbarLayers.setOrientation( Qt.Horizontal )
		self.toolbarLayers.setMaximumHeight( 20 )

		self.toolbarMain = QtWidgets.QToolBar( window.containerCanvas )
		self.toolbarMain.setOrientation( Qt.Horizontal )
		# self.toolbarMain.setIconSize( 32 )
		
		self.treeLayers = TileMapLayerTreeWidget(
			window.containerLayers,
			editable = True
		 )
		self.treeLayers.parentModule = self
		self.treeLayers.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding )

		self.listTerrain = TileMapTerrainList(
			window.containerLayers,
			editable = False,
			mode = 'list'
		)
		self.listTerrain.parentModule = self
		self.listTerrain.setFixedHeight( 70 )
		self.listTerrain.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )

		self.listCodeTile = CodeTilesetList(
			window.containerLayers,
			editable = False,
			mode = 'list'
		)
		self.listCodeTile.parentModule = self
		self.listCodeTile.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding )
		self.listCodeTile.hide()

		self.canvas.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding )

		canvasLayout = QtWidgets.QVBoxLayout( window.containerCanvas )
		canvasLayout.setSpacing( 0 )
		canvasLayout.setContentsMargins( 0 , 0 , 0 , 0 )

		layersLayout = QtWidgets.QVBoxLayout( window.containerLayers )
		layersLayout.setSpacing( 0 )
		layersLayout.setContentsMargins( 0 , 0 , 0 , 0 )

		canvasLayout.addWidget( self.canvas )
		canvasLayout.addWidget( self.listTerrain )
		canvasLayout.addWidget( self.listCodeTile )
		canvasLayout.addWidget( self.toolbarMain )

		layersLayout.addWidget( self.toolbarLayers )
		layersLayout.addWidget( self.treeLayers )

		self.addToolBar( 'tilemap_layers', self.toolbarLayers )
		self.addToolBar( 'tilemap_main', self.toolbarMain )
		
		self.addTool( 'tilemap_layers/add_layer',    label = 'Add', icon = 'add' )
		self.addTool( 'tilemap_layers/remove_layer', label = 'Remove', icon = 'remove' )
		self.addTool( 'tilemap_layers/layer_up',     label = 'up', icon = 'arrow-up' )
		self.addTool( 'tilemap_layers/layer_down',   label = 'down', icon = 'arrow-down' )
		self.addTool( 'tilemap_layers/----' )
		self.addTool( 'tilemap_layers/edit_property',label = 'edit', icon = 'settings' )
		self.addTool( 'tilemap_layers/----' )
		self.addTool( 'tilemap_layers/inc_subdiv',   label = 'subD+' )
		self.addTool( 'tilemap_layers/dec_subdiv',   label = 'subD-' )
		self.addTool( 'tilemap_layers/----' )
		self.addTool( 'tilemap_layers/view_selected_only', label = 'View Selected Only', type='check' )
		

		self.addTool( 'tilemap_main/find_tilemap', icon = 'find', label = 'Find TileMap' ) 
		self.addTool( 'tilemap_main/----' ) 
		self.addTool( 'tilemap_main/tool_pen', 
			widget = SceneToolButton( 'tilemap_pen',
				icon = 'tilemap/pen',
				label = 'Pen'
			)
		)
		self.addTool( 'tilemap_main/tool_terrain', 
			widget = SceneToolButton( 'tilemap_terrain',
				icon = 'tilemap/terrain',
				label = 'Terrain'
			)
		)
		self.addTool( 'tilemap_main/tool_eraser', 
			widget = SceneToolButton( 'tilemap_eraser',
				icon = 'tilemap/eraser',
				label = 'Eraser'
			)
		)

		# self.addTool( 'tilemap_main/tool_flipx', 
		# 	widget = SceneToolButton( 'tilemap_flipx',
		# 		icon = 'tilemap/flip_x',
		# 		label = 'Flip X'
		# 	)
		# )

		self.addTool( 'tilemap_main/tool_fill', 
			widget = SceneToolButton( 'tilemap_fill',
				icon = 'tilemap/fill',
				label = 'Fill'
			)
		)
		self.addTool( 'tilemap_main/----' )
		self.addTool( 'tilemap_main/tool_random',   label = 'Random', icon = 'tilemap/random', type = 'check' )
		self.addTool( 'tilemap_main/----' )
		self.addTool( 'tilemap_main/tool_clear',    label = 'Clear', icon = 'tilemap/clear' )

		signals.connect( 'selection.changed', self.onSceneSelectionChanged )

		self.targetTileMap = None
		self.targetTileMapLayer = None

	def onStart( self ):
		self.container.show()
		# self.container.setEnabled( False )
		self.setEditActive( False )
		
		viewSelectedOnly = self.getWorkspaceConfig( 'view_selected_only', True )
		self.findTool( 'tilemap_layers/view_selected_only' ).setValue(
			viewSelectedOnly
		)
		self.setViewSelectedOnly( viewSelectedOnly )

	def onStop( self ):
		self.setWorkspaceConfig( 'view_selected_only', self.viewSelectedOnly )

	def onSetFocus( self ):
		self.getModule( 'scene_editor' ).setFocus()
		self.container.show()
		self.container.setFocus()

	def onSceneSelectionChanged( self, selection, key ):
		if key != 'scene': return
		#find animator component
		target = self.canvas.callMethod( 'editor', 'findTargetTileMap' )
		self.setTargetTileMap( target )

	def onLayerSelectionChanged( self, selection ):
		if selection:
			self.setTargetTileMapLayer( selection[0] )
		else:
			self.setTargetTileMapLayer( None )
		signals.emit( 'scene.update' )

	def onTerrainSelectionChanged( self, selection ):
		if selection:
			self.canvas.callMethod( 'editor', 'setTerrainBrush', selection[0] )
			self.changeSceneTool( 'tilemap_terrain' )

	def onCodeTileSelectionChanged( self, selection ):
		if selection:
			self.canvas.callMethod( 'editor', 'selectCodeTile', selection[0] )
			self.changeSceneTool( 'tilemap_pen' )


	def setEditActive( self, active ):
		self.window.containerLayers.setEnabled( active )
		self.canvas.setEnabled( active )
		self.enableTool( 'tilemap_main/tool_pen', active )
		self.enableTool( 'tilemap_main/tool_terrain', active )
		self.enableTool( 'tilemap_main/tool_eraser', active )
		# self.enableTool( 'tilemap_main/tool_flipx', active )
		self.enableTool( 'tilemap_main/tool_fill', active )
		self.enableTool( 'tilemap_main/tool_random', active )
		self.enableTool( 'tilemap_main/tool_clear', active )


	def setViewSelectedOnly( self, toggle ):
		self.viewSelectedOnly = toggle
		self.canvas.callMethod( 'editor', 'setViewSelectedOnly', self.viewSelectedOnly )

	def clearTerrainSelection( self ):
		self.listTerrain.selectNode( None )

	def clearCodeTileSelection( self ):
		self.listCodeTile.selectNode( None )

	def setTargetTileMap( self, tileMap ):
		self.setTargetTileMapLayer( None )
		self.canvas.callMethod( 'editor', 'setTargetTileMap', tileMap )
		self.targetTileMap = tileMap
		if not self.targetTileMap:
			self.treeLayers.clear()
			# self.container.setEnabled( False )
			self.setEditActive( False )
			return
		# self.container.setEnabled( True )
		self.setEditActive( True )
		self.treeLayers.rebuild()
		layers = self.getLayers()
		if layers:
			self.treeLayers.selectNode( layers[0] )

	def setTargetTileMapLayer( self, layer ):
		self.canvas.callMethod( 'editor', 'setTargetTileMapLayer', layer )
		self.canvas.updateCanvas()
		self.targetTileMapLayer = layer
		if isMockInstance( layer, 'CodeTileMapLayer' ):
			self.listCodeTile.show()
			self.listTerrain.hide()
			self.canvas.hide()
			self.listCodeTile.rebuild()
		else:
			self.listCodeTile.hide()
			self.listTerrain.show()
			self.canvas.show()
			self.listTerrain.rebuild()

	def getTerrainTypeList( self ):
		if self.targetTileMapLayer:
			tileset = self.targetTileMapLayer.tileset
			brushTable = tileset.getTerrainBrushes( tileset )
			return [ brush for brush in brushTable.values() ]
		return []

	def getCodeTilesetList( self ):
		if self.targetTileMapLayer:
			tileset = self.targetTileMapLayer.tileset
			return [ key for key in tileset.idToTile.values() ]
		return []

	def getLayers( self ):
		if not self.targetTileMap: return []
		layers = self.targetTileMap.getLayers( self.targetTileMap )
		return [ layer for layer in layers.values() ]

	def createLayer( self, tilesetNode ):
		layer = self.canvas.callMethod( 'editor', 'createTileMapLayer', tilesetNode.getPath() )
		if layer:
			self.treeLayers.addNode( layer )
			self.treeLayers.selectNode( layer )
			self.treeLayers.editNode( layer )

	def renameLayer( self, layer, name ):
		layer.name = name

	def listTileMapLayerTypes( self, typeId, context, option ):
		res = self.canvas.callMethod( 'editor', 'requestAvailTileMapLayerTypes' )
		entries = []
		for n in list(res.values()):
			entry = ( n, n, 'LayerTypes', 'obj' )
			entries.append( entry )
		return entries

	def changeTool( self, toolId ):
		self.canvas.callMethod( 'editor', 'changeTool', toolId )
		if toolId == 'terrain':
			currentBrush = self.canvas.callMethod( 'editor', 'getTerrainBrush' )
			
	def selectTileMapEntity( self, com ):
		entity = com._entity
		if not entity: return
		self.changeSelection( entity )

	def onTool( self, tool ):
		name = tool.name
		if   name == 'find_tilemap':
			requestSearchView( 
				context   = 'scene',
				type      = _MOCK.TileMap,
				on_selection = self.selectTileMapEntity
			)

		elif name == 'add_layer':
			if not self.targetTileMap: return
			supportedTilesetTypes = self.targetTileMap.getSupportedTilesetType( self.targetTileMap )
			requestSearchView( 
				info         = 'select tileset for new layer',
				context      = 'asset',
				type         = supportedTilesetTypes,
				multiple_selection = False,
				on_selection = self.createLayer,
				# on_search    = self.listTileMapLayerTypes	
			)

		elif name == 'remove_layer':
			self.canvas.callMethod( 'editor', 'removeTileMapLayer' )
			self.treeLayers.rebuild()

		elif name == 'layer_up':
			self.canvas.callMethod( 'editor', 'moveTileMapLayerUp' )
			self.treeLayers.rebuild()

		elif name == 'layer_down':
			self.canvas.callMethod( 'editor', 'moveTileMapLayerDown' )
			self.treeLayers.rebuild()

		elif name == 'tool_clear':
			self.canvas.callMethod( 'editor', 'clearLayer' )
		
		elif name == 'tool_random':
			self.canvas.callMethod( 'editor', 'toggleToolRandom', tool.getValue() )

		elif name == 'inc_subdiv':
			if self.targetTileMapLayer:
				self.canvas.callMethod( 'editor', 'incSubDivision' )
				self.treeLayers.refreshNodeContent( self.targetTileMapLayer )

		elif name == 'dec_subdiv':
			if self.targetTileMapLayer:
				self.canvas.callMethod( 'editor', 'decSubDivision' )
				self.treeLayers.refreshNodeContent( self.targetTileMapLayer )

		elif name == 'view_selected_only':
			self.setViewSelectedOnly( tool.getValue() )

		elif name == 'edit_property':
			if self.targetTileMapLayer:
				self.editLayerProperty( self.targetTileMapLayer )
	
	def editLayerProperty( self, layer ):
		requestProperty(
			'Edit TileMapLayer: ' + layer.name ,
			layer,
			cancel_button = False
		)
		self.treeLayers.refreshNodeContent( layer )
		m = layer.getMap( layer )
		if m:
			m.markDataModified( m )

##----------------------------------------------------------------##
class TileMapLayerTreeWidget( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Name',120),  ('Vis', 30), ('SubD', 35),  ('Tileset',100), ('TilesetSize', 80 ), ('Material', -1) ]

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
		item.setIcon( 0, getIcon( 'tilemap/layer' ) )
		item.setText( 0, node.name )

		if node.visible:
			item.setText( 1, 'Y' )
		else:
			item.setText( 1, '' )

		item.setText( 2, '%d' % node.subdivision )
		
		path = node.getTilesetPath( node ) or ''
		item.setText( 3, os.path.basename(path) )

		tw, th = node.getTilesetSize( node )
		size = '( %d, %d )' % ( tw, th )
		item.setText( 4,  size )

		matPath = node.materialPath
		if matPath:
			item.setText( 5, os.path.splitext( os.path.basename( matPath ) )[0] )
		else:
			item.setText( 5, '--' )


	def onItemChanged( self, item, col ):
		self.parentModule.renameLayer( item.node, item.text( col ) )

	def onItemSelectionChanged( self ):
		self.parentModule.onLayerSelectionChanged( self.getSelection() )

	def onDClicked( self, item, col ):
		if col != 0:
			self.parentModule.editLayerProperty( item.node )


##----------------------------------------------------------------##
class TileMapTerrainList( GenericListWidget ):
	def getNodes( self ):
		return self.parentModule.getTerrainTypeList()

	def updateItemContent( self, item, node, **option ):
		item.setText( node.name )
		item.setIcon( getIcon( 'tilemap/terrain_item' ) )

	def onItemSelectionChanged( self ):
		self.parentModule.onTerrainSelectionChanged( self.getSelection() )


##----------------------------------------------------------------##
class CodeTilesetList( GenericListWidget ):
	def getNodes( self ):
		return self.parentModule.getCodeTilesetList()

	def updateItemContent( self, item, node, **option ):
		item.setText( node.name )
		item.setIcon( getIcon( 'tilemap/code_item' ) )

	def onItemSelectionChanged( self ):
		self.parentModule.onCodeTileSelectionChanged( self.getSelection() )
