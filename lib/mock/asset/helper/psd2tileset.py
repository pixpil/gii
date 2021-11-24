from os.path import basename, splitext
import math
import io
from PIL import Image
from .psd_tools_helper import *

from psd_tools import PSDImage, Group, Layer
from psd_tools.constants import ImageResourceID
from psd_tools.utils import read_fmt, read_unicode_string, read_pascal_string

from .atlas2 import AtlasGenerator, Img

import logging
import json

import re


##----------------------------------------------------------------##
def saveJSON( data, path, **option ):
	outputString = json.dumps( data , 
			indent    = option.get( 'indent' ,2 ),
			sort_keys = option.get( 'sort_keys', True ),
			ensure_ascii=True
		)
	with open( path, 'w', encoding = 'utf-8' ) as fp:
		fp.write( outputString )
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
class LayerImg(Img): #	
	def getImage(self, imgSet = None ):
		return self.animModule.getImage()

def extract_layer_channel_data( l ):
	decoded_data = l._psd.decoded_data
	layer_index = l._index
	layers = decoded_data.layer_and_mask_data.layers
	layer = layers.layer_records[layer_index]
	channels_data = layers.channel_image_data[layer_index]
	return ( channels_data, layer.width(), layer.height() )

def compare_layer_image( l1, l2 ):
	d1 = extract_layer_channel_data(l1)
	d2 = extract_layer_channel_data(l2)
	#compare size
	if d1[1] != d2[1]: return False
	if d1[2] != d2[2]: return False
	#compare channel raw data
	chs1 = d1[0]
	chs2 = d2[0]
	if len(chs1) != len(chs2): return False
	for i in range(0, len(chs1)):
		ch1 = chs1[i]
		ch2 = chs2[i]
		if ch1.data != ch2.data: return False
	return True

##----------------------------------------------------------------##
class TileImg(Img): #	
	def getImage(self, imgSet = None):
		return self.src.getImage()

##----------------------------------------------------------------##
class TileModule(object):
	def __init__( self, project, psdLayer ):
		self._project = project
		self._layer = psdLayer
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

	def getSize( self ):
		return (self.w, self.h)

	def getImage( self ):
		if self.img: return self.img
		self.img = self._layer.as_PIL()
		return self.img

	def getOffset( self ):
		return self.x, self.y

	def getImageSourceData( self ):
		return self._layer

	def getAtlasNode( self ):
		return self.imgInfo.node

	def getDeckRect( self ):
		return self.deckRect

	def getDeckOffset( self ):
		return self.deckOffset

	def getRawRect( self ):
		return self.rawRect

	def getRawIndex( self ):
		return self.rawIndex

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

	def build( self ):
		#pass name
		mo = re.search( '([\w_-]+)\s*:(\w*)\(\s*(\d+)\s*\)', self.rawName )
		if mo:
			self.name = mo.group( 1 )
			self.tileType = mo.group( 2 ) or 'C'
			self.tileAlt  = int( mo.group( 3 ) )
		else:
			raise Exception( 'invalid tileset name format: %s' % self.rawName )
		self.fullname = self.theme.name + ':' + self.name
		if self.tileType == 'C':
			self.buildCommonTiles()
		elif self.tileType == 'T':
			self.buildTerrainTiles()

	def buildCommonTiles( self ):
		tw, td, alt = self.getDim()
		for tile in self.tiles:
			k = tile.name
			w, h = tile.w, tile.h
			ox, oy = 0, alt
			tile.itemName = '%s.%s' % ( self.name, k )
			tile.fullName = '%s.%s' % ( self.fullname, k )
			tile.deckRect = ( ox, oy, ox + w, oy + h )

	def buildTerrainTiles( self ):
		tw, th, alt = self.getDim()
		for tile in self.tiles:
			k = tile.name
			w, h = tile.w, tile.h
			ox, oy = 0, 0
			tile.itemName = '%s.%s' % ( self.name, k )
			tile.fullName = '%s.%s' % ( self.fullname, k )
			if k == 'n':
				ox = 0
				oy = alt
			elif k == 's':
				ox = 0
				oy = alt + th - h
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
				oy = alt + th - h
			elif k == 'nw':
				ox = tw - w
				oy = alt
			elif k == 'sw':
				ox = tw - w
				oy = alt + th - h
			elif k == '-ne':
				ox = 0
				oy = alt + th - h
			elif k == '-se':
				ox = 0
				oy = alt
			elif k == '-nw':
				ox = 0
				oy = alt + th - h
			elif k == '-sw':
				ox = 0
				oy = alt
			elif k == 'we':
				ox = 0
				oy = alt + th - h
			elif k == 'ew':
				ox = 0
				oy = alt + th - h
			elif k == 'c':
				ox = 0
				oy = alt
			tile.deckRect   = ( ox, oy, ox+w, oy+h )
			tile.deckOffset = ( ox, oy )
	
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
				'raw_index'  : t.getRawIndex()
			}
			tileDatas.append( tileData )
		data[ 'name'     ] = self.name
		data[ 'raw_name' ] = self.rawName
		data[ 'type'     ] = self.tileType
		data[ 'alt'      ] = self.tileAlt
		data[ 'tiles'    ] = tileDatas
		return data

##----------------------------------------------------------------##
class TilesetTheme(object):
	def __init__( self ):
		self.groups = []
		self.wallTiles   = {}
		self.groundTiles = {}
		self.tiles = []
		self.rawName = ''
		self.name = None
		self.tileWidth = 0
		self.tileDepth = 0
		self.tileHeight = 0

	def addGroup( self, group ):
		self.groups.append( group )
		group.theme = self

	def build( self ):
		#parse Name
		mo = re.search( '([\w_-]+)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', self.rawName )
		if mo:
			self.name = mo.group( 1 )
			self.tileWidth  = int( mo.group( 2 ) )
			self.tileHeight = int( mo.group( 3 ) )
		else:
			raise Exception( 'tile size not specified: %s' % self.rawName )

		for group in self.groups:
			group.build()

	def __repr__( self ):
		return '%s: ( %d, %d )' % ( self.name, self.tileWidth, self.tileHeight )

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
		return data


##----------------------------------------------------------------##
class TilesetProject(object):
	"""docstring for TilesetProject"""
	def __init__(self):
		self.tiles = []
		self.tileSize = ( 50, 50 )
		self.columns = 4
		self.themes = []

	def loadPSD( self, path ):
		image = PSDImage.load( path )
		#meta data
		bx0 ,	by0 ,	bx1 ,	by1 = image.bbox
		self.bbox = ( bx0, by0, bx1, by1 )		
		self.tileSize = ( bx1, by1 )
		for layer in image.layers:
			theme = self.collectTheme( layer )
			if theme :
				self.themes.append( theme )

	def collectTheme( self, group ):
		if not isinstance( group, Group ): return
		layerName = group.name
		if not layerName: return
		if layerName.startswith( '//' ): return
		theme = TilesetTheme()
		theme.rawName = layerName
		theme.name = theme.rawName
		for sub in group.layers:
			tileGroup = self.collectGroup( sub, theme )
			if tileGroup:
				theme.addGroup( tileGroup )
		return theme

	def collectGroup( self, group, theme ):
		if not isinstance( group, Group ): return
		tileGroup = TileGroup()
		tileGroup.rawName = group.name
		tileGroup.name = tileGroup.rawName
		def collectLayer( l ):
			for layer in l.layers:
				layerName = layer.name
				if layerName.startswith( '//' ): continue
				if isinstance( layer, Group ):
					collectLayer( layer )
				else:
					tile = TileModule( self, layer )
					tile.rawName = layerName
					tile.name = layerName
					tileGroup.addTile( tile )
		collectLayer( group )
		return tileGroup


	def save( self, atlasPath, jsonPath, atlasSize = ( 1024, 1024 ) ):
		for theme in self.themes:
			theme.build()
		atlas = self.generateAtlas( atlasPath, atlasSize )
		themeDatas = []
		for theme in self.themes:
			themeDatas.append( theme.save() )
		output = {
			'atlas' : {
				'w' : atlas.w,
				'h' : atlas.h
			},
			'themes' : themeDatas
		}
		saveJSON( output, jsonPath )


	def generateAtlas( self, atlasPath, atlasSize ):
		infos = []
		for theme in self.themes:			
			for group in theme.groups:
				for tile in group.tiles:
					( w, h ) = tile.getSize()
					img = TileImg ( '', w, h, (0, 0, w, h) )	
					img.src = tile
					tile.imgInfo = img
					infos.append( img )
		kwargs = {}
		prefix='output' #TODO: use real output name
		kwargs['spacing'] = 1
		atlasGen = AtlasGenerator( prefix, atlasSize, **kwargs )
		atlas = atlasGen.generateOneAtlas( infos, [] )

		atlas.name = atlasPath
		atlasGen.paintAtlas( atlas, atlas.name )
		atlas.id = 0

		return atlas
##----------------------------------------------------------------##

if __name__ == '__main__':
	proj = TilesetProject()
	proj.loadPSD( 'tile.psd' )
	proj.save( 'tile', ( 1024, 1024 ) )
	proj.save( 'chicago' )

	proj.loadPSD( 'tmpnumber.psd' )
	proj.save( 'numbers' )

	proj.loadPSD( 'number2.psd' )
	proj.save( 'numbers2' )
