import sys
import os
import os.path
from gii.FileWatcher import FileWatch

from gii.core 		import *
from gii.core           import EditorModule

from qtpy 				import QtCore
from qtpy.QtCore import QTimer


##----------------------------------------------------------------##
def affirmPath( path ):
	if os.path.exists( path ): return True
	try:
		os.mkdir( path )
		return True
	except Exception as e:
		return False

def affirmFile( path ):
	if os.path.exists(path): return True
	try:
		open( path, 'w').close()
		return True
	except Exception as e:
		return False
##----------------------------------------------------------------##
class ExternalEditTransferSessionFactory():
	def build(self,guid,sessionType,option):
		return None
		
##----------------------------------------------------------------##
class ExternalEditTransferSession():
	def modified(self):
		pass

	def removed(self):
		pass

	def ocess(self,path,status):
		pass

	def openExternalEdit(self):
		pass

	def getId(self):
		return None

##----------------------------------------------------------------##
class ExternalEditTransferManager( EditorModule ):
	name = 'external_edit_manager'
	dependency = [ 'file_watcher' ]

	_sessionFactories = []
	_sessions = {}
	sessionsData = {}
	sessionsData['guids'] = []

	def onLoad(self):
		self.watchedFolder = self.getProject().getWorkspacePath( 'ExternalEdit' )
		self.sessionsFolder = self.getProject().getWorkspacePath( 'ExternalEditSessions' )
		affirmPath( self.watchedFolder )
		affirmPath( self.sessionsFolder )
		self.sessionsFilePath = self.sessionsFolder + '/sessions'
		affirmFile( self.sessionsFilePath )
		
	def onStart(self):	
		self.fileWatch = ExternalEditTransferFileWatch()
		self.fileWatch.ownerModule = self
		self.fileWatch.register()
		externalFile = open( self.sessionsFilePath, 'r')
		content = externalFile.read()
		if content:
			sessionsdata = JSONHelper.loadJSON(self.sessionsFilePath)
			for guid in sessionsdata['guids']:
				sessionType = sessionsdata[guid]['sessionType']
				options = sessionsdata[guid]['options']
				self.requestSession(guid,sessionType,options)

	def registerExternalEditSession(self, sessionFactory ):
		if isinstance(sessionFactory, ExternalEditTransferSessionFactory):
			self._sessionFactories.append(sessionFactory)

	def requestSession( self, guid, sessionType, options ):
		for sessionFactory in self._sessionFactories:
			session = sessionFactory.build( guid, sessionType, options )
			if session:
				sessionid = session.getId()
				if self._sessions.get(sessionid):
					session = self._sessions.get(sessionid)
				else:
					self._sessions[sessionid] = session
					self.sessionsData['guids'].append(guid)
					self.sessionsData['guids'] = list( set( self.sessionsData['guids'] ) )
					self.sessionsData[ guid ] = { 'sessionType' : sessionType, 'options' : options}
					JSONHelper.trySaveJSON( self.sessionsData, self.sessionsFilePath, 'session_data')
				return session
		return None
	
	def flushFileStatus( self, path, id, status ):
		session = self._sessions.get( id )
		if session:
			session.onProcess( path, status )
		pass

##----------------------------------------------------------------##
class ExternalEditTransferFileWatch(FileWatch):
	def __init__( self ):
		super( ExternalEditTransferFileWatch, self ).__init__()
		self.fileStatusMap = {}
		self.timer = None
		self.ownerModule = None

	def getPath( self ):
		return self.ownerModule.watchedFolder

	def onFileMoved( self, path, newpath ):
		self.markDirty()
		self.fileStatusMap[path] = 'removed'
		self.fileStatusMap[newpath] = 'modified'

	def onFileCreated( self, path ):
		self.markDirty()
		self.fileStatusMap[path] = 'modified'

	def onFileModified( self, path ):
		self.markDirty()
		self.fileStatusMap[path] = 'modified'

	def onFileDeleted( self, path ):
		self.markDirty()
		self.fileStatusMap[path] = 'removed'

	def markDirty( self ):
		self.timer.start()

	def onStart( self ):
		self.timer = QtCore.QTimer()
		self.timer.timeout.connect( self.flushFileStatus )
		self.timer.setInterval( 100 )
		self.timer.setSingleShot( True )

	def onStop( self ):
		if self.timer:
			self.timer.stop()

	def flushFileStatus( self ):
		for path, status in list(self.fileStatusMap.items()):
			if os.path.isfile(path):
				dirname, filename = os.path.split( path )
				dirname, guid = os.path.split( dirname )
				app.getModule('external_edit_manager').flushFileStatus( path, guid, status )
		self.fileStatusMap = {}
