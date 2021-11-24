import os.path
import logging
import subprocess
import shutil
import json

from gii.core import *
from mock import _MOCK

_PMATERIAL_EXT  = '.p_material'
_PMATERIAL_TYPE = 'physics_material'

_PBODYDEF_EXT   = '.p_bodydef'
_PBODYDEF_TYPE  = 'physics_body_def'

##----------------------------------------------------------------##
##----------------------------------------------------------------##
class PhysicsMaterialAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.' + _PMATERIAL_TYPE

	def getMetaType( self ):
		return 'serializable'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		if not ext in [ _PMATERIAL_EXT ]: return False
		return True

	def importAsset( self, node, reload = False ):
		node.assetType = _PMATERIAL_TYPE
		node.setObjectFile( 'def', node.getFilePath() )
		return True

	def editAsset(self, node):	
		editor = app.getModule( 'serializable_editor' )
		if not editor: 
			return alertMessage( 'Editor not load', 'Asset Editor not found!' )
		else:
			editor.openAsset( node )

##----------------------------------------------------------------##
class PhysicsMaterialAssetCreator(AssetCreator):
	def getAssetType( self ):
		return _PMATERIAL_TYPE

	def getLabel( self ):
		return 'Physics Material'

	def createAsset( self, name, contextNode, assetType ):
		filename = name + _PMATERIAL_EXT
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		
		_MOCK.createEmptySerialization( fullpath, 'mock.PhysicsMaterial' )
		return nodepath


##----------------------------------------------------------------##
##----------------------------------------------------------------##
class PhysicsBodyDefAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.' + _PBODYDEF_TYPE

	def getMetaType( self ):
		return 'serializable'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		if not ext in [ _PBODYDEF_EXT ]: return False
		return True

	def importAsset( self, node, reload = False ):
		node.assetType = _PBODYDEF_TYPE
		node.setObjectFile( 'def', node.getFilePath() )
		return True

	def editAsset(self, node):	
		editor = app.getModule( 'serializable_editor' )
		if not editor: 
			return alertMessage( 'Editor not load', 'Asset Editor not found!' )
		else:
			editor.openAsset( node )
			
##----------------------------------------------------------------##
class PhysicsBodyDefAssetCreator(AssetCreator):
	def getAssetType( self ):
		return _PBODYDEF_TYPE

	def getLabel( self ):
		return 'Physics Body Defination'

	def createAsset( self, name, contextNode, assetType ):
		filename = name + _PBODYDEF_EXT
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		
		_MOCK.createEmptySerialization( fullpath, 'mock.PhysicsBodyDef' )
		return nodepath



##----------------------------------------------------------------##
PhysicsMaterialAssetManager().register()
PhysicsMaterialAssetCreator().register()

PhysicsBodyDefAssetManager().register()
PhysicsBodyDefAssetCreator().register()

AssetLibrary.get().setAssetIcon( 'physics_material',  'crate' )
AssetLibrary.get().setAssetIcon( 'physics_body_def',  'crate' )
