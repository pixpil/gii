import os.path
from gii.core import AssetManager, AssetLibrary, getProjectPath, app, JSONHelper
from .helper.PSDLUTExtractor import extractLUTImage
from . import ImageHelpers 


import json

from mock import _MOCK, _MOCK_EDIT, isMockInstance, getMockClassName


def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


class LUTPSDAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.lut_psd'
	
	def getPriority( self ):
		return 1000

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		if not filepath.endswith( '.lut.psd' ): return False
		return True

	def importAsset(self, node, reload = False ):
		if node.isVirtual(): return
		node.assetType = 'lut_texture'
		node.groupType = None
		
		output = node.getCacheFile( 'texture' )
		node.setObjectFile( 'texture', output )
		lut, filter = extractLUTImage( node.getAbsFilePath() )
		if lut:
			lut.save( output, 'PNG' )
			node.setProperty( 'filter', filter )
			return True
		else:
			return False

	def hasAssetThumbnail( self, assetNode ):
		if assetNode.isVirtual(): return False
		return True

	def buildAssetThumbnail( self, assetNode, targetPath, size ):
		srcPath = assetNode.getAbsFilePath()
		if not ImageHelpers.buildThumbnail( srcPath, targetPath, size ):
			return False
		return True

LUTPSDAssetManager().register()

AssetLibrary.get().setAssetIcon( 'lut_texture',  'color' )
