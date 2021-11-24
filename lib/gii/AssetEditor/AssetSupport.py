import sys
import os

from gii.core import *
from gii.core.selection import SelectionManager

from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import QEventLoop, QEvent, QObject

from gii.qt.IconCache       import getIcon
from gii.qt.controls.Window import MainWindow
from gii.qt.controls.Menu   import MenuManager
from gii.qt  import TopEditorModule, SubEditorModule

import gii.FileWatcher
from gii.SearchView       import requestSearchView, registerSearchEnumerator
from gii.SceneEditor  import SceneEditorModule

		
##----------------------------------------------------------------##
class AssetSupport( SceneEditorModule ):
	name       = 'asset_support'

	def onLoad( self ):
		self.externRunning = False
		self.projectScanPaused = False

		self.mainToolBar = self.addToolBar( 'asset', self.getMainWindow().requestToolBar( 'main' ) )
		####
		self.addMenu('main/asset', {'label':'&Asset'})
		self.addMenuItem(
			'main/asset/reset_all_asset', 
			dict( label='Reset Asset Library' )
		)
		self.addMenuItem(
			'main/asset/clear_free_meta', 
			dict( label='Clear Metadata' )
		)

		self.addMenuItem(
			'main/asset/touch_all_scenes',
			dict( label='Touch All Scenes' )
		)

		self.projectScanTimer = self.getMainWindow().startTimer( 20, self.checkProjectScan )
		registerSearchEnumerator( assetSearchEnumerator )
		registerSearchEnumerator( assetFolderSearchEnumerator )

		signals.connect( 'external_player.start', self.onExternRunStart )
		signals.connect( 'external_player.stop', self.onExternRunStop )

	def pauseProjectScan( self ):
		self.projectScanPaused = True

	def resumeProjectScan( self ):
		self.projectScanPaused = False

	def checkProjectScan( self ):
		if self.projectScanPaused: return
		# if self.externRunning: return
		lib = self.getAssetLibrary()
		lib.tryScanProject()

	def onExternRunStart( self, target ):
		self.externRunning = True

	def onExternRunStop( self ):
		self.externRunning = False

	def onMenu(self, node):
		name = node.name
		if name == 'reset_all_asset':
			# self.getAssetLibrary().reset()
			pass

		elif name == 'clear_free_meta':
			self.getAssetLibrary().clearFreeMetaData()

		elif name == 'touch_all_scenes':
			allSceneAssets = self.getAssetLibrary().enumerateAsset( 'scene' )
			for node in allSceneAssets:
				if node.getType() == 'scene':
					node.touch()
			
		
	def onTool( self, tool ):
		pass

##----------------------------------------------------------------##
def assetSearchEnumerator( typeId, context, option ):
		if not context in [ 'all', 'asset' ] : return
		result = []
		lib = AssetLibrary.get()
		for node in AssetLibrary.get().enumerateAsset( typeId, **option ):
			assetType = node.getType()
			iconName = lib.getAssetIcon( assetType ) or 'normal'
			entry = ( node, node.getNodePath(), node.getType(), iconName )
			result.append( entry )
		return result

##----------------------------------------------------------------##
def assetFolderSearchEnumerator( typeId, context, option ):
		if not context in [ 'asset_folder' ] : return
		result = []
		lib = AssetLibrary.get()
		for node in AssetLibrary.get().enumerateAsset( typeId, **option ):
			if not node.getGroupType() in ('folder','package') : continue
			assetType = node.getType()
			iconName = lib.getAssetIcon( assetType ) or 'normal'
			entry = ( node, node.getNodePath(), node.getType(), iconName )
			result.append( entry )
		return result
