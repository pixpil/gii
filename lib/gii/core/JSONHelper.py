import logging
import ujson as json
import json as _json
import msgpack

def saveJSON( data, path, **option ):
	# output = output.encode('utf-8')
	with open( path, mode = 'w', encoding='utf-8' ) as fp:
		output = json.dump( data , fp,
			indent    = option.get( 'indent' ,2 ),
			sort_keys = option.get( 'sort_keys', True ),
			ensure_ascii = False,
			escape_forward_slashes = False
		)
	return True

def loadJSON( path, **option ):
	encoding = option.get( 'encoding', 'utf-8' )
	with open( path, mode = 'r', encoding = encoding ) as fp:
		data = json.load( fp )
	return data

def trySaveJSON( data, path, dataName = None, **option ):
	try:
		saveJSON( data, path, **option )
		return True
	except Exception as e:
		if dataName:
			logging.warn( 'failed to save %s: %s' % ( dataName or 'JSON', path ) )
			logging.exception( e )
		return False


def tryLoadJSON( path, dataName = None, **options ):
	try:
		data = loadJSON( path, **options )
		return data
	except Exception as e:
		if dataName:
			logging.warn( 'failed to load %s: %s' % ( dataName or 'JSON', path ) )
			logging.exception( e )
		return False


def encodeJSON( inputData, **option ):
	outputString = json.dumps( inputData , 
			indent    = option.get( 'indent' ,2 ),
			sort_keys = option.get( 'sort_keys', True ),
			ensure_ascii = False,
			escape_forward_slashes = False
		)
	return outputString


def decodeJSON( inputString, **option ):
	data = json.loads( inputString )
	return data


def saveMsgPack( data, path, **option ):
	output = msgpack.packb( data )
	with open( path, 'wb' ) as fp:
		fp.write( output )
	return True

def trySaveMsgPack( data, path, dataName = None, **option ):
	try:
		saveMsgPack( data, path, **option )
		return True
	except Exception as e:
		if dataName:
			logging.warn( 'failed to save %s: %s' % ( dataName or 'MsgPack', path ) )
			logging.exception( e )
		return False

def convertJSONFileToMsgPack( jsonFile, msgPackFile, dataName = None ):
	data = tryLoadJSON( jsonFile, dataName )
	if not data:
		return False
	return trySaveMsgPack( data, msgPackFile )
