import os.path
import logging
import subprocess
import shutil
import json

from gii.core import *
from mock import _MOCK

from gii.qt.dialogs   import requestString, alertMessage, requestConfirm

##----------------------------------------------------------------##
class ParticleSystemAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.particle'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		if ext == '.particle':
			return _MOCK.checkSerializationFile( filePath, 'mock.ParticleSystemConfig' )
		elif ext == '.particle_simple':
			return _MOCK.checkSerializationFile( filePath, 'mock.SimpleParticleSystemConfig' )

	def importAsset( self, node, reload = False ):
		fileName, ext = os.path.splitext( node.getFilePath() )
		if ext == '.particle':
			node.assetType = 'particle_system'		
		elif ext == '.particle_simple':
			node.assetType = 'particle_simple'
		node.setObjectFile( 'def', node.getFilePath() )
		return True

	def editAsset(self, node):
		if node.isType( 'particle_simple' ):
			editor = app.getModule( 'simple_particle_editor' )
			if not editor: 
				return alertMessage( 'Editor not load', 'Simple Particle Editor not found!' )
			editor.openAsset( node )

		elif node.isType( 'particle_system' ):
			editor = app.getModule( 'particle_editor' )
			if not editor: 
				return alertMessage( 'Editor not load', 'Particle Editor not found!' )
			editor.openAsset( node )


##----------------------------------------------------------------##
class ParticleSystemCreator(AssetCreator):
	def getAssetType( self ):
		return 'particle_system'

	def getLabel( self ):
		return 'Particle System'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.particle'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		
		_MOCK.createEmptySerialization( fullpath, 'mock.ParticleSystemConfig' )
		return nodepath


##----------------------------------------------------------------##
class SimpleParticleSystemCreator(AssetCreator):
	def getAssetType( self ):
		return 'particle_simple'

	def getLabel( self ):
		return 'Simple Particle System'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.particle_simple'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		
		_MOCK.createEmptySerialization( fullpath, 'mock.SimpleParticleSystemConfig' )
		return nodepath


##----------------------------------------------------------------##
ParticleSystemAssetManager().register()

ParticleSystemCreator().register()
SimpleParticleSystemCreator().register()

AssetLibrary.get().setAssetIcon( 'particle_system',  'particle' )
AssetLibrary.get().setAssetIcon( 'particle_simple',  'particle_simple' )
