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

from mock import MOCKEditCanvas
from gii.moai import _LuaObject

from qtpy  import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt

from mock import getMockClassName
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
class Box(object):
	def __init__(self):
		self.items = []


##----------------------------------------------------------------##

class ShaderEditor( SceneEditorModule ):
	"""docstring for ShaderEditor"""
	def __init__(self):
		super(ShaderEditor, self).__init__()
		self.editingAsset  = None		
		self.editingConfig = None

		self.emitters = Box()
		self.emitters.items=[]
		
		self.states = Box()
		self.states.items=[]
		self.scriptModifyFlag = 0
	
	def getName(self):
		return 'shader_editor'

	def getDependency(self):
		return [ 'qt', 'mock' ]

	def onLoad(self):
		self.windowTitle = 'Shader Editor'
		self.container = self.requestDocumentWindow('ShaderEditor',
				title       = 'Shader Editor',
				size        = (500,300),
				minSize     = (500,300),
				# allowDock = False
			)

		self.tool = self.addToolBar( 'shader_editor', self.container.addToolBar() )
		self.addTool( 'shader_editor/save',    label = 'Save', icon = 'save' )
		self.addTool( 'shader_editor/refresh', label = 'Refresh', icon = 'refresh' )

		
		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('ShaderEditor.ui')
		)
		self.canvas = addWidgetWithLayout(
			MOCKEditCanvas( window.containerPreview )
		)
		self.tree = addWidgetWithLayout(
			ShaderUniformTreeWidget( 
					window.containerTree, 
					multiple_selection = False,
					editable           = True
				)
			)
		self.tree.module = self

		# self.propEditor = addWidgetWithLayout(
		# 	PropertyEditor( window.containerProperty )
		# 	)

		# window.textScriptRender.textChanged.connect( self.onScriptModified )
		# window.textScriptInit.textChanged.connect( self.onScriptModified )

		# self.propEditor.propertyChanged.connect( self.onPropertyChanged )

	def onStart( self ):
		self.canvas.loadScript( _getModulePath('ShaderEditor.lua') )
		# self.canvas.setDelegateEnv( 'editor', self )

	def onSetFocus( self ):
		self.container.show()
		self.container.raise_()
		self.container.activateWindow()
		self.container.setFocus()

	def openAsset( self, node ):
		self.setFocus()
		if self.editingAsset == node: return
		self.checkScriptTimer = self.container.startTimer( 3, self.checkScript )
		
		self.container.setDocumentName( node.getNodePath() )
		self.editingAsset  = node

		self.canvas.makeCurrentCanvas()
		self.editingConfig = self.canvas.safeCallMethod( 'preview', 'open', node.getPath() )
		
		self.tree.rebuild()
		self.tree.setAllExpanded( True )

	def closeAsset( self ):
		self.checkScriptTimer.stop()

	def changeSelection( self, selection ):
		self.propEditor.setTarget( selection )
		self.canvas.safeCallMethod( 'preview', 'changeSelection', selection )

	def refreshScriptTitle( self ):
		state = self.editingState
		self.window.labelStateName.setText( 'current editing state script: <%s>' % state.name )
		# if not state: return
		# tabParent = self.window.panelScript
		# idx = tabParent.indexOf( self.window.tabInit )
		# tabParent.setTabText( idx, 'Init Script <%s>' % state.name )
		# idx = tabParent.indexOf( self.window.tabRender )
		# tabParent.setTabText( idx, 'Render Script <%s>' % state.name )

	def onScriptModified( self ):
		self.scriptModifyFlag = 1

	def checkScript( self ):
		if self.scriptModifyFlag == 0:
			self.canvas.safeCallMethod(
				'preview',
				'updateScript', 
				self.window.textScriptInit.toPlainText(),
				self.window.textScriptRender.toPlainText()
			 )
		if self.scriptModifyFlag >= 0:
			self.scriptModifyFlag -= 1

	# def onPropertyChanged( self, obj, field, value ):
	# 	if field == 'name':
	# 		self.tree.refreshNodeContent( obj )
	# 		if obj == self.editingState:
	# 			self.refreshScriptTitle()
	# 	else:
	# 		self.canvas.safeCallMethod( 'preview', 'update', obj, field, value )

	def onTool( self, tool ):
		name = tool.name
		if name == 'refresh':
			if self.editingAsset:
				self.canvas.safeCallMethod( 'preview', 'refresh' )
		elif name == 'add_uniform':
			pass
		elif name == 'remove_uniform':
			pass
		elif name == 'save':
			self.saveAsset()

##----------------------------------------------------------------##
class ShaderUniformTreeWidget( GenericTreeWidget ):
	def getHeaderInfo( self ):
		return [ ('Name', 80), ('Type',-1) ]

	def getRootNode( self ):
		return self.module

	def saveTreeStates( self ):
		pass

	def loadTreeStates( self ):
		pass

	def getNodeParent( self, node ): # reimplemnt for target node	
		return None

	def getNodeChildren( self, node ):
		return []

	def updateItemContent( self, item, node, **option ):
		return
		
	def onItemSelectionChanged(self):
		pass

	def onItemChanged( self, item, col ):
		pass


##----------------------------------------------------------------##
ShaderEditor().register()
##----------------------------------------------------------------##
