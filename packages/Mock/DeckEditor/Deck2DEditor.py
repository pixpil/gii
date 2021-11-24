import subprocess
import os.path
import shutil
import time
import json

from gii.core         import *

from gii.qt           import *
from gii.qt.IconCache import getIcon
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor
from gii.qt.dialogs   import requestString, alertMessage, requestColor
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget

from gii.qt.controls.PropertyEditor  import PropertyEditor

from gii.SceneEditor  import SceneEditorModule

from mock    import MOCKEditCanvas

from qtpy  import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt

from .Triangulator import triangulatePolygon
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

class Deck2DEditor( SceneEditorModule ):
	"""docstring for Deck2DEditor"""
	def __init__(self):
		super(Deck2DEditor, self).__init__()
		self.editingAsset  = None
		self.editingPack   = None
		self.editingDeck   = None
		self.spriteToItems = {}
	
	def getName(self):
		return 'deck2d_editor'

	def getDependency(self):
		return [ 'qt', 'mock', 'asset_browser' ]

	def onLoad(self):
		self.windowTitle = 'Deck2D Pack Editor'
		self.container = self.requestDocumentWindow('MockDeck2DEditor',
				title       = 'Deck2D Pack Editor',
				size        = (500,300),
				minSize     = (500,300),
				dock        = 'right'
				# allowDock = False
			)
		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('Deck2DEditor.ui')
		)
		
		self.propEditor = addWidgetWithLayout(
			PropertyEditor(window.settingsContainer),
			window.settingsContainer
		)

		self.canvas = addWidgetWithLayout(
			MOCKEditCanvas( window.canvasContainer ),
			window.canvasContainer
		)
		self.canvas.loadScript( _getModulePath('Deck2DEditor.lua') )
		self.canvas.setDelegateEnv( 'updateEditor', self.onCanvasUpdateRequested )
		self.canvas.setDelegateEnv( 'triangulatePolygon',  triangulatePolygon )

		#setup listwidget
		treeSprites = addWidgetWithLayout( 
			SpriteTreeWidget( self.window.containerSpriteTree, 
				multiple_selection = False 
				)
			)
		treeSprites.module = self
		treeSprites.setSortingEnabled(True)
		self.treeSprites = treeSprites

		#signals
		window.toolAddQuad         .clicked. connect( lambda: self.addItem('quad') )
		window.toolAddQuadArray    .clicked. connect( lambda: self.addItem('quad_array') )
		window.toolAddTileset      .clicked. connect( lambda: self.addItem('tileset') )
		window.toolAddStretchPatch .clicked. connect( lambda: self.addItem('stretchpatch') )
		window.toolAddPoly         .clicked. connect( lambda: self.addItem('polygon') )

		window.toolSave            .clicked. connect( self.saveAsset )
		window.toolRemove          .clicked. connect( self.onRemoveItem )
		window.toolClone           .clicked. connect( self.onCloneItem )

		window.toolOriginE         .clicked. connect( lambda: self.setOrigin('E') )
		window.toolOriginS         .clicked. connect( lambda: self.setOrigin('S') )
		window.toolOriginW         .clicked. connect( lambda: self.setOrigin('W') )
		window.toolOriginN         .clicked. connect( lambda: self.setOrigin('N') )
		window.toolOriginSE        .clicked. connect( lambda: self.setOrigin('SE') )
		window.toolOriginSW        .clicked. connect( lambda: self.setOrigin('SW') )
		window.toolOriginNE        .clicked. connect( lambda: self.setOrigin('NE') )
		window.toolOriginNW        .clicked. connect( lambda: self.setOrigin('NW') )
		window.toolOriginC         .clicked. connect( lambda: self.setOrigin('C') )
		window.checkAlphaView      .stateChanged .connect( self.toggleAlphaView )

		self.propEditor .propertyChanged .connect(self.onPropertyChanged)
		signals.connect('asset.modified', self.onAssetModified)

		self.container.setEnabled( False )

	def onStop( self ):
		self.saveAsset()

	def onSetFocus(self):
		self.container.show()
		self.container.raise_()
		self.container.activateWindow()
		self.container.setFocus()

	def saveAsset(self):
		if not self.editingAsset or not self.editingPack: return
		self.canvas.callMethod( 'editor', 'savePack' , self.editingAsset.getAbsFilePath() )
		
	def openAsset(self, node, subnode=None):
		self.setFocus()
		
		if self.editingAsset != node:
			self.saveAsset()
			self.container.setEnabled( True )
			self.treeSprites.clear()
			assert node.getType() == 'deck2d'
			self.editingAsset = node
			self.container.setDocumentName( node.getNodePath() )
			self.editingPack = self.canvas.safeCallMethod( 'editor', 'openPack', node.getNodePath() )

			self.treeSprites.rebuild()

		if subnode:
			name = subnode.getName()
			deck = self.editingPack.getDeck( self.editingPack, name )
			if deck:
				self.treeSprites.selectNode( deck )
		

	def getSpriteList( self ):
		return []

	def onCanvasUpdateRequested(self):
		item = self.editingDeck
		if not item : return		
		self.propEditor.refreshAll()

	def selectDeck( self, deck ):
		self.editingDeck = deck
		if deck:
			self.propEditor.setTarget( deck )
			self.canvas.safeCall( 'selectDeck', deck )			

	def changeDeckName( self, deck, name ):
			self.canvas.safeCall( 'renameDeck', deck, name )
			
	def addItem( self, atype ):
		if not self.editingAsset: return

		selection = self.getModule( 'asset_browser' ).getItemSelection()
		if not selection: return

		newItems = []		
		for n in selection:
			if not isinstance(n, AssetNode): continue
			if not n.isType( 'texture' ): continue
			#create item
			item = { 
				'name' : n.getBaseName(),
				'src'  : n.getPath(),
				'type' : atype
				}
			deck = self.canvas.safeCall( 'addItem', item )
			self.treeSprites.addNode( deck )

		self.treeSprites.selectNode( deck )
		self.saveAsset()


	def onRemoveItem( self ):
		selection = self.treeSprites.getSelection()
		for deck in selection:
			self.treeSprites.removeNode( deck )
			self.canvas.safeCallMethod( 'editor', 'removeItem', deck )
		self.saveAsset()

	def onCloneItem( self ):
		pass

	def setOrigin( self, direction ):
		if not self.editingDeck: return 
		self.canvas.safeCall( 'setOrigin', direction )		

	def onPreviewTextChanged( self ):
		pass

	def toggleAlphaView( self, state ):
		self.canvas.safeCallMethod( 'editor', 'toggleAlphaView', state == Qt.Checked )

	def onAssetModified( self, asset ):
		pass

	def onPropertyChanged( self, obj, id, value ):
		self.canvas.safeCall( 'updateDeck' )


##----------------------------------------------------------------##
Deck2DEditor().register()

##----------------------------------------------------------------##
class SpriteTreeWidget( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Name', 140), ('Type', 40) ]

	def getRootNode( self ):
		return self.module.editingPack

	def getNodeParent( self, node ):
		if node == self.getRootNode(): return None
		return self.getRootNode()

	def getNodeChildren( self, node ):
		if node == self.module.editingPack:
			return [ deck for deck in list(node.decks.values()) ]
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		if node == self.getRootNode() : return
		
		item.setText( 0, node['name'] )
		item.setText( 1, node['type'] )

		if node['type'] == 'stretchpatch':
			item.setIcon( 0, getIcon('deck_patch'))
		elif node['type'] == 'tileset':
			item.setIcon( 0, getIcon('deck_tileset'))
		elif node['type'] == 'quad_array':
			item.setIcon( 0, getIcon('deck_quad_array'))
		elif node['type'] == 'polygon':
			item.setIcon( 0, getIcon('deck_polygon'))
		else:
			item.setIcon( 0, getIcon('deck_quad'))

	def onItemSelectionChanged( self ):
		for deck in self.getSelection():
			app.getModule('deck2d_editor').selectDeck( deck )
			break

	def onItemActivated( self, item, col ):
		pass

	def onItemChanged( self, item, col ):
		deck = self.getNodeByItem( item )
		app.getModule('deck2d_editor').changeDeckName( deck, item.text(0) )

	def onClipboardCopy( self ):
		clip = QtWidgets.QApplication.clipboard()
		out = None
		for node in self.getSelection():
			if out:
				out += "\n"
			else:
				out = ""
			out += node.getNodePath()
		clip.setText( out )
		return True