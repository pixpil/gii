import logging
import toml


def saveTOML( data, path, **option ):
	outputString = toml.dumps( data , 
			indent    = option.get( 'indent' ,2 ),
			sort_keys = option.get( 'sort_keys', True ),
			ensure_ascii=False
		).encode('utf-8')
	fp = open( path, 'w' )
	fp.write( outputString )
	fp.close()
	return True

def loadTOML( path ):
	with open(path, mode = 'r', encoding = 'utf-8' ) as f:
		data = toml.loads( f.read() )
	return data

# def trySaveTOML( data, path, dataName = None, **option ):
# 	try:
# 		saveTOML( data, path, **option )
# 		return True
# 	except Exception, e:
# 		logging.warn( 'failed to save %s: %s' % ( dataName or 'TOML', path ) )
# 		logging.warn( e )
# 		return False


def tryLoadTOML( path, dataName = None ):
	try:
		data = loadTOML( path )
		return data
	except Exception as e:
		logging.warn( 'failed to load %s: %s' % ( dataName or 'TOML', path ) )
		logging.warn( e )
		return False
