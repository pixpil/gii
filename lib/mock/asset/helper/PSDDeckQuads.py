from psd_tools import PSDImage, Group, Layer
from .psd_tools_helper import extract_leaf_layers

from PIL import Image

from .PSDDeckPackProject import *
from .NormalMapHelper import makeNormalMap
from .MetaTag import parseMetaTag

def clamp( x, a, b ):
	return max( a, min( b, x ) )

def getArray( l, idx, default = None ):
	if idx < 0: return default
	if idx >= len( l ): return default
	v = l[ idx ]
	if v is None: return default
	return v

def getArrayI( l, idx, default = None ):
	return int( getArray( l, idx, default ) )

def getArrayF( l, idx, default = None ):
	return float( getArray( l, idx, default ) )

def alphaPasted( im, mark, position ):
	if im.mode != 'RGBA':
		im = im.convert('RGBA')
	# create a transparent layer the size of the image and draw the
	# watermark in that layer.
	layer = Image.new('RGBA', im.size, (0,0,0,0))
	layer.paste(mark, position)
	# composite the watermark with the layer
	return Image.composite( layer, im, layer )


##----------------------------------------------------------------##
class QuadsDeckPart( DeckPart ):
	def getData( self ):
		src = self.src
		node = self.getAtlasNode()
		if not node:
			logging.warning( 'no atlas node for deck', self.src.name )
			return None
		w, h = self.getSize()
		align = src.align
		
		if   align == 'TL':
			x0, y0, x1, y1= 0,-h, w,0
		elif align == 'TR':
			x0, y0, x1, y1= -w,-h, 0,0
		elif align == 'TC':
			x0, y0, x1, y1= -w/2,-h, w/2,0

		elif align == 'CL' or align == 'L' :
			x0, y0, x1, y1= 0,-h/2, w, h/2
		elif align == 'CR' or align == 'R' :
			x0, y0, x1, y1= -w,-h/2, 0,h/2
		elif align == 'CC' or align == 'C' :
			x0, y0, x1, y1= -w/2,-h/2, w/2,h/2

		elif align == 'BL':
			x0, y0, x1, y1= 0,0, w, h
		elif align == 'BR':
			x0, y0, x1, y1= -w,0, 0,h
		elif align == 'BC':
			x0, y0, x1, y1= -w/2,0, w/2,h

		else: #if align == 'C':
			if not align in ['C', 'CC']:
				logging.warning( 'unknown deck alignment:' + align )
			x0, y0, x1, y1= -w/2, -h/2, w/2, h/2

		return {
			'rect' : ( x0,y0,x1,y1 ),
			'uv'    : node.getUVRect(),
			'index' : self.index,
		}

##----------------------------------------------------------------##
class QuadsDeckItem(DeckItem):
	def __init__( self, name, partLayers ):
		super( QuadsDeckItem, self ).__init__()
		self.name = name
		self.parts = []
		self.partLayers = partLayers
		self.align = 'C'

	def setAlign( self, align ):
		self.align = align

	def onBuild( self, project ):
		i = 0
		for layer in self.partLayers:
			i += 1
			part = self.addPart( layer )
			part.index = i
			
	def postBuild( self, project ):
		pass

	def createPart( self, layer ):
		return QuadsDeckPart( self, layer )

	def getData( self ):
		quads = []
		for part in self.parts:
			quads.append( part.getData() )
		return {
			'name' : self.name,
			'quads': quads,
			'type' : 'deck2d.quads'
		}


##----------------------------------------------------------------##
class QuadsDeckProcessor( DeckProcessor ):
	def onLoadImage( self, psdImage ):
		pass

	def acceptLayer( self, psdLayer, metaInfo, fallback ):
		tags = metaInfo[ 'tags' ]
		if fallback:
			return True
		else:
			return 'QUADS' in tags

	def processLayer( self, psdLayer, metaInfo, namespace ):
		project = self.project
		tags = metaInfo[ 'tags' ]
		partLayers = []
		if isinstance( psdLayer, Group ):
			partLayers = extract_leaf_layers( psdLayer )
		else:
			partLayers = [ psdLayer ]
		name = metaInfo[ 'name' ]
		fullname = namespace and ( namespace + '.' + name ) or name
		deck = QuadsDeckItem( fullname, partLayers )
		tags = metaInfo.get( 'tags', {}) 
		if 'ALIGN' in tags:
			args = tags[ 'ALIGN' ]
			deck.setAlign( args[0] )
		project.addDeckItem( deck )

##----------------------------------------------------------------##
registerDeckProcessor( 'quads', QuadsDeckProcessor )


##----------------------------------------------------------------##
if __name__ == '__main__':
	from . import PSDDeckPackTest
	