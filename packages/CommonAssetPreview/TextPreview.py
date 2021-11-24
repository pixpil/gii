from gii.core import *
from gii.AssetEditor import AssetPreviewer
from qtpy import QtWidgets, QtGui, QtCore

class TextPreviewer( AssetPreviewer ):
	def createWidget(self, container):
		self.textBrowser = QtWidgets.QTextBrowser(container)
		self.textBrowser.setLineWrapMode(0)
		self.textBrowser.setTabStopWidth(20)
		return self.textBrowser

	def accept(self, assetNode):
		return assetNode.getMetaType() in [ 'text', 'script' ]
		# return assetNode.isType( 'lua', 'script', 'text' )

	def onStart(self, assetNode):
		try:
			fp=open(assetNode.getAbsFilePath(),'r')
			text=fp.read().decode('utf8')
			self.textBrowser.setText(text)
			fp.close()
		except Exception as e:
			return False

	def onStop(self):
		pass

@slot( 'module.loaded' )
def registerTextPreviewer():
	TextPreviewer().register()
