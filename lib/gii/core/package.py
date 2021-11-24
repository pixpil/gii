import sys
import os
import os.path
import imp
import logging
import json
from types import ModuleType

_GII_PACKAGE_NAME   = 'gii_package'
_INFO_FILE_NAME     = '__gii__.json'

_GII_MODULE = ModuleType( _GII_PACKAGE_NAME )
sys.modules[ _GII_PACKAGE_NAME ] = _GII_MODULE

##----------------------------------------------------------------##
def _clearSysModule( prefix ):
	toremove = []
	for k in sys.modules:
		if k.startswith( prefix ):
			toremove.append( k )

	for k in toremove:
		del sys.modules[ k ]

##----------------------------------------------------------------##
class PackageManager( object ):
	def __init__( self ):
		self.packages = {}
		self.excludedPackages = []

	def addExcludedPackage( self, excluded ):
		if isinstance( excluded, list ):
			self.excludedPackages += excluded
		else:
			self.excludedPackages.append( excluded )

	def registerPackage( self, name, path ):
		infoFilePath = path + '/' + _INFO_FILE_NAME
		if not os.path.exists( infoFilePath ): 
			logging.info( 'no %s found in package folder: %s' % ( _INFO_FILE_NAME, path ) )
			return None

		logging.debug( 'reading package settings: %s ' % path )
		try:
			data = json.load( open( infoFilePath, 'r', encoding = 'utf-8' ) )
			prev = self.getPackage( name )
			if prev:
				logging.warn( 'duplicated package: %s \n\tfound:\t%s\n\tat:\t%s' % ( name, prev.path, path ) )
				return None
			package = Package( name, path, data )
			package.manager = self
			self.packages[ name ] = package
			return package

		except Exception as e:
			logging.error( 'failed reading package settings:%s' % name )
			logging.exception( e )
			return None
		return data	

	def getPackage( self, name ):
		return self.packages.get( name, None )

	def scanPackages( self, path ):
		if not os.path.exists( path ): return
		logging.info( 'scanning package in:' + path )

		for currentDir, dirs, files in os.walk( str(path) ):
			for dirname in dirs:
				if dirname in self.excludedPackages: continue
				fullpath = currentDir + '/' + dirname
				settingFile = fullpath + '/' + _INFO_FILE_NAME
				self.registerPackage( dirname, fullpath )
			break #just scan first level

		#load all packages
		toLoad = []
		for p in list(self.packages.values()):
			if p.needLoad(): toLoad.append( p )

		#check dependency
		succ = True
		for p in list(self.packages.values()):
			if not p.isDependencyExist():
				succ = False
		if not succ:
			
			return False

		while True:
			notLoad = []
			loadedCount = 0
			for package in toLoad:
				if not package.load():
					notLoad.append( package )
				else:
					loadedCount += 1
			if notLoad:
				if loadedCount == 0:
					for package in notLoad:
						logging.warning( 'failed to load package: %s' % package.name )
					return False
			else:
				logging.info( 'packages loaded!' )
				break
			toLoad = notLoad

		return True

##----------------------------------------------------------------##
class Package(object):
	def __init__( self, name, path, settings ):
		self.name     = name
		self.path     = path
		self.settings = settings

		self.moduleName   = _GII_PACKAGE_NAME + '.' + name
		self.loaded       = False
		self.loadedModule = None
		
		if name != 'base':
			self.active       = settings.get( 'active', True )
			self.dependencies = settings.get( 'dependency', [] )
			if not 'base' in self.dependencies:
				self.dependencies.append( 'base' )
		else:
			self.active = True
			self.dependencies = []
		# self.dependents   = []
		self.manager = None

	def needLoad( self ):
		if not self.active: return False
		return True

	def reload( self ):
		if self.unload():
			return self.load()
		else:
			return False

	def isDependencyExist( self ):
		if not self.dependencies: return True
		manager = self.manager
		if not manager: return False
		succ = True
		for depId in self.dependencies:
			p = manager.getPackage( depId )
			if not p:
				logging.warning( 'dependency package not found:%s, required by %s' % ( depId, self.name ) )
				succ = False
		return succ

	def isDependencyReady( self ):
		manager = self.manager
		if not manager: return False
		succ = True
		for depId in self.dependencies:
			p = manager.getPackage( depId )
			if not ( p and p.isLoaded() ):
				return False
		return True

	def isLoaded( self ):
		return self.loaded

	def load( self ):
		if self.loaded: return True
		if not self.isDependencyReady(): return False
		logging.info( 'loading package:' + self.name )
		self.loadedModule = imp.load_module( self.moduleName, None, self.path, ('', '', 5) )
		self.loaded = True
		setattr( _GII_MODULE, self.name, self.loadedModule )
		return True

	def unload( self ):
		if self.loadedModule:
			_clearSysModule( self.moduleName )
			self.loadedModule = None
			self.loaded = False
			return True
		return True
		#TODO: package callback?
		#TODO: unload dylib?
