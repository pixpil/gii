from gii.AssetEditor         import AssetPreviewer
from mock import MOCKEditCanvas

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

class ProtoPreviewer( AssetPreviewer ):
	def createWidget(self, container):
		self.canvas = MOCKEditCanvas( container )
		self.canvas.loadScript( _getModulePath('ProtoPreviewer.lua') )
		return self.canvas

	def accept(self, assetNode):
		return assetNode.getType() in [ 
			'proto',
			'prefab',
			]

	def onStart(self, assetNode):
		self.canvas.safeCallMethod( 'preview', 'setTaretProto', assetNode.getPath() )
		
	def onStop(self):
		self.canvas.safeCallMethod( 'preview', 'setTaretProto', None )

# ProtoPreviewer().register()
