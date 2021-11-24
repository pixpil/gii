from gii import app
from mock import _MOCK

if app.getModule('asset_browser'): 

	from gii.AssetEditor import AssetPreviewer
	from qtpy import QtWidgets, QtGui, QtCore
	from gii.qt.controls.PropertyEditor  import PropertyEditor

	##----------------------------------------------------------------##		
	class SerializableAssetPreviewer(AssetPreviewer):
		def createWidget(self,container):
			self.scroll = scroll = QtWidgets.QScrollArea( container )
			scroll.verticalScrollBar().setStyleSheet('width:4px')
			scroll.setWidgetResizable( True )
			self.editor = PropertyEditor( scroll )
			self.editor.setReadonly()
			scroll.setWidget( self.editor )
			return self.scroll

		def accept(self, assetNode):
			return assetNode.getManager().getMetaType() in [ 'serializable' ]

		def onStart(self, selection):
			data = _MOCK.loadAsset( selection.getPath() )
			if data:
				asset, luaAssetNode = data
				self.editor.setTarget( asset )
			else:
				self.editor.setTarget( None )

		def onStop(self):
			self.editor.setTarget( None )

	SerializableAssetPreviewer().register();
