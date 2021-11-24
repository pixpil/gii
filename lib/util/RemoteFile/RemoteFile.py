# -*- coding: utf-8 -*-
import re
import io
import sys
import os
import shutil
import tempfile
import json
import logging
import dirsync

##----------------------------------------------------------------##
def _fixPath( path ):
		path = path.replace( '\\', '/' ) #for windows
		if path.startswith('./'): path = path[2:]
		return path	

##----------------------------------------------------------------##
def _makePath( base, path ):
	if path:
		return base + '/' + path
	else:
		return base

##----------------------------------------------------------------##
def _affirmPath( path ):
	if os.path.exists( path ): return True
	try:
		os.mkdir( path )
		return True
	except Exception as e:
		return False


##----------------------------------------------------------------##
class RemoteFileProvider(object):
	def init( self ):
		pass

	def stopWatch( self, protocol, sourcePath, context = None ):
		return False

	def stopWatchTree( self, protocol, sourcePath, context = None ):
		return False

	def watch( self, protocol, sourcePath, context = None ):
		return False

	def watchTree( self, protocol, sourcePath, context = None ):
		return False

	def fetch( self, protocol, sourcePath, targetPath, context = None ):
		return False

	def fetchTree( self, protocol, sourcePath, targetPath, context = None ):
		return False

	def getTimestamp( self, protocol, sourcePath, context = None ):
		return 0

	def getFileURL( self, protocol, sourcePath, context = None ):
		return None

##----------------------------------------------------------------##
class RemoteFileManager(object):
	"""docstring for RemoteFileManager"""
	ProtocolMatch = re.compile( '(\w+)::(.*)' )

	_singleton=None
	@staticmethod
	def get():
		return RemoteFileManager._singleton

	def __init__(self):
		assert not RemoteFileManager._singleton
		RemoteFileManager._singleton=self
		self.providers = []

	def registerProvider( self, provider ):
		self.providers.append( provider )

	def init( self ):
		for p in self.providers:
			p.init()

	def splitProtocol( self, src ):
		mo = RemoteFileManager.ProtocolMatch.match( src )
		if mo:
			return mo.group( 1 ), mo.group( 2 )
		else:
			return None, src

	def watch( self, sourcePath, context ):
		p, f = self.splitProtocol( sourcePath )
		for provider in self.providers:
			if provider.watch( p, f, context ):
				return True
			if not context.running: return False

	def stopWatch( self, sourcePath, context ):
		p, f = self.splitProtocol( sourcePath )
		for provider in self.providers:
			if provider.stopWatch( p, f, context ):
				return True
			if not context.running: return False

	def checkModified( self, sourcePath, context ):
		t = context.getFileTime( sourcePath )
		t1 = self.getTimestamp( sourcePath, context )
		if t1 > t:
			context.result = True
			return context.finish()

	def fetch( self, sourcePath, targetPath, context ):
		p, f = self.splitProtocol( sourcePath )
		for provider in self.providers:
			if provider.fetch( p, f, targetPath, context ):
				t = provider.getTimestamp( p, f, context )
				context.setFileTime( sourcePath, t )
				return True
			if not context.running: return False
		return context.skip( 'no valid provider found:' + sourcePath )

	def fetchTree( self, sourcePath, targetPath, context ):
		p, f = self.splitProtocol( sourcePath )
		for provider in self.providers:
			if provider.fetchTree( p, f, targetPath, context ):
				t = provider.getTimestamp( p, f, context )
				context.setFileTime( sourcePath, t )
				return True
			if not context.running: return False
		return context.skip( 'no valid provider found:' + sourcePath )

	def getTimestamp( self, sourcePath, context ):
		p, f = self.splitProtocol( sourcePath )
		for provider in self.providers:
			stamp = provider.getTimestamp( p, f, context )
			if type( stamp ) in ( int, float ):
				return stamp
		return 0

	def appendFileURL( self, sourcePath, targetPath, context ):
		p, f = self.splitProtocol( sourcePath )
		files = context.getInfo( 'files' )
		for provider in self.providers:
			url = provider.getFileURL( p, f, context )
			if url:
				entry = {
					'target' : targetPath,
					'source' : sourcePath,
					'url' : url,
				}
				files.append( entry )
			if not context.running: return False

##----------------------------------------------------------------##
class RemoteFileContext(object):
	def __init__( self, rule ):
		self.option = {}
		self.rule = rule
		self.baseDir     = tempfile.mkdtemp()
		self.currentDir  = self.baseDir
		self.dirStack = []
		self.fileMetaTable = {}
		self.info = {}
		self.rootType = None
		self.rootPath = None
		self.ruleName = 'unkown'
		
		self.skipping = False

		self.stopped = False
		self.running = True
		self.stopReason = ''

		self.result  = None

	def __del__(self):
		shutil.rmtree( self.baseDir )

	def stop( self, reason ):
		self.stopReason = reason
		self.stopped = True
		self.running = False

	def skip( self, reason ):
		logging.warning( 'skipping: {0}'.format( str(reason) ) )
		self.skipping = True

	def finish( self ):
		self.stopped = False
		self.running = False

	def pushDir( self, path ):
		self.dirStack.append( self.currentDir )
		self.currentDir = path

	def popDir( self ):
		if self.dirStack:
			self.currentDir = self.dirStack.pop()
		else:
			assert self.currentDir, 'no more dir to pop'

	def getRule( self ):
		return self.rule

	def getCurrentDir( self ):
		return self.currentDir

	def getBaseDir( self ):
		return self.baseDir

	def setRoot( self, rootType, path ):
		if self.rootType:
			logging.warning( 'multiple root node for remote file rule:'+self.ruleName )
			return False
		self.rootType = rootType
		self.rootPath = path
		return True

	def getFileMetaDict( self, filename ):
		return self.fileMetaTable.get( filename, None )

	def affirmFileMetaDict( self, filename ):
		d = self.getFileMetaDict( filename )
		if d == None:
			d = {}
			self.fileMetaTable[ filename ] = d
		return d

	def setFileMeta( self, filename, key, value ):
		d = self.affirmFileMetaDict( filename )
		d[ key ] = value

	def getFileMeta( self, filename, key, value = None ):
		d = self.getFileMetaDict( filename )
		if not d: return value
		return d.get( key, value )

	def setFileTime( self, filename, timestamp ):
		self.setFileMeta( filename, 'mtime', timestamp )

	def getFileTime( self, filename ):
		return self.getFileMeta( filename, 'mtime', -1 )

	def getInfo( self, key, default = None ):
		return self.info.get( key, default )

	def setInfo( self, key, value ):
		self.info[ key ] = value

##----------------------------------------------------------------##
class RemoteFileRuleNode( object ):
	def __init__( self ):
		self.name     = None
		self.children = []
		self.parent   = None
		self.indent   = -1
		self.depth    = -1
		self.args     = []

	def isRoot( self ):
		return self.depth == 0

	def addChild( self, n ):
		n.parent = self
		self.children.append( n )
		n.depth	 = self.depth + 1
		return n

	def _checkModified( self, context ):
		res = self.checkModified( context )
		if res: return True

	def checkModified( self, context ):
		return True

	def execute( self, op, context ):
		pass

	def executeOnChildren( self, op, context, **options ):
		accept = options.get( 'accept', None )
		for childNode in self.children:
			if accept and ( not type( childNode ) in accept ): continue
			childNode.execute( op, context )
			if not context.running:
				return False
		
	def getArg( self, idx, default = None ):
		if idx < len( self.args ):
			return self.args[ idx ]
		else:
			return default

	def getArgCount( self ):
		return len( self.args )


##----------------------------------------------------------------##
class RemoteFileRuleNodeFolder(RemoteFileRuleNode):
	'''
	create a folder with given name ( or root name ) if not exists
	'''

	def execute( self, op, context ):
		targetPath = None
		if self.isRoot():
			targetPath = context.currentDir + '/root'
			if not context.setRoot( 'dir', targetPath ):
				return context.stop( 'remote rule root type already set' )
		else:
			name = self.getArg( 1 )
			if not name:
				return context.stop( 'folder name is required for non root node' )
			targetPath = context.currentDir + '/' + name

		if op == 'pull':
			if not _affirmPath( targetPath ):
				return context.stop( 'failed to create local directory:' + targetPath )

		context.pushDir( targetPath )
		self.executeOnChildren( op, context,
			accept = [ RemoteFileRuleNodeFolder, RemoteFileRuleNodeFile, RemoteFileRuleNodeTree ]
		)
		context.popDir()

##----------------------------------------------------------------##
class RemoteFileRuleNodeFile(RemoteFileRuleNode):
	'''
	fetch file from source url
	'''
	def execute( self, op, context ):
		if self.getArgCount() == 1:
			sourcePath = self.getArg( 0 )
			targetName = os.path.basename( sourcePath )
		elif self.getArgCount() > 1:
			targetName = os.path.basename( self.getArg( 0 ) )
			sourcePath = self.getArg( 1 )
		else:
			return context.stop( 'invalid file rule params, syntax: file <src> | file <tgt> <src>' )

		targetPath = context.getCurrentDir() + '/' + targetName
		if self.isRoot():
			if not context.setRoot( 'file', targetPath ):
				return context.stop( 'rule root type already set' )

		manager = RemoteFileManager.get()

		if op == 'pull':
			manager.fetch( sourcePath, targetPath, context )
		elif op == 'checkModified':
			manager.checkModified( sourcePath, context )
		elif op == 'watch':
			manager.watch( sourcePath, context )
		elif op == 'stopWatch':
			manager.stopWatch( sourcePath, context )
		elif op == 'getURL':
			manager.appendFileURL( sourcePath, targetName, context )

##----------------------------------------------------------------##
class RemoteFileRuleNodeTree(RemoteFileRuleNode):
	'''
	fetch tree from target url
	'''
	def execute( self, op, context ):
		if self.getArgCount() == 1:
			sourcePath = self.getArg( 0 )
			targetName = os.path.basename( sourcePath )
		elif self.getArgCount() > 1:
			targetName = os.path.basename( self.getArg( 0 ) )
			sourcePath = self.getArg( 1 )
		else:
			return context.stop( 'invalid tree rule params, syntax: tree <src> | tree <tgt> <src>' )

		if self.isRoot():
			targetPath = context.currentDir + '/root'
			if not context.setRoot( 'dir', targetPath ):
				return context.stop( 'rule root type already set' )
		else:
			targetPath = context.getCurrentDir() + '/' + targetName
			
		manager = RemoteFileManager.get()
		if op == 'pull':
			manager.fetchTree( sourcePath, targetPath, context )
		elif op == 'checkModified':
			manager.checkModified( sourcePath, context )
		elif op == 'watch':
			manager.watch( sourcePath, context )
		elif op == 'stopWatch':
			manager.stopWatch( sourcePath, context )
##----------------------------------------------------------------##
class RemoteFileRuleNodeRename(RemoteFileRuleNode):
	'''
	rename fetched file with specified regex rule
	'''
	#TODO
	pass


# ##----------------------------------------------------------------##
# class RemoteFileRuleNodeKeep(RemoteFileRuleNode):
# 	'''
# 	rename fetched file with specified regex rule
# 	'''
# 	def execute( self, op, context ):
# 		pass


_Name2RuleNodeClass = {
	'folder' : RemoteFileRuleNodeFolder,
	'file'   : RemoteFileRuleNodeFile,
	'rename' : RemoteFileRuleNodeRename,
	'tree'   : RemoteFileRuleNodeTree,
	# 'keep'   : RemoteFileRuleNodeKeep,
}

##----------------------------------------------------------------##
class RemoteFileRule( object ):
	LineMatch = re.compile( '(\t*)(.*)' )
	SpanMatch = re.compile( '[^\s]+' )

	def __init__( self ):
		self.userdata = None

	def getUserData( self ):
		return self.userdata

	def setUserData( self, ud ):
		self.userdata = ud

	def parseFile( self, path ):
		fp = io.open( path, 'rt', encoding = 'utf-8' )
		source = fp.read()
		fp.close()
		return self.parse( source )

	def reset( self ):
		self.parsingLongNode = False
		self.rootNode = RemoteFileRuleNode()
		self.rootNode.indent = -1
		self.contextNode = self.rootNode
		self.prevNode    = None
		self.lineId      = 0

	def parse( self, source ):
		self.reset()
		for line in source.split( '\n' ):
			self.lineId += 1
			self._parseLine( line )
		return self

	def _parseLine( self, line ):
		indentSize = 0
		if not line.strip(): return False
		if line.strip().startswith( '//' ): return False

		mo = RemoteFileRule.LineMatch.match( line )
		content = mo.group( 2 )
		
		indentSize   = len( mo.group(1) )
		parts = RemoteFileRule.SpanMatch.findall( content )
		if not parts: return False
 
		if self.prevNode:
			if indentSize == self.prevNode.indent:
				pass #do nothing

			elif indentSize > self.contextNode.indent: #INCINDENT
				self.contextNode = self.prevNode

			else:
				while indentSize <= self.contextNode.indent:
					self.contextNode = self.contextNode.parent

		nodeClas = _Name2RuleNodeClass.get( parts[0], None )
		if not nodeClas:
			print(line)
			logging.warning( 'unkown remote file node rule "%s"' % parts[0] )
			return False
		node = nodeClas()
		node.indent = indentSize
		node.args = parts[1:]
		self.contextNode.addChild( node )
		self.prevNode = node
	
	def stopWatch( self ):
		context = self.execute( 'stopWatch' )
		return context.result 

	def watch( self ):
		context = self.execute( 'watch' )
		return context.result 

	def checkModified( self, fileMetaTable ):
		context = self.execute( 'checkModified', fileMetaTable )
		return context.result 

	def getURL( self, fileMetaTable = None, **option ):
		context = RemoteFileContext( self )
		files = []
		context.setInfo( 'files', files )
		self.execute( 'getURL', fileMetaTable, context, **option )
		return files, context

	def pull( self, targetPath, fileMetaTable = None, **option ):
		context = self.execute( 'pull', fileMetaTable, **option )
		if context.stopped:
			logging.warning( 'remote file rule stopped:' + context.stopReason )
			return False, context

		rootPath = context.rootPath
		if not rootPath:
			return True, context

		if os.path.isfile( rootPath ):
			shutil.copy2( str(rootPath), str(targetPath) )

		elif os.path.isdir( rootPath ):
			canPurge = True
			if context.skipping: canPurge = False

			metaPath = targetPath + '/.assetmeta'
			hasMeta = os.path.isdir( metaPath )
			if hasMeta:
				#keep asset meta dir
				metaTmp = tempfile.mkdtemp()
				dirsync.sync( str(metaPath), str(metaTmp), 'sync', create=True )
			
			dirsync.sync( str(rootPath), str(targetPath), 'sync', purge = canPurge, create=True, verbose = True )
			
			if hasMeta:
				#restore asset meta dir
				dirsync.sync( str(metaTmp), str(metaPath), 'sync', create=True )
		
		return True, context

	def execute( self, op, fileMetaTable = None, context = None, **option ):
		#fetch files into tmp folder 
		if not context:
			context = RemoteFileContext( self )

		if fileMetaTable != None:
			context.fileMetaTable = fileMetaTable
		context.option = option
		
		if not self.rootNode.children: return context

		firstNode = self.rootNode.children[ 0 ]
		firstNode.execute( op, context )
		
		return context

##----------------------------------------------------------------##
RemoteFileManager()

def registerRemoteFileProvider( provider ):
	RemoteFileManager.get().registerProvider( provider )

##----------------------------------------------------------------##
#COMMON Provider
class LocalRemoteFileProvider( RemoteFileProvider ):
	# def watch( self, protocol, sourcePath, context  ):
	# 	if protocol != 'file': return False
	# 	print 'watch', sourcePath
	# 	return False

	def fetch( self, protocol, sourcePath, targetPath, context ):
		if protocol != 'file': return False
		if os.path.isfile( sourcePath ):
			shutil.copy2( sourcePath, targetPath )
		else:
			return context.skip( 'source file not found:' + sourcePath )
		return True

	def fetchTree( self, protocol, sourcePath, targetPath, context ):
		if protocol != 'file': return False
		if os.path.isfile( sourcePath ):
			shutil.copy2( sourcePath, targetPath )
		elif os.path.isdir( sourcePath ):
			shutil.copytree( sourcePath, targetPath )
		else:
			return context.skip( 'source file/directory not found:' + sourcePath )
		return True

	def getTimestamp( self, protocol, sourcePath, context ):
		if protocol != 'file': return False
		if os.path.isfile( sourcePath ):
			return os.path.getmtime( sourcePath )
		elif os.path.isdir( sourcePath ):
			#TODO?
			return self._getDirMTime( sourcePath )
		return 0

	def _getDirMTime( self, path ):
		mtime = 0
		for currentDir, dirs, files in os.walk( path ):
			for filename in files:
				mtime1 = os.path.getmtime( currentDir + '/' + filename )
				if mtime1 > mtime:
					mtime = mtime1
			dirs2 = dirs[:]
			for dirname in dirs2:
				mtime1 = os.path.getmtime( currentDir + '/' + dirname )
				if mtime1 > mtime:
					mtime = mtime1
		return mtime

	def getFileURL( self, protocol, sourcePath, context ):
		if protocol != 'file': return False
		return sourcePath

registerRemoteFileProvider( LocalRemoteFileProvider() )

__all__ = [
	'RemoteFileProvider',
	'RemoteFileManager',
	'registerRemoteFileProvider',
	'RemoteFileContext',
	'RemoteFileRuleNode',
	'RemoteFileRuleNodeFolder',
	'RemoteFileRuleNodeFile',
	'RemoteFileRuleNodeTree',
	'RemoteFileRuleNodeRename',
	# 'RemoteFileRuleNodeKeep',
	'RemoteFileRule',
	'LocalRemoteFileProvider',
]

##----------------------------------------------------------------##
if __name__ == '__main__':
	text = '''
folder
	file sss.txt file::/Users/tommo/fmod_designer.log
	file aaa.txt file::/Users/tommo/pgadmin.log
	tree mmm file::/Users/tommo/fmod
'''
	
	import logging
	import json

	# def saveJSON( data, path, **option ):
	# 	outputString = json.dumps( data , 
	# 			indent    = option.get( 'indent' ,2 ),
	# 			sort_keys = option.get( 'sort_keys', True ),
	# 			ensure_ascii=False
	# 		).encode('utf-8')
	# 	fp = open( path, 'w' )
	# 	fp.write( outputString )
	# 	fp.close()
	# 	return True

	rule = RemoteFileRule().parse( text )
	meta = {}
	rule.watch()
	rule.pull( '/Users/tommo/tmp/remotetest', meta )
	os.utime( '/Users/tommo/fmod_designer.log', None )
	print(rule.checkModified( meta ))

	# data = node.toJSON()

	# saveJSON( data, 'test.json' )

