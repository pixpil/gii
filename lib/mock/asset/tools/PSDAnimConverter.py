from os.path import basename, splitext
import io
from psd_tools import PSDImage, Group, Layer
from psd_tools.constants import ImageResourceID
from psd_tools.utils import read_fmt, read_unicode_string, read_pascal_string
from .atlas import AtlasGenerator, Img


##----------------------------------------------------------------##
def read_psd_string ( f ):
	l, = read_fmt("I", f)
	if l==0: l = 4;
	return f.read( l )

def read_psd_obj( f, vt = None ):
	if not vt: vt = f.read( 4 )
	if vt == 'long':
		v, = read_fmt('l', f)
		return v

	elif vt == 'bool':
		result, = read_fmt('b', f)
		return result != 0

	elif vt == 'doub':
		result, = read_fmt('d', f)
		return result

	elif vt == 'VlLs':
		count, = read_fmt('I', f)
		result = []
		for i in range( 0, count ):
			v = read_psd_obj( f )
			result.append (v)
		return result

	elif vt == 'Objc':
		nameLen, = read_fmt("I", f)
		f.seek( nameLen * 2, 1 ) #skip name
		classId = read_psd_string( f )
		count, = read_fmt("I", f)
		result = {}
		for i in range( 0, count ):
			key = read_psd_string( f )
			value = read_psd_obj( f )
			result[key] = value
		return result

	elif vt == 'enum':
		typeId = read_psd_string( f )
		value = read_psd_string( f )
		return ( typeId, value )

	elif vt == 'UntF':
		unit = f.read(4)
		value, = read_fmt('d', f)
		return (value, unit)
	
	elif vt == 'TEXT':
		size, = read_fmt("I", f)
		text = f.read( size * 2 ) #TODO: unicode?
		return text

	else:
		raise Exception('not implement: %s ' % vt )

def get_mlst( layer ):
	for md in layer._tagged_blocks['shmd']:
		if md.key == 'mlst':
			f = io.StringIO( md.data )
			f.read(4)
			desc = read_psd_obj( f, 'Objc' )
			return desc
	return None

def get_mani( image ):
	for r in image.decoded_data.image_resource_blocks:
		if r.resource_id == 4000:
			f = io.StringIO( r.data )		
			pluginName = f.read(4)
			assert pluginName == 'mani', pluginName 
			f.seek( 24, 1 )
			desc = read_psd_obj( f, 'Objc' )
			return desc
	return None

def extractLeafLayers( image ):
	def extractGroup( layers, result ):
		for l in layers:
			if isinstance( l, Group ):
				extractGroup( l.layers, result )
			else:
				result.append( l )
	result = []
	extractGroup( image.layers, result )
	return result

##----------------------------------------------------------------##
class LayerImg(Img): #	
	def getImage(self):
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

class ModuleCache(object):
	def __init__(self):
		self.cache0 = {}


class AnimFrame(object):
	def __init__( self ):
		self.parts = []
		self.name = "null"

	def addModule( self, m, offsetX, offsetY ):
		self.parts.append( { 'module':m, 'offset': (offsetX, offsetY) } )

class AnimModule(object):
	def __init__( self, psdLayer ):
		self._layer = psdLayer
		self.img = None
		x1,y1,x2,y2 = psdLayer.bbox
		self.w = x2-x1
		self.h = y2-y1
		self.imgInfo = None

	def getSize( self ):
		return (self.w, self.h)

	def getImage( self ):
		if self.img: return self.img
		self.img = self._layer.as_PIL()
		return self.img

	def getImageSourceData( self ):
		return self._layer

	def getAtlasNode( self ):
		return self.imgInfo.node


class Anim(object):
	def __init__(self):
		self.name = "null"
		self.frames = []

	def addFrame( self, frame, offsetX, offsetY ):
		self.frames.append( { 'frame':frame, 'offset': (offsetX, offsetY) } )
		pass

	def setOrigin( self, x, y ):
		self.ox = x
		self.oy = y

	def setBound( self, x, y, w, h ):
		self.bound = ( x,y,w,h )
 
class AnimProject(object):
	def __init__(self):		
		self.modules = []
		self.animations = []
		self.frames = []
		self.moduleCache = {}
		self.atlases = None
		self.currentModuleId = 0
		self.currentFrameId = 0
		self.currentAnimId = 0

	def addAnim( self, anim ):
		self.animations.append( anim )
		anim.id = self.currentAnimId + 0x3000
		self.currentAnimId += 1

	def addFrame( self, frame ):
		self.frames.append( frame )
		frame.id = self.currentFrameId + 0x2000
		self.currentFrameId += 1

	def generateImagesInfo( self ):
		infos = []
		for m in self.moduleCache.values():
			( w, h ) = m.getSize()
			img = LayerImg ( '', w, h, (0, 0, w, h) )	
			img.animModule = m
			infos.append( img )
			m.imgInfo = img
		return infos

	def generateAtlases( self, path, size, **kwargs ):
		#5. pack all bitmap in cache into atlas
		prefix='output' #TODO: use real output name
		kwargs['spacing'] = 1
		atlasGen = AtlasGenerator( prefix, size, **kwargs )
		imageInfos = self.generateImagesInfo()
		atlases = atlasGen.generateAtlases( imageInfos )
		id = 0
		for atlas in atlases:
			atlas.name = 'output_atlas.png'
			atlasGen.paintAtlas( atlas, atlas.name )
			atlas.id = id
			id += 1
		self.atlases = atlases

	def saveAurora( self, path, size, **kwargs ):
		if not self.atlases:
			self.generateAtlases( path, size, **kwargs )
		#6. write into final file.
		fp = open( path + '.sprite', 'w' )
		def writeln( x ): fp.write( x ); fp.write( '\n' )
		writeln( '// saved by AuroraGT v0.7.2 (SpriteEditor v0.8.3)' )
		writeln( '////////////////////////////////////////////////////////////////////////////////' )
		writeln( '/*SPRITE*/ {')
		writeln( 'VERSION 0001')
		writeln( '' )
		writeln( '////////////////////////////////////////////////////////////////////////////////' )
		writeln( '// Images...')
		for atlas in self.atlases:
			writeln( 'IMAGE 0x%04X ".\%s"' % ( atlas.id, atlas.name ) )

		writeln( '' )
		writeln( '////////////////////////////////////////////////////////////////////////////////' )
		writeln( '// Modules...')
		writeln( 'MODULES')
		writeln( '{')

		for m in self.moduleCache.values():
			node = m.getAtlasNode()
			writeln( '    MD\t0x%04X\tMD_IMAGE\t%d\t%d\t%d\t%d\t%d' % \
				( m.id, node.root.id, node.x, node.y, node.w, node.h ) )
		writeln( '}')

		writeln( '' )
		writeln( '////////////////////////////////////////////////////////////////////////////////' )
		writeln( '// Frames...')
		for frame in self.frames:
			writeln( 'FRAME "%s"' % frame.name)
			writeln( '{')
			writeln( '    0x%04X' % frame.id )
			for part in frame.parts:
				moduleId = part['module'].id
				( offsetX, offsetY ) = part['offset']
				writeln( '    FM\t0x%04X\t%d\t%d' % ( moduleId, offsetX, offsetY ) )
			writeln( '}')

		writeln( '' )
		writeln( '////////////////////////////////////////////////////////////////////////////////' )
		writeln( '// Anim...')
		for anim in self.animations:
			writeln( 'ANIM "%s"' % anim.name )
			writeln( '{')
			writeln( '    0x%04X' % anim.id )
			for entry in anim.frames:
				frame = entry['frame']
				( offsetX, offsetY ) = entry['offset']
				writeln( '    AF\t0x%04X\t%d\t%d\t%d' % ( frame.id, frame.delay / 10, offsetX, offsetY ) )
			writeln( '}')

		writeln( '' )
		writeln( 'SPRITE_END')
		writeln( '' )
		writeln( '} // SPRITE')
		writeln( '////////////////////////////////////////////////////////////////////////////////' )
		fp.close()


	def getModule( self, psdLayer ):
		m = self.moduleCache.get( psdLayer )		
		if m: return m
		for l1, m1 in self.moduleCache.items():
			if compare_layer_image( psdLayer, l1 ):
				return m1
		m = AnimModule( psdLayer )
		self.moduleCache[ psdLayer ] = m
		m.id = self.currentModuleId + 0x1000
		self.currentModuleId += 1
		return m

	def loadFolder( self, path ):
		pass

	def loadPSD( self, path ):
		image = PSDImage.load( path )
		#meta data
		ox = 0
		oy = 0
		bx0 ,	by0 ,	bx1 ,	by1 = image.bbox
		mani = get_mani( image )
		# print(mani)
		layers = extract_leaf_layers ( image )
		layerModifyDict = {}
		outputLayers = []
		#1. extract meta data:  X/Y axis,  output bound box
		for l in layers:
			stat = get_mlst(l)
			# print(stat, l.name)
			layerModifyDict[ l ] = stat
			name = l.name.encode( 'utf-8' )
			if name == '@axis-x': 
				x0, y0, x1, y1 = l.bbox
				oy = y0
			elif name == '@axis-y': 
				x0, y0, x1, y1 = l.bbox
				ox = x0
			elif name == '@output': 
				bx0 ,	by0 ,	bx1 ,	by1 = l.bbox
			elif not ( name and name[0] == '@' ):
				outputLayers.append( l )
		#2. foreach frame: 
		#      find valid layer (visible & inside output bbox)
		#      find in cache ( using hash/ direct comparison )
		#      if not in cache, add new one
		# for l in layers:
		anim = Anim()
		# print(mani)
		frameDelays = {}
		for data in mani['FrIn']:
			frameDelays[ data['FrID'] ] = data[ 'FrDl' ]

		frameList = mani['FSts'][0]['FsFr']
		index = 0
		layerStates = {}
		outputLayers.reverse()
		for l in outputLayers:
			x0 = 0
			y0 = 0
			visible = l.visible
			states = {}
			for mod in layerModifyDict[l]['LaSt']:
				fid =  mod['FrLs'][0]
				ofst = mod.get('Ofst', None)
				if ofst:
					x0 = ofst['Hrzn']
					y0 = ofst['Vrtc']
				visible = mod.get('enab', visible)
				states[ fid ] = ( visible, x0, y0 )
			layerStates[ l ] = states

		for fid in frameList:
			frame = AnimFrame()
			frame.delay = frameDelays.get( fid, 0 )
			frame._fid = fid
			for l in outputLayers:
				#find modify state
				layerModify = None
				for s in layerModifyDict[l]['LaSt']:
					if s['FrLs'][0] == fid: 
						layerModify = s
						break
				# #check meta
				# if l.name[0] == '@' : continue
				states = layerStates[l]
				#check enabled
				visible, offx, offy = states[ fid ]
				if not visible: continue
				#check inside bbox				
					
				x0, y0 ,x1 ,y1 = l.bbox
				if x0 + offx <= bx0: continue
				if y0 + offy <= by0: continue
				if x1 + offx >= bx1: continue
				if y1 + offy >= by1: continue
				m = self.getModule( l )
				x = x0 - ox + offx 
				y = y0 - oy + offy
				frame.addModule( m, x, y )
			anim.addFrame( frame, 0, 0 )
			self.addFrame( frame )
		self.addAnim( anim )
		n,ext = splitext( basename( path ) )
		anim.name = n

# proj = AnimProject()
# proj.loadPSD( 'attack.psd' )
# proj.loadPSD( 'shout.psd' )
# proj.loadPSD( 'fall.psd' )
# proj.loadPSD( 'idle.psd' )
# proj.loadPSD( 'walk.psd' )
# # proj.loadPSD( 'test.psd' )

# proj.saveAurora( 'output', ( 90, 90 ) )

