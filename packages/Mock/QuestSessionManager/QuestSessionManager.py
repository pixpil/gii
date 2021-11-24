import random
import logging
import os.path

##----------------------------------------------------------------##
from gii.core        import app, signals, JSONHelper
from gii.qt          import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter
from gii.qt.controls.GraphicsView.YEdGraphView import YEdGraphView
from gii.qt.dialogs   import requestString, alertMessage, requestConfirm
from gii.moai.MOAIRuntime import MOAILuaDelegate
from gii.SceneEditor      import SceneEditorModule, getSceneSelectionManager
from gii.qt.helpers   import addWidgetWithLayout, QColorF, unpackQColor

##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt

##----------------------------------------------------------------##
from gii.SearchView       import requestSearchView, registerSearchEnumerator

from util.YEd import *

##----------------------------------------------------------------##
from mock import _MOCK, isMockInstance
##----------------------------------------------------------------##


##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


##----------------------------------------------------------------##
class QuestSchemeGraphView( YEdGraphView ):
	pass
	# def onNodeDClicked( self, item ):
	# 	node = item.node
	# 	fullname = node.getFullLabel()
	# 	if node.isGroup():
	# 		app.getModule( 'quest_session_manager' ).locatePortalGroup( fullname )
	# 	else:		
	# 		app.getModule( 'quest_session_manager' ).locatePortal( fullname )

##----------------------------------------------------------------##
class QuestSessionManager( SceneEditorModule ):
	name = 'quest_session_manager'
	dependency = [ 'mock' ]

	def onLoad( self ):
		#UI
		self.container = self.requestDockWindow( 'QuestSessionManager',
			title     = 'Quest',
			size      = (120,120),
			minSize   = (120,120),
			dock      = 'left',
			toolWindow =  False
		)

		self.window = window = self.container.addWidgetFromFile(
			_getModulePath('container.ui')
		)

		#Components
		leftLayout = QtWidgets.QVBoxLayout( window.containerLeft )
		leftLayout.setSpacing( 0 )
		leftLayout.setContentsMargins( 0 , 0 , 0 , 0 )

		rightLayout = QtWidgets.QVBoxLayout( window.containerRight )
		rightLayout.setSpacing( 0 )
		rightLayout.setContentsMargins( 0 , 0 , 0 , 0 )

		self.treeFilter = GenericTreeFilter( window.containerRight )
		self.treeFilter.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
		self.tree = QuestSchemeTreeWidget( window.containerLeft )
		self.treeFilter.setTargetTree( self.tree )
		self.toolbar = QtWidgets.QToolBar( window.containerLeft )
		self.toolbar.setOrientation( Qt.Horizontal )
		self.toolbar.setMaximumHeight( 32 )

		self.graphView = QuestSchemeGraphView( 
			parent = window.containerRight,
			use_gl = False,
			antialias = True
		)

		leftLayout.addWidget( self.toolbar )
		leftLayout.addWidget( self.treeFilter )
		leftLayout.addWidget( self.tree )

		rightLayout.addWidget( self.graphView )

		self.addToolBar( 'quest_session_manager', self.toolbar )
		self.addTool( 'quest_session_manager/add_session',     label = 'Add', icon = 'add_folder' )
		self.addTool( 'quest_session_manager/----' )
		self.addTool( 'quest_session_manager/add_scheme',      label = 'Add', icon = 'add' )
		self.addTool( 'quest_session_manager/remove_scheme',   label = 'Remove', icon = 'remove' )
		self.addTool( 'quest_session_manager/----' )
		self.addTool( 'quest_session_manager/refresh', label = 'Refresh', icon = 'refresh' )

		
		self.portalRegistry = None
		self.showAllScenePortals = False
		self.updatingSelection = False

		self.currentSchemeEntry = None
		self.currentSession = None

	def onAppReady( self ):
		self.tree.rebuild()

	def setCurrentSelection( self, session, schemeEntry ):
		self.currentSession = session
		self.currentSchemeEntry = schemeEntry
		self.graphView.clear()
		if schemeEntry:
			parser = YEdGraphMLParser()
			assetPath = schemeEntry.path
			assetNode = self.getAssetLibrary().getAssetNode( assetPath )
			g = parser.parse( assetNode.getAbsFilePath() )
			if g:
				self.graphView.loadGraph( g )
				self.graphView.fitAll()

	def addSession( self ):
		mgr = _MOCK.getQuestManager()
		session = mgr.addSession( mgr )
		self.tree.addNode( session )
		self.tree.editNode( session )
		return session

	def removeSession( self, session ):
		mgr = _MOCK.getQuestManager()
		mgr.removeSession( mgr, session )
		self.tree.removeNode( session )

	def renameSession( self, session, name ):
		mgr = _MOCK.getQuestManager()
		mgr.renameSession( mgr, session, name )
		self.tree.refreshNodeContent( session )

	def addSchemeEntry( self, assetNode ):
		if not self.currentSession:
			logging.warn( 'no quest session specified' )
			return False
		session = self.currentSession
		schemeEntry = session.addSchemeEntry( session, assetNode.getPath() )
		self.updateQuestNodeList()
		if schemeEntry:
			self.tree.addNode( schemeEntry )
			return schemeEntry

	def updateQuestNodeList( self ):
		pass

	def removeSchemeEntry( self, schemeEntry ):
		if not self.currentSession:
			logging.warn( 'no quest session specified' )
			return False
		self.tree.removeNode( schemeEntry )
		session = self.currentSession
		session.removeSchemeEntry( session, schemeEntry )

	def enumerateSelectableGraphs( self, typeId, context, option ):
		result = []
		session = self.currentSession
		if not session: return []
		for asset in self.getAssetLibrary().iterAssets():
			if asset.getType() != 'quest_scheme': continue
			path = asset.getPath()
			if session.hasScheme( session, path ): continue
			entry = ( asset, path, 'quest_scheme', 'quest_scheme' )
			result.append( entry )
		return result

	def onTool( self, tool ):
		name = tool.name
		if name == 'add_session':
			self.addSession()

		elif name == 'add_scheme':
			if not self.currentSession:
				logging.warn( 'no quest session specified' )
				return False
			requestSearchView( 
				info    = 'select quest scheme to add',
				context = 'quest_scheme',
				on_search = self.enumerateSelectableGraphs,
				on_selection = self.addSchemeEntry
			)

		elif name == 'remove_scheme':
			if not self.currentSession:
				logging.warn( 'no quest session specified' )
				return False
			for node in self.tree.getSelection():
				if isMockInstance( node, 'QuestSessionSchemeEntry' ):
					self.removeSchemeEntry( node )
				elif isMockInstance( node, 'QuestSession' ):
					self.removeSession( node )

		elif name == 'refresh':
			self.tree.rebuild()


##----------------------------------------------------------------##
class QuestSchemeTreeWidget( GenericTreeWidget ):
	def getDefaultOptions( self ):
		return {
			'editable' : True
		}

	def getHeaderInfo( self ):
		return [ ('Name',-1) ]

	def getRootNode( self ):
		return _MOCK.getQuestManager()

	def getNodeParent( self, node ):
		if node == self.getRootNode(): return None
		if isMockInstance( node, 'QuestSession' ):
			return self.getRootNode()
		elif isMockInstance( node, 'QuestSessionSchemeEntry' ):
			return node.session
		else:
			print(node)
			raise Exception( 'Unknown Quest Object Type' )

	def getNodeChildren( self, node ):
		if node == self.getRootNode():
			return [ session for session in list(node.sessions.values()) ]
		elif isMockInstance( node, 'QuestSession' ):
			return [ entry for entry in list(node.schemeEntries.values()) ]
		elif isMockInstance( node, 'QuestSessionSchemeEntry' ):
			return []

	def getItemFlags( self, node ):
		flags = {
			'editable' : False
		}
		if isMockInstance( node, 'QuestSession' ):
			flags[ 'editable' ] = True
		return flags

	def updateItemContent( self, item, node, **option ):
		if node == self.getRootNode():
			return

		elif isMockInstance( node, 'QuestSession' ):
			item.setText( 0, node.name or '<NONAME>' )
			item.setIcon( 0, getIcon( 'folder' ) )
			
		elif isMockInstance( node, 'QuestSessionSchemeEntry' ):
			path = node.path
			name = os.path.basename( path )
			if name.endswith( '.quest.graphml' ):
				shortName = name[:-14]
			else:
				shortName, ext = os.path.splitext( name )
			item.setText( 0, shortName )
			item.setIcon( 0, getIcon( 'quest_scheme' ) )

	def onItemSelectionChanged( self ):
		m = app.getModule( 'quest_session_manager' )
		for node in self.getSelection():
			if isMockInstance( node, 'QuestSession' ):
				session = node
				schemeEntry = None
				m.setCurrentSelection( session, schemeEntry )

			elif isMockInstance( node, 'QuestSessionSchemeEntry' ):
				session = node.session
				schemeEntry = node
				m.setCurrentSelection( session, schemeEntry )

			break

	def onItemChanged( self, item, col ):
		node = self.getNodeByItem( item )
		if isMockInstance( node, 'QuestSession' ):
			app.getModule( 'quest_session_manager' ).renameSession( node, item.text(0) )
		else:
			print('WTF?')

	def onItemActivated( self, item, col ):
		node = item.node
		if isMockInstance( node, 'QuestSessionSchemeEntry' ):
			path = node.path
			app.getModule( 'asset_browser' ).locateAsset( path )



