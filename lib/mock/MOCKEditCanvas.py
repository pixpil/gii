from gii.qt.controls.GLWidget import GLWidget
from gii.moai.MOAIEditCanvas import  MOAIEditCanvas
from gii.moai.MOAIRuntime import _G, _GII

from gii.SceneEditor.GamePreview import GamePreviewCanvas

from .MockRuntime import _MOCK, _MOCK_EDIT

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
def isBoundMethod( v ):
	return hasattr(v,'__func__') and hasattr(v,'im_self')

def boundToClosure( value ):
	if isBoundMethod( value ):
		func = value
		value = lambda *args: func(*args)
	return value


##----------------------------------------------------------------##
class MOCKPreviewCanvas( GamePreviewCanvas ):
	def __init__( self, *args, **kwargs ):
		self.mockRenderContext = None
		super(MOCKPreviewCanvas, self).__init__( *args, **kwargs )

	def createRenderContext( self ):
		assert not self.renderContext
		ctx = _MOCK_EDIT.GIIMockPreviewCanvasContext()
		return ctx

	def getMockRenderContext( self ):
		return self.mockRenderContext

	def onDraw( self ):
		# print( 'draw preview', self )
		ctx = self.renderContext
		ctx.makeCurrent( ctx )
		ctx.draw( ctx )

	def onContextReady( self, ctx ):
		self.mockRenderContext = ctx.mockContext


##----------------------------------------------------------------##
class MOCKEditCanvas( MOAIEditCanvas ):
	def __init__( self, *args, **kwargs ):
		self.mockRenderContext = None
		super(MOCKEditCanvas, self).__init__( *args, **kwargs )

	def createRenderContext( self ):
		assert not self.renderContext
		ctx = _MOCK_EDIT.GIIMockCanvasContext()
		return ctx

	def getMockRenderContext( self ):
		return self.mockRenderContext

	def onContextReady( self, ctx ):
		self.mockRenderContext = ctx.mockContext

	def makeDelegateEnv( self ):
		env = super( MOCKEditCanvas, self ).makeDelegateEnv()
		env[  'getMockRenderContext' ] = boundToClosure( self.getMockRenderContext )
		return env

	def onDraw( self ):
		# print( 'draw edit', self )
		super(MOCKEditCanvas, self).onDraw()


