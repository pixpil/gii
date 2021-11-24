import sys
import struct
import io
import zlib

from PIL import Image, ImageChops
import numpy as np
from util.ImageTool.UniqueImageSet import UniqueImageSet

def read_fmt(fmt, fp):
	"""
	Reads data from ``fp`` according to ``fmt``.
	"""
	fmt = str("<" + fmt)
	fmt_size = struct.calcsize(fmt)
	data = fp.read(fmt_size)
	assert len(data) == fmt_size, (len(data), fmt_size)
	x = struct.unpack(fmt, data)
	if len( x ) == 1: return x[0]
	return x

def read_string( fp ):
	s = read_fmt( 'H', fp )
	string = fp.read( s )
	return str(string,encoding='utf-8')

##----------------------------------------------------------------##
class ASEFrame(object):
	def __init__( self ):
		self.cels = []
		self.duration = 10
		self.parentDocument = None

	def getParentDocument( self ):
		return self.parentDocument

	def getCels( self ):
		return self.cels

	def findCelByLayer( self, layerIndex ):
		for cel in self.cels:
			if cel.layerIndex == layerIndex: return cel
		return None


##----------------------------------------------------------------##
class ASECel(object):
	def __init__( self ):
		self.x, self.y = 0, 0
		self.w, self.h = 0, 0
		self.type       = 0
		self.layerIndex = None
		self.layer      = None
		self.linked     = None
		self.linkedCel  = None
		self.image      = None
		self.bbox       = (0,0,0,0)
		self.parentFrame = None

	def getParentFrame( self ):
		return self.parentFrame

	def getParentDocument( self ):
		return self.parentFrame and self.parentFrame.getParentDocument()

	def getImage( self ):
		return self.getRealCel().image

	def getRealCel( self ):
		if self.linkedCel:
			return self.linkedCel.getRealCel()
		else:
			return self


##----------------------------------------------------------------##
class ASELayer(object):
	def __init__( self ):
		self.flags = 0
		self.type = 0
		self.childLevel = 0
		self.blend = 0
		self.opacity = 255
		self.name = ''
		self.name_stripped = ''
		self.children = []
		self.parent = None

	def isGroup( self ):
		return self.type == 1

	def getParent( self ):
		return self.parent

	def getChildren( self ):
		return self.children

	def isVisible( self ):
		return bool( self.flags & 1 )

	def isEditable( self ):
		return bool( self.flags & 2 )

	def isLocked( self ):
		return bool( self.flags & 4 )

	def isBackground( self ):
		return bool( self.flags & 8 )

	def isPreferLinkedCels( self ):
		return bool( self.flags & 16 )

##----------------------------------------------------------------##					
class ASEFrameTag(object):
	def __init__( self ):
		self.name = ''
		self.name_stripped = ''
		self.color = ( 1,1,1,1 )
		self.frameFrom = 0
		self.frameTo = 0
		self.direction = 0
		

def compare_image(img1, img2):
	if img1.size != img2.size:
		return False
	return ImageChops.difference(img1, img2).getbbox() is None

##----------------------------------------------------------------##
class ASEDocument(object):
	def __init__( self ):
		self.frames = []
		self.layers = []
		self.tags   = []
		self.flags  = 0
		self.width  = 0
		self.height = 0
		self.speed  = 1
		self.depth  = 0
		self.palette = None

	def _convertPaletteImage( self, img ):
		pix = img.load()
		w, h = img.size
		img1 = Image.new( 'RGBA', ( w, h ) )
		pix1 = img1.load()
		palette = self.palette
		for y in range( h ):
			for x in range( w ):
				p = pix[ x, y ]
				pix1[ x, y ] = palette[ p ]
		return img1

	def _clearZeroArea( self, img ):
		a = np.array( img, np.uint8 )
		a[ a[:,:,3] == 0 ] = 0
		return Image.fromarray( a )

	def load( self, path, image_cache = None ):
		#read header
		self.frames = []
		fp = open( path, 'rb' )
		
		
		if not image_cache:
			image_cache = UniqueImageSet()

		filesize, mnumber = read_fmt( 'LH', fp )
		frameNum          = read_fmt( 'H', fp )
		w, h              = read_fmt( 'HH', fp )
		depth             = read_fmt( 'H', fp )
		flags             = read_fmt( 'L', fp )
		speed             = read_fmt( 'H', fp )

		read_fmt( 'LL', fp) #skip
		transparentIdx = read_fmt( 'B', fp )
		fp.read( 3 )
		colorNum = read_fmt( 'H', fp )
		fp.read( 94 )
		self.flags = flags
		self.width, self.height = w, h
		self.speed = speed
		self.colorNum = colorNum
		self.depth = depth 
		self.transparentIdx = transparentIdx
		if not ( depth in [ 32, 8 ] ):
			raise Exception( 'only RGBA/Indexed mode is supported' )
			
		#frames
		for fid in range( frameNum ):
			#header
			frameSize, mnumber = read_fmt( 'LH', fp )
			chunkNum = read_fmt( 'H', fp )
			duration = read_fmt( 'H', fp )
			fp.read( 6 )

			if mnumber != 0xf1fa:
				for i in range( frameNum - fid ):
					frame = ASEFrame() #workaround for 'incorrect' ase format
					frame.duration = 0
					frame.parentDocument = self
					self.frames.append( frame )
				break #unknown frame, what the fuck?

			frame = ASEFrame()
			frame.duration = duration
			frame.parentDocument = self
			self.frames.append( frame )
			
			contextObject = None
			for ci in range( chunkNum ):
				chunkSize, chunkType = read_fmt( 'LH', fp )

				chunkData = fp.read( chunkSize - 6 )
				dp = io.BytesIO( chunkData )
				
				if chunkType == 0x0004: #old palette SKIP
					pass

				elif chunkType == 0x0011: #old palette SKIP
					pass

				elif chunkType == 0x2004: #layer
					layer = ASELayer()
					layer.flags = read_fmt( 'H', dp )
					layer.type, layer.childLevel = read_fmt( 'HH', dp )
					defaultw, defaulth = read_fmt( 'HH', dp )
					layer.blend   = read_fmt( 'H', dp )
					layer.opacity = read_fmt( 'B', dp )
					dp.read( 3 )
					layer.name = read_string( dp )
					layer.name_stripped = layer.name.strip()
					self.layers.append( layer )
					contextObject = layer

				elif chunkType == 0x2005: #cel
					cel = ASECel()
					cel.layerIndex = read_fmt( 'H', dp )
					cel.x, cel.y   = read_fmt( 'hh', dp )
					cel.opacity    = read_fmt( 'B', dp )
					cel.type       = read_fmt( 'H', dp )
					dp.read( 7 )
					ctype = cel.type
					if ctype == 1: #linked cel
						cel.linked = read_fmt( 'H', dp )

					else:
						cel.w, cel.h = read_fmt( 'HH', dp )
						data = dp.read()
						if ctype == 2: #raw cel
							data = zlib.decompress( data )

						if self.depth == 32: #rgba
							img = Image.frombuffer( 'RGBA', (cel.w, cel.h), data, 'raw', 'RGBA', 0, 1 )
							img = self._clearZeroArea( img )

						elif self.depth == 8: #palette
							img = Image.frombuffer( 'P', (cel.w, cel.h), data, 'raw', 'P', 0, 1 )
							#convert into rgba
							img = self._convertPaletteImage( img )
							
						bbox = img.getbbox()
						cropped = img.crop( bbox )
						
						cel.image = image_cache.affirm( cropped )
						cel.bbox  = bbox

					frame.cels.append( cel )
					cel.parentFrame = frame
					contextObject = cel

				elif chunkType == 0x2016: #mask SKIP
					pass

				elif chunkType == 0x2017: #path SKIP
					pass

				elif chunkType == 0x2018: #frame tags
					tagNum = read_fmt( 'H', dp )
					dp.read( 8 )
					for tid in range( tagNum ):
						tag = ASEFrameTag()
						tag.id = tid
						tag.frameFrom, tag.frameTo = read_fmt( 'HH', dp )
						tag.direction = read_fmt( 'B', dp )
						dp.read( 8 )
						dp.read( 3 )
						dp.read( 1 )
						tag.name = read_string( dp )
						tag.name_stripped = tag.name.strip()

						self.tags.append( tag )

				elif chunkType == 0x2019: #new palette 
					size = read_fmt( 'L', dp )
					index0 = read_fmt( 'L', dp )
					index1 = read_fmt( 'L', dp )
					dp.read( 8 )
					palette = {}
					paletteName = {}
					for cid in range( size ):
						hasName = read_fmt( 'H', dp )
						r,g,b,a = read_fmt( 'BBBB', dp )
						if hasName:
							colorName = read_string( dp )
						else:
							colorName = ''
						idx = index0 + cid
						palette[ idx ] = (r,g,b,a)
						paletteName[ idx ] = colorName
					self.palette = palette
					self.paletteName = paletteName
					palette[ self.transparentIdx ] = ( 0,0,0,0 )

				elif chunkType == 0x2020: #userdata
					flags = read_fmt( 'L', dp )
					userText = None
					userColor = None
					if flags & 0x1:
						userText = read_string( dp )
					if flags & 0x2:
						userColor = read_fmt( 'cccc', dp )
					contextObject.userText  = userText
					contextObject.userColor = userColor

				elif chunkType == 0x2021: #slices
					pass

				elif chunkType == 0x2022: #slice
					pass

				else:
					print( "unknown chunkType", chunkType )
					pass

		#update linked cel cel.layer
		for frame in self.frames:
			for cel in frame.cels:
				cel.layer = self.layers[ cel.layerIndex ]
				if cel.type == 1:
					targetFrame = self.frames[ cel.linked ]
					cel.linkedCel = targetFrame.findCelByLayer( cel.layerIndex )

		#process layer groups
		currentGroups = {}
		for layer in self.layers:
			clevel = layer.childLevel
			currentGroups[ clevel ] = layer
			plevel = clevel - 1
			if plevel >= 0:
				parent = currentGroups[ plevel ]
				if parent:
					parent.children.append( layer )
					layer.parent = parent

		
if __name__ == '__main__':
	# doc = ASEDocument()
	# doc.load( 'JohnSitidle.ase' )
	# print 'layer count:', len( doc.layers )
	# for i, frame in enumerate( doc.frames ):
	# 	print 'frame #',i
	# 	for j, cel in enumerate( frame.cels ):
	# 		print cel.type, cel.layerIndex, cel.x, cel.y, cel.w, cel.h
	import numpy as np  
	a = np.random.randn(2,2,3) 
	print( a )
	print('----')
	a[a[:,:,2]<0] = 0
	print( a )
	# print('-------')
	# print(np.where(a[3,:] > 0 ) )
	# print( a.min(axis=0))
	
	# print(a)
	