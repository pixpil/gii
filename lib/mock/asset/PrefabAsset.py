import os.path
import json
from gii.core import *
from mock import _MOCK, _MOCK_EDIT, isMockInstance, getMockClassName

class PrefabAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.prefab'

	def acceptAssetFile( self, filePath ):
		if not os.path.isfile(filePath): return False		
		name,ext = os.path.splitext(filePath)
		if not ext in ['.prefab']: return False
		return True
		# data = JSONHelper.tryLoadJSON( filePath )
		# return data and data.get( '_assetType', None ) == 'prefab'

	def importAsset( self, node, reload = False ):
		node.assetType = 'prefab'
		node.setObjectFile( 'def', node.getFilePath() )
		return True

	def hasAssetThumbnail( self, assetNode ):
		if assetNode.getType() == 'prefab': return True
		return False

	def buildAssetThumbnail( self, assetNode, targetPath, size ):
		nodePath = assetNode.getPath()
		w, h = size
		if _MOCK_EDIT.buildProtoThumbnail( nodePath, targetPath, w, h ):
			return True
		else:
			return False

##----------------------------------------------------------------##
class PrefabCreator(AssetCreator):
	def getAssetType( self ):
		return 'prefab'

	def getLabel( self ):
		return 'prefab'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.prefab'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		data={
			'_assetType' : 'prefab', #checksum
			'map'        : False ,
			'body'       : False #empty
		}
		if os.path.exists(fullpath):
			raise Exception('File already exist:%s'%fullpath)
		fp = open(fullpath,'w')
		json.dump( data, fp, sort_keys=True, indent=2 )
		fp.close()
		return nodepath

##----------------------------------------------------------------##
PrefabAssetManager().register()
PrefabCreator().register()

AssetLibrary.get().setAssetIcon( 'prefab',  'prefab' )
