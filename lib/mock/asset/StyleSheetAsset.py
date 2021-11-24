import os.path

from gii.core         import AssetManager, AssetLibrary, AssetCreator, app
from gii.qt.dialogs   import requestString, alertMessage, requestConfirm

from mock import _MOCK

##----------------------------------------------------------------##
class TextStyleAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.stylesheet'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		if not filepath.endswith( '.stylesheet' ): return False
		return True

	def importAsset(self, node, reload = False ):
		node.assetType = 'stylesheet'
		node.setObjectFile( 'def', node.getFilePath() )
		return True

	def editAsset(self, node):	
		editor = app.getModule('mock.stylesheet_editor')
		if not editor: 
			return alertMessage( 'Editor not load', 'Style Editor not found!' )
		editor.setFocus()
		editor.openAsset( node )

##----------------------------------------------------------------##
class TextStyleCreator( AssetCreator ):
	def getAssetType( self ):
		return 'stylesheet'

	def getLabel( self ):
		return 'Text Style Sheet'

	def createAsset(self, name, contextNode, assetType):
		ext = '.stylesheet'
		filename = name + ext

		if contextNode.isType( 'folder' ):
			nodepath = contextNode.getChildPath(filename)
			print(nodepath)
		else:
			nodepath = contextNode.getSiblingPath(filename)

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		modelName = _MOCK.Model.findName( 'StyleSheet' )
		assert( modelName )
		_MOCK.createEmptySerialization( fullpath, modelName )
		return nodepath
		

##----------------------------------------------------------------##
TextStyleAssetManager().register()
TextStyleCreator().register()

AssetLibrary.get().setAssetIcon('stylesheet', 'text')
