#---------------------------------------------------------------##
import ctypes
import time
import os
import sys
import sys,imp
import math
import random

from PIL import Image, ImageChops, ImageOps, ImageFilter, ImageFont, ImageDraw

##----------------------------------------------------------------##
#BUILTIN-functions
##----------------------------------------------------------------##
def getAlpha(im):
	return im.split()[-1]

def hex2rgb(value):
	value = value.lstrip('#')
	lv = len(value)
	return tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

def rgb2hex(red, green, blue):
	return '#%02x%02x%02x' % (red, green, blue)

def colorTuple( src ):
	if isinstance( src, tuple ): return src
	if isinstance( src, str ): return hex2rgb( src )
	#todo
	return src

##----------------------------------------------------------------##
def premultiplyAlpha_hack( img ):
	if img.mode != 'RGBA':
		img = img.convert( 'RGBA' )
	preAlpha = img.convert( 'RGBa' )
	imBytes = preAlpha.tobytes() 
	preAlpha = Image.frombuffer( "RGBA", img.size, imBytes, 'raw', "RGBA", 0, 1 )
	return preAlpha

##----------------------------------------------------------------##
#Image Filters?
##----------------------------------------------------------------##
def GaussianBlur( img, radius ):
	blurFilter = ImageFilter.GaussianBlur( radius )
	#todo: de-premulitple alpha
	# preAlpha = img.convert( 'RGBa' )
	# preAlpha.mode = 'RGBA' #hacking
	preAlpha = premultiplyAlpha_hack( img )
	return preAlpha.filter( blurFilter )

##----------------------------------------------------------------##
def ResizeRelative( img, sx, sy=-1 ):
	w, h = img.size
	if sy<0: sy = sx
	newSize = ( int(w*sx), int(h*sy) )
	return img.resize( newSize, Image.BILINEAR )

##----------------------------------------------------------------##
def CropRelative( img, expand = (0,0,0,0) ): #LTRB
	w, h = img.size
	l,t,r,b = expand
	box = ( 0 - l, 0 - t, w + r, h + b ) 
	return Crop( img, box )

##----------------------------------------------------------------##
def Crop( img, box ):
	return img.crop( box )

##----------------------------------------------------------------##
def Colorize(im, color):
	return ImageOps.colorize(im.convert('L'), (0,0,0), color).convert(im.mode)

##----------------------------------------------------------------##
def DropShadow(imSrc, horizontal_offset=5, vertical_offset=5, border=8,
				shadow_blur=3, shadow_color=0x444444):
	size = imSrc.size
	back_size = (size[0] + abs(horizontal_offset) + 2 * border,
				 size[1] + abs(vertical_offset) + 2 * border)

	image_mask = getAlpha(imSrc)
	shadow = Image.new('L', back_size, 0)

	shadow_left = border + max(horizontal_offset, 0)
	shadow_top = border + max(vertical_offset, 0)

	shadow.paste(image_mask, (shadow_left, shadow_top,
								shadow_left + size[0], shadow_top + size[1]))
	del image_mask

	for n in range(shadow_blur):
		shadow = shadow.filter(ImageFilter.BLUR)

	back = Image.new('RGBA', back_size, shadow_color)
	back.putalpha(shadow)
	del shadow

	image_left = border - min(horizontal_offset, 0)
	image_top = border - min(vertical_offset, 0)

	back.paste(imSrc, (image_left, image_top), imSrc.convert('RGBA'))
	back = back.crop((image_left, image_top, image_left+size[0], image_top+size[1]))

	return back


##----------------------------------------------------------------##
def Outline( imSrc, radius, color = '#FFFFFF' ):
	# imIn = imSrc.convert('RGB')
	# im = ImageOps.colorize( getAlpha( imSrc ), colorTuple( color ), (255,255,255) )
	offset  = ImageChops.offset
	chAlpha = getAlpha( imSrc )
	target = chAlpha.copy()
	for i in range( radius ):
		target = ImageChops.add( offset( chAlpha, 0, i ), target )
		target = ImageChops.add( offset( chAlpha, 0, -i ), target )
		target = ImageChops.add( offset( chAlpha, i, 0 ), target )
		target = ImageChops.add( offset( chAlpha, -i, 0 ), target )
	back = Image.new( imSrc.mode, imSrc.size, colorTuple( color ) )
	back.putalpha( target )
	result = Image.alpha_composite( back, imSrc )
	return result

##----------------------------------------------------------------##
def InnerShadow(imSrc, radius=3, shade_color='#FFFFFF'):
	imIn = imSrc.convert('RGB')
	im = ImageOps.colorize( getAlpha( imSrc ), colorTuple( shade_color ), (255,255,255) )
	for i in range(radius):
		im = im.filter(ImageFilter.SMOOTH)
	im = ImageChops.multiply(imIn, im)
	im.putalpha( getAlpha(imSrc) )
	return im

##----------------------------------------------------------------##
def InnerGlow(imSrc, radius=3, glow_color='#FFFFFF'):
	imIn = imSrc.convert('RGB')
	im = ImageOps.colorize( getAlpha( imSrc ), colorTuple( glow_color ), (0,0,0) )
	for i in range(radius):
		im = im.filter(ImageFilter.SMOOTH)
	im = ImageChops.add(imIn, im)
	im.putalpha( getAlpha(imSrc) )
	return im

##----------------------------------------------------------------##
def ColorOverlay( imSrc, color, op = 'multiply' ):
	color = colorTuple( color )
	im = imIn = imSrc.convert('RGB')
	fill = Image.new( 'RGB', im.size, color )
	if op == 'multiply':
		im = ImageChops.multiply( imIn, fill )
	elif op == 'add':
		im = ImageChops.add( imIn, fill )
	else:
		pass
		#todo

	im.putalpha(getAlpha(imSrc))
	return im

##----------------------------------------------------------------##
# Glow on text image
def Glow(imSrc, radius = 3, power = 2, glow_color = '#FFFFFF'):
	glow = Image.new( imSrc.mode, imSrc.size, colorTuple( '#FFFFFF' ) )
	glow.putalpha( getAlpha( imSrc ) )
	power = 1
	for n in range( power ):
		glow = glow.filter( ImageFilter.GaussianBlur( radius/2.0 ) )
		glow = ImageChops.add( glow, glow )
	# for n in xrange(radius):
	# 	glow = glow.filter(ImageFilter.SMOOTH)
	glowColored = Image.new( glow.mode, glow.size, colorTuple( glow_color ) )
	glowColored.putalpha( getAlpha( glow ) )
	result = Image.alpha_composite( glowColored.convert('RGBA'), imSrc )
	return result.convert( 'RGBA' )


##----------------------------------------------------------------##
def Noise(imgSrc, amount=1 ):
	random.seed( time.process_time_ns() )
	w,h = imgSrc.size
	imgOut = Image.new( 'RGBA', ( w,h ), (0,0,0,0 ) )
	pixIn = imgSrc.load()
	pixOut= imgOut.load()
	for y in range( h ):
		for x in range( w ):
			r,g,b,a = pixIn[ x, y ]
			k = random.random()
			pixOut[x,y] = ( int(r*k), int(g*k), int(b*k), a )
	return imgOut


##----------------------------------------------------------------##
def Sharpen(imgsrc, amount=1):
	imgOut = imgsrc.filter( ImageFilter.SHARPEN )
	return imgOut
