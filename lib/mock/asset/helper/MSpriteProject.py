# -*- coding: utf-8 -*-
import os.path
import io
from psd_tools import PSDImage, Layer
from psd_tools.decoder.actions import Boolean, Integer, List, Descriptor
from psd_tools.constants import ImageResourceID
from psd_tools.utils import read_fmt, read_unicode_string, read_pascal_string

import re

from util.AsepriteFile import *
import util.ImageProcessPreset

import logging
import json

from PIL import ImageChops, Image, ImageStat
from util.ImageTool.UniqueImageSet import UniqueImageSet, affirmImgHash

if __name__ != '__main__':
	from .atlas2 import AtlasGenerator, Img
	from .psd_tools_helper import *
else:
	from atlas2 import AtlasGenerator, Img
	from psd_tools_helper import *

def isAseLayerCommented( layer ):
	while layer:
		if layer.name.startswith( '//' ): return True
		layer = layer.parent
	return False

def getAseLayerFeature( layer ):
	if hasattr( layer, '__MSpriteFeature' ):
		return layer.__MSpriteFeature
	parent = layer.parent
	
	if parent:
		parentFeature = getAseLayerFeature( parent )
	else:
		parentFeature = False

	layerName = layer.name_stripped
	if layerName.startswith( '#' ):
		mo = re.search( '#([\w_\-:]+)', layerName )
		if mo:
			featureName = mo.group( 1 )
			if parentFeature:
				featureName = parentFeature + '.' + featureName
			layer.__MSpriteFeature = featureName
			return featureName
	else:
		layer.__MSpriteFeature = parentFeature
		return parentFeature


def saveJSON( data, path, **option ):
	outputString = json.dumps( data , 
			indent    = option.get( 'indent' ,2 ),
			sort_keys = option.get( 'sort_keys', True ),
			ensure_ascii=False
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


def mulTuple( t, scl ):
	return tuple( [ n * scl for n in t ] )

##----------------------------------------------------------------##
def collectAnchors( cel, ox, oy ):
	cel = cel.getRealCel()
	if not cel.bbox: return None
	anchors = []
	img = cel.getImage()
	bx0, by0, bx1, by1 = cel.bbox
	pixels = img.load()
	for y in range( by0, by1 ):
		for x in range( bx0, bx1 ):
			(r, g, b, a) = pixels[ x, y ]
			if a == 0: continue
			hexcolor = '#%02x%02x%02x' % ( r,g,b )
			anchors.append( [x+cel.x -ox, y+cel.y -oy, hexcolor] )
	return anchors

##----------------------------------------------------------------##
class LayerPreProcessor(object):
	pass


##----------------------------------------------------------------##
class LayerImg(Img): #	
	def getImage(self, imgSet = None):
		return self.src.getImage()

##----------------------------------------------------------------##
class AnimFrame(object):
	def __init__( self ):
		self.parts = []
		self.meta  = {}
		self.name  = "null"

	def addModule( self, m, offsetX, offsetY ):
		self.parts.append( { 'module':m, 'offset': (offsetX, offsetY) } )

	def setMetaData( self, key, value ):
		self.meta[ key ] = value

	def applyScale( self, scale ):
		self.scale = scale
		for part in self.parts:
			part[ 'offset' ] = mulTuple( part[ 'offset' ], scale )
			part[ 'module' ].applyScale( scale )

##----------------------------------------------------------------##
class AnimModule(object):
	def __init__( self, subImg ):
		self.subImg = subImg
		self.feature = None
		self.scale = 1
		self.scaled = False
		self.meta = {}
		subImg.getImage()
		self.padX = subImg.padX
		self.padY = subImg.padY

	def getMetaData( self, key, default ):
		return self.meta.get( key, default )

	def setMetaData( self, key, value ):
		self.meta[ key ] = value

	def getImageMetaData( self, key, default ):
		return self.subImg.getMetaData( key, default )

	def applyScale( self, scale ):
		if self.scaled: return
		self.scaled = True
		self.scale = scale
		self.subImg.applyScale( scale )

##----------------------------------------------------------------##
class SubImg(object):
	def __init__( self ):
		self.scaled = False
		self.w = 0
		self.h = 0
		self.img = None
		self.imgInfo = None
		self.scale = 1
		self.meta = {}

	def getMetaData( self, key, default ):
		return self.meta.get( key, default )

	def setMetaData( self, key, value ):
		self.meta[ key ] = value

	def getSize( self ):
		return ( self.w, self.h )

	def getImage( self ):
		return self.img

	def getImageSourceData( self ):
		return None

	def getAtlasNode( self ):
		if not hasattr( self.imgInfo, 'node' ): #image too large??????
			return None
		else:
			return self.imgInfo.node

	def applyScale( self, scale ):
		if self.scaled: return
		self.scaled = True
		self.scale = scale
		self.w = int( self.w * scale )
		self.h = int( self.h * scale )

##----------------------------------------------------------------##
class SubImgPsdLayer( SubImg) :
	def __init__( self, psdLayer ):
		super( SubImgPsdLayer, self ).__init__()
		self._layer = psdLayer
		x1,y1,x2,y2 = psdLayer.bbox
		self.w = x2-x1
		self.h = y2-y1
		self.padX = 0
		self.padY = 0

	def getImage( self ):
		if self.img: return self.img
		self.img = self._layer.as_PIL()
		( w, h ) = self.img.size
		scale = self.scale
		if scale != 1:
			self.img = self.img.resize( 
				( int(w * scale), int(h * scale) ), 
				Image.BILINEAR 
			)
		return self.img

	def getImageSourceData( self ):
		return self._layer
	
##----------------------------------------------------------------##
class SubImgASECel( SubImg ):
	def __init__( self, cel, options = None ):
		super( SubImgASECel, self ).__init__()
		self.options = options
		self._cel = cel
		x1,y1,x2,y2 = cel.bbox
		self.w = x2-x1
		self.h = y2-y1
		self.padX = 0
		self.padY = 0
		# print self.w, self.h

	def getImageSourceData( sel ):
		return self._cel

	def getImage( self ):
		if self.img: return self.img
		self.img = self._cel.getImage()
		( w, h ) = self.img.size
		scale = self.scale
		if scale != 1:
			self.img = self.img.resize( w * scale, h * scale )
		if self.options:
			if '/noise' in self.options:
				self.img = util.ImageProcessPreset.Noise( self.img )

			if '/glow' in self.options:
				pad = 5
				self.img = util.ImageProcessPreset.CropRelative( self.img, ( pad,pad,pad,pad ) )
				stat = ImageStat.Stat( self.img )
				self.setMetaData( 'glow_sum', stat.sum[3] )
				self.img = util.ImageProcessPreset.Glow( self.img, 5, 1 )
				self.w = w + pad*2
				self.h = h + pad*2
				self.padX = pad
				self.padY = pad

			if '/glow_lite' in self.options:
				pad = 5
				self.img = util.ImageProcessPreset.CropRelative( self.img, ( pad,pad,pad,pad ) )
				stat = ImageStat.Stat( self.img )
				self.setMetaData( 'glow_sum', stat.sum[3] )
				self.img = util.ImageProcessPreset.Glow( self.img, 2, 1 )
				self.w = w + pad*2
				self.h = h + pad*2
				self.padX = pad
				self.padY = pad

		return self.img
		

##----------------------------------------------------------------##
class Anim(object):
	def __init__(self):
		self.scale = 1
		self.name = "null"
		self.srcType  = "psd"
		self.frames = []
		self.ox = 0
		self.oy = 0
		self.deprecated = False

	def addFrame( self, frame, offsetX, offsetY ):
		self.frames.append( { 'frame':frame, 'offset': (offsetX, offsetY) } )

	def setOrigin( self, x, y ):
		self.ox = x
		self.oy = y

	def getOrigin( self ):
		return self.ox, self.oy

	def applyScale( self, scale ):
		self.scale = scale
		if scale == 1: return
		self.ox = self.ox * scale
		self.oy = self.oy * scale
		for frame in self.frames:
			frame[ 'frame' ].applyScale( scale )
			frame[ 'offset' ] = mulTuple( frame[ 'offset' ], scale )

##----------------------------------------------------------------##
class MSpriteProject(object):
	def __init__(self):		
		self.modules = []
		self.animations = []
		self.frames = []
		self.moduleCache = {}
		self.subImgCache = {}
		self.moduleSubImgCache = {}
		self.featureNames = {}
		self.currentModuleId = 0
		self.currentFrameId = 0
		self.currentAnimId = 0
		self.currentFeatureId = 0

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
		for subImg in self.subImgCache.values():
			( w, h ) = subImg.getSize()
			img = LayerImg ( '', w, h, (0, 0, w, h) )	
			img.src = subImg
			img.node = None
			infos.append( img )
			subImg.imgInfo = img
		return infos

	def generateAtlas( self, atlasPath, atlasSize, **kwargs ):
		#5. pack all bitmap in cache into atlas
		prefix='output' #TODO: use real output name
		kwargs['spacing'] = 1

		imageInfos = self.generateImagesInfo()

		atlasGen = AtlasGenerator( prefix, atlasSize, **kwargs )
		atlas = atlasGen.generateOneAtlas( imageInfos, [] )
		
		atlas.name = atlasPath
		atlasGen.paintAtlas( atlas, atlas.name )
		atlas.id = 0

		return atlas

	def addFeature( self, featureName ):
		if self.featureNames.get( featureName ): return
		self.currentFeatureId += 1
		self.featureNames[ featureName ] = self.currentFeatureId
		return self.currentFeatureId

	def affirmFeature( self, featureName ):
		id = self.getFeature( featureName )
		if id != None: return id
		return self.addFeature( featureName )

	def getFeature( self, featureName ):
		if not featureName: return 0
		return self.featureNames.get( featureName, None )

	def save( self, atlasPath, jsonPath, atlasSize = (4096,4096) ):
		atlases = [ self.generateAtlas( atlasPath, atlasSize, bleeding = True ) ]
		atlasData  = {}
		moduleData = {}
		frameData  = {}
		animData   = {}
		featureData = []
		#atlas
		for atlas in atlases:
			atlasData[ str( atlas.id ) ] = atlas.name

		#modules
		for m in self.moduleCache.values():
			node = m.subImg.getAtlasNode()			
			moduleData[ str( m.id ) ] = {
				'atlas' : str( node.root.id ),
				'rect'  : node.getRect(),
				'feature' : m.feature
			}
			
		#frames
		for frame in self.frames:
			parts = []
			for part in frame.parts:
				moduleId = part['module'].id
				( offsetX, offsetY ) = part['offset']
				parts.append( [ str(moduleId), offsetX, offsetY  ] )
			frameData[ str( frame.id ) ] = {
				'name'  : frame.name,
				'parts' : parts,
				'meta'  : frame.meta
			}
		
		#anims
		for anim in self.animations:
			seq = []
			for entry in anim.frames:
				frame = entry['frame']
				( offsetX, offsetY ) = entry['offset']
				seq.append(
					[ str( frame.id ), frame.delay, offsetX, offsetY ]
				)
			animData[ str( anim.id ) ] = {
				'name' :anim.name,
				'seq'  :seq,
				'src_type':anim.srcType,
				'deprecated': anim.deprecated
			}

		for name, id in self.featureNames.items():
			featureData.append( {
				'id': id,
				'name': name,
				} )

		output = {
			'atlases' : atlasData,
			'modules' : moduleData,
			'frames'  : frameData,
			'anims'   : animData,
			'features' : featureData
		}

		saveJSON( output, jsonPath )
		return output

	def addModule( self, subImg ):
		m = AnimModule( subImg )
		m.id = self.currentModuleId + 0x1000
		self.currentModuleId += 1
		return m

	def getModuleByPsdLayer( self, psdLayer, scale ):
		# print( 'getting module', psdLayer )
		m = self.moduleCache.get( psdLayer )
		if m: return m
		subImg = None
		for l1, img1 in self.subImgCache.items():
			if not isinstance( l1, Layer ): continue
			if scale == img1.scale:
				if compare_layer_image( psdLayer, l1 ):
					subImg = img1
					break
		if not subImg:
			subImg = SubImgPsdLayer( psdLayer )
			self.subImgCache[ psdLayer ] = subImg
		
		subImg.scale = scale
		m = self.addModule( subImg )
		m.feature = psdLayer._featureId
		self.moduleCache[ psdLayer ] = m
		return m

	def getModuleByASECel( self, cel, options = None ):
		m = self.moduleCache.get( cel )
		if m : return m
		return self.createModuleFromASECel( cel, options )

	def createModuleFromASECel( self, cel, options ):
		if not cel.bbox: return None
		rcel = cel.getRealCel()
		layerName = rcel.layer.name_stripped

		subImg = None
		doc0 = cel.getParentDocument()
		img0 = cel.getImage()
		
		if not options: 		
			subImg = self.moduleSubImgCache.get( affirmImgHash( img0 ), None )

		if not subImg:
			subImg = SubImgASECel( cel, options )
			self.subImgCache[ cel ] = subImg
			self.moduleSubImgCache[ affirmImgHash( img0 ) ] = subImg
		
		m = self.addModule( subImg )
		m.feature = 0
		self.moduleCache[ cel ] = m
		return m

	def loadFolder( self, path ):
		self.imageCache = UniqueImageSet()
		for fileName in os.listdir( path ):
			fullPath = path + '/' + fileName
			name, ext = os.path.splitext( fileName )
			if ext == '.psd':
				self.loadPSD( fullPath )
			elif ext in ['.ase', '.aseprite']:
				self.loadASE( fullPath )
		self.imageCache = None

	def loadASE( self, path ):
		doc = ASEDocument()
		doc.load( path, image_cache = self.imageCache )
		if not doc.frames: return

		anim = Anim()
		anim.srcType = 'ase'

		layer2Anchor = {}

		ox, oy = 0, 0

		flist = []

		frameInUse = []
		for i in range( len( doc.frames ) + 1 ):
			frameInUse.append( 0 )

		#split tag into sub animations
		for tagData in doc.tags:
			f0, f1 = tagData.frameFrom, tagData.frameTo
			name = tagData.name
			if name.startswith( '//' ): 
				for i in range( f0, f1 + 1 ):
					if frameInUse[ i ] == 0:
						frameInUse[ i ] = -1
			else:
				for i in range( f0, f1 + 1 ):
					frameInUse[ i ] = 1

		for fi in range ( len( doc.frames )):
			frameData = doc.frames[ fi ]
			skipFrame = frameInUse[ fi ] < 0

			anchorData = {}
			frame = AnimFrame()
			frame.setMetaData( 'anchors', anchorData )
			flist.append( frame )

			frame.delay = float(frameData.duration)/1000.0
			for cel in frameData.cels:
				rcel = cel.getRealCel()
				layerName = rcel.layer.name_stripped
				if layerName == '@origin':
					if rcel.bbox:
						bx0, by0, bx1, by1 = rcel.bbox
					else:
						bx0, by0, bx1, by1 = 0,0,0,0
					ox = bx0 + cel.x
					oy = by1 + cel.y
					break
			
			frame.setMetaData( 'origin', [ ox, oy ] )
			totalGlowSum = 0

			if not skipFrame: 
				for cel in frameData.cels:
					rcel = cel.getRealCel()
					layer = rcel.layer
					layerName = layer.name_stripped
					if layer.isBackground(): continue

					if isAseLayerCommented( layer ): 
						continue

					if layerName.startswith( '@' ) : 
						if layerName.startswith( '@anchor' ):
							anchorName = layer2Anchor.get( layer, None )
							if anchorName == None: #affirm anchor
								mo = re.search( '@anchor:(\w+)', layerName )
								if not mo:
									logging.warn( 'invalid @anchor meta tag:' + layerName )
									layer2Anchor[ layer ] = False
								else:
									anchorName = mo.group( 1 )
									layer2Anchor[ layer ] = anchorName
							if anchorName:
								anchorData[ anchorName ] = collectAnchors( cel, ox, oy )
							continue
						else:
							continue

					options = re.findall( '/\w+', layerName )

					m = self.getModuleByASECel( rcel, options )
					if m:
						featureName = getAseLayerFeature( layer )
						if featureName: m.feature = self.affirmFeature( featureName )
						bx0, by0, bx1, by1 = rcel.bbox
						padX = m.padX
						padY = m.padY
						frame.addModule( m, bx0+cel.x -ox - padX, by0+cel.y -oy -padY )
						totalGlowSum += m.getImageMetaData( 'glow_sum', 0 )

			anim.addFrame( frame, 0, 0 )
			self.addFrame( frame )
			frame.setMetaData( 'glow_sum', totalGlowSum )

		self.addAnim( anim )
		animName,ext = os.path.splitext( os.path.basename( path ) )
		anim.name = animName

		#split tag into sub animations
		for tagData in doc.tags:
			f0, f1 = tagData.frameFrom, tagData.frameTo
			name = tagData.name
			deprecated = False

			if name.startswith( '///' ): #deprecated
				deprecated = True
				name = name[ 3: ]

			elif name.startswith( '//' ):
				continue

			subAnim = Anim()
			subAnim.setOrigin( ox, oy )
			subAnim.name = animName + ':' + name
			subAnim.srcType = 'ase'
			for sfid in range( f0, f1 + 1 ):
				frame = flist[ sfid ]
				subAnim.addFrame( frame, 0, 0 )
			subAnim.deprecated = deprecated
			self.addAnim( subAnim )


	def loadPSD( self, path ):
		image = PSDImage.load( path )
		#meta data
		ox = 0
		oy = 0
		globalScale = 1
		bx0 ,	by0 ,	bx1 ,	by1 = image.bbox
		mani = get_mani( image )
		layers   = extract_leaf_layers ( image )
		docFeatures = get_psd_features( image )
		if docFeatures:
			for entry in docFeatures.values():
				self.addFeature( entry['name'] )

		layerModifyDict = {}
		outputLayers = []
		layerFeatures = {}

		#1. extract meta data:  X/Y axis,  output bound box
		for l in layers:
			stat = get_mlst(l)
			# print(stat, l.name)
			layerModifyDict[ l ] = stat
			name = l.name
			if name == '@axis-x': 
				x0, y0, x1, y1 = l.bbox
				oy = y0
			elif name == '@axis-y': 
				x0, y0, x1, y1 = l.bbox
				ox = x0
			elif name == '@output': 
				bx0 ,	by0 ,	bx1 ,	by1 = l.bbox

			elif name.startswith( '@scale' ): 
				mo = re.search( '@scale\s*\(\s*([0-9.]*)\s*\)', name )
				if mo:
					_scl = float( mo.group( 1 ) )
					if _scl:
						globalScale = _scl
				
			elif not ( name and ( name[0] == '@' or name=='背景' ) ):
				p = l.parent
				while p:
					if p.name == '_RootGroup': break
					layerModifyDict[ p ] = get_mlst(p)
					p = p.parent
				outputLayers.append( l )
		#2. foreach frame: 
		#      find valid layer (visible & inside output bbox)
		#      find in cache ( using hash/ direct comparison )
		#      if not in cache, add new one
		# for l in layers:
		# print 'layer count:', len( outputLayers )
		anim = Anim()
		anim.srcType = 'psd'

		frameDelays = {}
		if mani: #single frame
			frameList = mani[b'FSts'][0][b'FsFr']
			activeFrame = mani[b'FSts'][0][b'AFrm']
			for data in mani[b'FrIn']:
				frameDelays[ data[b'FrID'] ] = 0.1
				# frameDelays[ data['FrID'] ] = data[ 'FrDl' ]
		else:
			frameList = [0]
			frameDelays[0] = 0.1
			activeFrame = 0


		index = 0
		layerStates = {}
		outputLayers.reverse()
		for l in outputLayers:
			# print 'L:', l.name.encode('utf-8'), l.visible
			x0 = 0
			y0 = 0
			visible = True
			states = {}
			modData = layerModifyDict[l]
			if modData:
				#find initial visiblity

				#calculate visiblity for each frame
				for mod in modData[b'LaSt']:
					fid =  mod[b'FrLs'][0]
					ofst = mod.get(b'Ofst', None)
					if ofst:
						x0 = ofst[b'Hrzn']
						y0 = ofst[b'Vrtc']
					visible = mod.get(b'enab', visible)
					states[ fid ] = ( visible, x0, y0 )
			else:
				states[0] = ( l.visible, 0, 0 )

			p = l.parent
			while p:
				if p.name == '_RootGroup': break
				modData = layerModifyDict[p]
				p = p.parent
				if modData:
					for mod in modData[b'LaSt']:
						fid =  mod[b'FrLs'][0]
						ofst = mod.get(b'Ofst', None)
						if ofst:
							x0 = ofst[b'Hrzn']
							y0 = ofst[b'Vrtc']
						else:
							x0 = 0
							y0 = 0
						visible = mod.get(b'enab', visible)
						if states.get( fid, None ):
							( _vis, _x0, _y0 ) = states[ fid ] 
							states[ fid ] = ( _vis and visible, _x0 + x0 , _y0 + y0)
						else:
							states[ fid ] = ( visible, x0, y0 )

			layerStates[ l ] = states
			l._featureId = 0
			if docFeatures:
				localFeatureId = get_layer_feature( l )
				if localFeatureId >= 0:
					fname = docFeatures[ localFeatureId ].get( 'name', None )
					l._featureId = self.getFeature( fname )

		for fid in frameList:
			frame = AnimFrame()
			frame.delay = 0.1
			# frame.delay = frameDelays.get( fid, 0 )
			frame._fid = fid
			for l in outputLayers:
				#find modify state
				layerModify = None
				modData = layerModifyDict[l]
				if modData:
					for mod in modData[b'LaSt']:
						if mod[b'FrLs'][0] == fid: 
							layerModify = mod
							break				
				states = layerStates[l]

				#check enabled
				defaultState = ( l.visible, 0, 0 ) 
				fstate = states.get( fid, defaultState )
				visible, offx, offy = fstate
				name = l.name
				if not visible: continue
				#check inside bbox				
					
				x0, y0 ,x1 ,y1 = l.bbox
				if x0 + offx < bx0:	continue
				if y0 + offy < by0:	continue
				if x1 + offx > bx1:	continue
				if y1 + offy > by1:	continue
				m = self.getModuleByPsdLayer( l, globalScale )
				x = x0 - ox + offx 
				y = y0 - oy + offy
				frame.addModule( m, x, y )
			anim.addFrame( frame, 0, 0 )
			self.addFrame( frame )

		anim.applyScale( globalScale )
		self.addAnim( anim )
		n,ext = os.path.splitext( os.path.basename( path ) )
		anim.name = n

if __name__ == '__main__':
	proj = MSpriteProject()
	# proj.loadFolder( 'test/InsectCrow.msprite' )
	# proj.save( 'test/InsectCrow_data.png', 'test/InsectCrow_data.json' )
	
	# proj.loadFolder( 'test/doors.msprite' )
	# proj.save( 'test/doors.png', 'test/doors.json' )

	# proj.loadFolder( 'test/Slug.msprite' )
	# proj.save( 'test/Slug.png', 'test/Slug.json' )

	# proj.save( 'test/idleW.png', 'test/idleW.json' )

	# proj.loadPSD( 'test/idle_S.psd' )
	# proj.save( 'test/idle_S.png', 'test/idle_S.json' )
	
	# proj.loadFolder( 'test/AnchorTest.msprite' )
	# proj.save( 'test/AnchorTest.png', 'test/AnchorTest.json' )

	# proj.loadFolder( 'test/Monkey.msprite' )
	# proj.save( 'test/Monkey.png', 'test/Monkey.json' )
	
	# proj.loadFolder( 'test/john.msprite' )
	# proj.save( 'test/john.png', 'test/john.json' )

	# proj.loadFolder( 'test/SolomonEye.msprite' )
	# proj.save( 'test/SolomonEye.png', 'test/SolomonEye.json' )

	proj.loadFolder( 'test/simple.msprite' )
	proj.save( 'test/simple.png', 'test/simple.json' )
	
	# print( 'loading' )
	# proj.loadFolder( 'test/Charon.msprite' )
	# print( 'saving' )
	# proj.save( 'test/Charon.png', 'test/Charon.json' )

	# proj.loadFolder( 'test/waitress.msprite' )
	# proj.save( 'test/waitress.png', 'test/waitress.json' )
