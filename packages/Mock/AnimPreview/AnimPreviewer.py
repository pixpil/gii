from gii.core                 import *
from mock  import MOCKEditCanvas
from gii.AssetEditor          import AssetPreviewer
from gii.qt.helpers           import addWidgetWithLayout
from gii.qt.IconCache         import getIcon

from gii.qt.controls.GenericListWidget import GenericListWidget, GenericListFilter

from qtpy import uic
from qtpy import QtWidgets, QtGui

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


##----------------------------------------------------------------##
class AnimPreviewer(AssetPreviewer):
	def createWidget(self, container):
		self.container=uic.loadUi( _getModulePath('AnimPreview.ui') )
		self.canvas=addWidgetWithLayout(
			MOCKEditCanvas(container),
			self.container.canvasContainer
		)
		self.filterAnim = addWidgetWithLayout( GenericListFilter( self.container.containerList ) )
		self.listAnim = addWidgetWithLayout( AnimClipListWidget( self.container.containerList ) )
		self.listAnim.setSortingEnabled(True)

		self.filterAnim.setTargetList( self.listAnim )
		self.listAnim.parentModule = self

		self.container.buttonPlay.setIcon( getIcon('play') )
		# self.container.slider
		self.canvas.loadScript( _getModulePath('AnimPreview.lua') )
		return self.container

	def accept(self, assetNode):
		return assetNode.getType() in [ 'spine', 'msprite' ]

	def getClipNames( self ):
		return self.clipNames

	def setActiveClip( self, clip ):
		self.canvas.safeCallMethod( 'preview', 'setAnimClip', clip )

	def onStart(self, assetNode):
		atype = assetNode.getType()
		self.listAnim.clear()		
		self.canvas.makeCurrentCanvas()
		luaClipNames = self.canvas.safeCallMethod( 'preview', 'showAnimSprite', assetNode.getPath() )
		self.clipNames = luaClipNames and [ name for name in list(luaClipNames.values()) ] or []
		self.listAnim.rebuild()
		self.filterAnim.clearFilter()
		if self.clipNames:
			self.listAnim.selectNode( self.clipNames[ 0 ] )
		self.canvas.startUpdateTimer( 60 )

	def onPause( self, paused ):
		if paused:
			self.canvas.stopUpdateTimer()
		else:
			self.canvas.startUpdateTimer( 60 )
		
	def onStop(self):
		self.canvas.stopUpdateTimer()


##----------------------------------------------------------------##
class AnimClipListWidget( GenericListWidget ):
	def getNodes( self ):
		return self.parentModule.getClipNames()

	def updateItemContent( self, item, node, **options ):
		item.setText( node )

	def onItemSelectionChanged(self):
		for clip in self.getSelection():
			self.parentModule.setActiveClip( clip )
			break

AnimPreviewer().register()

