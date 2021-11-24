import os.path
import json

from gii.core import *
from gii.qt.dialogs   import requestString, alertMessage

from mock import _MOCK

##----------------------------------------------------------------##
class AnimatorDataCreator(AssetCreator):
	def getMetaType( self ):
		return 'internal'

	def getAssetType( self ):
		return 'animator_data'

	def getLabel( self ):
		return 'Animator Data'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.animator_data'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )

		modelName = _MOCK.Model.findName( 'AnimatorData' )
		assert( modelName )
		_MOCK.createEmptySerialization( fullpath, modelName )
		return nodepath

##----------------------------------------------------------------##
class AnimatorDataAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.animator_data'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False
		if not filepath.endswith( '.animator_data' ): return False
		return True

	def importAsset(self, node, reload = False ):
		node.assetType = 'animator_data'
		node.setObjectFile( 'data', node.getFilePath() )

	# def editAsset(self, node):	
	# 	editor = app.getModule( 'animator' )
	# 	if not editor: 
	# 		return alertMessage( 'Designer not load', 'AnimatorData Designer not found!' )
	# 	editor.openAsset( node )

##----------------------------------------------------------------##
AnimatorDataAssetManager().register()
AnimatorDataCreator().register()

AssetLibrary.get().setAssetIcon( 'animator_data',  'clip' )
