import random
##----------------------------------------------------------------##
from gii.core        import app, signals
from gii.qt          import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter
from gii.moai.MOAIRuntime import MOAILuaDelegate
from gii.SceneEditor      import SceneEditorModule, getSceneSelectionManager
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor

##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt

##----------------------------------------------------------------##
from gii.SearchView       import requestSearchView, registerSearchEnumerator

##----------------------------------------------------------------##
from mock import _MOCK, isMockInstance
##----------------------------------------------------------------##


##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

def _fixDuplicatedName( names, name, id = None ):
	if id:
		testName = name + '_%d' % id
	else:
		id = 0
		testName = name
	#find duplicated name
	if testName in names:
		return _fixDuplicatedName( names, name, id + 1)
	else:
		return testName

##----------------------------------------------------------------##
class SceneGroupFilterSelector( QtWidgets.QComboBox ):
	def __init__( self, *args ):
		super(SceneGroupFilterSelector, self).__init__(*args)
		self.addItem( 'NO FILTER', False )

	def addFilters( self, filters ):
		for data in filters:
			self.addItem( data[ 'name' ], data )

	def clear( self ):
		count = self.count()
		for idx in range( count-1, 1, -1 ):
			self.removeItem( idx )


##----------------------------------------------------------------##
class SceneGroupFilterManager( SceneEditorModule ):
	def __init__(self):
		super( SceneGroupFilterManager, self ).__init__()
		self.refreshScheduled = False

	def getName( self ):
		return 'scene_group_filter_manager'

	def getDependency( self ):
		return [ 'scene_editor', 'mock' ]

	def loadFilters( self ):
		filterConfig = {}
		reposSettingApp = app.getUserSetting( 'scene_group_filter', {} )
		for k,v in list(reposSettingApp.items()):
			filterConfig[ k ] = v

		prj = app.getProject()
		if prj:
			reposSettingPrj = prj.getProjectSetting( 'scene_group_filter', {} )
			for k,v in list(reposSettingPrj.items()):
				filterConfig[ k ] = v

			reposSettingPrjUser = prj.getUserSetting( 'scene_group_filter', {} )
			for k,v in list(reposSettingPrjUser.items()):
				filterConfig[ k ] = v

		filters = []
		for key, config in filterConfig.items():
			name = config.get( 'name', None )
			if not name:
				name = key

			incStr = config.get( 'include', None )
			inc = False
			if incStr:
				inc = [ a.strip() for a in incStr.split( ',' ) ]

			excStr = config.get( 'exclude', None )
			exc = False
			if excStr:
				exc = [ a.strip() for a in excStr.split( ',' ) ]

			data = {
				'id'       :key,
				'name'     :name,
				'include'  :inc,
				'exclude'  :exc,
			}

			filters.append( data )

		self.filters = filters


	def onLoad( self ):
		self.selectorWidget = SceneGroupFilterSelector( None )
		self.selectorWidget.currentIndexChanged.connect( self.onFilterSelectionChanged )

		self.addTool( 'game_preview_tools/scene_group_filter_selector' ,
			widget = self.selectorWidget
		)
		self.filters = []
		self.currentFilterIdx = 0
		self.currentFilter = False
		self.loadFilters()

		self.selectorWidget.clear()
		self.selectorWidget.addFilters( self.filters )
		self.setWorkspaceConfig( 'current_filter', self.currentFilter )


	def onFilterSelectionChanged( self, idx ):
		self.currentFilterIdx = idx
		if idx == 0:
			self.currentFilter = False
		else:
			self.currentFilter = self.filters[ idx - 1 ]
		#TODO: update filter
		self.setWorkspaceConfig( 'current_filter', self.currentFilter )

	def onTool( self, tool ):
		name = tool.name
		if name == 'add':
			requestSearchView( 
				info    = 'select global object class to create',
				context = 'global_object_class',
				on_selection = lambda objName: self.createGlobalObject( objName )				
				)

		if name == 'add_group':
			group = self.delegate.safeCall( 'addGroup' )
			self.tree.addNode( group )
			self.tree.editNode( group )
			self.tree.selectNode( group )

		elif name == 'remove':
			for node in self.tree.getSelection():
				self.doCommand( 'scene_editor/remove_global_object', target = node )
				self.tree.removeNode( node )

		elif name == 'refresh':
			self.scheduleRefreshObject()

##----------------------------------------------------------------##
SceneGroupFilterManager().register()
