import os

from gii.moai.MOAIRuntime import MOAILuaDelegate
from gii.core import *
from gii.core.AssetUtils import *
from gii.ExternalEditTransfer import *
from mock import _MOCK, isMockInstance, getMockClassName


class ScriptEditSession( ExternalEditTransferSession ):
	def __init__( self, guid, sessionType, options ):
		self.target = None
		self.type = sessionType
		self.id = guid
		self.options = options
		self.path = app.getModule('external_edit_manager').watchedFolder + self.getPathName()
		affirmPath( self.path )
		self.filePath = None
		
		
	def getId( self ):
		return self.id

	def getPathName( self ):
		return "/%s/"%( self.id )

	def getExternalFileName( self ):
		self.target = self.findTarget()
		if not self.target:
			print('Can not find component')
			return
		entityName = self.target.getEntityName( self.target )
		comName = self.target['__name']
		filename = "%s_%s%s"%( entityName,comName, self.options.get( 'ext' ) )
		entity = self.target.findEntity( self.target, entityName )
		parent = entity.getParent( entity )
		while parent:
			ParentName = parent.getName( parent)
			filename = "%s_%s"%( ParentName, filename)
			parent = parent.getParent( parent)
		return filename

	def onModified( self  ):
		self.target = self.findTarget()
		if not self.target:
			print(( 'onModified, can\'t find script session target, guid: ', self.id ))
			return
		if not self.filePath:
			self.filePath = self.generateFilePath()
		externalFile = open( self.filePath, 'r' )
		content = externalFile.read()
		externalFile.close()
		self.target.script = content
		entity = self.target.getEntity( self.target )
		_MOCK.markProtoInstanceOverrided( self.target, 'script' )
		signals.emit( 'entity.modified', entity )

	def findTarget( self ):
		target = app.getModule('scenegraph_editor').findComByGUID( self.id )
		if not target:
			print(( 'findTarget, can\'t find script session target, guid: ', self.id ))
		return target

	def generateFilePath( self ):
		return self.path + self.getExternalFileName()

	def onRemoved( self ):
		pass

	def onProcess( self, path, status ):
		self.filePath = path
		if status == 'modified':
			self.onModified()
		elif status == 'removed':
			self.onRemoved()
		return True

	def openExternalEdit( self ):
		self.target = self.findTarget()
		if not self.target:
			print(( 'findTarget, can\'t find script session target, guid: ', self.id ))
			return
		self.filePath = self.generateFilePath()
		externalFile = open( self.filePath, 'wb' )
		externalFile.write( self.target.script.encode( 'utf-8' ) )
		externalFile.close()
		openFileInOS( self.filePath )

class ScriptEditSessionFactory(ExternalEditTransferSessionFactory):
	def build( self, guid, sessionType, options ):		
		if guid:
			if sessionType == 'behaviour_script':
				session = ScriptEditSession( guid, sessionType, options)
				return session
		return None

app.getModule('external_edit_manager').registerExternalEditSession( ScriptEditSessionFactory() )