##----------------------------------------------------------------##
#find gii library
import os
import os.path
import platform
import sys

try:
	import faulthandler
	faulthandler.enable()
except Exception as e:
	pass

SYSTEM = platform.system()

def fixPath( p ):
	if SYSTEM == 'Windows':
		return p.replace('/','\\')
	else:
		return p.replace('\\','/')

def isPythonFrozen():
	return hasattr( sys, "frozen" )

def getMainModulePath():
	if isPythonFrozen():
		p = os.path.dirname(str(sys.executable, sys.getfilesystemencoding( )))
		if SYSTEM == 'Darwin':
			path = os.path.realpath( p + '/../../..' )
			if os.path.basename( path ) == 'dist':
				return os.path.realpath( path + '/..' )
			else:
				return path
		elif SYSTEM == 'Windows':
			return p
		elif SYSTEM == u'Linux':
			return p
		else:
			return p
	if __name__ == 'main':
		mainfile = os.path.realpath( __file__ )
		return os.path.dirname( mainfile )
	else:
		import __main__
		if hasattr( __main__, "__gii_path__" ):
			return __main__.__gii_path__
		else:
			mainfile = os.path.realpath( __main__.__file__ )
			return os.path.dirname( mainfile )

def addEnvPath( key, entry, prepend = False ):
	if not isinstance( entry, list ):
		entry = [ entry ]
	processedEntry = [ fixPath( p ) for p in entry ]

	try:
		path0 = os.environ[ key ]
		if prepend:
			processedEntry = processedEntry + [ path0 ]
		else:
			processedEntry = [ path0 ] + processedEntry
	except KeyError as e:
		processedEntry = processedEntry
	path1 = os.pathsep.join( processedEntry )
	os.environ[ key ] = path1
	os.putenv( key, path1 )
	return path1

##----------------------------------------------------------------##
def setupEnvironment():
	#builtin env
	giipath = getMainModulePath() + '/lib'
	thirdPartyPathBase = getMainModulePath() + '/lib/3rdparty'
	thirdPartyPathCommon = thirdPartyPathBase + '/common'
	supportPath = getMainModulePath() + '/support'
	if SYSTEM == 'Darwin':
		thirdPartyPathNative = thirdPartyPathBase + '/osx'
		supportPathNative = supportPath + '/osx'
	elif SYSTEM == u'Linux':
		thirdPartyPathNative = thirdPartyPathBase + '/linux'
		supportPathNative = supportPath + '/linux'
	else:
		thirdPartyPathNative = thirdPartyPathBase + '/windows'
		supportPathNative = supportPath + '/windows'

	sharedPath = supportPathNative + '/shared'
	sharedQt5Path = sharedPath + '/Qt5'
	modulePaths = [
		giipath,
		thirdPartyPathNative,
		thirdPartyPathCommon
	]

	#apply to sys
	for filename in os.listdir( thirdPartyPathCommon ):
		if filename.endswith( '.egg' ) or filename.endswith( '.module.zip' ):
			eggpath = thirdPartyPathCommon + '/' + filename
			sys.path.insert( 1, eggpath )
			modulePaths.insert( 1, eggpath )
	sys.path.insert( 1, thirdPartyPathCommon )

	for filename in os.listdir( thirdPartyPathNative ):
		if filename.endswith( '.egg' ) or filename.endswith( '.module.zip' ):
			eggpath = thirdPartyPathNative + '/' + filename
			sys.path.insert( 1, eggpath )
			modulePaths.insert( 1, eggpath )
	sys.path.insert( 0, thirdPartyPathNative )
	sys.path.insert( 0, giipath )

	
	#qt5 support?
	giiPythonExecPath = getMainModulePath() + '/support/osx/Gii.app/Contents/MacOS'
	Qt5PluginPath = os.path.join( sharedQt5Path, 'plugins' )
	Qt5QmlPath = os.path.join( sharedQt5Path, 'qml' )
	os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = Qt5PluginPath
	os.environ['QML2_IMPORT_PATH'] = Qt5QmlPath
	os.environ[ 'QTWEBENGINEPROCESS_PATH' ] = giiPythonExecPath +'/QtWebEngineProcess'
	os.environ[ 'QT_SIP_API_HINT' ] = "2"
	os.environ[ 'QT_VERBOSE' ] = "True"
	os.environ[ 'QT_API' ] = 'pyqt5'	

	#user env
	homePath = os.path.expanduser("~")
	userPath = homePath + '/.gii'
	if os.path.isdir( userPath ):
		userPath = userPath
		userLibPath = userPath + '/lib'
	else:
		userPath = False
		userLibPath = False

	if userPath and os.path.isdir( userLibPath ):
		modulePaths.insert( 0, userLibPath )
		sys.path.insert( 0, userLibPath )

	#apply to environ
	addEnvPath( 'PATH', sharedPath, True )
	addEnvPath( 'PATH', sharedQt5Path )

	addEnvPath( 'DYLD_FRAMEWORK_PATH', sharedPath, True )
	addEnvPath( 'DYLD_FRAMEWORK_PATH', sharedQt5Path, True )
	addEnvPath( 'DYLD_LIBRARY_PATH', sharedPath, True )
	addEnvPath( 'DYLD_LIBRARY_PATH', sharedQt5Path, True )
	
	addEnvPath( 'PYTHONPATH', modulePaths, True )
	
	os.environ[ 'GII_ENV_SET' ] = 'OK'
	os.environ[ 'GII_CWD' ] = os.getcwd();
	os.environ[ 'GII_BASE_PATH' ] = getMainModulePath()
	os.environ[ 'GII_SUPPORT_PATH' ] = supportPath
	os.environ[ 'GII_NATIVE_SUPPORT_PATH' ] = supportPathNative

DO_PROFILE = False

def main():
	import gii_cfg
	import gii
	if DO_PROFILE:
		import cProfile, pstats, io
		pr = cProfile.Profile()
		pr.enable()

		gii.startup()

		pr.disable()
		ps = pstats.Stats(pr)
		ps.sort_stats( 'calls', 'time' )
		ps.print_stats()
	else:
		gii.startup()

if __name__ == '__main__':
	if isPythonFrozen():
		sys.argv = ['gii', 'stub']

	if os.environ.get( 'GII_ENV_SET' ) != 'OK':
		setupEnvironment()
		import subprocess
		executable = sys.executable
		subprocess.call( [ executable, os.path.realpath(__file__) ] + sys.argv[1:] )

	else:
		os.environ[ 'GII_ENV_SET' ] = 'DONE'
		
		class Unbuffered(object):
			 def __init__(self, stream):
					 self.stream = stream
			 def write(self, data):
					 self.stream.write(data)
					 self.stream.flush()
			 def writelines(self, datas):
					 self.stream.writelines(datas)
					 self.stream.flush()
			 def __getattr__(self, attr):
					 return getattr(self.stream, attr)

		import sys
		sys.stdout = Unbuffered(sys.stdout)

		import signal
		def exitProc(signum, frame):
			print( 'User stop detected' )
			sys.exit(0)
			
		signal.signal(signal.SIGINT, exitProc)
		signal.signal(signal.SIGTERM, exitProc)

		main()
		