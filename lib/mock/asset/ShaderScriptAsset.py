import os
import os.path
import logging
import subprocess
import shutil
import json

from gii.core import *

from simple_task_queue import task, Task, WorkerPool

from mock import _MOCK, _MOCK_EDIT
from util.ShaderTool import convertGLSLSet



##----------------------------------------------------------------##
@task( 'ConvertGLSLSet' )
def taskConvertGLSLSet( **kw ):
	return convertGLSLSet( **options )

##----------------------------------------------------------------##
EMPTY_SCRIPT = '''
----------------------------------------------------------------
-- Shader Script: %s
----------------------------------------------------------------

-- pass {
-- 	[0] = 'main'
-- }

----------------------------------------------------------------
shader 'main' {
	uniform = {
		_sampler_          = sampler( 1 );

		constants = block {
			mtxModelToView    = global( MODEL_TO_VIEW_MTX );
		}
	};

	program_vertex   = 'vsh';
	program_fragment = 'fsh';
}

----------------------------------------------------------------
source 'vsh' [[
	@in vec4 position;
	@in vec2 uv;
	@in vec4 color;

	@out LOWP vec4 colorVarying;
	@out MEDP vec2 uvVarying;
	@out MEDP vec2 uvScreen;

	@block constants;

	void main () {
		uvVarying    = uv;
		colorVarying = color;
		gl_Position  = position;
	}
]]

----------------------------------------------------------------
source 'fsh' [[
	@in LOWP vec4 colorVarying;
	@in MEDP vec2 uvVarying;
	@in MEDP vec2 uvScreen;

	@sampler _sampler_;

	void main () {
		gl_FragColor = texture2D ( _sampler_, uvVarying ) * colorVarying;
	}
]]

'''

##----------------------------------------------------------------##
class ShaderScriptAssetManager( AssetManager ):
	def getName( self ):
		return 'asset_manager.shader_script_new'

	def getMetaType( self ):
		return 'script'

	def acceptAssetFile(self, filePath):
		if not os.path.isfile( filePath ): return False
		name, ext = os.path.splitext( filePath )
		if not ext in [ '.shader_script', '.shader', '.glsl', '.fsh', '.vsh' ]: return False
		return True

	def importAsset( self, node, reload = False ):
		name, ext = os.path.splitext( node.getFilePath() )
		if ext in [ '.glsl', '.fsh', '.vsh' ]:
			node.assetType = 'glsl'
			
		elif ext in [ '.shader_script', '.shader' ]:
			node.assetType = 'shader_script'		

		node.setObjectFile( 'src', node.getFilePath() )
		
		if node.assetType == 'shader_script':			
			self.precompileShaderScript( node )
		return True

	def precompileShaderScript( self, node ):
		compiled = node.getCacheFile( 'export', is_dir = True )
		node.setObjectFile( 'compiled', compiled )
		shutil.rmtree( compiled )
		_MOCK.generateShaderSourceFiles( node.getAbsFilePath(), compiled )
		
		print( "convert shader", node )
		# with WorkerPool( worker_num = 3 ):
		if os.path.isdir( compiled ):
			for f in os.listdir( compiled ):
				inputDir = compiled + '/' + f
				if os.path.isdir( inputDir ):
					convertGLSLSet( input = inputDir )
					# Task( 'ConvertGLSLSet' ).promise( input = compiled + '/' + f )
					

##----------------------------------------------------------------##
class ShaderScriptAssetCreator(AssetCreator):
	def getAssetType( self ):
		return 'shader_script'

	def getLabel( self ):
		return 'ShaderScript'

	def createAsset( self, name, contextNode, assetType ):
		ext = '.shader_script'
		filename = name + ext
		if contextNode.isType('folder'):
			nodepath = contextNode.getChildPath( filename )
		else:
			nodepath = contextNode.getSiblingPath( filename )

		fullpath = AssetLibrary.get().getAbsPath( nodepath )
		if os.path.exists( fullpath ):
			raise Exception( 'File already exist:%s' % fullpath )
		fp = open( fullpath, 'w' )
		fp.write( EMPTY_SCRIPT % name )
		fp.close()

		return nodepath


##----------------------------------------------------------------##
ShaderScriptAssetCreator().register()
ShaderScriptAssetManager().register()

AssetLibrary.get().setAssetIcon( 'shader_script',  'shader' )
AssetLibrary.get().setAssetIcon( 'glsl',  'text-red' )
