from gii.core                 import *
from mock  import MOCKEditCanvas
from gii.AssetEditor          import AssetPreviewer
from gii.qt.helpers           import addWidgetWithLayout

from qtpy import uic
from qtpy import QtWidgets, QtGui

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

class FontPreviewer(AssetPreviewer):
	def createWidget(self, container):
		self.container = uic.loadUi( _getModulePath('FontPreview.ui') )

		self.canvas = addWidgetWithLayout(
			MOCKEditCanvas(container),
			self.container.canvasContainer
		)
		self.canvas.loadScript( _getModulePath('FontPreview.lua') )

		self.container.textPreview.textChanged.connect( self.onTextChanged )
		self.container.spinFontSize.valueChanged.connect( self.onSizeChanged )

		return self.container

	def accept(self, assetNode):
		return assetNode.getType() in ('font_ttf','font_bmfont','font_bdf')

	def onStart(self, assetNode):
		atype=assetNode.getType()
		self.canvas.safeCallMethod( 'preview', 'setFont', assetNode.getPath().encode( 'utf-8' ) )
		preview = self.canvas.getDelegateEnv( 'preview' )

		self.container.spinFontSize.setValue( preview.currentFontSize )
		self.container.textPreview.setPlainText( preview.currentText )

	def onStop(self):
		self.canvas.safeCallMethod( 'preview', 'setFont',None)

	def onTextChanged(self):
		text = self.container.textPreview.toPlainText()
		self.canvas.safeCallMethod( 'preview', 'setText', text )

	def onSizeChanged(self, size):
		self.canvas.safeCallMethod( 'preview', 'setFontSize', size )
		

FontPreviewer().register()
