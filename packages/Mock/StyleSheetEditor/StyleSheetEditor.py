import subprocess
import os.path
import shutil
import time
import json

from gii.core                            import *

from gii.qt                              import *
from gii.qt.IconCache                    import getIcon
from gii.qt.helpers                      import addWidgetWithLayout, QColorF, unpackQColor
from gii.qt.dialogs                      import requestString, alertMessage, requestColor
from gii.qt.controls.GraphicsView        import TimelineWidget
from gii.qt.controls.GenericTreeWidget   import GenericTreeWidget
from gii.qt.controls.PropertyEditor      import PropertyEditor
from gii.SceneEditor                     import SceneEditorModule
from mock             import MOCKEditCanvas

from qtpy                               import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore                        import Qt

from gii.SearchView   import requestSearchView, registerSearchEnumerator


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
_LOREM = '''Lorem ipsum dolor sit amet, consectetur adipisicing elit, '''
##----------------------------------------------------------------##
class MockStyleSheetEditor( SceneEditorModule ):
	def __init__(self):
		super(MockStyleSheetEditor, self).__init__()
		self.editingNode = None
		self.styleSheetData = None
		self.currentStyle   = None
	
	def getName(self):
		return 'mock.stylesheet_editor'

	def getDependency(self):
		return [ 'qt', 'mock' ]

	def onLoad(self):
		self.container = self.requestDocumentWindow( 'MockStyleSheetEditor',
				title       = 'Style Sheet Editor',
				size        = (500,300),
				minSize     = (500,300),
				dock        = 'right'
			)
		self.toolBar = self.addToolBar( 'style_sheet', self.container.addToolBar() )

		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('styleEditor.ui')
		)
		
		self.tree = addWidgetWithLayout( 
			StyleTreeWidget( self.window.containerTree, 
				multiple_selection = False,
				editable  = True,
				show_root = False,
				sorting   = True,
				drag_mode = False
				)
			)
		self.tree.module = self

		self.propEditor = addWidgetWithLayout(
			PropertyEditor( window.containerProp )
		)

		#Previews
		self.canvasPreviewSheet = addWidgetWithLayout(
			MOCKEditCanvas(window.previewSheet)
		)
		self.canvasPreviewSheet.loadScript( _getModulePath('StyleSheetPreview.lua') )

		self.canvasPreviewStyle = addWidgetWithLayout(
			MOCKEditCanvas(window.previewStyle)
		)
		self.canvasPreviewStyle.loadScript( _getModulePath('SingleStylePreview.lua') )

		#Tools
		self.addTool( 'style_sheet/save',         label = 'Save', icon = 'save' )
		self.addTool( 'style_sheet/add_style',    label = 'Add Style', icon = 'add' )
		self.addTool( 'style_sheet/remove_style', label = 'Remove Style', icon = 'remove' )
		self.addTool( 'style_sheet/clone_style',  label = 'Clone Style', icon = 'clone' )

		#signals
		self.propEditor .propertyChanged .connect(self.onPropertyChanged)

		window.textStylePreview.textChanged.connect( self.onStylePreviewTextChanged )
		window.textSheetPreview.textChanged.connect( self.onSheetPreviewTextChanged )

# 		window.comboAlign.currentIndexChanged.connect( self.onAlignChanged )
		
	def onSetFocus(self):
		self.container.show()
		self.container.raise_()
		self.container.activateWindow()
		self.container.setFocus()

	def openAsset( self, node ):
		self.setFocus()
		if self.editingNode == node: return
		self.closeAsset()
		self.container.setEnabled( True )
		self.editingNode = node
		self.container.setDocumentName( node.getNodePath() )
		self.editingSheet = self.canvasPreviewSheet.safeCallMethod( 'preview', 'open', node.getNodePath() )
		self.tree.rebuild()
		self.previewText = self.editingNode.getMetaData( 'previewText', _LOREM )
		self.window.textSheetPreview.setPlainText( self.previewText )
		self.window.textStylePreview.setText( "Hello, Gii!" )

	def closeAsset( self ):
		if self.editingNode:
			self.saveAsset()
			self.container.setEnabled( False )
			self.editingNode  = None
			self.editingSheet = None
			self.tree.clear()
			self.propEditor.clear()

	def saveAsset(self):
		if not self.editingNode: return
		style = self.canvasPreviewSheet.callMethod( 'preview', 'save', self.editingNode.getAbsFilePath() )

	def onStop( self ):
		self.saveAsset()

	def updateCurrentStyle( self ):
		self.canvasPreviewSheet.safeCall( 'updateStyle', self.currentStyle )
		self.canvasPreviewStyle.safeCall( 'updatePreview' )

	def addStyle( self ):
		style = self.canvasPreviewSheet.callMethod( 'preview', 'addStyle' )
		self.tree.addNode( style )
		self.tree.selectNode( style )
		self.tree.editNode( style )

	def renameStyle( self, style, name ):
		self.canvasPreviewSheet.callMethod( 'preview', 'renameStyle', style, name )
		self.propEditor.refreshAll()
	
	def removeStyle( self, style = None ):
		if not style: style = self.tree.getFirstSelection()
		if self.canvasPreviewSheet.callMethod( 'preview', 'removeStyle', style ):
			self.tree.removeNode( style )

	def cloneStyle( self, style = None ):
		if not style: style = self.tree.getFirstSelection()
		cloned = self.canvasPreviewSheet.callMethod( 'preview', 'cloneStyle', style )
		if cloned:
			self.tree.addNode( cloned )
			self.tree.selectNode( cloned )
			self.tree.editNode( cloned )

	def selectStyle( self, style ):
		self.propEditor.setTarget( style )
		self.canvasPreviewStyle.callMethod( 'preview', 'setStyle', style )

	def getStyleList( self ):
		if not self.editingSheet: return []
		return [ style for style in list(self.editingSheet['styles'].values()) ]

	def onPropertyChanged( self, obj, id, value ):
		if id == 'size' or id == 'name':
			self.tree.refreshNodeContent( obj )		
		self.canvasPreviewSheet.callMethod( 'preview', 'updateStyles' )
		self.canvasPreviewStyle.callMethod( 'preview', 'updateStyle' )

	def onTool( self, tool ):
		name = tool.name
		if name == 'save':
			self.saveAsset()
		elif name == 'add_style':
			self.addStyle()
		elif name == 'remove_style':
			self.removeStyle()
		elif name == 'clone_style':
			self.cloneStyle()

# 	def onAlignChanged( self, index ):
# 		text = self.window.comboAlign.itemText( index )
# 		if text:
# 			self.canvasPreviewSheet.safeCall('setAlign', text.encode('utf-8'))

	def onSheetPreviewTextChanged( self ):
		if not self.editingNode: return
		self.previewText = self.window.textSheetPreview.toPlainText() 
		self.editingNode.setMetaData( 'previewText', self.previewText )
		self.canvasPreviewSheet.callMethod( 'preview', 'setPreviewText', self.previewText )

	def onStylePreviewTextChanged( self, text ):
		if not self.editingNode: return
		self.canvasPreviewStyle.callMethod( 'preview', 'setPreviewText', text )
		
##----------------------------------------------------------------##
class StyleTreeWidget( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Name', 110), ('Size', 30) ]

	def getRootNode( self ):
		return self.module

	def getNodeParent( self, node ):
		if node == self.getRootNode(): return None
		return self.getRootNode()

	def getNodeChildren( self, node ):		
		if node == self.module:
			return self.module.getStyleList()
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		if node == self.getRootNode(): return
		item.setText( 0, node['name'] )
		item.setText( 1, '%d' % node['size'] )
		
	def onItemSelectionChanged(self):
		self.module.selectStyle( self.getFirstSelection() )

	def onItemChanged( self, item, col ):
		node = item.node
		self.module.renameStyle( node, item.text(0) )

##----------------------------------------------------------------##

MockStyleSheetEditor().register()

