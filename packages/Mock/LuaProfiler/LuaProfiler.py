from gii.core        import app, signals
from gii.qt          import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget
from gii.moai.MOAIRuntime import MOAILuaDelegate
from gii.DebugView      import DebugViewModule
from gii.qt.helpers       import addWidgetWithLayout, QColorF, unpackQColor

##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt


class LuaProfiler( DebugViewModule ):
	name = 'lua_profiler'
	dependency = ['debug_view']

	def onLoad( self ):
		self.windowTitle = 'LuaProfiler'
		self.window = self.requestDockWindow( 'LuaProfiler',
			title     = 'Profiler',
			size      = (120,120),
			minSize   = (120,120),
			dock      = 'right'
			)
