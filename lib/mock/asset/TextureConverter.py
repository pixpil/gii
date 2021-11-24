import logging
from . import ImageHelpers 
from PIL import Image

##----------------------------------------------------------------##
_TextureConverterRegistry = []
_defaultTextureFormat     = 'png'

def registerTextureConverter( converter, **option ):
	_TextureConverterRegistry.append( converter )
	converter.priority = option.get( 'priority', converter.priority )
	_TextureConverterRegistry.sort( key = lambda c: c.priority )

def convertTextureFormat( srcFormat, dstFormat, srcPath, dstPath, **option ):
	if dstFormat == 'auto':
		dstFormat = _defaultTextureFormat
	# logging.info( 'convert texture', dstFormat, srcPath, dstPath
	for converter in _TextureConverterRegistry:
		if converter.convert( srcFormat, dstFormat, srcPath, dstPath, **option ):
			return True
	return False

##----------------------------------------------------------------##
def setDefaultTextureFormat( fmt ):
	global _defaultTextureFormat
	_defaultTextureFormat = fmt

def getDefaultTextureFormat():
	return _defaultTextureFormat


##----------------------------------------------------------------##
_priority = 0
class TextureConverter(object):
	def __init__( self ):
		global _priority
		self.priority = _priority
		_priority += 1

	def convert( self, srcFormat, dstFormat, srcPath, dstPath, **option ):
		return False

##----------------------------------------------------------------##
class DefaultTextureConverter( TextureConverter ):
	def __init__( self ):
		super( DefaultTextureConverter, self ).__init__()
		self.priority = 0

	def convert( self, srcFormat, dstFormat, srcPath, dstPath, **options ):
		logging.info( 'converting texture: %s -> %s' % ( srcPath, dstFormat ) )
		if dstFormat == 'webp':
			ImageHelpers.convertToWebP( srcPath, dstPath, **options )

		elif dstFormat == 'png':
			ImageHelpers.convertToPNG( srcPath, dstPath, **options )

		elif dstFormat == 'PVR-2':
			options[ 'bbp' ] = 2
			ImageHelpers.convertToPVR( srcPath, dstPath, **options )

		elif dstFormat == 'PVR-4':
			options[ 'bbp' ] = 4
			ImageHelpers.convertToPVR( srcPath, dstPath, **options )

		else:
			return False
			
		return True


##----------------------------------------------------------------##
registerTextureConverter( DefaultTextureConverter() )