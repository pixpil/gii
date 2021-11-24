# -*- coding: utf-8 -*-

import subprocess
import os.path
import shutil
import time
import json

from gii.core         import *
from gii.qt           import *
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor
from gii.qt.dialogs   import requestString, alertMessage, requestColor

from gii.SceneEditor  import SceneEditorModule

from gii.moai.MOAIRuntime import MOAILuaDelegate

from util.IDPool  import IDPool

from qtpy  import QtCore, QtWidgets, QtGui, QtOpenGL
from qtpy.QtCore import Qt

from .SQScriptEditorWidget import SQScriptEditorWidget

from mock import _MOCK, isMockInstance

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
class SQScriptEditor( SceneEditorModule ):
	"""docstring for SQScriptEditor"""

	name = 'sq_script_editor'
	dependency = [ 'mock', 'qt' ]

	def __init__(self):
		self.instances      = []
	
	def onLoad(self):		
		self.idPool = IDPool()
		
	def onStart( self ):
		# self.delegate = MOAILuaDelegate( self )
		# self.delegate.load( _getModulePath( 'SQScriptEditor.lua' ) )
		pass

	def openAsset( self, target ):
		instance = self.findInstances( target )
		if not instance:
			instance = self.createInstance( target )
		else:
			instance.refresh()

	def createInstance( self, target ):
		#todo: pool
		id = self.idPool.request()
		title = target.getNodePath()
		container = self.requestDocumentWindow( 'SQScriptEditor-%d'%id,
				title   = title,
				minSize = (200,100)
		)
		instance = SQScriptEditorInstance(id)
		instance.parentModule = self
		instance.createWidget( container )
		instance.setTarget( target )
		self.instances.append( instance )
		container.show()
		return instance

	def findInstances(self, targetNode):
		for ins in self.instances:
			if ins.targetNode == targetNode:
				return ins
		return None

	def removeInstance( self, instance ):
		self.instances.remove( instance )

	def refresh( self, targetNode = None, context = None ):
		for ins in self.instances:
			if not targetNode or ins.hasTarget( targetNode ):
				ins.refresh()

##----------------------------------------------------------------##
class SQScriptEditorInstance( object ):
	def __init__( self, id ):
		self.id = id
		self.targetScript = None
		self.targetNode = None

	def createWidget( self, container ):
		self.container = container
		class TestRoutineNode(object):
			def __init__( self, parent ):
				self.parent = parent
				self.children = []
				self.mark = None
				self.index = 0

			def getParent( self ):
				return self.parent

			def getChildren( self ):
				return self.children

			def getTag( self ):
				testTag = [
					'SAY',#'<font color="#900">SAY</font>',
					'ANIM',#'<font color="#090">ANIM</font>',
					'SPAWN'#'<font color="#90a">SPAWN</font>'
				]
				return testTag[ self.index % len( testTag ) ]

			def getDesc( self ):
				testDesc = [
					"The <b>Dock Widgets</b> example demonstrates how to use ",
					"Qt's dock widgets. You can enter your own text, click a ",
					"customer to add a customer name and address, and click ",
					"standard paragraphs to add them.",
					"THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS",
					"* Neither the name of Nokia Corporation and its Subsidiary(-ies) nor"
				]

				return testDesc[ self.index % 6 ]

			def getMark( self ):
				return self.mark

			def getIndex( self ):
				return self.index

			def getMarkText( self ):
				if self.mark: return '<%s>' % self.mark
				return '%d' % self.index

			def addChild( self, node ):
				self.children.append( node )
				node.parent = self
				node.index = len( self.children )
				return node

		class TestRoutine(object):
			def __init__( self ):
				self.rootNode = TestRoutineNode( None )

			def getRootNode( self ):
				return self.rootNode

		testRoutine = TestRoutine()
		root = testRoutine.rootNode
		for k in range( 20 ):
			node = root.addChild(
				TestRoutineNode( None )
			)
			if k == 5:
				for j in range( 5 ):
					node.addChild(
						TestRoutineNode( None )
					)
		self.window = container.addWidget( SQScriptEditorWidget( container ) )
		self.window.owner = self

	def setTarget( self, node ):
		self.targetNode = node
		data = _MOCK.loadAsset( node.getPath() )
		if data:
			( script, luaAssetNode ) = data
			self.targetScript = script
			self.window.rebuild()
		else:
			self.targetScript = None
			self.window.rebuild()

	def getTargetScript( self ):
		return self.targetScript

	def saveAsset( self ):
		if self.targetScript:
			path = self.targetNode.getAbsFilePath()
			_MOCK.serializeToFile( self.targetScript, path )
		return True

	def locateAsset( self ):
		if self.targetNode:
			browser = app.getModule( 'asset_browser' )
			if browser:
				browser.locateAsset( self.targetNode )

	def refersh( self ):
		self.window.rebuild()


##----------------------------------------------------------------##
@slot( 'module.loaded' )
def registerCommonSQNodeEditors():
	pass
