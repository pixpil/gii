from gii.AssetEditor         import AssetPreviewer
from mock import MOCKEditCanvas

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

class TexturePreviewer(AssetPreviewer):
	def createWidget(self, container):
		self.canvas = MOCKEditCanvas( container )
		self.canvas.loadScript( _getModulePath('TexturePreview2.lua') )
		return self.canvas

	def accept(self, assetNode):
		return assetNode.getType() in [ 'texture', 'render_target' ]

	def onStart(self, assetNode):
		self.canvas.safeCall( 'show', assetNode.getPath() )		
		
	def onStop(self):
		self.canvas.safeCall('show',None)

TexturePreviewer().register()
