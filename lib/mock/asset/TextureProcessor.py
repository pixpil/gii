import os.path
import logging
import subprocess
import shutil
import json
import sys

from gii.core import *

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


##----------------------------------------------------------------##
_EMPTY_PROCESSOR_SCRIPT = '''
#----------------------
#Texture Processor Script
#----------------------

def onProcess( img ):
	return img

'''

##----------------------------------------------------------------##
class TextureProcessorAssetManager( AssetManager ):
	def getName(self):
		return 'asset_manager.texture_processor'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name,ext=os.path.splitext(filepath)
		return ext in [ '.texture_processor' ]

	def importAsset(self, node, reload = False ):
		node.assetType = 'texture_processor'
		return True


##----------------------------------------------------------------##
class TextureProcessorAssetCreator(AssetCreator):
	def getAssetType( self ):
		return 'texture_processor'

	def getLabel( self ):
		return 'Texture Processor'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.texture_processor'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		f = open( fullpath, 'w' )
		f.write( _EMPTY_PROCESSOR_SCRIPT )
		f.close()
		return nodepath

##----------------------------------------------------------------##
TextureProcessorAssetManager().register()
TextureProcessorAssetCreator().register()

##----------------------------------------------------------------##

def runTextureProcessor( procFilePath, filePath, outputPath = None ):
	if not outputPath:
		outputPath = filePath

	interpreter = sys.executable
	arglist = [
		interpreter,
		_getModulePath( 'tools/ImageProcessorStub.py' ),
		procFilePath,
		filePath,
		outputPath
	]
	try:
		ex = subprocess.call( arglist ) #run packer
	except Exception as ex:
		pass


def applyTextureProcessor( procPath, filePath, outputPath = None ):
	procNode = AssetLibrary.get().getAssetNode( procPath )
	procFilePath = procNode.getAbsFilePath()
	return runTextureProcessor( procFilePath, filePath, outputPath )
