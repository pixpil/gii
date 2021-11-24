import platform
import os
import os.path
import logging
import subprocess
import shutil
import time
from gii.core import *

from mock import _MOCK


##----------------------------------------------------------------##
_SETTING_KEY_FMOD_STUDIO_PATH = 'fmod_studio_path'
_FMOD_STUDIO_PROJECT_CONFIG_NAME = 'fs_project.json'


##----------------------------------------------------------------##
def _affirmPath( path ):
	if os.path.exists( path ): return True
	try:
		os.mkdir( path )
		return True
	except Exception as e:
		return False

##----------------------------------------------------------------##
def getFallbackFMODPath():
	if platform.system() == 'Darwin':
		return '/Applications/FMOD Studio'
	elif platform.system() == 'Windows':
		#TODO
		return None
	else:
		return None


##----------------------------------------------------------------##
def getFMODBinaryPath():
	basePath = app.getUserSetting( _SETTING_KEY_FMOD_STUDIO_PATH, getFallbackFMODPath() )
	if not basePath:
		logging.warn( 'no fmod studio path specified' )
		return None

	if platform.system() == 'Darwin':
		path = os.path.realpath( basePath + '/FMOD Studio.app/Contents/MacOS/fmodstudio' )
		return path

	elif platform.system() == 'Windows':
		path = os.path.realpath( basePath + '/FMOD Studio.exe' )
		return path

	else: #Linux??
		logging.warn( 'unknown platform' )
		return None

##----------------------------------------------------------------##
def callFMODStudioBinary( args ):
	binPath = getFMODBinaryPath()
	if not binPath:
		logging.warn( 'no fmod studio binary found' )
		return False
	args = [ binPath ] + args
	env = os.environ.copy()
	env['QT_QPA_PLATFORM_PLUGIN_PATH'] = ''
	try:
		subprocess.call( args, env=env )
	except Exception as e:
		logging.exception( e )
		return False
	return True

##----------------------------------------------------------------##
def buildFMODStudioProject( path, **options ):
	args = [ '-build' ]
	
	banks = options.get( 'banks', None )
	if banks:
		args += [ '-banks', ','.join( banks ) ]

	platforms = options.get( 'platforms', None )
	if platforms:
		args += [ '-platforms', ','.join( platforms ) ]

	if options.get( 'diagnostic', False ):
		args += [ '-diagnostic' ]

	if options.get( 'ignore_warnings', False ):
		args += [ '-ignore-warnings' ]

	args += [ path ]
	# print args
	return callFMODStudioBinary( args )


##----------------------------------------------------------------##
class FMODStudioAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.fmod_studio'

	def acceptAssetFile(self, filepath):
		if not os.path.isdir(filepath): return False
		name, ext = os.path.splitext(filepath)
		if not ext in ['.fmod']: return False
		return True

	def importAsset(self, node, reload = False ):
		if node.isVirtual(): return
		node.assetType = 'fs_project'
		node.groupType = 'package'
		node.setBundle()
		app.getModule( 'fmod_studio_support' ).scheduleImport( node )
		node.setObjectFile( 'data', node.getFilePath() )
		return True

	def getDefaultAssetDeployConfig( self, assetNode ):
		return {
			'package' : 'audio'
		}



##----------------------------------------------------------------##
class FMODStudioAssetCreator(AssetCreator):
	def getAssetType( self ):
		return 'fs_project'

	def getLabel( self ):
		return 'FMOD Studio Project Config'

	def createAsset( self, name, contextNode, assetType ):		
		ext = '.fmod'
		filename = name + ext
		if contextNode.isType('folder'):
			nodePath = contextNode.getChildPath( filename )
		else:
			nodePath = contextNode.getSiblingPath( filename )
		fullPath = AssetLibrary.get().getAbsPath( nodePath )
		if os.path.exists(fullPath):
			raise Exception( 'File already exist:%s' % fullPath )
		os.mkdir( fullPath )
		emptyConfigFileData = {
			'source_path' : False,
			'source_type' : 'built',
		}
		JSONHelper.trySaveJSON( emptyConfigFileData, fullPath + '/' + _FMOD_STUDIO_PROJECT_CONFIG_NAME )
		return nodePath
		

##----------------------------------------------------------------##
class FMODStudioSupport( EditorModule ):
	name = 'fmod_studio_support'
	dependency = 'mock'

	def onLoad( self ):
		self.ready = False
		self.pendingImports = {}
		self.getAssetLibrary().addFileIgnorePattern( '.*\.fmod/Build' )

	def onAppReady( self ):
		self.ready = True
		self.doPendingImport()

	def scheduleImport( self, node ):
		self.pendingImports[ node ] = True
		if self.ready:
			self.doPendingImport()

	def doPendingImport( self ):
		imports = self.pendingImports
		self.pendingImports = {}
		for node in imports.keys():
			self.importFMODProject( node )

	def importFMODProject( self, node ):
		filePath   = node.getAbsFilePath()
		configPath = filePath + '/' + _FMOD_STUDIO_PROJECT_CONFIG_NAME
		configData = JSONHelper.tryLoadJSON( configPath )
		if not configData:
			logging.warning( 'missing or invalid FMOD project config:' + configPath )
			return False

		projPathCandidates  = configData.get( 'source_path', None )
		projType  = configData.get( 'source_type', 'built' )
		platforms = configData.get( 'platforms', [] )

		projPath = None
		projFilePath = None
		if not projPathCandidates: 
			logging.warning( 'no FMOD project path specified:' + configPath )
			return False
		
		candidates = None
		if isinstance( projPathCandidates, str ) or isinstance( projPathCandidates, str ):
			candidates = [ projPathCandidates ]
		elif isinstance( projPathCandidates, list ):
			candidates = projPathCandidates

		cadidateProjFilePath = None
		for candidate in candidates:
			if candidate.endswith( '.fspro' ):
				cadidateProjFilePath = candidate
				candidate = os.path.dirname( candidate )
			elif os.path.isdir( candidate ):
				for f in os.listdir( candidate ):
					if f.endswith( '.fspro' ):
						cadidateProjFilePath = candidate + '/' + f
						break
			if cadidateProjFilePath and os.path.isfile( cadidateProjFilePath ):
				projFilePath = cadidateProjFilePath
				projPath = candidate

		if projType == 'source': #try build source
			if projFilePath:

				succ = buildFMODStudioProject( 
					projFilePath,
					# banks = ['Character','Vehicles'],
					# diagnostic = True
					ignore_warnings = True
				)
				if succ:
					print('succeed building FMOD project:' + projFilePath)
				else:
					logging.warning( 'fail building FMOD project:' + projFilePath )

			else:
				logging.warning( 'skip building due to missing FMOD project file:' + repr( projPathCandidates ) )

		if projPath:
			#copy built files
			buildPath = projPath + '/Build'
			localBuildPath = filePath + '/Build'

			localDataPath = node.getFilePath() + '/Build/.*'

			if os.path.isdir( buildPath ):
				if os.path.exists( localBuildPath ):
					shutil.rmtree( localBuildPath )
				ignore = shutil.ignore_patterns( '.*' )
				shutil.copytree( buildPath, localBuildPath, ignore )			
				#clear modifystate
				# node.fileTime = time.time()
				# node.modifyState = None
				# for child in node.children:
					#	self.getAssetLibrary().unregisterAssetNode( child )
			else:
				logging.warning( 'cannot find FMOD build files:' + buildPath )
				
		else:
			logging.warning( 'skip copying built files' )

		#rebuild virtual nodes
		return self.rebuildChildNodes( node )

	def rebuildChildNodes( self, node ):
		_MOCK.releaseAsset( node.getPath() )
		t = _MOCK.loadAsset( node.getPath() )
		if not t : return False
		( proj, luaAssetNode ) = t
		if not proj: return False

		strings = proj.getStrings( proj )
		eventRootNode     = node.affirmChildNode( 'event',    'fs_folder', manager = 'asset_manager.fmod_studio' )
		snapshotRootNode  = node.affirmChildNode( 'snapshot', 'fs_folder', manager = 'asset_manager.fmod_studio' )
		bankRootNode      = node.affirmChildNode( 'bank',     'fs_folder', manager = 'asset_manager.fmod_studio' )
		busRootNode       = node.affirmChildNode( 'bus',      'fs_folder', manager = 'asset_manager.fmod_studio' )
		eventRootNode.groupType    = 'package'
		snapshotRootNode.groupType = 'package'
		bankRootNode.groupType     = 'package'
		busRootNode.groupType      = 'package'
		
		def _affirmChildNode( rootNode, itemType, path ):
			parts = path.split( '/' )
			itemName = parts[ -1 ]
			currentNode = rootNode
			for p in parts[ :-1 ]:
				if p:
					currentNode = currentNode.affirmChildNode( p, 'fs_folder', manager = 'asset_manager.fmod_studio' )
					currentNode.groupType = 'package'
			node = currentNode.affirmChildNode( itemName, itemType, manager = 'asset_manager.fmod_studio' )
			return node

		for path, guid in list(strings.items()):
			resType, itemPath = path.split( ':/' )
			itemNode = None
			if resType == 'event':
				itemNode = _affirmChildNode( eventRootNode, 'fs_event', itemPath )

			elif resType == 'snapshot':
				itemNode = _affirmChildNode( snapshotRootNode, 'fs_event', itemPath )

			elif resType == 'bus':
				#TODO
				pass

			elif resType == 'bank':
				#TODO
				pass

			if itemNode:
				itemNode.setProperty( 'guid', guid )
				itemNode.setProperty( 'path', path )

		return True

##----------------------------------------------------------------##
FMODStudioAssetManager().register()
FMODStudioAssetCreator().register()

AssetLibrary.get().setAssetIcon( 'fs_project',   'fmod_studio' )
AssetLibrary.get().setAssetIcon( 'fs_folder',    'fmod_group' )
AssetLibrary.get().setAssetIcon( 'fs_event',     'audio' )
# AssetLibrary.get().setAssetIcon( 'fs_snapshot',     'audio' )
# AssetLibrary.get().setAssetIcon( 'fs_bank',     'audio' )


if __name__ == '__main__':
	testFile = '/Volumes/data/audio/fmod/EWAudio/eastward.fspro'
	buildFMODStudioProject( 
		testFile,
		banks = ['Character','Vehicles'],
		# diagnostic = True
		ignore_warnings = True
	)
