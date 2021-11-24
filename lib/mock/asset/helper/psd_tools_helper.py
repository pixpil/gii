from PIL import Image
import io
from psd_tools import PSDImage, Group, Layer
from psd_tools.decoder.actions import Boolean, Integer, List, Descriptor
from psd_tools.constants import ImageResourceID
from psd_tools.utils import read_fmt, read_unicode_string, read_pascal_string
##----------------------------------------------------------------##
from weakref import WeakKeyDictionary

import re

##----------------------------------------------------------------##
def read_psd_string ( f ):
	l, = read_fmt("I", f)
	if l==0: l = 4;
	return f.read( l )

def read_psd_obj( f, vt = None ):
	if not vt: vt = f.read( 4 )
	if vt == b'long':
		v, = read_fmt('l', f)
		return v

	elif vt == b'bool':
		result, = read_fmt('b', f)
		return result != 0

	elif vt == b'doub':
		result, = read_fmt('d', f)
		return result

	elif vt == b'VlLs':
		count, = read_fmt('I', f)
		result = []
		for i in range( 0, count ):
			v = read_psd_obj( f )
			result.append (v)
		return result

	elif vt == b'Objc':
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

	elif vt == b'enum':
		typeId = read_psd_string( f )
		value = read_psd_string( f )
		return ( typeId, value )

	elif vt == b'UntF':
		unit = f.read(4)
		value, = read_fmt('d', f)
		return (value, unit)
	
	elif vt == b'TEXT':
		size, = read_fmt("I", f)
		text = f.read( size * 2 ) #TODO: unicode?
		return str(text,'utf-8')

	else:
		raise Exception('not implement: %s ' % vt )

def namedTupleToValue( t ):
	tt = type( t )
	if   tt == Descriptor:
		r = {}
		for entry in t.items:
			key, data = entry
			r[ key ] = namedTupleToValue( data )
		return r

	elif tt == List:
		r = []
		for entry in t.items:
			r.append( namedTupleToValue( entry ) )
		return r

	else: #Boolean/Integer/String/...
		return t.value

def get_mlst( layer ):
	for md in layer._tagged_blocks[b'shmd']:
		if md.key == b'mlst':
			return namedTupleToValue( md.data )
	return None

def _parse_feature_meta( s ):
	lines = s.split( '||' )
	maxId = int( lines[ 1 ] );
	count = int( lines[ 2 ] );
	result = {}
	for i in range( count ):
		ss = lines[ i + 3 ]
		f = _str_to_feature( ss )
		result[ f['id'] ] = f
	return result

def _ITB( k ):
	if k == 1:
		return True
	else:
		return False

def _str_to_feature( s ):
	lines = s.split( ']/[' )
	return {
		'id'   : int( lines[0] ),
		'name' : lines[1],
		'active' :_ITB( int( lines[2] ) ),
		'visible' :_ITB( int( lines[3] ) ),
	}

def get_psd_features( image ):
	for r in image.decoded_data.image_resource_blocks:
		if r.resource_id == ImageResourceID.XMP_METADATA:
			m = re.search( '<photoshop:Source>(.+)</photoshop:Source>', str(r.data) )
			if m:
				return _parse_feature_meta( m.group( 1 ) )
			return None

def get_mani( image ):
	for r in image.decoded_data.image_resource_blocks:
		if r.resource_id >= ImageResourceID.PLUGIN_RESOURCES_0 and r.resource_id < ImageResourceID.PLUGIN_RESOURCES_LAST:
			f = io.BytesIO( r.data )
			pluginName = f.read(4)
			if pluginName == b'mani':
				f.seek( 24, 1 )
				desc = read_psd_obj( f, b'Objc' )
				return desc
	return None

def get_layer_feature( layer ):
	for md in layer._tagged_blocks[b'shmd']:
		if md.key == b'cust':
			data = namedTupleToValue( md.data )
			xmp = data.get( b'layerXMP', None )
			if not xmp: return False
			m = re.search( '<exif:feature>(\w+)', xmp )
			return int( m.group( 1 ) )
	return -1

def extract_leaf_layers( group ):
	def extractGroup( layers, result ):
		for l in layers:
			if isinstance( l, Group ):
				extractGroup( l.layers, result )
			else:
				result.append( l )
	result = []
	extractGroup( group.layers, result )
	return result

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
_layerImageCache = WeakKeyDictionary()
def layer_to_PIL( layer ):
	img = _layerImageCache.get( layer, None )
	if not img:
		img = layer.as_PIL()
		_layerImageCache[ layer ] = img
	return img


##----------------------------------------------------------------##
class LayerProxy( Layer ):
	def __init__( self, srcLayer ):
		self._index   = srcLayer._index
		self._psd     = srcLayer._psd
		self.srcLayer = srcLayer

	@property
	def name(self):
		return self.srcLayer.name

	@property
	def visible(self):
		return self.srcLayer.visible

	@property
	def visible_global(self):
		return self.srcLayer.visible_global

	@property
	def layer_id(self):
		return self.srcLayer.layer_id

	@property
	def opacity(self):
		return self.srcLayer.opacity

	@property
	def blend_mode(self):
		return self.srcLayer.blend_mode

	@property
	def _info(self):
		return self.srcLayer._info

	@property
	def _tagged_blocks(self):
		return self.srcLayer._tagged_blocks

	def as_PIL(self):
		return self.srcLayer.as_PIL()

	def as_pymaging(self):
		return self.srcLayer.as_pymaging()

	@property
	def bbox(self):
		return self.srcLayer.bbox

	@property
	def transform_bbox(self):
		return self.srcLayer.transform_bbox

	@property
	def placed_layer_size(self):
		return self.srcLayer.placed_layer_size

	def _placed_layer_block(self):
		return self.srcLayer._placed_layer_block()

	@property
	def text_data(self):
		return self.srcLayer.text_data

	@property
	def __repr__(self):
		return self.srcLayer.__repr__()
