from os.path import basename, splitext
import math
import io
from PIL import Image
from .psd_tools_helper import *

from psd_tools import PSDImage, Group, Layer
from psd_tools.constants import ImageResourceID
from psd_tools.utils import read_fmt, read_unicode_string, read_pascal_string

import logging
import json

import re


##----------------------------------------------------------------##
def saveJSON( data, path, **option ):
	outputString = json.dumps( data , 
			indent    = option.get( 'indent' ,2 ),
			sort_keys = option.get( 'sort_keys', True ),
			ensure_ascii=True
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

##----------------------------------------------------------------##

def get_layer_fullname( l ):
	name = None
	while l and (not isinstance( l, PSDImage ) ) :
		layerName = l.name
		if layerName == '_RootGroup': break
		if name:
			name = layerName + '.' + name
		else:
			name = layerName
		l = l.parent
	return name

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
class PSDLayerExtractor(object):
	"""docstring for TilesetProject"""
	def __init__(self):
		self.tiles = []
		self.tileSize = ( 50, 50 )
		self.columns = 4
		self.themes = []

	def extract( self, path, outputPath ):
		image = PSDImage.load( path )
		#meta data
		bx0 ,	by0 ,	bx1 ,	by1 = image.bbox
		self.bbox = ( bx0, by0, bx1, by1 )		
		self.tileSize = ( bx1, by1 )
		collected = []

		for layer in image.layers:
			self.collectLayer( layer, collected )

		result = []
		idx = 0
		for l in collected:
			idx += 1
			name = get_layer_fullname( l )
			filename = 'exported_%d' % idx
			filepath = outputPath + '/'+filename+'.png'
			img = l.as_PIL()
			img.save( filepath, 'PNG' )
			result.append( ( name, filepath, filename ) )
		return result

	def collectLayer( self, l, result ):
		if l.name.startswith( '//' ): return
		if isinstance( l, Group ):
			for layer in l.layers:
				self.collectLayer( layer, result )
		else:
			result.append( l )

	def save( self, atlasPath, jsonPath, atlasSize = ( 1024, 1024 ) ):
		for theme in self.themes:
			theme.build()
		atlas = self.generateAtlas( atlasPath, atlasSize )
		themeDatas = []
		for theme in self.themes:
			themeDatas.append( theme.save() )
		output = {
			'atlas' : {
				'w' : atlas.w,
				'h' : atlas.h
			},
			'themes' : themeDatas
		}
		saveJSON( output, jsonPath )

		return atlas
##----------------------------------------------------------------##

if __name__ == '__main__':
	extractor = PSDLayerExtractor()
	extractor.extract( 'test/quadtest.decks.psd', 'test/output' )