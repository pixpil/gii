from psd_tools import PSDImage, Group, Layer
from .psd_tools_helper import extract_leaf_layers, LayerProxy

from PIL import Image

from .PSDDeckPackProject import *
from .NormalMapHelper import makeNormalMap
from .MetaTag import parseMetaTag

import math

def isEmptyLayer( layer ):
	lx0, ly0, lx1, ly1 = layer.bbox
	if lx0 == lx1 and ly0 == ly1: return True
	return False

def clamp( x, a, b ):
	return max( a, min( b, x ) )

def getArray( l, idx, default = None ):
	if idx < 0: return default
	if idx >= len( l ): return default
	v = l[ idx ]
	if v is None: return default
	return v

def getArrayI( l, idx, default = None ):
	v = getArray( l, idx, default )
	if v == None: return v
	return int( v )

def getArrayF( l, idx, default = None ):
	v = getArray( l, idx, default )
	if v == None: return v
	return float( v )

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
class MQuadDeckPart( DeckPart ):
	def __init__( self, parentItem, psdLayer ):
		super( MQuadDeckPart, self ).__init__( parentItem, psdLayer )
		self.meshes = []
		self.globalMeshes = []
		layerName = psdLayer.name
		meta = parseMetaTag( layerName )
		if meta:
			tags = meta[ 'tags' ]
		else:
			tags = {}

		self.foldMode = 'auto'
		self.altOffset = 0

		if 'FOLD' in tags:
			self.foldMode = 'fold'
			args = tags[ 'FOLD' ]
			self.foldPos  = getArrayI( args, 0, 0 )
		
		elif 'SLOPE' in tags:
			self.foldMode = 'slope'
			args = tags [ 'SLOPE' ]
			self.slopeHeight  = getArrayF( args, 0, 50 )
			self.slopeSmoothStepTop    = getArrayI( args, 1, None )
			self.slopeSmoothStepBottom = getArrayI( args, 2, None )

		elif 'FLOOR' in tags or 'F' in tags:
			self.foldMode = 'floor'

		elif 'WALL' in tags or 'W' in tags:
			self.foldMode = 'wall'

		if 'OFF' in tags:
			args = tags[ 'OFF' ]
			self.rectOffset = ( getArrayF( args, 0, 0 ), getArrayF( args, 1, 0 ), getArrayF( args, 2, 0 ) )
		else:
			self.rectOffset = ( 0,0,0 )

		if 'YZ' in tags:
			args = tags[ 'YZ' ]
			y = getArrayF( args, 0, 0 )
			z = getArrayF( args, 1, y )
			self.rectOffset = ( self.rectOffset[0], y, z )

		if 'XY' in tags:
			args = tags[ 'XY' ]
			x = getArrayF( args, 0, 0 )
			y = getArrayF( args, 1, x )
			self.rectOffset = ( x, y, self.rectOffset[2] )

		if 'XZ' in tags:
			args = tags[ 'XZ' ]
			x = getArrayF( args, 0, 0 )
			z = getArrayF( args, 1, x )
			self.rectOffset = ( x, self.rectOffset[1], z )

		if 'ALT' in tags:
			args = tags[ 'ALT' ]
			self.altitude = getArrayF( args, 0, 0 )
		else:
			self.altitude = None

		if 'NSCL' in tags:
			args = tags[ 'NSCL' ]
			self.normalScale = getArrayF( args, 0, parentItem.normalScale )
		else:
			self.normalScale = parentItem.normalScale

		if 'ROT' in tags:
			args = tags[ 'ROT' ]
			self.rectRotation = ( getArrayF( args, 0, 0 ), getArrayF( args, 1, 0 ), getArrayF( args, 2, 0 ) )
		else:
			self.rectRotation = None


	def getImage( self, imgSet ):
		if imgSet == 'normal':
			return self.getNormalMap()
		else:
			return self.getTextureMap()
	
	def getTextureMap( self ):
		return self.getRawImage()

	def getNormalMap( self ):
		if self.imgNormal:
			return self.imgNormal
		else:
			return self.getTextureMap()

	def onBuild( self, project ):
		foldMode = self.foldMode
		concave  = False
		
		( w, h ) = self.getSize()
		( x, y ) = self.getOffset()

		(rectOffX, rectOffY, rectOffZ) = self.rectOffset

		localGuideTopFace = h
		if foldMode == 'auto':
			concave = False
			guideTopFace = project.getOption( 'global-guide-top-face', 0 )
			localGuideTopFace = clamp( guideTopFace - y, 0, h )

		elif foldMode == 'fold':
			foldPos = self.foldPos
			if foldPos < 0: 
				concave = True
				localGuideTopFace = clamp( - foldPos , 0, h )
			else:
				concave = False
				localGuideTopFace = clamp( h - foldPos , 0, h )

		elif foldMode == 'slope':
			concave = False
			localGuideTopFace = 0

		elif foldMode == 'wall':
			concave = False
			localGuideTopFace = 0

		elif foldMode == 'floor':
			concave = False
			localGuideTopFace = h

		#build normal
		px0, py0, px1, py1 = self.parentItem.aabb
		offx = self.getLeft() - px0
		offy = self.getTop()  - py0
		tex = self.getTextureMap()
		normalOption = {
			'guide-top-face'      : localGuideTopFace,
			'concave'             : concave,
			'height_guide'        : self.parentItem.heightGuideImage,
			'height_guide_offset' : ( offx, offy ),
			'height_guide_opacity': 1.0,
			'normal_scale'        : self.normalScale,
			'global_rotation'     : self.rectRotation,
			'slope'               : None,
		}
		if foldMode == 'slope' :
			inclination = math.atan2( self.slopeHeight, h ) / math.pi * 180.0
			smooth1 = self.slopeSmoothStepTop
			smooth2 = self.slopeSmoothStepBottom
			if smooth1 == None:	smooth1 = min( h/8, 10 )
			if smooth2 == None:	smooth2 = min( h/8, 10 )
			normalOption['slope'] = \
				( inclination, smooth1, smooth2 )

		self.imgNormal    = makeNormalMap( tex, normalOption )
		self.guideTopFace = localGuideTopFace

		#build mesh
		#format: x,y,z/ u,v /color

		#SLOPE MODE
		if foldMode == 'slope':
			hh = h
			x0 = 0
			y0 = 0
			z0 = 0
			x1 = w
			y1 = self.slopeHeight
			z1 = z0 - hh + self.slopeHeight
			u0 = 0
			v0 = 0
			u1 = 1
			v1 = hh/h
			quadWall = {
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
			self.meshes.append( quadWall )

		else:
			#Classic F/W 2Face Mode
			hh = h - localGuideTopFace
			if concave:
				if localGuideTopFace < h: #TOP
					x0 = 0
					y0 = 0
					z0 = 0
					x1 = w
					# y1 = h - localGuideTopFace
					# z1 = -( y1 - y0 )
					y1 = y0
					z1 = - hh
					u0 = 0
					v0 = 0
					u1 = 1
					v1 = float( hh )/h
					quadWall = {
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
					self.meshes.append( quadWall )

				if localGuideTopFace > 0: #WALL
					x0 = 0
					y0 = 0
					z0 = -hh
					# y0 = h - localGuideTopFace
					# z0 = -y0
					x1 = w
					y1 = localGuideTopFace
					z1 = z0
					# y1 = h
					# z1 = -y0
					u0 = 0
					v0 = 1
					u1 = 1
					v1 = float(hh) / h
					quadTop = {
						'verts' : [
							[ x0,y0,z0 ], 
							[ x1,y0,z0 ], 
							[ x1,y1,z1 ], 
							[ x0,y1,z1 ]
						],
						'uv' : [
							[ u0,v1 ],
							[ u1,v1 ],
							[ u1,v0 ],
							[ u0,v0 ],
						]
					}
					self.meshes.append( quadTop )

			else:
				if localGuideTopFace < h: #WALL
					x0 = 0
					y0 = 0
					z0 = 0
					x1 = w
					y1 = hh
					z1 = 0
					u0 = 0
					v0 = 0
					u1 = 1
					v1 = float(hh)/h
					quadWall = {
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
					self.meshes.append( quadWall )

				if localGuideTopFace > 0: #TOP
					x0 = 0
					y0 = hh
					z0 = 0
					x1 = w
					# y1 = h
					# z1 = -( y1 - y0 )
					y1 = y0
					z1 = z0 - localGuideTopFace
					u0 = 0
					v0 = float(hh) / h
					u1 = 1
					v1 = 1
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

		if self.rectRotation:
			(rx, ry, rz) = self.rectRotation
			self.applyLocalMeshRotation( rx, ry, rz )
		self.applyLocalMeshOffset( rectOffX, rectOffY, rectOffZ )

	def postBuild( self ):
		self.buildAtlasUV()

	def updateGlobalMesh( self, globalLeft, globalBottom ):
		offy = globalBottom - self.getBottom()
		offx = globalLeft   - self.getLeft()
		offz = 0
		self.globalMeshes = []
		for mesh in self.meshes:
			gmesh = copy.deepcopy( mesh )
			self.globalMeshes.append( gmesh )
		if self.altitude != None :
			diff = offy - self.altitude
			offy = offy - diff
			offz = -diff
		self.applyGlobalMeshOffset( -offx, offy, offz )
		
	def applyGlobalMeshOffset( self, dx, dy, dz ):
		for gmesh in self.globalMeshes:
			for vert in gmesh['verts']:
				vert[ 0 ] += dx
				vert[ 1 ] += dy
				vert[ 2 ] += dz

	def applyLocalMeshRotation( self, rx, ry, rz ):
		for mesh in self.meshes:
			for vert in mesh['verts']:
				x = vert[ 0 ]
				y = vert[ 1 ]
				z = vert[ 2 ]
				dx = 0
				dy = 0
				dz = 0
				a  = x * math.tan( ry/180.0*math.pi )
				a1 = y * math.tan( rx/180.0*math.pi )
				a2 = x * math.tan( rz/180.0*math.pi )
				dz -= a
				dy -= a
				dz -= a1
				dy -= a1
				dz -= a2
				dy -= a2
				#ignore rz for now
				# vert[ 0 ] += dx
				vert[ 1 ] += dy
				vert[ 2 ] += dz


	def applyLocalMeshOffset( self, dx, dy, dz ):
		for mesh in self.meshes:
			for vert in mesh['verts']:
				vert[ 0 ] += dx
				vert[ 1 ] += dy
				vert[ 2 ] += dz

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

	def getGlobalMeshes( self, skew = True ):
		if skew:
			skewedMeshes = []
			for mesh in self.globalMeshes:
				skewed = copy.deepcopy( mesh )
				for vert in skewed[ 'verts' ]:
					z = vert[ 2 ]
					vert[ 1 ] += (-z)
				skewedMeshes.append( skewed )
			return skewedMeshes
		else:
			return self.globalMeshes


##----------------------------------------------------------------##
class MQuadDeckItem(DeckItem):
	def __init__( self, name, partLayers, variationName = None  ):
		super( MQuadDeckItem, self ).__init__()
		meta = parseMetaTag( name )
		if meta:
			self.name = meta['name']
		else:
			meta = {}
			print(name)
			self.name = name
		if variationName:
			self.name = name = self.name + '/' + variationName
		self.rawName = name
		self.heightGuides = []
		self.heightGuideImage = None

		tags = meta.get( 'tags', {} )
		if 'NSCL' in tags:
			args = tags[ 'NSCL' ]
			self.normalScale = getArrayF( args, 0,  0.5 )
		else:
			self.normalScale = 0.5

		if 'OFF' in tags:
			args = tags[ 'OFF' ]
			self.offset = ( getArrayF( args, 0, 0 ), getArrayF( args, 1, 0 ), getArrayF( args, 2, 0 ) )
		else:
			self.offset = None

		for layer in reversed( partLayers ):
			layerName = layer.name
			if layerName.startswith( '//' ): continue
			if layerName.startswith( '@' ) :
				if layerName.startswith( '@hmap' ):
					#normal guide
					self.heightGuides.append( layer )
				continue
			if isEmptyLayer( layer ): continue
			part = self.addPart( layer )

	def createPart( self, layer ):
		return MQuadDeckPart( self, layer )

	def getData( self ):
		meshes = []
		for part in self.parts:
			meshes += part.getGlobalMeshes()
		return {
			'name'  : self.name,
			'meshes': meshes,
			'type'  : 'deck2d.mquad'
		}

	def buildAABB( self ):
		bottom = 0
		right  = 0
		top    = 0xffffffff #huge number
		left   = 0xffffffff #huge number
		for part in self.parts:
			bottom = max( bottom, part.getBottom() )
			left   = min( left,   part.getLeft()   )
			right  = max( right,  part.getRight()  )
			top    = min( top,    part.getTop()    )
		self.aabb = ( left, top, right, bottom )
		self.width = right - left
		self.height = bottom - top

	def getAABB( self ):
		return self.aabb

	def getSize( self ):
		left, top, right, bottom = self.aabb		
		return ( right - left, bottom - top )

	def onBuild( self, project ):
		self.buildAABB()
		left, top, right, bottom = self.aabb		
		self.buildHeightGuide( left, top, right, bottom )
		
		for part in self.parts:
			part.onBuild( project )

		#move mesh
		for part in self.parts:
			part.updateGlobalMesh( left, bottom )

		self.buildMeshAABB()

	
	def buildMeshAABB( self ):
		x0 =  100000000
		y0 =  100000000
		z0 =  100000000
		x1 = -100000000
		y1 = -100000000
		z1 = -100000000
		for part in self.parts:
			for quad in part.meshes:
				for vert in quad[ 'verts' ]:
					x,y,z = vert[0],vert[1],vert[2]
					x0 = min( x, x0 )
					y0 = min( y, y0 )
					z0 = min( z, z0 )
					x1 = max( x, x1 )
					y1 = max( y, y1 )
					z1 = max( z, z1 )
		self.meshAABB = ( x0,y0,z0, x1,y1,z1 )

	def getMeshAABB( self ):
		return self.meshAABB

	def buildHeightGuide( self, x0, y0, x1, y1 ):
		if not self.heightGuides: return
		w, h = x1-x0, y1-y0
		self.heightGuideImage = None
		targetImage = Image.new( "RGBA", (w,h), (0,0,0,0) )
		for layer in reversed(self.heightGuides):
			lx0, ly0, lx1, ly1 = layer.bbox
			if lx0 == lx1 and ly0 == ly1: continue
			image = layer.as_PIL()
			px, py = lx0 - x0, ly0 - y0
			tmpLayer = Image.new( "RGBA", (w,h), (0,0,0,0) )
			tmpLayer.paste( image, (px, py) )
			targetImage = Image.blend( targetImage, tmpLayer, layer.opacity/255.0 )

		self.heightGuideImage = targetImage

	def postBuild( self, project ):
		if self.offset:
			ox, oy, oz = self.offset
			for part in self.parts:
				part.applyGlobalMeshOffset( ox, oy, oz )
		for part in self.parts:
			part.postBuild()

	def applyGlobalMeshOffset( self, dx, dy, dz ):
		for part in self.parts:
			part.applyGlobalMeshOffset( dx, dy, dz )

##----------------------------------------------------------------##
class MQuadDeckProcessor( DeckProcessor ):
	def onLoadImage( self, psdImage ):
		#root layers
		for layer in psdImage.layers:
			if not isinstance( layer, Group ):
				layerName = layer.name
				if layerName == '@guide-top-face':
					x1,y1,x2,y2 = layer.bbox
					self.project.setOption ( 'global-guide-top-face', y1 )
					return

	def acceptLayer( self, psdLayer, metaInfo, fallback ):
		tags = metaInfo[ 'tags' ]
		if fallback:
			return True
		else:
			return 'MQ' in tags

	def processLayer( self, psdLayer, metaInfo, namespace ):
		project = self.project
		tags = metaInfo[ 'tags' ]
		partLayers = []
		if isinstance( psdLayer, Group ):
			partLayers = extract_leaf_layers( psdLayer )
		else:
			partLayers = [ psdLayer ]
		if partLayers:
			name = metaInfo[ 'name' ]
			fullname = namespace and ( namespace + '.' + name ) or name
			deck = MQuadDeckItem( fullname, partLayers )
			project.addDeckItem( deck )

##----------------------------------------------------------------##
registerDeckProcessor( 'mquad', MQuadDeckProcessor )


##----------------------------------------------------------------##
if __name__ == '__main__':
	from . import PSDDeckPackTest
	