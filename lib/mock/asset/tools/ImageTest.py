##----------------------------------------------------------------##
import ctypes
import os
if 'MAGICK_HOME' not in os.environ:
	os.environ['MAGICK_HOME'] = '/opt/local'

##----------------------------------------------------------------##
from .wand.image import Image, CHANNELS
from .wand.api   import library
from .wand.display import display

with Image(filename='shaman.png') as img:
	library.MagickGaussianBlurImageChannel.argtypes = [
		ctypes.c_void_p,
		ctypes.c_int,
		ctypes.c_double,
		ctypes.c_double
		]
	
	w, h = img.width, img.height
	r = 10
	for k in range( 1, r, 2 ):
		k = 1 + k * 0.1
		copy = img.clone() 
		copy.resize( int(w/k), int(h/k) )
		library.MagickGaussianBlurImageChannel( copy.wand, CHANNELS['all_channels'], r, r/3 )
		copy.resize( w, h )
		# display( copy )
		copy.save(filename='shaman{0}.png'.format(k * 10))
	