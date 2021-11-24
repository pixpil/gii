import os
import os.path

from gii.core         import *
##----------------------------------------------------------------##
class FolderCreator(AssetCreator):
	def getAssetType( self ):
		return 'folder'

	def getLabel( self ):
		return 'Folder'

	def createAsset(self, name, contextNode, assetType):
		if assetType == 'folder':
			if contextNode.isType('folder'):
				nodepath = contextNode.getChildPath(name)
			else:
				nodepath = contextNode.getSiblingPath(name)
			fullpath = app.getAssetLibrary().getAbsPath( nodepath )
			try:
				os.mkdir( fullpath )
			except Exception as e :
				print(( 'failed create folder', e ))
				return False
			return nodepath
		else:
			return False

FolderCreator().register()