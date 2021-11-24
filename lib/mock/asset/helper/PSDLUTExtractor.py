from os.path import basename, splitext
import io
from psd_tools import PSDImage, Group, Layer
from psd_tools.constants import ImageResourceID
from psd_tools.utils import read_fmt, read_unicode_string, read_pascal_string

from .MetaTag import parseMetaTag

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

def extractLUTImage( path ):
	psd = PSDImage.load( path )
	layers = extractLeafLayers( psd )

	for l in layers:
		layerName = l.name.encode( 'utf-8' )
		metaInfo = parseMetaTag( layerName )
		if not metaInfo: continue
		name = metaInfo[ 'name' ]
		if name != '@LUT': continue
		tags = metaInfo[ 'tags' ]
		filter = tags.get( 'FILTER', 'linear' )
		bbox = l.bbox
		output = psd.as_PIL()
		output = output.crop( bbox )
		return output, filter

	return None, None


if __name__ == '__main__':
	output, filter = extractLUTImage( 'test/lut.psd' )
	if output:
		print('extracted', filter)
		output.save( 'test/lut_output.png' )
	else:
		print('no valid LUT')


