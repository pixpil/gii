#---------------------------------------------------------------##
import ctypes
import os
import sys
import types
# import sys,imp

from PIL import Image, ImageChops, ImageOps, ImageFilter, ImageFont, ImageDraw
from util.ImageProcessPreset import *

##----------------------------------------------------------------##
# STUB
##----------------------------------------------------------------##
def main():
	if len( sys.argv ) == 1:
		return test()

	procPath     = sys.argv[1]
	inputPath    = sys.argv[2]
	if len( sys.argv ) > 3:
		outputPath = sys.argv[3]
	else:
		outputPath = inputPath

	procModule = types.ModuleType( procPath.replace( '.', '_' ) )
	with open( procPath, 'r' ) as f:
		code = f.read()
	
	env = {}
	exec( code, globals(), env )
	img = Image.open( inputPath )
	onProcess = env.get( 'onProcess', None ) 

	if not onProcess:
		print("warning: onProcess not defined", procPath)
		sys.exit(1)

	output = onProcess( img )
	if output:
		output.save( outputPath, 'PNG' )
		sys.exit( 0 )
	else:
		sys.exit( 1 )


def test():
	img = Image.open( 'test/testIcon.png' )
	output = Glow( img, 13, 2, '#6C9CFD' )
	output.save( 'test/testoutput.png', 'PNG' )


##----------------------------------------------------------------##
if __name__ == '__main__':
	main()
	# test()
