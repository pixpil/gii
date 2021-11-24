from gii.AssetEditor         import AssetPreviewer
from mock import MOCKEditCanvas

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

class Deck2DPreviewer(AssetPreviewer):
	def createWidget(self, container):
		self.canvas = MOCKEditCanvas( container )
		self.canvas.loadScript( _getModulePath('Deck2DPreview.lua') )
		return self.canvas

	def accept(self, assetNode):
		return assetNode.getType() in [ 
			'deck2d.quad',
			'deck2d.stretchpatch',
			'deck2d.quad_array',
			'deck2d.tileset',
			'deck2d.polygon',
			'deck2d.mquad',
			'deck2d.quads',
			]

	def onStart(self, assetNode):
		self.canvas.safeCallMethod( 'preview', 'show', assetNode.getPath() )
		
	def onStop(self):
		self.canvas.safeCallMethod( 'preview', 'show', None )

Deck2DPreviewer().register()
