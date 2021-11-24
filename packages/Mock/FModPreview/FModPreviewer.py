from gii.core                 import *
from mock  import MOCKEditCanvas
from gii.AssetEditor          import AssetPreviewer
from gii.qt.helpers           import addWidgetWithLayout

from qtpy import uic
from qtpy import QtWidgets, QtGui

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

class FModPreviewer(AssetPreviewer):
	def createWidget(self, container):
		self.container = uic.loadUi( _getModulePath('FModPreview.ui') )

		self.canvas = addWidgetWithLayout(
			MOCKEditCanvas(container),
			self.container.canvasContainer
		)
		self.canvas.loadScript( _getModulePath('FModPreview.lua') )

		return self.container

	def accept(self, assetNode):
		return assetNode.getType() in ('fmod_event','fs_event')

	def onStart(self, assetNode):
		atype=assetNode.getType()
		self.canvas.safeCallMethod( 'preview', 'setEvent', assetNode.getPath() )

	def onStop(self):
		self.canvas.safeCallMethod( 'preview', 'setEvent', None )		

FModPreviewer().register()
