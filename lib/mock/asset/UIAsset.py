import os.path
import logging
import subprocess
import shutil
import json

from gii.core import *
from mock import _MOCK

from gii.qt.dialogs   import requestString, alertMessage, requestConfirm


EMPTY_STYLE_SHEET = '''----------------------------------------------------------------
-- UI style sheet: %s
--[[
	#example:
	import 'another_style_sheet'

	style 'UIWidgetName :state .featureA .featureB' {
		color = 'red';
		background_color = '#000';
		image = 'path/to/gfxAsset'; 
		padding = { 0,0,10,10 };
		min_size = { 100, 100 };
	}
]]
----------------------------------------------------------------


'''

##----------------------------------------------------------------##
class UIStyleAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.ui_style'

	def getMetaType( self ):
		return 'script'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		return ext == '.ui_style'

	def importAsset( self, node, reload = False ):
		fileName, ext = os.path.splitext( node.getFilePath() )
		node.assetType = 'ui_style'
		node.setObjectFile( 'def', node.getFilePath() )
		return True


##----------------------------------------------------------------##
class UIStyleSheetCreator(AssetCreator):
	def getAssetType( self ):
		return 'ui_style'

	def getLabel( self ):
		return 'UI Style Sheet'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.ui_style'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		if os.path.exists(fullpath):
			raise Exception('File already exist:%s'%fullpath)
		fp = open(fullpath,'w')
		fp.write( EMPTY_STYLE_SHEET % nodepath )
		fp.close()
		return nodepath


##----------------------------------------------------------------##
UIStyleAssetManager().register()
UIStyleSheetCreator().register()

AssetLibrary.get().setAssetIcon( 'ui_style',  'guistyle' )
