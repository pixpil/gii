from PIL import Image
import math
from gameobject.matrix44 import Matrix44
from gameobject.vector3 import Vector3


def calcHeight( r,g,b, a ):
	if a <5: return 0
	h1 = (r * 1.0 + g * 1.0  + b * 1.0)/3/255.0
	# return math.sqrt( h1 )
	# return h1 * h1 * 0.2
	return h1 * 0.3

def calcPixHeight( pix, x,y, heightPix, heightOffset, heightOpacity ):
	r,g,b,a = pix[ x, y ]
	# if a < 5: return 0
	h = (r/255.0 + g/255.0  + b/255.0) / 3.0
	if not heightPix is None:
		ox, oy = heightOffset
		r,g,b,a = heightPix[ x + ox, y + oy ]
		k = heightOpacity * a/255.0
		h = ( h * ( 1.0 - k ) +  r/255.0 * k )
	return h 

def calcNormal( pix, x, y, w, h, heightPix = None, heightOffset = None, heightOpacity = 0.7, normalScale = 0.5 ):
	r,g,b,a = pix[ x, y ]
	if a == 0:
		return 0, 0, 0, 0
	
	h0 = calcPixHeight( pix, x,y, heightPix, heightOffset, heightOpacity )
	if h0 < 0.03:
		return 0, 0, 0.5, h0

	h1 = 0
	#left
	fx, fy = 0, 0
	for r in range( 1, 3 ):
		if x >= r:
			xx, yy = x - r, y
			h1 = calcPixHeight( pix, xx, yy, heightPix, heightOffset, heightOpacity )
			# r1,g1,b1,a1 = pix[ xx, yy ]
			# h1 = calcHeight( r1, g1, b1, a1 )
			fx = fx + ( h1 - h0 ) * normalScale/r/r

		if x < w - r:
			xx, yy = x + r, y
			h1 = calcPixHeight( pix, xx, yy, heightPix, heightOffset, heightOpacity )
			# r1,g1,b1,a1 = pix[ xx, yy ]
			# h1 = calcHeight( r1, g1, b1, a1 )
			fx = fx + ( h1 - h0 ) * -normalScale/r/r

		if y > r:
			xx, yy = x, y  - r
			h1 = calcPixHeight( pix, xx, yy, heightPix, heightOffset, heightOpacity )
			# r1,g1,b1,a1 = pix[ xx, yy ]
			# h1 = calcHeight( r1, g1, b1, a1 )
			fy = fy + ( h1 - h0 ) * -normalScale/r/r
	
	for r in range( 1, 1 ):
		if y < h - r:
			xx, yy = x, y + r
			h1 = calcPixHeight( pix, xx, yy, heightPix, heightOffset, heightOpacity )
			# r1,g1,b1,a1 = pix[ xx, yy ]
			# h1 = calcHeight( r1, g1, b1, a1 )
			fy = fy + ( h1 - h0 ) * ( 1 - r/3 ) * normalScale

	return fx , fy, 1, h0

PI  = math.pi
PI4 = -math.pi/4
PI2 = -math.pi/2
CosPI2 = math.cos( PI2 )
SinPI2 = math.sin( PI2 )
CosPI4 = math.cos( PI4 )
SinPI4 = math.sin( PI4 )
CosPI4H = math.cos( PI4/4 )
SinPI4H = math.sin( PI4/4 )
CosPI4N = math.cos( -PI4 )
SinPI4N = math.sin( -PI4 )


affines = {}
def rotateNormal( n, rot ):
	m = Matrix44.xyz_rotation( *rot )
	v = Vector3( *n )
	return m.transform( v )

def rotateTopDouble( ny, nz ):
	nny = ny * CosPI2 - nz * SinPI2
	nnz = ny * SinPI2 + nz * CosPI2
	return nny, nnz

def rotateTop( ny, nz ):
	nny = ny * CosPI4 - nz * SinPI4
	nnz = ny * SinPI4 + nz * CosPI4
	return nny, nnz

def rotateTopHalf( ny, nz ):
	nny = ny * CosPI4H - nz * SinPI4H
	nnz = ny * SinPI4H + nz * CosPI4H
	return nny, nnz

def rotateFront( ny, nz ):
	nny = ny * CosPI4N - nz * SinPI4N
	nnz = ny * SinPI4N + nz * CosPI4N
	return nny, nnz

def rotateYZ( ny, nz, cs, sn ):
	nny = ny * cs - nz * sn
	nnz = ny * sn + nz * cs
	return nny, nnz

def makeNormalMap( img, option ):
	w,h = img.size
	imgOut = Image.new( 'RGBA', ( w,h ), (0,0,0,0 ) )
	if img.mode != 'RGBA':
		img = img.convert( 'RGBA' )
		
	pixIn = img.load()
	pixOut= imgOut.load()
	guideTopFace = option.get( 'guide-top-face', 0 )
	concave      = option.get( 'concave', False )
	heightGuideImage   = option.get( 'height_guide', None )
	heightGuideOffset  = option.get( 'height_guide_offset', None )
	heightGuideOpacity = option.get( 'height_guide_opacity', 0.7 )
	normalScale        = option.get( 'normal_scale', 0.5 )
	globalRotation     = option.get( 'global_rotation', None )
	slopeParam         = option.get( 'slope', None )

	if heightGuideImage :
		pixHeight = heightGuideImage.load()
	else:
		pixHeight = None

	for y in range( h ):
		for x in range( w ):
			mx,my,mz, height = calcNormal( 
				pixIn, x, y, w, h,
				pixHeight,
				heightGuideOffset,
				heightGuideOpacity,
				normalScale
			 )
			# if my > 1.0: my = 1.0
			l = math.sqrt( mx*mx + my*my + mz*mz )
			if l > 0:
				nx,ny,nz = mx/l, my/l, mz/l
			else:
				nx,ny,nz = 0,0,0

			nx = nx/2.0 + 0.5
			ny = ny/2.0 + 0.5
			nz = nz/2.0 + 0.5
			pixOut[ x, y ] = ( 
				int(nx*255), int(ny*255), int(nz*255), 255 - int( min( 255 * height, 255 ) )
				)

	if globalRotation:
		#conver into radian
		rx, ry, rz = globalRotation
		globalRotation = ( -rx*PI/180.0, ry*PI/180.0, rz*PI/180.0 )

	if slopeParam:
		rot = -( 45.0 - slopeParam[ 0 ] )
		slopeCS = math.cos( rot*PI/180.0 )
		slopeSN = math.sin( rot*PI/180.0 )
		
	#shape pass
	for y in range( h ):
		if slopeParam:
			if y < slopeParam[ 1 ]: #step1
				slopeSmoothInterp = math.pow( 1.0 - float(y) / slopeParam[ 1 ], 2.0 )
			elif ( h - y ) <= slopeParam[ 2 ]:
				slopeSmoothInterp = math.pow( 1.0 - float( h - y ) / slopeParam[ 2 ], 2.0 )
			else:
				slopeSmoothInterp = None

		for x in range( w ):
			nx,ny,nz, a = pixOut[ x, y ]
			nx= ( nx/255.0 - 0.5 ) * 2.0
			ny= ( ny/255.0 - 0.5 ) * 2.0
			nz= ( nz/255.0 - 0.5 ) * 2.0
			if concave:
				if y > guideTopFace:
					ny, nz = rotateTop( ny, nz )
				elif y > guideTopFace - 1:
					ny, nz = rotateTopHalf( ny, nz )
			else:
				if y < guideTopFace:
					ny, nz = rotateTop( ny, nz )
				elif guideTopFace > 0 and y < guideTopFace + 1:
					ny, nz = rotateTopHalf( ny, nz )
			if globalRotation:
				nx,ny,nz = rotateNormal( (nx,ny,nz), globalRotation )

			if slopeParam:
				ny1,nz1 = rotateYZ( ny,nz, slopeCS, slopeSN )
				if slopeSmoothInterp:
					ny0,nz0 = rotateTop( ny, nz )
					ny = ny0 * slopeSmoothInterp + ny1 * ( 1.0 - slopeSmoothInterp )
					nz = nz0 * slopeSmoothInterp + nz1 * ( 1.0 - slopeSmoothInterp )
				else:
					ny,nz = ny1,nz1

			nx = nx/2.0 + 0.5
			ny = ny/2.0 + 0.5
			nz = nz/2.0 + 0.5
			pixOut[ x, y ] = ( 
				int(nx*255), int(ny*255), int(nz*255), a 
				)
	
	return imgOut


if __name__ == '__main__':
	from . import PSDDeckPackTest
	# img = Image.open( 'tile.tileset.png' )
	# w,h = img.size
	# imgOut = Image.new( 'RGBA', ( w,h ), (0,0,0,0 ) )
	# pixIn = img.load()
	# pixOut= imgOut.load()
	# for y in range( h ):
	# 	for x in range( w ):
	# 		mx,my,mz = calcNormal( pixIn, x, y, w, h )
	# 		l = math.sqrt( mx*mx + my*my + mz*mz )
	# 		if l > 0:
	# 			nx,ny,nz = mx/l, my/l, mz/l
	# 		else:
	# 			nx,ny,nz = 0,0,0
	# 		pixOut[ x, y ] = ( 
	# 			int(nx*255), int(ny*255), int(nz*255), 255 
	# 			)
	# imgOut.save( 'output.png', 'PNG' )
