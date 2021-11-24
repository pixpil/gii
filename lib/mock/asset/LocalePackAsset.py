import os
import os.path
import shutil
import tempfile
import io
import io
import re
import time

import dirsync

import logging
import ujson as json

from gii.core import *
from mock import _MOCK, loadMockAsset

import polib

##----------------------------------------------------------------##
LOCALE_PACK_CONFIG_NAME = 'locale_pack.json'

OVERVIEW_HEAD = '''
<!DOCTYPE html>
<html>
<head>
	<style>
		body {
			background-color: #aaa;
		}

		file {
			display: block;
			border: 1px solid;
			border-radius: 5px;
			margin: 2em;
			padding: 1em;
			background-color: white;
		}

		info {
			display: block;
			font-weight: bold;
			color: #000;
		}
		entries {
			display: block;
			margin-top: 1em;
		}
		entry {
			display: block;
			border-top: 1px dotted #aaa;
			margin-bottom: 1em;
		}

		id {
			margin-left:1em;
			display: block;
			font-size:.8em;
			color:#ddd;
		}
		ctx {
			margin-left:1em;
			display: block;
			font-size:.8em;
			color:#edd;
		}
		text {
			display: block;
			font-size:1.2em;
			padding-left: 2em;
			margin-bottom: 10px;
			color: #573C27;
		}
		pre{
			margin:0;
			padding:0.5em;
		}
	</style>
</head>
'''

OVERVIEW_FOOT = '''
</html>
'''
##----------------------------------------------------------------##
def makeLocaleOverview( outputPath, packPath, pofiles, basePofiles ):
	# output = cStringIO.StringIO()
	output = open( outputPath, mode = 'w', encoding = 'utf-8' )
	output.writelines([
		OVERVIEW_HEAD,
		'<body>'
		'<title>PACK NAME: %s</title>' % packPath,
		'<title>DATE: %s</title>' % time.strftime('%H:%M:%S %Z %A %Y-%m-%d '),
	])
	for name, po in pofiles.items():
		fileOutput = io.StringIO()
		count = 0
		basePO = None
		if basePofiles:
			basePO = basePofiles.get( name, None )

		for entry in po:
			count += 1
			if entry.msgid_plural:
				#TODO: plural support
				pass
			else:
				msgid = polib.escape( entry.msgid )
				msgstr = polib.escape( entry.msgstr )
				msgctxt = polib.escape( entry.msgctxt )

				if ( not msgstr ) and basePO:
					baseEntry = basePO.find( msgid )
					if baseEntry:
						msgstr2 = polib.escape( baseEntry.msgstr )
						if msgstr2:
							msgstr = msgstr2

				fileOutput.write ( '<entry>\n' )
				fileOutput.write ( '<id>id:%s</id>\n' % msgid )
				if msgctxt:
					fileOutput.write ( '<ctx>ctx:%s</ctx>\n' % msgctxt )
				if msgstr:
					fileOutput.write( '<text><pre>')
					msgstr = msgstr.replace( '\\n', '\n' )
					msgstr = msgstr.replace( '\\t', '\t' )
					fileOutput.write( '%s\n' % msgstr )
					fileOutput.write( '</pre></text>')
				fileOutput.write ( '</entry>\n' )
		output.writelines([
			'\n',
			'<file>\n',
			'<info>FILE: %s</info>\n' % name,
			'<info>count: %d</info>\n' % count,
			'<entries/>\n'
		])
		output.write( fileOutput.getvalue() )
		output.write( '\n')
		output.write( '</entries></file>\n')
	output.write( '</body>\n' )
	output.write( OVERVIEW_FOOT )
	output.close()


_assetLocaleDataExtractor = []
##----------------------------------------------------------------##
class AssetLocaleDataExtractor(object):
	def register( self ):
		global _assetLocaleDataExtractor
		_assetLocaleDataExtractor = [ self ] + _assetLocaleDataExtractor

	def acceptAssetNode( self, assetNode ):
		return False

	def preExtractLocaleData( self, assetNode, name, builder ):
		pass

	def extractLocaleData( self, assetNode, name, builder ):
		pass

	def postExtractLocaleData( self, assetNode, name, builder ):
		pass

##----------------------------------------------------------------##
def clonePOEntry( src ):
	tgt = polib.POEntry()
	tgt.msgid                 = src.msgid
	tgt.msgstr                = src.msgstr
	tgt.msgid_plural          = src.msgid_plural
	if src.msgstr_plural:
		tgt.msgstr_plural         = src.msgstr_plural
	tgt.msgctxt               = src.msgctxt
	tgt.obsolete              = src.obsolete
	tgt.encoding              = src.encoding
	tgt.msgid                 = src.msgid
	tgt.msgstr                = src.msgstr
	tgt.comment               = src.comment
	tgt.tcomment              = src.tcomment
	if src.occurrences:
		tgt.occurrences           = src.occurrences[:]
	if src.flags:
		tgt.flags                 = src.flags[:]
	tgt.previous_msgctxt      = src.previous_msgctxt
	tgt.previous_msgid        = src.previous_msgid
	tgt.previous_msgid_plural = src.previous_msgid_plural
	tgt.linenum               = src.linenum
	return tgt


##----------------------------------------------------------------##
def _affirmPath( path ):
	if os.path.exists( path ): return True
	try:
		os.mkdir( path )
		return True
	except Exception as e:
		return False

##----------------------------------------------------------------##
class TempDir(object):
	"""docstring for TempDir"""
	def __init__(self, **kwarg):
		self._dir=tempfile.mkdtemp(**kwarg)
	
	def __del__(self):
		shutil.rmtree(self._dir)

	def __call__(self, name):
		return self._dir+'/'+name

	def __str__(self):
		return self._dir

##----------------------------------------------------------------##
class LocalePackBuilder(object):
	def __init__( self, path, **option ):
		self.packPath = path
		self.packAssetNode = AssetLibrary.get().getAssetNode( self.packPath )
		self.tmpPath = TempDir()
		self.buildingTemplatesPath = self.tmpPath( 'templates' )
		_affirmPath( self.buildingTemplatesPath )
		self.POTFiles = {}
		self.outputMode = option.get( 'output_mode', 'single' )
		self.sourceLocale = None

	def affirmPOT( self, name, localeId = None ):
		po = self.POTFiles.get( name, None )
		if po: return po
		return self.addPOT( name, localeId )

	def addPOT( self, name, localeId = None ):
		#TODO: name checking?
		if self.POTFiles.get( name ):
			raise Exception( 'duplicated POT:' + name )
		path = self.buildingTemplatesPath + '/' + name + '.pot'
		pot = polib.POFile( fpath = path, wrapwidth = 0 )
		pot.metadata = {
			'Project-Id-Version'        : '1.0',
			'MIME-Version'              : '1.0',
			'Content-Type'              : 'text/plain; charset=utf-8',
			'Content-Transfer-Encoding' : '8bit',
			'Language'                  : localeId or self.sourceLocale,
			'Source-Name'               : name,
			'Export-Time'               : time.strftime('%H:%M:%S %Z %A %Y-%m-%d '),
		}
		self.POTFiles[ name ] = pot
		return pot

	def saveTextOverview( self ):
		pofiles = self.POTFiles
		outputDir = self.packAssetNode.getAbsFilePath() + '/.report'
		_affirmPath ( outputDir )
		outputPath = outputDir + '/overview.html'
		makeLocaleOverview( outputPath, self.packPath, pofiles, None )

	def savePOTFiles( self ):
		regex = re.compile( 'rev:(\w+)' )
		def _getEntryRevision( entry ):
			for f in entry.flags:
				mo = regex.match( f )
				if mo:
					return int( mo.group( 1 ) )
			return 0

		def _setEntryRevision( entry, revision ):
			for f in entry.flags:
				mo = regex.match( f )
				if mo:
					entry.flags.remove( mo.group(0) )
					break
			entry.flags.append( 'rev:%d' % revision )

		for name, pot in self.POTFiles.items():
			#set REVISION flags
			pot0Path = self.targetTemplatesPath + '/' + name + '.pot'
			if os.path.exists( pot0Path ):
				pot0 = polib.pofile( str( pot0Path) )
				entryMap = {}
				obsoleteEntries = []

				for entry in pot:
					entryMap[ entry.msgid ] = entry
					entry.obsolete = False
					_setEntryRevision( entry, 0 )

				for entry0 in pot0:
					entry = entryMap.get( entry0.msgid, None )
					if entry:
						revision0 = _getEntryRevision( entry0 )
						if entry.msgstr != entry0.msgstr: #Modfied
							_setEntryRevision( entry, revision0 + 1 )
						else:
							_setEntryRevision( entry, revision0 )

					else: #removed
						obsEntry = clonePOEntry( entry0 )
						obsoleteEntries.append( obsEntry )
						obsEntry.obsolete = True

				#insert obsolete entries
				for obsEntry in obsoleteEntries:
					pot.append( obsEntry )

			pot.save()

	def saveTargetPOFiles( self, localeId ):
		basePath = self.targetSourcePath + '/' + localeId
		_affirmPath( basePath )
		POLocaleId = localeId.replace( '-', '_' )
		for name, pot in self.POTFiles.items():
			#clone
			po = polib.pofile( str( pot ) )
			po.metadata[ 'Language' ] = POLocaleId
			for entry in po:
				if not entry.msgstr: entry.msgstr = entry.msgid
				if not entry.msgstr_plural: entry.msgstr_plural = entry.msgid_plural
			po.save( basePath + '/' + name + '.po' )

	def buildSource( self ):
		pack = loadMockAsset( self.packPath )
		if not pack: return False
		sourceLocale = pack.getSourceLocale( pack )
		self.sourceLocale = sourceLocale

		#update files
		packFilePath = self.packAssetNode.getFilePath()
		self.targetSourcePath    = targetSourcePath    = packFilePath + '/locales'
		self.targetTemplatesPath = targetTemplatesPath = packFilePath + '/templates'
			
		_affirmPath( targetSourcePath )
		_affirmPath( targetTemplatesPath )

		print('preparing to extract locale data')
		#extraction
		for item in list(pack[ 'items' ].values()):
			self.extractAssetLocaleData( 'pre', item )
		
		print('update asset library')
		AssetLibrary.get().importModifiedAssets()
		signals.dispatchAll()

		print('extracting data')
		for item in list(pack[ 'items' ].values()):
			self.extractAssetLocaleData( 'main', item )

		for item in list(pack[ 'items' ].values()):
			self.extractAssetLocaleData( 'post', item )

		print('done')
		self.savePOTFiles()
		self.saveTextOverview()

		#overwrite templates
		if os.path.exists( targetTemplatesPath ):
			shutil.rmtree( targetTemplatesPath )
		shutil.copytree( self.buildingTemplatesPath, targetTemplatesPath )

		#overwrite source_locale
		if sourceLocale:
			sourceLocalePath = targetSourcePath + '/' + sourceLocale
			if os.path.exists( sourceLocalePath ):
				shutil.rmtree( sourceLocalePath )
			self.saveTargetPOFiles( sourceLocale )

		return True

	def buildOutput( self ):
		pass

	def extractAssetLocaleData( self, phase, item ):
		path = item[ 'path' ]
		name = item[ 'name' ]
		assetLib = AssetLibrary.get()
		assetNode = assetLib.getAssetNode( path )
		if not assetNode: return False

		extractors = []
		for extractor in _assetLocaleDataExtractor:
			if extractor.acceptAssetNode( assetNode ):
				extractors.append( extractor )
		
		if not extractors:
			return None

		try:
			if phase == 'pre':
				for extractor in extractors:
					extractor.preExtractLocaleData( assetNode, name, self )
			
			elif phase == 'main':
				for extractor in extractors:
					extractor.extractLocaleData( assetNode, name, self )
			
			elif phase == 'post':
				for extractor in extractors:
					extractor.postExtractLocaleData( assetNode, name, self )

		except Exception as e:
			print('error in locale data extraction')
			return False

##----------------------------------------------------------------##
def fixLocaleName( l ):
	fixTable = {
		'zh-cn' : 'zh-CN',
		'zh-tw' : 'zh-TW',
		'Zh-CN' : 'zh-CN',
		'Zh-TW' : 'zh-TW',
		'zh-cn2' : 'zh-CN2',
	}
	return fixTable.get( l, l )

##----------------------------------------------------------------##
# convert PO into lua i18n format
##----------------------------------------------------------------##
class LocalePackCompiler(object):
	def __init__( self, packPath, localePath, outputPath ):
		self.packPath = packPath
		self.localePath = localePath
		self.outputPath = outputPath
		self.potfiles = None

	def compilePO( self, po ):
		#compile into Lua code
		output = io.StringIO()
		output.write( '{\n' )
		idSet = {}
		for entry in po:
			if entry.msgid_plural:
				#TODO: plural support
				msgid = polib.escape( entry.msgid_plural )
				output.write( '\t["%s"] = { \n' % msgid )
				for k, s in entry.msgstr_plural.items():
					msgstr = polib.escape( s )
					if msgstr:
						msgstr = msgstr.replace( '\\r', '' )
						output.write( '\t\t["%s"] = "%s",\n' % ( k, msgstr ) )
				output.write( '\t};\n' )
			else:
				msgid = polib.escape( entry.msgid )
				msgstr = polib.escape( entry.msgstr )
				if msgstr:
					msgstr = msgstr.replace( '\\r', '' )
					output.write( '\t["%s"] = "%s";\n' % ( msgid, msgstr ) )
			
			if idSet.get( msgid, None ): logging.warning( 'entry Id duplicated: %s, %s' % ( msgid, self.packPath ) )
			idSet[ msgid ] = True

		output.write( '\t};\n' )
		return output.getvalue()

	def compileLocale( self, localeId ):
		pofiles = {}
		srcPath = self.localePath
		path = srcPath + '/' + localeId
		if not os.path.isdir( path ): return False
		print('compiling locale', localeId)

		outputFilePath = self.outputPath + '/'+ localeId
		outputFile = open( outputFilePath, 'w', encoding = 'utf-8' )
		outputFile.write ( 'return {\n' )
		for n in os.listdir( path ):
			if n.startswith( '.' ) : continue
			print('compiling locale file', n)
			filePath = path + '/' + n
			name, ext = os.path.splitext( n )
			# outputFilePath = self.outputPath + '/' + name + '.' + localeId
			output = None
			if ext == '.po':
				po = polib.pofile( filePath )
				pofiles[ name ] = po
				output = self.compilePO( po )
			if output:
				outputFile.write( '["%s"]=' % name )
				outputFile.write( output )
		outputFile.write ( '}\n' )
		outputFile.close()

		overviewDir = self.packPath + '/.report'
		_affirmPath ( overviewDir )
		overviewPath = overviewDir + ( '/overview.%s.html' % localeId )
		makeLocaleOverview( overviewPath, self.packPath, pofiles, self.potfiles )

	def compile( self ):
		print('compiling locale pack', self.packPath)
		potPath = self.packPath + '/templates'
		potfiles = {}
		for n in os.listdir( potPath ):
			if n.startswith( '.' ) : continue
			name, ext = os.path.splitext( n )
			if ext == '.pot':
				filePath = potPath + '/' + n
				potfiles[ name ] = polib.pofile( filePath )
		self.potfiles = potfiles

		for n in os.listdir( self.localePath ):
			if n.startswith( '.' ) : continue
			if n == 'templates' : continue
			#TODO: only include necessary locales
			self.compileLocale( n )

##----------------------------------------------------------------##
class LocalePackAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.locale_pack'

	def getMetaType( self ):
		return 'misc'

	def acceptAssetFile(self, filepath):
		if not os.path.isdir(filepath): return False		
		name, ext = os.path.splitext(filepath)
		if not ext in ['.locale_pack']: return False
		data = JSONHelper.tryLoadJSON( filepath + '/' +  LOCALE_PACK_CONFIG_NAME )
		if not data:
			logging.warning( 'invalid locale pack config: ' + filepath )
			return False
		return True

	def importAsset(self, node, reload = False ):
		node.assetType = 'locale_pack'
		node.groupType = None
		node.setBundle()
		node.setObjectFile( 'config', node.getFilePath() + '/' + LOCALE_PACK_CONFIG_NAME )
		dataPath = node.getCacheFile( 'data', is_dir = True )
		node.setObjectFile( 'data', dataPath )
		#clear
		shutil.rmtree( dataPath )
		os.mkdir( dataPath )
		packPath = node.getFilePath()
		localePath = packPath + '/locales'
		if os.path.isdir( localePath ):
			compiler = LocalePackCompiler( packPath, localePath, dataPath )
			compiler.compile()
		return True

	def editAsset( self, node ):
		editor = app.getModule( 'locale_pack_manager' )
		if not editor: 
			return alertMessage( 'Editor not load', 'Locale Pack Manager not found!' )
		editor.locatePack( node )

	def syncExternal( self, node ):
		project = app.getProject()
		userSettings = project.getUserSetting( 'locale_manager', {} )
		externPath = userSettings.get( 'external_path', None )
		if not externPath:
			logging.warning( 'no external path defined' )
			return False

		if not os.path.isdir( externPath ):
			print(externPath)
			logging.warning( 'invalid external path: ' )
			return False

		packFilePath = node.getAbsFilePath()
		packName = node.getName()
		externSourcePath = externPath + '/source'
		externTranslationPath = externPath + '/translation'
		
		packTemplatePath = packFilePath + '/templates'
		packTranslationPath = packFilePath + '/locales'
		packConfigPath = packFilePath + '/' + LOCALE_PACK_CONFIG_NAME

		targetSourcePath = externSourcePath + '/' + packName
		targetTemplatePath = targetSourcePath + '/templates'
		targetConfigPath = targetSourcePath + '/' + LOCALE_PACK_CONFIG_NAME


		print(( 'start syncing locale pack', node.getPath() ))
		#sync template
		if os.path.isdir( packTemplatePath ):
			print( 'syncing templates' )
			dirsync.sync( packTemplatePath, targetTemplatePath, "sync", create = True )

		#sync config
		if os.path.isfile( packConfigPath ):
			shutil.copy( packConfigPath, targetConfigPath )

		#sync translation
		if os.path.isdir( externTranslationPath ):
			for lname in os.listdir( externTranslationPath ):
				#TODO: verify?
				externLocale = externTranslationPath + '/' + lname + '/' + packName
				if os.path.isdir( externLocale ):
					lnameFixed = fixLocaleName( lname )
					# if lnameFixed != 'ja': continue
					projLocale = packTranslationPath + '/' + lnameFixed
					print( 'syncing translation', lname )
					print( 'copy: {}->{}'.format( externLocale, projLocale ))
					dirsync.sync(
						externLocale, projLocale, 
						"sync", 
						create = True
					)

		print( 'done' )
		return True

##----------------------------------------------------------------##
class LocalePackAssetCreator(AssetCreator):
	def getAssetType( self ):
		return 'locale_pack'

	def getLabel( self ):
		return 'Locale Pack'

	def createAsset( self, name, contextNode, assetType ):		
		ext = '.locale_pack'
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
			'items' : [],
			'guid'   : generateGUID()
		}
		JSONHelper.trySaveJSON( emptyConfigFileData, fullPath + '/' + LOCALE_PACK_CONFIG_NAME )
		return nodePath

LocalePackAssetManager().register()
LocalePackAssetCreator().register()

AssetLibrary.get().setAssetIcon( 'locale_pack', 'locale_pack' )

