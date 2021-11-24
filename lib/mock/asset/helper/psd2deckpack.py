from os.path import basename, splitext
import math
import io
from PIL import Image
import copy
import logging
import json
import re

from psd_tools import PSDImage, Group, Layer
from .atlas2 import AtlasGenerator, Img

from .NormalMapHelper import makeNormalMap
from .MetaTag import parseMetaTag

def clamp( x, a, b ):
	return max( a, min( b, x ) )

##----------------------------------------------------------------##
def saveJSON( data, path, **option ):
	outputString = json.dumps( data , 
			indent    = option.get( 'indent' ,2 ),
			sort_keys = option.get( 'sort_keys', True ),
			ensure_ascii=True
		).encode('utf-8')
	fp = open( path, 'w' )
	fp.write( outputString )
	fp.close()
	return True

def trySaveJSON( data, path, dataName = None, **option ):
	try:
		saveJSON( data, path, **option )
		return True
	except Exception as e:
		logging.warn( 'failed to save %s: %s' % ( dataName or 'JSON', path ) )
		logging.exception( e )
		return False

##----------------------------------------------------------------##
class DeckPartImg(Img): #	
	def getImage(self, imgSet = None ):
		return self.src.getImage( imgSet )

##----------------------------------------------------------------##
class DeckPart( object ):
	def __init__( self, project, psdLayer ):
		self._project = project
		self._layer = psdLayer
		layerName = psdLayer.name.encode( 'utf-8' )
		self.rawName = layerName
		self.name    = layerName
		self.img = None
		x1,y1,x2,y2 = psdLayer.bbox
		self.w = x2-x1
		self.h = y2-y1
		self.x = x1
		self.y = y1
		self.deckRect = ( 0,0,1,1 )
		self.deckOffset = ( 0,0 )
		self.rawRect  = ( x1,y1,x2,y2 )
		self.imgInfo = None
		self.rawIndex = psdLayer._index
		self.options = {}

	def getSize( self ):
		return (self.w, self.h)

	def getOffset( self ):
		return self.x, self.y

	def getImageSourceData( self ):
		return self._layer

	def getRawIndex( self ):
		return self.rawIndex

	def getRawRect( self ):
		return self.rawRect

	def getDeckRect( self ):
		return self.deckRect

	def getDeckSize( self ):
		x, y, x1, y1 = self.deckRect
		return x1-x, y1-y

	def getDeckOffset( self ):
		return self.deckOffset

	def getAtlasImgInfo( self ):
		return self.imgInfo

	def getAtlasNode( self ):
		return self.imgInfo.node

##----------------------------------------------------------------##
class DeckFactory():
	def build( self, project, psdLayerGroup, name, profix, meta ):
		return None

##----------------------------------------------------------------##
class DeckItem(object):
	def build( self, projectContext ):
		pass

	def postBuild( self, projectContext ):
		pass

	def getAtlasImgInfos( self ):
		return []		

	def save( self ):
		return None


##----------------------------------------------------------------##
class DeckPartMQuad( DeckPart ):
	def __init__( self, project, psdLayer ):
		super( DeckPartMQuad, self ).__init__( project, psdLayer )
		self.meshes = []
		self.globalMeshes = []		
		#parameter
		layerName = self.rawName
		metaInfo = parseMetaTag( layerName )
		print( metaInfo )
		self.options[ 'floor' ] = (':FLOOR' in layerName)
		self.options[ 'wall'  ] = (':WALL' in layerName)
		self.options[ 'fold'  ] = ('')

	def getImage( self, imgSet ):
		if imgSet == 'normal':
			return self.getNormalMap()
		else:
			return self.getTextureMap()
	
	def getTextureMap( self ):
		if self.img: return self.img
		self.img = self._layer.as_PIL()
		return self.img

	def getNormalMap( self ):
		if self.imgNormal:
			return self.imgNormal
		else:
			return self.getTextureMap()

	def build( self, projContext ):
		foldMode = 'auto'
		if self.options['floor']:
			foldMode = 'floor'
		elif self.options['wall']:
			foldMode = 'wall'

		( w, h ) = self.getSize()
		( x, y ) = self.getOffset()

		localGuideTopFace = h
		if foldMode == 'auto':
			guideTopFace = projContext.get( 'guide-top-face', 0 )
			localGuideTopFace = clamp( guideTopFace - y, 0, h )
		elif foldMode == 'wall':
			localGuideTopFace = 0
		elif foldMode == 'floor':
			localGuideTopFace = h

		img = DeckPartImg ( '', w, h, (0, 0, w, h) )	
		img.node = None
		img.src = self
		self.imgInfo = img
		#build normal
		tex = self.getTextureMap()
		normalOption = {
			'guide-top-face' : localGuideTopFace
		}
		self.imgNormal = makeNormalMap( tex, normalOption )
		self.guideTopFace = localGuideTopFace

		#build mesh
		#format: x,y,z/ u,v /color
		if localGuideTopFace < h:
			x0 = 0
			y0 = 0
			z0 = 0
			x1 = w
			y1 = h - localGuideTopFace
			z1 = 0
			u0 = float(x0) / w
			v0 = float(y0) / h
			u1 = float(x1) / w
			v1 = float(y1) / h
			quadFront = {
				'verts' : [
					[ x0,y0,z0 ], 
					[ x1,y0,z0 ], 
					[ x1,y1,z1 ], 
					[ x0,y1,z1 ]
				],
				'uv' : [
					[ u0,v0 ],
					[ u1,v0 ],
					[ u1,v1 ],
					[ u0,v1 ],
				]
			}
			self.meshes.append( quadFront )

		if localGuideTopFace > 0:
			x0 = 0
			y0 = h - localGuideTopFace
			z0 = 0
			x1 = w
			y1 = h
			z1 = -( y1 - y0 )
			u0 = float(x0) / w
			v0 = float(y0) / h
			u1 = float(x1) / w
			v1 = float(y1) / h
			quadTop = {
				'verts' : [
					[ x0,y0,z0 ], 
					[ x1,y0,z0 ], 
					[ x1,y1,z1 ], 
					[ x0,y1,z1 ]
				],
				'uv' : [
					[ u0,v0 ],
					[ u1,v0 ],
					[ u1,v1 ],
					[ u0,v1 ],
				]
			}
			self.meshes.append( quadTop )

	def getBottom( self ):
		return self.y + self.h

	def getLeft( self ):
		return self.x

	def updateGlobalMeshOffset( self, globalLeft, globalBottom ):
		offy = globalBottom - self.getBottom()
		offx = globalLeft   - self.getLeft()
		self.globalMeshes = []
		for mesh in self.meshes:
			gmesh = copy.deepcopy( mesh )
			for vert in gmesh['verts']:
				vert[ 0 ] -= offx
				vert[ 1 ] += offy
			self.globalMeshes.append( gmesh )

	def buildAtlasUV( self ):
		node = self.getAtlasNode()
		if not node:
			print(( 'no atlas node for deck', self.name ))
		uvrect = node.getUVRect()
		u0, v0, u1 ,v1 = uvrect
		du = u1 - u0
		dv = v1 - v0
		for mesh in self.globalMeshes:
			for uv in mesh['uv']:
				uv[0] = uv[0] * du + u0
				uv[1] = uv[1] * dv + v0

	def getGlobalMeshes( self ):
		return self.globalMeshes

##----------------------------------------------------------------##
class DeckItemMQuad(DeckItem):
	def __init__( self ):
		self.parts = []

	def addPart( self, part ):
		self.parts.append( part )

	def save( self ):
		meshes = []
		for part in self.parts:
			meshes += part.getGlobalMeshes()
		return {
			'name'  : self.name,
			'meshes': meshes,
			'type'  : 'deck2d.mquad'
		}

	def build( self, projContext = None ):
		meshDatas = []
		bottom = 0
		left   = 0xffffffff
		for part in self.parts:
			part.build( projContext )
			bottom = max( bottom, part.getBottom() )
			left   = min( left, part.getLeft() )
		#move mesh
		for part in self.parts:
			part.updateGlobalMeshOffset( left, bottom )

	def postBuild( self, projectContext = None ):
		for part in self.parts:
			part.buildAtlasUV()

	def getAtlasImgInfos( self ):
		infos = []
		for part in self.parts:
			infos.append( part.getAtlasImgInfo() )
		return infos

##----------------------------------------------------------------##
class DeckFactoryMQuad( DeckFactory ):
	def build( self, project, psdLayerGroup, name, profix, meta ):
		if not profix.startswith( 'MQUAD' ): return
		group = psdLayerGroup
		deck = DeckItemMQuad()
		deck.rawName = name
		deck.name    = name
		def collectLayer( l ):
			for layer in l.layers:
				layerName = layer.name.encode( 'utf-8' )
				if layerName.startswith( '//' ): continue
				if layerName.startswith( '@' ):	continue
				if isinstance( layer, Group ):
					collectLayer( layer )
				else:
					part = DeckPartMQuad( project, layer )					
					deck.addPart( part )
		collectLayer( group )
		return deck

##----------------------------------------------------------------##
class TileModule( DeckPart ):
	def __init__( self, project, psdLayer ):
		super( TileModule, self ).__init__( project, psdLayer )
		self.imgNormal = None
		self.alt = 0
		self.deckOffset = ( 0,0,0 )
		self.meshes = []

	def getImage( self, imageSet ):
		if imageSet == 'normal':
			return self.imgNormal
		else:
			if self.img: return self.img
			self.img = self._layer.as_PIL()
			return self.img

	def getImage( self, imgSet ):
		if imgSet == 'normal':
			return self.getNormalMap()
		else:
			return self.getTextureMap()
	
	def getTextureMap( self ):
		if self.img: return self.img
		self.img = self._layer.as_PIL()
		return self.img

	def getNormalMap( self ):
		if self.imgNormal:
			return self.imgNormal
		else:
			return self.getTextureMap()

	def build( self, projContext ):
		( dx0, dy0, dx1,dy1 ) = self.getDeckRect()
		# w = dx1 - dx0
		# h = dy1 - dy0
		w = self.w
		h = self.h
		
		ox, oy, oz = self.getDeckOffset()
		localGuideTopFace = self.h - ( self.alt - oy )
		oy = oy + oz
		oz = - oz
		# print self.fullName, w, h, '|', ox, oy, oz, '|', localGuideTopFace
		#build mesh
		#format: x,y,z/ u,v /color
		if localGuideTopFace < h:
			x0 = 0
			y0 = 0
			z0 = 0
			x1 = w
			y1 = h - localGuideTopFace
			z1 = 0
			u0 = float(x0) / w
			v0 = float(y0) / h
			u1 = float(x1) / w
			v1 = float(y1) / h
			quadFront = {
				'verts' : [
					[ x0 + ox, y0 +oy, z0 + oz ], 
					[ x1 + ox, y0 +oy, z0 + oz ], 
					[ x1 + ox, y1 +oy, z1 + oz ], 
					[ x0 + ox, y1 +oy, z1 + oz ]
				],
				'uv' : [
					[ u0,v0 ],
					[ u1,v0 ],
					[ u1,v1 ],
					[ u0,v1 ],
				]
			}
			self.meshes.append( quadFront )

		if localGuideTopFace > 0:
			x0 = 0
			y0 = h - localGuideTopFace
			z0 = 0
			x1 = w
			y1 = h
			z1 = -( y1 - y0 )
			u0 = float(x0) / w
			v0 = float(y0) / h
			u1 = float(x1) / w
			v1 = float(y1) / h
			quadTop = {
				'verts' : [
					[ x0 + ox, y0 + oy, z0 + oz ], 
					[ x1 + ox, y0 + oy, z0 + oz ], 
					[ x1 + ox, y1 + oy, z1 + oz ], 
					[ x0 + ox, y1 + oy, z1 + oz ]
				],
				'uv' : [
					[ u0,v0 ],
					[ u1,v0 ],
					[ u1,v1 ],
					[ u0,v1 ],
				]
			}
			self.meshes.append( quadTop )
		normalOption = {
			'guide-top-face' : localGuideTopFace
		}
		self.imgNormal = makeNormalMap( self.getTextureMap(), normalOption )

	def postBuild( self, projContext ):
		self.buildAtlasUV()

	def buildAtlasUV( self ):
		node = self.getAtlasNode()
		if not node:
			print(( 'no atlas node for deck', self.name ))
		uvrect = node.getUVRect()
		u0, v0, u1 ,v1 = uvrect
		du = u1 - u0
		dv = v1 - v0
		for mesh in self.meshes:
			for uv in mesh['uv']:
				uv[0] = uv[0] * du + u0
				uv[1] = uv[1] * dv + v0

	def getMeshes( self ):
		return self.meshes

##----------------------------------------------------------------##
class TileGroup(object):
	def __init__( self ):
		self.tiles = []
		self.name  = None
		self.rawName = None
		self.tileType   = 'T'
		self.tileWidth  = 0
		self.tileHeight = 0
		self.tileAlt  = 0
		self.theme = None

	def addTile( self, tile ):
		self.tiles.append( tile )

	def getDim( self ):
		return self.theme.tileWidth, self.theme.tileHeight, self.tileAlt

	def build( self, projContext ):
		#pass name
		mo = re.search( '([\w_-]+)\s*:\s*(\w*)\(\s*(\d+)\s*\)', self.rawName )
		if mo:
			self.name = mo.group( 1 )
			self.tileType = mo.group( 2 ) or 'C'
			self.tileAlt  = int( mo.group( 3 ) )
		else:
			raise Exception( 'invalid tileset name format: %s' % self.rawName )
		self.fullname = self.theme.name + ':' + self.name
		if self.tileType == 'C':
			self.buildCommonTiles( projContext )
		elif self.tileType == 'T':
			self.buildTerrainTiles( projContext )

	def postBuild( self, projContext ):
		for tile in self.tiles:
			tile.postBuild( projContext )

	def buildCommonTiles( self, projContext ):
		tw, td, alt = self.getDim()
		for tile in self.tiles:
			k = tile.name
			w, h = tile.w, tile.h
			ox, oy = 0, alt
			tile.itemName = '%s.%s' % ( self.name, k )
			tile.fullName = '%s.%s' % ( self.fullname, k )
			tile.deckRect = ( ox, oy, ox + w, oy + h )
			tile.alt = alt
			tile.deckOffset = ( 0,alt,0 )
			tile.build( projContext )

	def buildTerrainTiles( self, projContext ):
		tw, th, alt = self.getDim()
		for tile in self.tiles:
			tile.alt = alt
			k = tile.name
			w, h = tile.w, tile.h
			ox, oy = 0, 0
			oz = 0
			tile.itemName = '%s.%s' % ( self.name, k )
			tile.fullName = '%s.%s' % ( self.fullname, k )
			if k == 'n':
				ox = 0
				oy = alt
			elif k == 's':
				ox = 0
				oy = 0
				oz = alt + th - h
			elif k == 'w':
				ox = tw - w
				oy = alt
			elif k == 'e':
				ox = 0
				oy = alt
			elif k == 'ne':
				ox = 0
				oy = alt
			elif k == 'se':
				ox = 0
				oy = 0
				oz = alt + th - h
			elif k == 'nw':
				ox = tw - w
				oy = alt
			elif k == 'sw':
				ox = tw - w
				oy = 0
				oz = alt + th - h
			elif k == '-ne':
				ox = 0
				oy = 0
				oz = alt + th - h
			elif k == '-se':
				ox = 0
				oy = alt
			elif k == '-nw':
				ox = 0
				oy = 0
				oz = alt + th - h
			elif k == '-sw':
				ox = 0
				oy = alt
			elif k == 'we':
				ox = 0
				oy = 0
				oz = alt + th - h
			elif k == 'ew':
				ox = 0
				oy = 0
				oz = alt + th - h
			elif k == 'c':
				ox = 0
				oy = alt
			tile.deckRect   = ( ox, oy, ox+w, oy+oz+h )
			tile.deckOffset = ( ox, oy, oz )
			tile.build( projContext )
	
	def __repr__( self ):
		return '%s: %s( %d, %d, %d )' % ( self.name, self.tileType, self.tileWidth, self.tileDepth, self.tileHeight )

	def save( self ):
		data = {}
		tileDatas = []
		for t in self.tiles:
			node = t.getAtlasNode()
			assert node
			tileData = {
				'name'       : t.itemName,
				'basename'   : t.name,
				'fullname'   : t.fullName,
				'atlas'      : str( node.root.id ),
				'rect'       : node.getRect(),
				'deck_rect'  : t.getDeckRect(),
				'deck_offset': t.getDeckOffset(),
				'raw_rect'   : t.getRawRect(),
				'raw_index'  : t.getRawIndex(),
				'meshes'     : t.getMeshes()
			}
			tileDatas.append( tileData )
		data[ 'name'     ] = self.name
		data[ 'raw_name' ] = self.rawName
		data[ 'type'     ] = self.tileType
		data[ 'alt'      ] = self.tileAlt
		data[ 'tiles'    ] = tileDatas
		return data

##----------------------------------------------------------------##
class DeckItemTileset(DeckItem):
	def __init__( self ):
		self.groups      = []
		self.wallTiles   = {}
		self.groundTiles = {}
		self.tiles       = []
		self.rawName     = ''
		self.name        = None

		self.tileWidth  = 0
		self.tileDepth  = 0
		self.tileHeight = 0

	def addGroup( self, group ):
		self.groups.append( group )
		group.theme = self

	def build( self, projContext ):
		#parse Name
		mo = re.search( '([\w_-]+)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', self.rawName )
		if mo:
			# self.name = mo.group( 1 )
			self.tileWidth  = int( mo.group( 2 ) )
			self.tileHeight = int( mo.group( 3 ) )
		else:
			raise Exception( 'tile size not specified: %s' % self.rawName )

		for group in self.groups:
			group.build( projContext )

	def postBuild( self, projectContext = None ):
		for group in self.groups:
			group.postBuild( projectContext )

	def __repr__( self ):
		return '%s: ( %d, %d )' % ( self.name, self.tileWidth, self.tileHeight )

	def getAtlasImgInfos( self ):
		infos = []
		for group in self.groups:
			for tile in group.tiles:
				( w, h ) = tile.getSize()
				img = DeckPartImg ( '', w, h, (0, 0, w, h) )	
				img.src = tile
				tile.imgInfo = img
				infos.append( img )
		return infos

	def save( self ):
		data = {}
		groupsData = []
		for g in self.groups:
			groupData = g.save()
			groupsData.append( groupData )
		data[ 'name'     ] = self.name
		data[ 'raw_name' ] = self.rawName
		data[ 'size'     ] = ( self.tileWidth, self.tileHeight )
		data[ 'groups'   ] = groupsData
		data[ 'type'     ] = 'deck2d.mtileset'
		return data


##----------------------------------------------------------------##
class DeckFactoryTileset( DeckFactory ):
	def build( self, project, psdLayerGroup, name, profix, meta ):
		if 'TILESET' not in meta['tags']: return
		tileset = DeckItemTileset()
		tileset.rawName = psdLayerGroup.name.encode( 'utf-8' )
		tileset.name    = name
		for subLayer in psdLayerGroup.layers:
			if isinstance( subLayer, Group ):
				tileGroup = self.collectGroup( project, subLayer, tileset )
		return tileset

	def collectGroup( self, project, group, tileset ):
		tileGroup = TileGroup()
		tileGroup.rawName = group.name.encode( 'utf-8' )
		tileGroup.name    = tileGroup.rawName
		def collectLayer( l, parentName = None ):
			for layer in l.layers:
				layerName = layer.name.encode( 'utf-8' )
				if layerName.startswith( '//' ): continue
				if parentName:
					fullName = parentName + '/' + layerName
				else:
					fullName = layerName
				
				if isinstance( layer, Group ):
					collectLayer( layer, fullName )
				else:
					tile = TileModule( project, layer )
					tile.rawName = layerName
					tile.name    = fullName
					tileGroup.addTile( tile )
		collectLayer( group )
		tileset.addGroup( tileGroup )

##----------------------------------------------------------------##
class DeckPackProject(object):
	"""docstring for DeckPackProject"""
	def __init__(self):
		self.columns = 4
		self.decks = []
		self.globalGuideTopFace = 0
		self.defaultDeckProfix = 'MQUAD'
		self.deckFactories = [
			DeckFactoryTileset(),
			DeckFactoryMQuad()
		]

	def loadPSD( self, path ):
		image = PSDImage.load( path )
		#root layers
		for layer in image.layers:
			if not isinstance( layer, Group ):
				layerName = layer.name.encode( 'utf-8' )
				if layerName == '@guide-top-face':
					x1,y1,x2,y2 = layer.bbox
					self.globalGuideTopFace = y1

		for layer in image.layers:
			layerName = layer.name.encode( 'utf-8' )
			if layerName.startswith( '//' ): continue
			if isinstance( layer, Group ):
				mo = re.match( r'\s*([\w\-\._]+)(\s*:\s*(.*))?\s*', layerName )
				if mo:
					name, profix = mo.group(1), mo.group(3) or self.defaultDeckProfix
					meta = parseMetaTag( layerName )
					for factory in self.deckFactories:
						deck = factory.build( self, layer, name, profix, meta )
						if deck: self.decks.append( deck )

	def save( self, path, prefix, size ):
		projContext = {
			'guide-top-face' : self.globalGuideTopFace
		}

		for deck in self.decks:
			deck.build( projContext )

		#calc row/columns
		atlas = self.generateAtlas( path, prefix, size )
		for deck in self.decks:
			deck.postBuild( projContext )

		#save
		deckDatas = []
		for deck in self.decks:
			deckData = deck.save()
			if deckData: deckDatas.append( deckData )

		output = {
			'atlas' : {
				'w' : atlas.w,
				'h' : atlas.h
 			},
			'decks' : deckDatas
		}
		saveJSON( output, path + prefix + '.json' )

	def generateAtlas( self, path, prefix, size ):
		infos = []
		for deck in self.decks:
			infos += deck.getAtlasImgInfos()			
		kwargs = {}
		kwargs['spacing'] = 1
		atlasGen = AtlasGenerator( prefix, size, **kwargs )
		atlas = atlasGen.generateOneAtlas( infos, [] )

		atlas.name = prefix + '.png'
		atlas.nameNormal = prefix + '_n' + '.png'
		atlasGen.paintAtlas( atlas, path+atlas.name, format = 'PNG' )
		atlasGen.paintAtlas( atlas, path+atlas.nameNormal, format = 'PNG', imgSet = 'normal' )
		atlas.id = 0

		return atlas
##----------------------------------------------------------------##

if __name__ == '__main__':
	proj = DeckPackProject()
	proj.loadPSD( 'test/test.decks.psd' )
	proj.save( 'test/', 'testpack', ( 2048, 2048 ) )
	