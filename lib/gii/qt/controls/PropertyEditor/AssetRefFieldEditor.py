from gii.core import *
from gii.core.model import *

from gii.qt.helpers import repolishWidget
from gii.qt.dialogs import alertMessage, requestConfirm

import json 

from .PropertyEditor import FieldEditor, registerSimpleFieldEditorFactory
from .SearchFieldEditor import SearchFieldEditorBase

import os.path

##----------------------------------------------------------------##
class AssetRefFieldEditor( SearchFieldEditorBase ):
	def onInitEditor( self ):
		self.getEditorWidget().setButtonFlags( open = True )

	def getValueRepr( self, value ): #virtual
		lib = AssetLibrary.get()
		if value:
			node = lib.getAssetNode( value )
			if node:
				icon = lib.getAssetIcon( node.getType() )
				return ( value, icon )
		return value #str

	def getSearchType( self ): #virtual
		t = self.field.getType() #AssetRefType
		return t.getAssetType( self.getTarget() )

	def getSearchContext( self ): #virtual
		return "asset"

	def getSearchInitial( self ): #virtual
		return self.target and AssetLibrary.get().getAssetNode( self.target ) or None

	def setValue( self, node ): #virtual
		if node:
			value = node.getNodePath()
		else:
			value = None
		super( AssetRefFieldEditor, self ).setValue( value )

	def gotoObject( self ):
		assetBrowser = app.getModule( 'asset_browser' )
		if assetBrowser:
			assetBrowser.locateAsset( self.target )

	def openObject( self ):
		assetBrowser = app.getModule( 'asset_browser' )
		if assetBrowser:
			assetBrowser.openAsset( self.target )

	def syncSelection( self ):
		assetBrowser = app.getModule( 'asset_browser' )
		if assetBrowser:
			entries = self.enumerateSearch( include_deprecated = True )
			objects = [ entry.getObject() for entry in entries ]
			for node in assetBrowser.getItemSelection():
				if node in objects:
					if node.isDeprecated():
						if not requestConfirm( 'Deprecated Asset', 'applying DEPRECATED asset, confirm?', 'warning' ):
							return False
					return self.setValue( node )
		alertMessage( 'No matched asset', 'No matched asset selected' )
	
	def formatRefName( self, name )	:
		if isinstance( name, str ):
			baseName, ext = os.path.splitext( os.path.basename( name ) )
			return baseName
		else:
			return name

	def findMatchedAssetFromMime( self, mime ):
		if not mime.hasFormat( GII_MIME_ASSET_LIST ): return None
		assetList = json.loads( str(mime.data( GII_MIME_ASSET_LIST )), 'utf-8' )
		matched = False
		assetLib = AssetLibrary.get()

		assets = []
		for path in assetList:			
			asset = assetLib.getAssetNode( path )
			if asset:
				assets.append( asset )

		result = assetLib.enumerateAsset( self.getSearchType(), subset = assets )
		if result:
			return result[0]
		else:
			return None

	def clearObject( self ):
		self.setValue( False )
		
	def dragEnterEvent( self, ev ):
		mime = ev.mimeData()
		asset = self.findMatchedAssetFromMime( mime )
		button = self.getRefButton()
		if asset:
			button.setProperty( 'dragover', 'ok' )
		else:			
			button.setProperty( 'dragover', 'bad' )
		repolishWidget( button )
		ev.acceptProposedAction()

	def dropEvent( self, ev ):
		button = self.getRefButton()
		button.setProperty( 'dragover', False )
		repolishWidget( button )
		mime = ev.mimeData()
		asset = self.findMatchedAssetFromMime( mime )		
		if not asset: return False
		self.setValue( asset )
		ev.acceptProposedAction()

	def dragLeaveEvent( self, ev ):
		button = self.getRefButton()
		button.setProperty( 'dragover', False )
		repolishWidget( button )

	def isDropAllowed( self ):
		return True



registerSimpleFieldEditorFactory( AssetRefType, AssetRefFieldEditor )
