from os.path import basename, splitext
import math
import io
import copy
import logging
import json
import re

from psd_tools import PSDImage, Group, Layer
from .psd_tools_helper import layer_to_PIL

from .atlas2 import AtlasGenerator, Img
from .MetaTag import parseMetaTag


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
class DeckPartImgInfo( Img ): #	
	# def __init__( self, path, fw, fh, bbox ):
	# 	super( DeckPartImgInfo, self ).__init__( path, fw, fh, bbox )
	# 	self.src = None

	def getImage(self, imgSet = None ):
		return self.src.getImage( imgSet )

##----------------------------------------------------------------##
class DeckPart( object ):
	def __init__( self, parentItem, psdLayer ):
		self._layer = psdLayer
		layerName = psdLayer.name
		self.parentItem = parentItem
		self.rawName = layerName
		self.name    = layerName
		self.img = None
		x1,y1,x2,y2 = psdLayer.bbox
		self.w = w = x2-x1
		self.h = h = y2-y1
		self.x = x1
		self.y = y1
		self.deckRect = ( 0,0,1,1 )
		self.deckOffset = ( 0,0 )
		self.rawRect  = ( x1,y1,x2,y2 )

		self.imgInfo = DeckPartImgInfo( '', w,h, ( 0,0,w,h ) )
		self.imgInfo.node = None
		self.imgInfo.src = self

		self.rawImage = None

		self.rawIndex = psdLayer._index
		self.options = {}

	def getClipRect( self ):
		return self.src.clipRect

	def getSize( self ):
		return (self.w, self.h)

	def getOffset( self ):
		return self.x, self.y

	def getImageSourceData( self ):
		return self._layer

	def getImage( self, imgSet ):
		return self.getRawImage()

	def getRawImage( self ):
		if self.rawImage: return self.rawImage
		try:
			srcImage = layer_to_PIL( self._layer ) 
			clipRect = self.getClipRect()
			if clipRect:
				srcImage = srcImage.crop( srcImage )
			self.rawImage = srcImage
		except Exception as e:
			#FIXME: ignore empty layer?
			print(self._layer.name)
			print(e)
			return None
		return self.rawImage

	def getRawIndex( self ):
		return self.rawIndex

	def getRawRect( self ):
		return self.rawRect

	def getDeckRect( self ):
		return self.deckRect

	def getDeckSize( self ):
		x, y, x1, y1 = self.deckRect
		return x1-x, y1-y

	def getBottom( self ):
		return self.y + self.h

	def getLeft( self ):
		return self.x

	def getRight( self ):
		return self.x + self.w

	def getTop( self ):
		return self.y

	def getDeckOffset( self ):
		return self.deckOffset

	def getAtlasImgInfo( self ):
		return self.imgInfo

	def getAtlasNode( self ):
		return self.imgInfo.node

##----------------------------------------------------------------##
class DeckItem(object):
	def __init__( self ):
		self.parts = []
		self.clipRect = None

	def getClipRect( self ):
		return self.clipRect

	def onBuild( self, project ):
		pass

	def postBuild( self, project ):
		pass

	def getAtlasImgInfos( self ):
		infos = []
		for part in self.parts:
			info = part.getAtlasImgInfo()
			if info: infos.append( info )
		return infos

	def createPart( self, psdLayer ):
		return DeckPart( self, psdLayer )

	def addPart( self, psdLayer ):
		part = self.createPart( psdLayer )
		self.parts.append( part )
		part.src = self
		return part

	def getData( self ):
		return None

##----------------------------------------------------------------##
class DeckProcessor(object):
	def __init__( self, project ):
		self.project = project 
		self.isDefaultProcessor = False

	def onInit( self, project ):
		pass

	def onLoadImage( self, image ):
		pass

	def acceptLayer( self, layer, metaInfo, fallback ):
		return False
	
	def processLayer( self, layer, metaInfo, namespace ):
		pass

	def generateDecks( self, context ):
		pass

	def setDefault( self, default ):
		self.isDefaultProcessor = default

##----------------------------------------------------------------##
class DeckPackBuildContext(object):
	def pushAtlasItem( self, imgSet, img ):
		pass

##----------------------------------------------------------------##
_DeckProcessorClassRegistry = []
def registerDeckProcessor( id, clas, **options ):
	entry = {
		'id': id,
		'clas':clas,
		'options': options
	}
	_DeckProcessorClassRegistry.append( entry )



##----------------------------------------------------------------##
class PSDDeckPackProject(object):
	"""docstring for PSDDeckPackProject"""
	def __init__(self):
		#for building
		self.atlasImgInfos = []
		self.deckItems     = []
		self.imageSets     = [ 'color' ]
		self.dirty = True

		self.options = {}

		self.defaultProcessor = None
		#init
		self.processors = []
		self.processorMap = {}
		for entry in _DeckProcessorClassRegistry:
			id = entry[ 'id' ]
			clas = entry[ 'clas' ]
			processor = clas( self )
			processor.onInit( self )
			self.processorMap[ id ] = processor
			self.processors.append( processor )

	def findProcessor( self, id ):
		return self.processorMap.get( id, None )

	def setDefaultProcessor( self, id ):
		if self.defaultProcessor:
			self.defaultProcessor.setDefault( False )
		processor = self.findProcessor( id )
		self.defaultProcessor = processor
		if processor:
			processor.setDefault( True )
				
	##for building context
	def getOption( self, key, default = None ):
		return self.options.get( key, default )

	def setOption( self, key, value ):
		self.options[ key ] = value

	def hasOption( self, key ):
		return key in self.options

	def addAtlasImgInfo( self, info ):
		self.atlasImgInfos.append( info )

	def addDeckItem( self, deckItem ):
		self.deckItems.append( deckItem )

	def affirmImageSet( self, imgSet ):
		if imgSet in self.imageSets: return True
		self.imageSets.append( imgSet )

	##API
	def loadPSD( self, path ):
		# print 'loading', path
		image = PSDImage.load( path )
		for processor in self.processors:
			processor.onLoadImage( image ) 

		self.processGroup( image.layers )
		self.dirty = True

	def processGroup( self, layers, namespace = None, defaultDeckType = None ):
		for layer in layers:
			layerName = layer.name
			if layerName.startswith( '//' ): continue
			#category
			if isinstance( layer, Group ):
				metaInfo = parseMetaTag( layerName )
				if metaInfo:
					tags = metaInfo['tags']
					if 'GROUP' in tags:
						groupDeckType = tags[ 'GROUP' ]
						groupDeckType = groupDeckType and groupDeckType[ 0 ]
						self.processGroup( layer.layers, namespace, groupDeckType or defaultDeckType )
						continue

					if 'NAMESPACE' in tags:
						metaInfo = parseMetaTag( layerName )
						nsDeckType = tags[ 'NAMESPACE' ]
						nsDeckType = nsDeckType and nsDeckType[ 0 ]
						name = metaInfo[ 'name' ]
						if name:
							newNamespace = namespace and ( namespace + '.' + name ) or name
							self.processGroup( layer.layers, newNamespace, nsDeckType or defaultDeckType )
							continue
			self.processLayer( layer, namespace, defaultDeckType )
		
	def processLayer( self, layer, namespace = None, defaultDeckType = None ):
		metaInfo = parseMetaTag( layer.name )
		if not metaInfo:
			#invalid name, skip
			logging.warning( 'invalid psd deck layer name:' + layer.name )
			return False

		for processor in self.processors:
			if processor.acceptLayer( layer, metaInfo, False ):
				processor.processLayer( layer, metaInfo, namespace )
				return True
		
		#try specified default
		if defaultDeckType:
			processor = self.findProcessor( defaultDeckType )
			if not processor:
				logging.warning( 'invalid deck type:' + defaultDeckType )
				return False
			if processor.acceptLayer( layer, metaInfo, True ):
				processor.processLayer( layer, metaInfo, namespace )
				return True

		#try fallback
		if self.defaultProcessor:
			if self.defaultProcessor.acceptLayer( layer, metaInfo, True ):
				self.defaultProcessor.processLayer( layer, metaInfo, namespace )
				return True
		return False

	def generateAtlas( self, path, prefix, size ):
		infos = []
		for deck in self.deckItems:
			infos += deck.getAtlasImgInfos()

		option = {
			'spacing' : 1
		}
		atlasGen = AtlasGenerator( prefix, size, **option )
		atlas = atlasGen.generateOneAtlas( infos, [] )

		atlas.name = prefix + '.png'
		atlas.nameNormal = prefix + '_n' + '.png'
		atlasGen.paintAtlas( atlas, path+atlas.name,       format = 'PNG' )
		atlasGen.paintAtlas( atlas, path+atlas.nameNormal, format = 'PNG', imgSet = 'normal' )
		atlas.id = 0

		return atlas

	def build( self, path, prefix, size ):
		if not self.dirty: return

		for deck in self.deckItems:
			deck.onBuild( self )

		atlas = self.generateAtlas( path, prefix, size )
		self.generatedAtlas = atlas

		for deck in self.deckItems:
			deck.postBuild( self )

		self.dirty = False

	def save( self, path, prefix, size ):
		self.build( path, prefix, size )
		#save
		deckDatas = []
		for deck in self.deckItems:
			deckData = deck.getData()
			if deckData: deckDatas.append( deckData )

		#atlas info
		atlas = self.generatedAtlas
		atlasInfo = {
			'w' : atlas.w,
			'h' : atlas.h
		}

		#output
		output = {
			'atlas' : atlasInfo,
			'decks' : deckDatas,
		}

		saveJSON( output, path + prefix + '.json' )

##----------------------------------------------------------------##

if __name__ == '__main__':
	from . import PSDDeckPackTest	
