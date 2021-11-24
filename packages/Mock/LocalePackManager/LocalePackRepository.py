import os
import os.path
import shutil
import polib
import logging

##----------------------------------------------------------------##
from gii.core import *
from mock import _MOCK, isMockInstance, loadMockAsset


LOCALE_PACK_REPO_BASE_PATH = 'LocalePackRepos'
_localePackRepositoryFactories = []

##----------------------------------------------------------------##
def _affirmPath( path ):
	if os.path.exists( path ): return True
	try:
		os.mkdir( path )
		return True
	except Exception as e:
		return False

##----------------------------------------------------------------##
def _repalceDirFiles( src, dst, clear = False ):
	if clear:
		for n in os.listdir( dst ):
			if n.startswith( '.' ) : continue
			fullPath = dst + '/' + n
			if os.path.isfile( fullPath ):
				os.remove( fullPath )
	for n in os.listdir( src ):
		if n.startswith( '.' ) : continue
		srcPath = src + '/' + n
		dstPath = dst + '/' + n
		if os.path.isfile( srcPath ):
			shutil.copy( srcPath, dstPath )

##----------------------------------------------------------------##
def createLocalePackRepository( packPath ):
	assetNode = AssetLibrary.get().getAssetNode( packPath )
	remoteConfigPath = assetNode.getAbsFilePath() + '/remote.json'
	config = JSONHelper.tryLoadJSON( remoteConfigPath )
	if not config:
		logging.warning( 'no remote.json defined for locale pack:' + assetNode.getPath() )
		return None

	targetServiceName = config.get( 'service', None )
	if not targetServiceName:
		logging.warning( 'no remote service defined for locale pack:' + assetNode.getPath() )
		return None

	targetURL = config.get( 'url', None )
	if not targetURL:
		logging.warning( 'no remote URL defined for locale pack:' + assetNode.getPath() )
		return None

	repo = None
	for factory in _localePackRepositoryFactories:
		if targetServiceName != factory.getServiceName(): continue
		localPath = factory.rootPath + '/' + assetNode.getMangledName()
		repo = factory.create( assetNode, localPath, targetURL, 'master' )
		_affirmPath( localPath )

	if not repo:
		logging.warning( 'no remote service found for locale pack:' + assetNode.getPath() )
		return None

	return repo


##----------------------------------------------------------------##
class LocalePackRepositoryFactory(object):
	def register( self ):
		_localePackRepositoryFactories.append( self )
		#affirm workpath
		workBasePath = app.getProject().getWorkspacePath( LOCALE_PACK_REPO_BASE_PATH )
		_affirmPath( workBasePath )
		self.rootPath = workBasePath + '/' + self.getServiceName()
		_affirmPath( self.rootPath )
	
	def getServiceName( self ):
		raise Exception( 'override this' )

	def isActive( self ):
		#TODO: use project setting?
		return True

	def create( self, packAssetNode, localPath, repoURL, repoBranch ):
		return None



##----------------------------------------------------------------##
class LocalePackRepository( object ):
	def __init__( self, packAssetNode, localPath, repoURL, repoBranch ):
		self.packAssetNode = packAssetNode
		self.localPath = localPath
		self.repoURL  = repoURL
		self.repoBranch = repoBranch

	def getPackAssetNode( self ):
		return self.packAssetNode

	def getURL( self ):
		return self.repoURL

	def getPath( self ):
		return self.localPath

	def getSourcePath( self ):
		pass

	def updatePO( self, localeId, src, dst ):
		pot = polib.pofile( src )
		if not os.path.exists( dst ):
			#initialize from pot
			po = polib.pofile( str( pot ) )
			po.metadata[ 'Language' ] = localeId.replace( '-', '_' )
			#remove msgstr
			for entry in po:
				entry.msgstr = ''
				entry.msgstr_plural = ''
			po.save( dst )
		else:
			#merge with pot
			po = polib.pofile( dst )
			if not po:
				logging.warn( 'invalid pofile:' + dst )
				return False
			po.merge( refpot = pot )
			po.save( dst )

	def updateLocaleFromTemplate( self, localeId, localePath, templatePath ):
		_affirmPath( localePath )
		for n in os.listdir( templatePath ):
			if n.startswith( '.' ) : continue
			srcPath = templatePath + '/' + n
			name, ext  = os.path.splitext( n )
			if ext == '.pot':
				dstPath = localePath + '/' + name + '.po'
				self.updatePO( localeId, srcPath, dstPath )
			else:
				pass

	def update( self, pull = True, push = True, merge = True, store = True ):
		packFilePath = self.packAssetNode.getAbsFilePath()
		localPath = self.localPath
		localesPath = localPath + '/locales'

		mockPack = loadMockAsset( self.packAssetNode.getPath() )
		mockLocaleManager = _MOCK.getLocaleManager()
		locales = [ id for id in list(mockLocaleManager.locales.values()) ]
		sourceLocale = mockLocaleManager.sourceLocale

		if pull:
			#pull/ initialize
			try:
				self.onPull()
			except Exception as e:
				#TODO: do something
				logging.error( e )
				return False
		
		_affirmPath( localesPath )
		if merge:
			#copy source files ( overwrite )
			packSourcePath = packFilePath + '/' + 'source'
			if not os.path.exists( packSourcePath ):
				logging.warning( 'pack source not built yet' )
				return False
			
			for n in os.listdir( packSourcePath ):
				if n.startswith( '.' ) : continue
				srcPath = packSourcePath + '/' + n
				if os.path.isdir( srcPath ):
					dstPath = localesPath + '/' + n
					_affirmPath( dstPath )
					_repalceDirFiles( srcPath, dstPath, clear = False )

			#update other locales
			#merge/use POFile
			templatesPath = packSourcePath + '/templates'
			for localeId in locales:
				if localeId == sourceLocale: continue #skip sourcelocale
				localePath = localesPath + '/' + localeId
				self.updateLocaleFromTemplate( localeId, localePath, templatesPath )

		#push
		if push:
			try:
				self.onPush()
			except Exception as e:
				#TODO: do something
				logging.error( e )
				return False

		if store:
			#copy pulled result into
			packLocalesPath = packFilePath + '/' + 'locales'
			shutil.rmtree( packLocalesPath )
			shutil.copytree( localesPath, packLocalesPath )

		return True

	#callbacks
	def onPull( self ):
		pass

	def onPush( self ):
		pass
