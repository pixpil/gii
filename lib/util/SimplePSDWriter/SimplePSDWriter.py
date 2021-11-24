# -*- coding: utf-8 -*-
from struct import *
from functools import reduce


BLENDMODES = {
	'pass through'  : 'pass',
	'normal'        : 'norm',
	'dissolve'      : 'diss',
	'darken'        : 'dark',
	'multiply'      : 'mul ',
	'color burn'    : 'idiv',
	'linear burn'   : 'lbrn',
	'darker color'  : 'dkCl',
	'lighten'       : 'lite',
	'screen'        : 'scrn',
	'color dodge'   : 'div ',
	'linear dodge'  : 'lddg',
	'lighter color' : 'lgCl',
	'overlay'       : 'over',
	'soft light'    : 'sLit',
	'hard light'    : 'hLit',
	'vivid light'   : 'vLit',
	'linear light'  : 'lLit',
	'pin light'     : 'pLit',
	'hard mix'      : 'hMix',
	'difference'    : 'diff',
	'exclusion'     : 'smud',
	'subtract'      : 'fsub',
	'divide'        : 'fdiv',
	'hue'           : 'hue ',
	'saturation'    : 'sat ',
	'color'         : 'colr',
	'luminosity'    : 'lum '
}

COMPRESSION = {
	'raw': 0,
	'rle': 1,
	'zip without prediction': 2,
	'zip with prediction': 3
}

class DataView():
	def __init__( self, buf, off = 0 ):
		self.buf = buf
		self.offset = off

	def setU8( self, offset, n ):
		self.buf[offset] = pack('B', n)

	def setU16( self, offset, n ):
		self.buf[offset:offset+2] = pack('>H', n)

	def setU32( self, offset, n ):
		self.buf[offset:offset+4] = pack('>I', n)

	def setByteData( self, offset, bytearr, length ):
		self.buf[offset:offset+length] = bytearr

	def setByteArray( self, offset, bytearr ):
		l = len( bytearr )
		self.setU32( offset, l )
		self.setByteData( offset + 4, bytearr, l )

def pad2(l):
		return l % 2

def pad4(l):
	return (4 - (l % 4)) % 4

def unicodeString(value): # 4 byte length + ucs2	
	raw = value.encode( 'utf-16-be' )
	output = bytearray( len(raw) + 4 )
	output[0:4] = pack('>I', len( value ) )
	output[4:] = bytes(raw)
	return output

def pascalString(value): # 1 byte length + asc
	value = value.encode('utf-8')
	value = value[0:255]
	output = bytearray( len(value) + 1 )
	output[0] = len(value)
	output[1:] = value
	return output

def copyArray( tgt, src ):
	#TODO
	pass

def writeSignature(view, offset, value):
	data = bytearray( value )
	view.setU8( offset,     data[0] )
	view.setU8( offset + 1, data[1] )
	view.setU8( offset + 2, data[2] )
	view.setU8( offset + 3, data[3] )

def buildImageResource(resourceId, resourceData):
	buf = bytearray(12 + len(resourceData))
	view = DataView(buf)
	writeSignature(view, 0, '8BIM')
	view.setU16(4, resourceId | 0)
	# two zero byte for null name
	view.setByteArray( 12, resourceData )
	return buf

def extractChannelImageData(imageData, channelCount, channelOffset, compression):
	if compression != COMPRESSION['raw']:
		compression = COMPRESSION['raw'] # TODO: support rle
	pixelCount = len(imageData) / channelCount
	data = bytearray(2 + pixelCount)
	data[1] = compression
	i = 2
	j = channelOffset
	l = len( imageData )
	while j < l:
		data[i] = imageData[j]
		i += 1
		j += channelCount
	return data

def buildAdditionalLayerInformation(key, data):
	dataLength = len(data) + pad2(len(data)) # length of data with padding
	buf = bytearray(
		4 + # signature
		4 + # key
		4 + # length of data
		dataLength
	)
	view = DataView(buf)
	writeSignature(view, 0, '8BIM')
	writeSignature(view, 4, key)
	view.setByteArray( 8, data )
	return buf

def addByteLength( prev, curr ):
	return prev + len(curr)

def addLength( prev, curr ):
	return prev + len(curr)
	
def buildLayerRecord(top, left, bottom, right,
										name, opacity, blendMode,
										rLen, gLen, bLen, aLen,
										additionalLayerInformationList):
	nameData = pascalString(name)
	padding = pad4(len(nameData))
	additionalLayerInformationArrayByteLength = \
		reduce( addByteLength, additionalLayerInformationList, 0 )
	extraDataFieldLength = 4 # no mask data
	extraDataFieldLength+= 44 # 4 byte for length + src, dst blending ranges per channel (gray + g + b + a)
	extraDataFieldLength+= len(nameData) + padding # name
	extraDataFieldLength+= additionalLayerInformationArrayByteLength
	buf = bytearray(
		16 + # top, left, bottom, right
		2 + # number of channels. 4
		24 + # channel information(6) * number of channels(4)
		4 + # signature
		4 + # blend mode key
		1 + # opacity
		1 + # clipping
		1 + # flags
		1 + # filler
		4 + # length of extra data field
		extraDataFieldLength
	)
	view = DataView(buf)
	view.setU32(0, top)
	view.setU32(4, left)
	view.setU32(8, bottom)
	view.setU32(12, right)
	view.setU16(16, 4) # number of channels
	view.setU16(18, 0) # red
	view.setU32(20, rLen) # red channel data length
	view.setU16(24, 1) # green
	view.setU32(26, gLen) # green channel data length
	view.setU16(30, 2) # blue
	view.setU32(32, bLen) # blue channel data length
	view.setU16(36, 0xffff) # alpha
	view.setU32(38, aLen) # alpha channel data length
	writeSignature(view, 42, '8BIM')
	writeSignature(view, 46, BLENDMODES[blendMode])
	view.setU8(50, (opacity * 0xff) | 0) # opacity
	view.setU8(51, 0) # clipping
	view.setU8(52, 8) # flags. TODO: visibility
	view.setU8(53, 0) # filler
	view.setU32(54, extraDataFieldLength)
	view.setU32(58, 0) # no mask data
	view.setU32(62, 40) # length of layer blending ranges data
	view.setU32(66, 0x0000ffff) # gray src range
	view.setU32(70, 0x0000ffff) # gray dst range
	view.setU32(74, 0x0000ffff) # red src range
	view.setU32(78, 0x0000ffff) # red dst range
	view.setU32(82, 0x0000ffff) # green src range
	view.setU32(86, 0x0000ffff) # green dst range
	view.setU32(90, 0x0000ffff) # blue src range
	view.setU32(94, 0x0000ffff) # blue dst range
	view.setU32(98, 0x0000ffff) # alpha src range
	view.setU32(102, 0x0000ffff) # alpha dst range
	view.setByteData( 106, nameData, len(nameData) )
	offset = 106 + len(nameData) + padding
	for additionalLayerInformation in additionalLayerInformationList:
		view.setByteData( offset, additionalLayerInformation, len(additionalLayerInformation) )
		offset += len(additionalLayerInformation)
	return buf

def buildLayerInfo(layers):
	channelImageDataList = []
	layerRecordList = []
	for layer in layers:
		top       = layer.get( 'y', 0 )
		left      = layer.get( 'x', 0 )
		bottom    = top + (layer.get( 'height', 0) )
		right     = left + (layer.get( 'width', 0) )
		name      = layer.get( 'name', '' )
		opacity   = layer.get( 'opacity', 1 ) 
		blendMode = layer.get( 'blendMode', 'normal' )
		additionalLayerInformationList = []
		imageData   = layer.get( 'imageData', None )
		compression = COMPRESSION['raw']
		rImageData = extractChannelImageData( imageData, 4, 0, compression )
		gImageData = extractChannelImageData( imageData, 4, 1, compression )
		bImageData = extractChannelImageData( imageData, 4, 2, compression )
		aImageData = extractChannelImageData( imageData, 4, 3, compression )
		channelImageDataList += [ rImageData, gImageData, bImageData, aImageData ]
		
		data = unicodeString(name)
		additionalLayerInformationList.append(
			buildAdditionalLayerInformation('luni', data)
		)

		# TODO? fx: drop shadow, glow, bevel...
		record = buildLayerRecord(
			top, left, bottom, right,
			name, opacity, blendMode,
			len(rImageData), len(gImageData), len(bImageData), len(aImageData),
			additionalLayerInformationList
		)
		layerRecordList.append( record )

	layerRecordArrayByteLength = reduce( addByteLength, layerRecordList, 0 )
	channelImageDataArrayByteLength = reduce( addLength, channelImageDataList, 0 )

	layerInfoLength = ( 2 + # layer count
							layerRecordArrayByteLength +
							channelImageDataArrayByteLength +
							pad2(channelImageDataArrayByteLength) )# padding
	buf = bytearray(
		4 + # length
		layerInfoLength
	)
	view = DataView(buf)
	view.setU32(0, layerInfoLength)
	view.setU16(4, len(layers))

	offset = 6

	for layerRecord in layerRecordList: #buf
		view.setByteData( offset, layerRecord, len( layerRecord ) )
		offset += len( layerRecord )

	for channelImageData in channelImageDataList:
		view.setByteData( offset, channelImageData, len( channelImageData ) )
		offset += len(channelImageData)
	return buf

class SimplePSDWriter():
	def __init__( self, **option ):
		self.layers = []
		self.width              = option[ 'width' ]
		self.height             = option[ 'height' ]
		self.backgroundColor    = option[ 'backgroundColor' ]
		self.layers             = option[ 'layers' ]
		self.flattenedImageData = option[ 'flattenedImageData' ]

	def writeFileHeader( self ):
		data = bytearray(4 + 2 + 6 + 2 + 4 + 4 + 2 + 2)
		view = DataView(data)
		writeSignature(view, 0, '8BPS') # 0 Signature
		view.setU16(4, 1) # version
		view.setU16(12, 4) # number of channels, RGBA
		view.setU32(14, self.height | 0) # height of the image in pixels
		view.setU32(18, self.width | 0) # width of the image in pixels
		view.setU16(22, 8) # depth, 1 byte per channel
		view.setU16(24, 3) # color mode, RGB
		return data

	def writeColorModeData( self ):
		buf = bytearray(4)
		return buf

	def writeImageResources( self ):
		self = self
		imageResourceArray = []
		# if (self.backgroundColor != undefined):
		#     (def ():
		#         buf = bytearray(8)
		#         view = DataView(buf)
		#         view.setU16(0, 0) # RGB
		#         view.setU16(2, (self.backgroundColor.r * 0xffff) | 0)
		#         view.setU16(4, (self.backgroundColor.g * 0xffff) | 0)
		#         view.setU16(6, (self.backgroundColor.b * 0xffff) | 0)
		#         imageResourceArray.append(buildImageResource(0x03f2, buf))
		#     })()
		# }
		totalLength = reduce( addByteLength, imageResourceArray, 0 )

		buf = bytearray(totalLength + 4)
		view = DataView(buf)
		view.setU32(0, totalLength)
		offset = 4
		for imageResource in imageResourceArray:
			view.setByteArray( offset, imageResource )
			uint8array.set(newUint8Array(imageResource), offset)
			offset += len(imageResource)
		return buf

	def writeLayerAndMaskInformation( self ):
		layerInfo = buildLayerInfo(self.layers)
		layerAndMaskInformationByteLength = len(layerInfo) + 4 # no global layer mask information
		buf = bytearray(
			4 + # length of the layer and mask information section
			layerAndMaskInformationByteLength
		)
		view = DataView(buf)
		view.setU32(0, layerAndMaskInformationByteLength)
		view.setByteData( 4, layerInfo, len( layerInfo ) )
		return buf

	def writeImageData( self ):
		flattenedImageData = self.flattenedImageData
		compression = COMPRESSION['raw']
		length = len( flattenedImageData )
		buf = bytearray(
			2 + # compression
			length
		)
		view = DataView(buf)
		view.setU16(0, compression)
		offset = 2
		# for (i = 0 i < length i += 4) buf[offset++] = flattenedImageData[i]
		for i in range( 0, length, 4 ):
			buf[offset] = flattenedImageData[i]
			offset+=1
		# for (i = 1 i < length i += 4) buf[offset++] = flattenedImageData[i]
		for i in range( 1, length, 4 ):
			buf[offset] = flattenedImageData[i]
			offset+=1
		# for (i = 2 i < length i += 4) buf[offset++] = flattenedImageData[i]
		for i in range( 2, length, 4 ):
			buf[offset] = flattenedImageData[i]
			offset+=1
		# for (i = 3 i < length i += 4) buf[offset++] = flattenedImageData[i]
		for i in range( 3, length, 4 ):
			buf[offset] = flattenedImageData[i]
			offset+=1
		return buf

	def write( self, path ):
		f = open( path, 'wb' )
		header = self.writeFileHeader()
		print(( len( header ) ))
		f.write( self.writeFileHeader() )
		f.write( self.writeColorModeData() )
		f.write( self.writeImageResources() )
		f.write( self.writeLayerAndMaskInformation() )
		f.write( self.writeImageData( ) )
		f.close()

if __name__ == '__main__':
	writer = SimplePSDWriter(
		width = 2,
		height = 1,
		backgroundColor = 1,
		flattenedImageData = bytearray([255,255,255,255, 0,255,0,0]),
		layers = [
			dict(
					name      =  '我是好人',
					imageData =  bytearray([255,255,0,255]), #data...
					width     =  1, # pixel unit
					height    =  1, # pixel unit
					x         =  0, # pixel unit
					y         =  0, # pixel unit
					opacity   =  1, # 0(transparent) ~ 1(opaque)
					blendMode =  'normal' # see below (blend modes)
				),
		]
	)
	writer.write( 'test.psd' )
