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
from gii.qt.controls.CodeEditor import CodeEditor

from gii.SceneEditor  import SceneEditorModule

from mock import MOCKEditCanvas
from gii.moai import _LuaObject

from qtpy  import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt
from gii.SearchView import requestSearchView

##----------------------------------------------------------------##
from mock import _MOCK, isMockInstance
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

class EffectEditor( SceneEditorModule ):
	def __init__(self):
		super(EffectEditor, self).__init__()
		self.editingAsset     = None
		self.editConfig       = None
		self.previewing       = False
		self.refreshFlag      = -1
		self.scriptModifyFlag = -1
		self.refreshingScript = False
		self.checkScriptTimer = None
		self.checkRefershTimer = None

	def getName(self):
		return 'effect_editor'

	def getDependency(self):
		return [ 'qt', 'mock' ]

	def onLoad(self):
		self.windowTitle = 'Effect System Editor'
		self.container = self.requestDocumentWindow('MockEffectEditor',
				title       = 'Effect Editor',
				size        = (500,300),
				minSize     = (500,300),
				# allowDock = False
			)

		self.tool = self.addToolBar( 'effect_editor', self.container.addToolBar() )
		self.addTool( 'effect_editor/save',   label = 'Save', icon = 'save' )
		self.addTool( 'effect_editor/----' )
		self.addTool( 'effect_editor/remove_node', icon = 'remove' )
		self.addTool( 'effect_editor/clone_node',  icon = 'clone'    )
		self.addTool( 'effect_editor/add_system',  label = '+System' )
		self.addTool( 'effect_editor/add_child',   label = '+Child' )
		self.addTool( 'effect_editor/----' )
		self.addTool( 'effect_editor/add_move',  label = '+Move' )
		self.addTool( 'effect_editor/----' )
		self.addTool( 'effect_editor/move_up',     icon = 'arrow-up' )
		self.addTool( 'effect_editor/move_down',   icon = 'arrow-down' )
		self.addTool( 'effect_editor/----' )
		self.addTool( 'effect_editor/toggle_preview', icon = 'play', type = 'check' )
		
		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('EffectEditor.ui')
		)
		self.canvas = addWidgetWithLayout(
			MOCKEditCanvas( window.containerPreview )
		)
		window.setFocusProxy( self.canvas )
		self.tree = addWidgetWithLayout(
				EffectNodeTreeWidget( window.containerTree )
			)
		self.tree.module = self
		
		propLayout = QtWidgets.QVBoxLayout()
		window.containerEditor.setLayout( propLayout )
		propLayout.setSpacing( 2 )
		propLayout.setContentsMargins( 0 , 0 , 0 , 0 )

		self.nodePropEditor  = PropertyEditor( window.containerEditor )
		self.paramPropEditor = PropertyEditor( window.containerEditor )
				
		propLayout.addWidget( self.nodePropEditor )
		propLayout.addWidget( self.paramPropEditor )
		self.paramPropEditor.setVisible( False )
		window.containerScript.setVisible( False )

		self.codebox = codebox = addWidgetWithLayout(
			CodeEditor( window.containerScript )
		)
		
		settingData = JSONHelper.tryLoadJSON(
				self.getApp().findDataFile( 'script_settings.json' )
			)
		# if settingData:
		# 	codebox.applySetting( settingData )

		self.editingTarget = None
		
		#ShortCuts
		self.addShortcut( self.container, '+',  self.addSystem )
		self.addShortcut( self.container, '=',  self.promptAddChild )
		self.addShortcut( self.container, '-',  self.removeNode )
		# self.addShortcut( self.container, ']',  self.moveNodeUp )
		# self.addShortcut( self.container, '[',  self.moveNodeDown )
		self.addShortcut( self.container, 'ctrl+D',  self.cloneNode )
		self.addShortcut( self.container, 'f5',      self.togglePreview )
		self.addShortcut( self.container, 'f4',      self.restartPreview )

		#Signals
		self.nodePropEditor   .propertyChanged  .connect( self.onNodePropertyChanged  )
		self.paramPropEditor  .propertyChanged  .connect( self.onParamPropertyChanged )
		self.codebox          .textChanged      .connect( self.onScriptChanged )

		signals.connect( 'app.activate',   self.onAppActivate )
		signals.connect( 'app.deactivate', self.onAppDeactivate )

	def onStart( self ):
		self.canvas.loadScript( _getModulePath('EffectEditor.lua') )

	def onSetFocus( self ):
		self.container.show()
		self.container.raise_()
		self.container.activateWindow()
		self.container.setFocus()

	def onAppActivate(self):
		if self.previewing:
			self.canvas.callMethod( 'editor', 'pausePreview', False )

	def onAppDeactivate(self):
		if self.previewing:
			self.canvas.callMethod( 'editor', 'pausePreview', True )

	def openAsset( self, node ):
		self.setFocus()
		if self.editingAsset == node: return
		self.closeAsset()
		self.editConfig = self.canvas.safeCallMethod( 'editor', 'open', node.getNodePath() )
		self.editingAsset  = node
		self.container.setDocumentName( node.getNodePath() )
		self.tree.rebuild()
		self.selectEditTarget( None )
		self.checkScriptTimer  = self.container.startTimer( 3, self.checkScript )
		self.checkRefershTimer  = self.container.startTimer( 10, self.checkRefresh )

	def saveAsset( self ):
		if not self.editingAsset: return
		self.canvas.safeCallMethod( 'editor', 'save', self.editingAsset.getAbsFilePath() )

	def closeAsset( self ):
		if not self.editingAsset: return
		self.togglePreview( False )
		self.checkScriptTimer.stop()
		self.checkRefershTimer.stop()
		self.editingAsset = None

	def getEditingConfig( self ):
		return self.editConfig

	def selectEditTarget( self, node ):
		self.editingTarget = node
		self.nodePropEditor.setTarget( node )
		#check tool button state
		# isSystem = isMockInstance( node, 'EffectNodeParticleSystem' )
		if isMockInstance( node, 'EffectNodeParticleState' ):
			self.window.containerScript.setVisible( True )
			self.paramPropEditor.setVisible( True )
			self.updateScript()

		elif isMockInstance( node, 'EffectScript' ):
			self.window.containerScript.setVisible( True )
			self.paramPropEditor.setVisible( False )
			self.paramPropEditor.setTarget( None )
			self.updateScript()

		else:
			self.window.containerScript.setVisible( False )
			self.paramPropEditor.setVisible( False )
			self.paramPropEditor.setTarget( None )

	def renameNode( self, node, name ):
		node['name'] = name
		if node == self.editingTarget:
			self.nodePropEditor.refreshField( 'name' )

	def postCreateNode( self, node ):
		self.tree.addNode( node )
		self.tree.selectNode( node )
		self.tree.editNode( node )
		self.markNodeDirty( node )

	def listParticleSystemChildTypes( self, typeId, context, option ):
		res = self.canvas.callMethod( 'editor', 'requestAvailSubNodeTypes', self.tree.getFirstSelection() )
		entries = []
		for n in list(res.values()):
			entry = ( n, n, 'FX Node', 'effect/'+n )
			entries.append( entry )
		return entries

	def addChildNode( self, childType ):
		node = self.canvas.callMethod( 'editor', 'addChildNode', self.editingTarget, childType )
		self.postCreateNode( node )

	def removeNode( self ):
		if self.editingTarget:
			self.markNodeDirty( self.editingTarget )
			self.canvas.callMethod( 'editor', 'removeNode', self.editingTarget )
			self.tree.removeNode( self.editingTarget )

	def promptAddChild( self ):
		requestSearchView( 
			context      = 'effect_editor',
			type         = None,
			multiple_selection = False,
			on_selection = self.addChildNode,
			on_search    = self.listParticleSystemChildTypes				
		)

	def cloneNode( self ):
		if self.editingTarget:
			node = self.canvas.callMethod( 'editor', 'cloneNode', self.editingTarget )
			self.postCreateNode( node )

	def addSystem( self ):
		sys = self.canvas.callMethod( 'editor', 'addSystem' )
		self.postCreateNode( sys )

	def addMove( self ):
		sys = self.canvas.callMethod( 'editor', 'addMove' )
		self.postCreateNode( sys )

	def updateScript( self ):
		self.refreshingScript = True
		stateNode = self.editingTarget
		self.codebox.setPlainText( stateNode.script or '', 'text/x-lua' )
		self.updateParamProxy()
		self.refreshingScript = False
		#TODO: param

	def updateParamProxy( self ):
		if isMockInstance( self.editingTarget, 'EffectNodeParticleState' ):
			stateNode = self.editingTarget
			self.paramProxy = stateNode.buildParamProxy( stateNode )
			self.paramPropEditor.setTarget( self.paramProxy )

	def onScriptChanged( self ):
		if not self.editingTarget: return
		if self.refreshingScript: return
		src = self.codebox.toPlainText()
		stateNode = self.editingTarget
		stateNode.script = src
		self.scriptModifyFlag = 1

	def togglePreview( self, previewing = None ):
		if previewing == None:
			self.previewing = not self.previewing
		else:
			self.previewing = previewing
		if self.previewing:
			self.canvas.callMethod( 'editor', 'startPreview' )
		else:
			self.canvas.callMethod( 'editor', 'stopPreview' )
		self.checkTool( 'effect_editor/toggle_preview', self.previewing )

	def restartPreview( self ):
		if self.previewing:
			self.togglePreview()
		self.togglePreview()
					
	def onTool( self, tool ):
		name = tool.name
		if name == 'save':
			self.saveAsset()
		elif name == 'add_system':
			self.addSystem()

		elif name == 'add_move':
			self.addMove()

		elif name == 'add_child':
			self.promptAddChild()			
		
		elif name == 'remove_node':
			self.removeNode()			

		elif name == 'clone_node':
			self.cloneNode()

		elif name == 'toggle_preview':
			self.togglePreview()

	def onNodePropertyChanged( self, node, id, value ):
		if id == 'name':
			self.tree.refreshNodeContent( node )
		else:
			self.markNodeDirty( self.editingTarget )

	def onParamPropertyChanged( self, node, id, value ):
		self.markNodeDirty( self.editingTarget )

	def markNodeDirty( self, node ):
		self.canvas.callMethod( 'editor', 'markDirty', node )
		self.refreshFlag = 1

	def checkScript( self ):
		if self.scriptModifyFlag == 0:
			self.updateParamProxy()
			self.markNodeDirty( self.editingTarget )

		if self.scriptModifyFlag >= 0:
			self.scriptModifyFlag -= 1

	def checkRefresh( self ):
		if self.refreshFlag > 0 :
			self.canvas.callMethod( 'editor', 'refreshPreview' )
			self.refreshFlag = 0

##----------------------------------------------------------------##
class EffectNodeTreeWidget( GenericTreeWidget ):
	def getDefaultOptions( self ):
		return dict(
			multiple_selection = False,
			editable  = True,
			show_root = True
		)

	def getHeaderInfo( self ):
		return [ ('Name', 140), ('Type', 50) ]

	def getRootNode( self ):
		config = self.module.getEditingConfig()
		return config and config._root or None

	def getNodeParent( self, node ):
		if node == self.getRootNode(): return None
		return node.parent

	def getNodeChildren( self, node ):		
		result = []
		for node in list(node.children.values()):
			if not node[ '_hidden' ]: result.append( node )
		return result
		
	def updateItemContent( self, item, node, **option ):
		if node == self.getRootNode():
			item.setText( 0, node['name'] )
			item.setIcon( 0, getIcon('effect/group') )
		else:
			typeName = node.getTypeName( node )
			item.setText( 0, node['name'] )
			item.setText( 1, typeName )
			item.setIcon( 0, getIcon( 'effect/' + typeName.lower(), 'effect/unknown' ) )

	def getItemFlags( self, node ):
		if node == None or node == self.getRootNode():
			return dict( 
				draggable = False,
				droppable = True,
				editable  = False
			)
		else:
			return {}

	def onClicked(self, item, col):
		self.module.selectEditTarget( item.node )

	def onItemSelectionChanged(self):
		self.module.selectEditTarget( self.getFirstSelection() )

	def onItemChanged( self, item, col ):
		node = item.node
		self.module.renameNode( node, item.text(0) )

	def onDeletePressed( self ):
		self.module.removeNode()
		
##----------------------------------------------------------------##
EffectEditor().register()
