import os
import os.path
import platform
import sys

def isPythonFrozen():
	return hasattr( sys, "frozen" )

def _getMainModulePath():
	if isPythonFrozen():
		giiBinPath = sys.argv[1]
		p = os.path.dirname(str(giiBinPath, sys.getfilesystemencoding( )))
		if platform.system() == 'Darwin':
			path = os.path.realpath( p + '/../../..' )
			if os.path.basename( path ) == 'dist':
				return os.path.realpath( path + '/..' )
			else:
				return path
		elif platform.system() == 'Windows':
			return p
		else:
			return p
	
	import __main__
	if hasattr( __main__, "__gii_path__" ):
		return __main__.__gii_path__
	else:
		mainfile = os.path.realpath( __main__.__file__ )
		return os.path.dirname( mainfile )


def getMainModulePath( path = None ):
	base = _getMainModulePath()
	if not path: return base
	return base + '/' + path
