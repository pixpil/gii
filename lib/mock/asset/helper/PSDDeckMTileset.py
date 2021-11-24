from psd_tools import PSDImage, Group, Layer
from .psd_tools_helper import extract_leaf_layers, LayerProxy, layer_to_PIL

from .PSDDeckPackProject import *
from .PSDDeckMQuad import MQuadDeckPart, MQuadDeckItem
from .NormalMapHelper import makeNormalMap
from .MetaTag import parseMetaTag

def isEmptyLayer( layer ):
	lx0, ly0, lx1, ly1 = layer.bbox
	if lx0 == lx1 and ly0 == ly1: return True
	return False

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

def calcRelativeAABB( src, relativeTo ):
	( ax0, ay0, ax1, ay1 ) = src
	( bx0, by0, bx1, by1 ) = relativeTo
	return ( ax0-bx0, ay0-by0, ax1-bx0, ay1-by0 )

##----------------------------------------------------------------##
class SubLayerProxy( LayerProxy ):
	def __init__( self, src, bbox ):
		super( SubLayerProxy, self ).__init__( src )
		self.overrided_bbox = bbox
		self.subImage = None

	@property
	def bbox( self ):
		return self.overrided_bbox

	def as_PIL(self):
		if not self.subImage:
			srcImage = layer_to_PIL( self.srcLayer )
			self.subImage = srcImage.crop( calcRelativeAABB( self.overrided_bbox, self.srcLayer.bbox ) )
		return self.subImage


##----------------------------------------------------------------##
class TileItemPart( MQuadDeckPart ):
	def __init__( self, parentItem, psdLayer ):
		super( TileItemPart, self ).__init__( parentItem, psdLayer )
		self.imgNormal = None
		self.alt = 0
		self.deckOffset = ( 0,0,0 )
		self.meshes = []
		if self.foldMode == 'auto':
			self.foldMode = 'floor'

	def onBuild( self, project ):
		return super( TileItemPart, self ).onBuild( project )


##----------------------------------------------------------------##
class TileItem( MQuadDeckItem ):
	def __init__( self, parentItem, psdLayer, variationName = None ):
		super( TileItem, self ).__init__( parentItem, psdLayer, variationName )
		mo = re.search( '(^[-\w]+)(/(\w+))?', self.name )
		if mo:
			self.kind = mo.group( 1 )
		else:
			self.kind = self.name

	def createPart( self, layer ):
		return TileItemPart( self, layer )

	def onBuild( self, project ):
		super( TileItem, self ).onBuild( project )
		group = self.parentGroup
		self.itemName = '%s.%s' % ( group.name, self.name )
		self.fullName = '%s.%s' % ( group.fullname, self.name )
		if group.tileType == 'C':
			self.onBuildForCommon()
		elif group.tileType == 'T':
			self.onBuildForTerrain()

	def onBuildForCommon( self ):
		group = self.parentGroup
		tw, td, alt = group.getDim()
		self.alt = alt
		self.applyGlobalMeshOffset( 0, alt, 0 )
		self.deckOffset = [ 0, alt, 0 ]

	def onBuildForTerrain( self ):
		group = self.parentGroup
		tw, td, alt = group.getDim()
		self.alt = alt
		x0,y0,z0, x1,y1,z1 = self.getMeshAABB()
		mw, mh, md = x1 - x0, y1 - y0, z1 - z0
		ox, oy, oz = 0, 0, 0
		w, h = self.getSize()
		# print( self.fullName, x0,y0,z0, x1,y1,z1, mh, md )
		self.applyGlobalMeshOffset( -x0, -y0, -z0 - md )
		#align to top
		k = self.kind
		if k in [ 'n', 'c', 'ne', 'e', '-sw', 'we', 'ew' ] : #bottom left
			ox = 0
			oy = alt - mh
			oz = 0
		elif k in ['s', 'se', '-nw', '-ne' ]: #top left
			ox = 0
			oy = alt - mh
			oz = -td + md
		elif k in [ 'w', 'nw', '-se' ] : #bottom right
			ox = tw - mw
			oy = alt - mh
			oz = 0
		elif k in [ 'sw', 'ne' ] : #top right
			ox = tw - mw
			oy = alt - mh
			oz = -td + md

		self.applyGlobalMeshOffset( ox, oy, oz )
		self.deckOffset = [ ox, oy, oz ]

	def getData( self ):
		data = super( TileItem, self ).getData()
		data[ 'name' ] = self.itemName
		data[ 'basename' ] = self.name
		data[ 'fullname' ] = self.fullName
		data[ 'deck_offset' ] = self.deckOffset
		data[ 'raw_rect'    ] = self.aabb
		if self.parts:
			data[ 'raw_index' ] = self.parts[0].getRawIndex()
		else:
			data[ 'raw_index' ] = 0
		return data
		
##----------------------------------------------------------------##
class TileGroup(object):
	def __init__( self ):
		self.tiles = []
		self.name  = None
		self.rawName = None
		self.tileType   = 'T'
		self.tileWidth  = 0
		self.tileHeight = 0
		self.tileAlt    = 0
		self.tileset = None

	def addTile( self, tile ):
		self.tiles.append( tile )
		tile.parentGroup = self

	def getDim( self ):
		return self.tileset.tileWidth, self.tileset.tileHeight, self.tileAlt

	def onBuild( self, project ):
		#pass name
		mo = re.search( '([\w_-]+)\s*:\s*(\w*)\(\s*(\d+)\s*\)', self.rawName )
		if mo:
			self.name = mo.group( 1 )
			self.tileType = mo.group( 2 ) or 'C'
			self.tileAlt  = int( mo.group( 3 ) )
		else:
			raise Exception( 'invalid tileset name format: %s' % self.rawName )
		self.fullname = self.tileset.name + ':' + self.name

		for tile in self.tiles:
			tile.onBuild( project )

	def postBuild( self, project ):
		for tile in self.tiles:
			tile.postBuild( project )

	def __repr__( self ):
		return '%s: %s( %d, %d, %d )' % ( self.name, self.tileType, self.tileWidth, self.tileDepth, self.tileHeight )

	def getData( self ):
		data = {}
		tileDatas = []
		for t in self.tiles:
			tileData = t.getData()
			tileDatas.append( tileData )
		data[ 'name'     ] = self.name
		data[ 'raw_name' ] = self.rawName
		data[ 'type'     ] = self.tileType
		data[ 'alt'      ] = self.tileAlt
		data[ 'tiles'    ] = tileDatas
		return data

##----------------------------------------------------------------##
class MTilesetDeckItem( DeckItem ):
	def __init__( self, name, psdLayer ):
		self.groups      = []
		self.wallTiles   = {}
		self.groundTiles = {}
		self.tiles       = []
		self.rawName     = psdLayer.name
		self.name        = name

		self.tileWidth  = 0
		self.tileDepth  = 0
		self.tileHeight = 0

		#parse Name
		mo = re.search( '([\w_-]+)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', self.rawName )
		if mo:
			# self.name = mo.group( 1 )
			self.tileWidth  = int( mo.group( 2 ) )
			self.tileHeight = int( mo.group( 3 ) )
		else:
			raise Exception( 'tile size not specified: %s' % self.rawName )

		for subLayer in psdLayer.layers:
			if isinstance( subLayer, Group ):
				self.collectGroup( subLayer )

	def processItemLayer( self, psdLayer, metaInfo ):
		project = self.project
		tags = metaInfo[ 'tags' ]

	def buildGridTiles( self, itemName, layer, cols, rows, spacing ):
		partLayers = extract_leaf_layers( layer )
		tiles = []
		#find bbox
		bx0, by0 = None, None
		for subLayer in partLayers:
			subLayerName = subLayer.name
			if subLayerName.startswith( '//' ): continue
			if subLayerName.startswith( '@' ): continue
			if isEmptyLayer( subLayer ): continue
			bbox = subLayer.bbox
			if ( bx0 == None ) or bbox[0] < bx0:
				bx0 = bbox[0]
			if ( by0 == None ) or bbox[1] < by0:
				by0 = bbox[1]

		#split layer
		tw, th = self.tileWidth, self.tileHeight
		for ty in range( rows ):
			for tx in range( cols ):
				x = bx0 + tx * tw
				y = by0 + ty * th
				id = '%d-%d'%( tx, ty )
				proxies = []
				for subLayer in partLayers:
					subLayerName = subLayer.name
					if subLayerName.startswith( '//' ): continue
					proxy = SubLayerProxy( subLayer, ( x,y,x+tw,y+th ) )
					proxies.append( proxy )
				tile = TileItem( itemName, proxies, id )
				tiles.append( tile )

		return tiles
		
	def collectGroup( self, group ):
		tileGroup = TileGroup()
		tileGroup.rawName = group.name
		tileGroup.name    = tileGroup.rawName
		def _collectLayer( l, parentName = None ):
			for layer in l.layers:
				layerName = layer.name
				if layerName.startswith( '//' ): continue
				isGroup = isinstance( layer, Group )
				if isGroup:
					#if namespace
					mo = re.match( '\s*\[\s*([\w_-]+)\s*\]\s*', layerName )
					if mo:
						layerName = mo.group(1)
						fullName = parentName and (parentName + '/' + layerName) or layerName
						_collectLayer( layer, fullName )
						continue

					#if tile grid
					metaInfo = parseMetaTag( layer.name )
					tags = metaInfo and metaInfo[ 'tags' ]
					if tags and 'GRID' in tags:
						args = tags[ 'GRID' ]
						cols = getArrayI( args, 0, 0 )
						rows = getArrayI( args, 1, 0 )
						if cols*rows > 0:
							spacing = getArrayI( args, 2, 0 )
							fullName = parentName and (parentName + '/' + layerName) or layerName
							tiles = self.buildGridTiles( fullName, layer, cols, rows, spacing )
							for tile in tiles:
								tileGroup.addTile( tile )
						else:
							logging.warning( 'expecting grid dimension for layer:'+layerName )
						continue

				#common
				fullName = parentName and (parentName + '/' + layerName) or layerName
				partLayers = []
				if isinstance( layer, Group ):
					partLayers = extract_leaf_layers( layer )
				else:
					partLayers = [ layer ]
				if partLayers:
					tile = TileItem( fullName, partLayers )
					tileGroup.addTile( tile )

		_collectLayer( group )
		self.groups.append( tileGroup )
		tileGroup.tileset = self

	def onBuild( self, project ):
		for group in self.groups:
			group.onBuild( project )

	def postBuild( self, projectContext = None ):
		for group in self.groups:
			group.postBuild( projectContext )

	def __repr__( self ):
		return '%s: ( %d, %d )' % ( self.name, self.tileWidth, self.tileHeight )

	def getAtlasImgInfos( self ):
		infos = []
		for group in self.groups:
			for tile in group.tiles:
				infos += tile.getAtlasImgInfos()
		return infos

	def getData( self ):
		data = {}
		groupsData = []
		for g in self.groups:
			groupData = g.getData()
			groupsData.append( groupData )
		data[ 'name'     ] = self.name
		data[ 'raw_name' ] = self.rawName
		data[ 'size'     ] = ( self.tileWidth, self.tileHeight )
		data[ 'groups'   ] = groupsData
		data[ 'type'     ] = 'deck2d.mtileset'
		return data


##----------------------------------------------------------------##
class MTilesetDeckProcessor( DeckProcessor ):
	def onLoadImage( self, psdImage ):
		pass

	def acceptLayer( self, psdLayer, metaInfo, fallback ):
		if not isinstance( psdLayer, Group ): return False
		tags = metaInfo[ 'tags' ]
		return 'TILESET' in tags or 'TS' in tags

	def processLayer( self, psdLayer, metaInfo, namespace ):
		name = metaInfo[ 'name' ]
		fullname = namespace and ( namespace + '.' + name ) or name
		tileset = MTilesetDeckItem( fullname, psdLayer )
		self.project.addDeckItem( tileset )
		return True


##----------------------------------------------------------------##
registerDeckProcessor( 'mtileset', MTilesetDeckProcessor )

##----------------------------------------------------------------##


if __name__ == '__main__':
	from . import PSDDeckPackTest
