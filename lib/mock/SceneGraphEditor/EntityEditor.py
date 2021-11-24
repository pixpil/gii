from gii.core import  *
from gii.SceneEditor.Introspector   import ObjectEditor, CommonObjectEditor, registerObjectEditor
from gii.qt.controls.PropertyEditor import PropertyEditor
from gii.qt.helpers import addWidgetWithLayout, repolishWidget
from gii.qt.IconCache               import getIcon
from gii.SearchView       import requestSearchView, registerSearchEnumerator
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter

from qtpy import QtWidgets, QtGui, QtCore, uic
from qtpy.QtCore import Qt, Slot
from qtpy.QtCore import QEventLoop, QEvent, QObject
from qtpy.QtWidgets  import QMenu

from mock import _MOCK, isMockInstance, getMockClassName


##----------------------------------------------------------------##
def getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

##----------------------------------------------------------------##
_mockInited = False
_mockObjecteEditors = {}

def registerMOCKObjectEditor( mockClassName, editorClass ):
	_mockObjecteEditors[ mockClassName ] = editorClass
	if _mockInited:
		mockClass = _MOCK[ mockClassName ]
		registerObjectEditor( mockClass, editorClass )

@slot( 'mock.init' )
def onMockInited():
	global _mockInited
	_mockInited = True
	for mockClassName, editorClass in  list(_mockObjecteEditors.items()):
		mockClass = _MOCK[ mockClassName ]
		registerObjectEditor( mockClass, editorClass )


##----------------------------------------------------------------##
EntityHeaderBase, BaseClass = uic.loadUiType(getModulePath('EntityHeader.ui'))

def getProtoPath( obj ):
	state = obj['PROTO_INSTANCE_STATE']
	return state['proto'] or state['sub_proto']



##----------------------------------------------------------------##
class SceneObjectEditor( CommonObjectEditor ):
	def setTarget( self, target ):
		introspector = self.getIntrospector()
		self.target = target
		self.grid.setTarget( target )		
		if isMockInstance( target, 'Scene' ):
			for mgr in list(target.getManagers( target ).values()):
				if mgr.FLAG_INTERNAL: continue
				editor = introspector.addObjectEditor( mgr, show_after_add = False )
	# def needCache( self ):
	# 	return False



##----------------------------------------------------------------##
class SceneObjectEditorMixin():
	#field proto state
	def initFieldContextMenu( self, propertyEditor ):
		self.propertyEditor = propertyEditor
		propertyEditor.contextMenuRequested.connect( self.onFieldContextMenuRequested )
	
	def onFieldResetDefault( self ):
		target, fieldId = self.currentFieldContext
		_MOCK.resetFieldDefaultValue( target, fieldId )
		self.propertyEditor.refreshField( fieldId )
		self.currentFieldContext = None
		self.onPropertyReset( target, fieldId )

	def onFieldResetProto( self ):
		target, fieldId = self.currentFieldContext
		_MOCK.resetProtoInstanceOverridedField( target, fieldId )
		self.propertyEditor.refreshField( fieldId )
		self.currentFieldContext = None
		self.onPropertyReset( target, fieldId )

	def onFieldAddKey( self ):
		target, fieldId = self.currentFieldContext
		animator = app.getModule( 'animator' )
		animator.addKeyForField( target, fieldId )

	def onFieldContextMenuRequested( self, target, fieldId ):
		menu = QMenu( "Field Context" )
		itemTitle = menu.addAction( '[ %s ]' % fieldId )
		itemTitle.setEnabled( False )
		menu.addSeparator()

		animator = app.getModule( 'animator' )
		if animator:
			itemAddKey = menu.addAction( 'Add key' )
			itemAddKey.setIcon( getIcon('key') )
			itemAddKey.triggered.connect( self.onFieldAddKey )
			menu.addSeparator()

		itemDefault = menu.addAction( 'Set Default' )
		itemDefault.triggered.connect( self.onFieldResetDefault )

		if _MOCK.isProtoInstanceOverrided( target, fieldId ):
			menu.addSeparator()
			itemProtoReset = menu.addAction( 'Reset To Proto Value' )
			itemProtoReset.triggered.connect( self.onFieldResetProto )
			itemProtoReset.setIcon( getIcon('reset') )

		self.currentFieldContext = ( target, fieldId )
		menu.exec_(QtGui.QCursor.pos())

	#foldstate
	def initFoldState( self ):
		self.getContainer().foldChanged.connect( self.onFoldChanged )
	
	def restoreFoldState( self ):
		folded = self.getTarget()['__foldState'] or False
		self.getContainer().toggleFold( folded, False )

	def onFoldChanged( self, folded ):
		self.getTarget()['__foldState'] = folded

	#animtor track button
	def initAnimatorButton( self ):
		button = self.container.getButtonKey()
		button.clicked.connect( self.onCustomTrackMenuRequested )
		button.hide()

	def updateAnimatorButton( self ):
		animator = app.getModule( 'animator' )
		if not animator:
			return
		target = self.getTarget()
		button = self.container.getButtonKey()
		if target and _MOCK.objectHasAnimatorTrack( self.getTarget() ):
			button.show()
		else:
			button.hide()

	def onCustomTrackMenuRequested( self ):
		menu = QMenu("Animator Track Context")
		itemTitle = menu.addAction( 'Create Custom Animator Track' )
		itemTitle.setEnabled( False )
		menu.addSeparator()
		#check if there is animator track
		trackTypes = _MOCK.getCustomAnimatorTrackTypesForObject( self.getTarget() )
		if not trackTypes: return
		for id, clas in list(trackTypes.items()):
			action = menu.addAction( id )
			def _makeTrackCreator( trackId ):
				return lambda x: self.addCustomAnimatorTrack( trackId )
			action.triggered.connect( _makeTrackCreator( id ) )
			action.setIcon( getIcon('object_track') )
		menu.exec_(QtGui.QCursor.pos())

	def addCustomAnimatorTrack( self, id ):
		animator = app.getModule( 'animator' )
		animator.addCustomAnimatorTrack( self.getTarget(), id )

##----------------------------------------------------------------##
class EntityHeader( EntityHeaderBase, QtWidgets.QWidget ):
	def __init__(self, *args ):
		super(EntityHeader, self).__init__( *args )
		self.setupUi( self )

##----------------------------------------------------------------##
class ComponentEditor( CommonObjectEditor, SceneObjectEditorMixin ): #a generic property grid 
	def onPropertyChanged( self, obj, id, value ):
		if _MOCK.markProtoInstanceOverrided( obj, id ):
			self.grid.refershFieldState( id )
		signals.emit( 'entity.modified', obj._entity, 'introspector' )

	def onPropertyReset( self, obj, id ):
		self.grid.refershFieldState( id )
		signals.emit( 'entity.modified', obj._entity, 'introspector' )

	def initWidget( self, container, objectContainer ):
		self.grid = super( ComponentEditor, self ).initWidget( container, objectContainer )
		
		self.initFieldContextMenu( self.grid )
		self.initFoldState()
		self.initAnimatorButton()
		return self.grid

	def setTarget( self, target ):
		super( ComponentEditor, self ).setTarget( target )
		if target['__proto_history']:
			self.container.setProperty( 'proto', True )
		else:
			self.container.setProperty( 'proto', False )
		self.container.repolish()
		self.restoreFoldState()
		self.updateAnimatorButton()
		#recording check
		# for field, editor in self.grid.editors.items():
		# 	pass

	def refreshTitle( self ):
		target = self.getTarget()
		alias = target._alias
		if alias:
			self.getContainer().setTitle( 
				'[%s] %s' % ( alias, self.typeName )
			)
		else:
			super( ComponentEditor, self ).refreshTitle()
	
	def getTargetRepr( self ):
		target = self.getTarget()
		alias = target._alias
		if alias:
			return '[%s] %s' % ( alias, self.typeName )
		else:
			return self.typeName
		

##----------------------------------------------------------------##
class ScriptedComponentEditor( ComponentEditor ):
	def initWidget( self, container, objectContainer ):
		mainGrid = super( ScriptedComponentEditor, self ).initWidget( container, objectContainer )
		subGrid = PropertyEditor( container )
		mainGrid.setObjectName( 'ScriptedComponentMainPropertyEditor' )
		subGrid.setObjectName( 'ScriptedComponentDataPropertyEditor' )
		self.subGrid = subGrid
		return [ mainGrid, subGrid ]

	def onPropertyChanged( self, obj, id, value ):
		super( ScriptedComponentEditor, self ).onPropertyChanged( obj, id, value )
		if id == 'script':
			self.refreshSubGrid()

	def setTarget( self, target ):
		super( ScriptedComponentEditor, self ).setTarget( target )
		self.refreshSubGrid()

	def refresh( self ):
		super( ScriptedComponentEditor, self ).refresh()
		self.subGrid.refreshAll()

	def unload( self ):
		super( ScriptedComponentEditor, self ).unload()
		self.subGrid.clear()

	def refreshSubGrid( self ):
		dataInstance = self.getTarget().dataInstance
		if dataInstance:
			self.subGrid.setTarget( dataInstance )
			self.subGrid.show()
		else:
			self.subGrid.setTarget( None )
			self.subGrid.hide()


##----------------------------------------------------------------##
class EntityEditor( ObjectEditor, SceneObjectEditorMixin ): #a generic property grid 
	def initWidget( self, container, objectContainer ):
		self.header = EntityHeader( container )
		self.grid = PropertyEditor( self.header )
		self.header.layout().addWidget( self.grid )
		self.grid.setContext( 'scene_editor' )		

		self.grid.propertyChanged.connect( self.onPropertyChanged )		
		self.header.buttonEditProto   .clicked .connect ( self.onEditProto )
		self.header.buttonGotoProto   .clicked .connect ( self.onGotoProto )
		self.header.buttonUnlinkProto .clicked .connect ( self.onUnlinkProto )

		self.header.buttonGotoPrefab   .clicked .connect ( self.onGotoPrefab   )
		self.header.buttonUnlinkPrefab .clicked .connect ( self.onUnlinkPrefab )
		self.header.buttonPushPrefab   .clicked .connect ( self.onPushPrefab   )
		self.header.buttonPullPrefab   .clicked .connect ( self.onPullPrefab   )
		
		self.initFieldContextMenu( self.grid )
		self.initFoldState()
		self.initAnimatorButton()

		return self.header

	def setTarget( self, target ):
		if not target.components: return
		introspector = self.getIntrospector()
		self.target = target
		self.grid.setTarget( target )		
		if isMockInstance( target, 'Entity' ):
			if target['__proto_history']:				
				self.container.setProperty( 'proto', True )
			else:
				self.container.setProperty( 'proto', False )
			self.container.repolish()
			
			#setup proto tool
			protoState = target['PROTO_INSTANCE_STATE']
			if protoState:
				self.header.containerProto.show()
				protoPath = getProtoPath( target )
				self.header.labelProtoPath.setText( protoPath )
			else:
				self.header.containerProto.hide()

			prefabPath = target['__prefabId']
			if prefabPath:
				self.header.containerPrefab.show()
				self.header.labelPrefabPath.setText( prefabPath )
			else:
				self.header.containerPrefab.hide()

			#add component editors
			for com in list(target.getSortedComponentList( target ).values()):
				if com.FLAG_INTERNAL: continue
				editor = introspector.addObjectEditor(
						com,
						context_menu = 'component_context',
						editor_class = ComponentEditor,
						show_after_add = False
					)

			self.buttonAddComponent = buttonAddComponent = QtWidgets.QToolButton()
			buttonAddComponent.setObjectName( 'ButtonIntrospectorAddComponent' )
			buttonAddComponent.setText( 'Add Component ...' )
			buttonAddComponent.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
			buttonAddComponent.clicked.connect( self.onButtonAddComponent )
			introspector.addWidget( self.buttonAddComponent )

			self.buttonPasteComponent = buttonPasteComponent = QtWidgets.QToolButton()
			buttonPasteComponent.setObjectName( 'ButtonIntrospectorAddComponent' )
			buttonPasteComponent.setText( 'Paste Component' )
			buttonPasteComponent.setSizePolicy( QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed )
			buttonPasteComponent.clicked.connect( self.onButtonPasteComponent )
			introspector.addWidget( self.buttonPasteComponent )

		self.restoreFoldState()
		self.updateAnimatorButton()

	def onButtonAddComponent( self ):
		requestSearchView( 
				info    = 'select component type to create',
				context = 'component_creation',
				on_selection = lambda obj: 
					app.doCommand( 'scene_editor/create_component', name = obj, target = self.getTarget() )
				)

	def onButtonPasteComponent( self ):
		app.getModule( 'scenegraph_editor' ).onPasteComponent( self.getTarget(), None )

	def onPropertyChanged( self, obj, id, value ):
		if _MOCK.markProtoInstanceOverrided( obj, id ):
			self.grid.refershFieldState( id )
		if id == 'name':
			signals.emit( 'entity.renamed', obj, value )
		elif id == 'layer':
			signals.emit( 'entity.renamed', obj, value )
		elif id == 'zOrder':
			signals.emit( 'entity.reorder', obj )
		elif id == '__gizmoIcon':
			signals.emit( 'entity.gizmo_changed', obj, value )
		elif id == 'visible':
			signals.emit( 'entity.visible_changed', obj )
		signals.emit( 'entity.modified', obj, 'introspector' )

	def onPropertyReset( self, obj, id ):
		self.grid.refershFieldState( id )
		if id == 'name':
			signals.emit( 'entity.renamed', obj, obj.getName( obj ) )
		elif id == 'layer':
			signals.emit( 'entity.renamed', obj, obj.getName( obj ) )
		elif id == 'zOrder':
			signals.emit( 'entity.reorder', obj )
		elif id == '__gizmoIcon':
			signals.emit( 'entity.gizmo_changed', obj, value )
		elif id == 'visible':
			signals.emit( 'entity.visible_changed', obj )
		signals.emit( 'entity.modified', obj, 'introspector' )

	def onGotoProto( self ):
		assetBrowser = app.getModule( 'asset_browser' )
		if assetBrowser:
			assetBrowser.locateAsset( getProtoPath(self.target) )

	def onEditProto( self ):
		path = getProtoPath( self.target )
		assetNode = app.getAssetLibrary().getAssetNode( path )
		if assetNode:
			assetNode.edit()

	def onUnlinkProto( self ):
		app.doCommand(
			'scene_editor/unlink_proto',
			entity = self.target	
		)
		self.getIntrospector().refresh( self.target )

	def onGotoPrefab( self ):
		assetBrowser = app.getModule( 'asset_browser' )
		if assetBrowser:
			assetBrowser.locateAsset( self.target['__prefabId'] )

	def onUnlinkPrefab( self ):
		app.doCommand(
			'scene_editor/unlink_prefab',
			entity = self.target	
		)
		self.getIntrospector().refresh( self.target )
		
	def onPushPrefab( self ):
		app.doCommand(
			'scene_editor/push_prefab',
			entity = self.target	
		)

	def onPullPrefab( self ):
		app.doCommand(
			'scene_editor/pull_prefab',
			entity = self.target	
		)

	def refresh( self ):
		self.grid.refreshAll()

	def unload( self ):
		self.target = None
		self.grid.clear()

	def refreshTitle( self ):
		title = self.getTargetRepr()
		self.getContainer().setTitle( title )

	def getTargetRepr( self ):
		target = self.getTarget()
		if not target: return '<????>'
		name = target.getName( target )
		return '[%s] %s' % ( name, self.typeName )

##----------------------------------------------------------------##
class EntityGroupEditor( CommonObjectEditor ):
	def onPropertyChanged( self, obj, id, value ):
		if _MOCK.markProtoInstanceOverrided( obj, id ):
			self.grid.refershFieldState( id )
		signals.emit( 'entity.modified', obj._entity, 'introspector' )

	def onPropertyChanged( self, obj, id, value ):
		if id == 'name':
			signals.emit( 'entity.renamed', obj, value )
		elif id == 'visible':
			signals.emit( 'entity.visible_changed', obj )
		signals.emit( 'entity.modified', obj, 'introspector' )


##----------------------------------------------------------------##
class CompactEntityEditorTreeWidget( GenericTreeWidget ):
	def __init__( self, *args, **options ):
		options[ 'show_root' ] = True
		super( CompactEntityEditorTreeWidget, self ).__init__( *args, **options )
		# self.headerItem().setHidden( True )
		self.setMinimumSize( 30, 30 )

	def getHeaderInfo( self ):
		return [ ('Type',150, True ), ('Name', 80, True ), ('Desc',-1, True) ]

	def getRootNode( self ):
		return self.parent().target

	def getNodeParent( self, node ): # reimplemnt for target node	
		root = self.getRootNode()
		if node == root:
			return None
		return node._entity

	def getNodeChildren( self, node ):
		root = self.getRootNode()
		if node == root:
			result = []
			for com in list(root.getSortedComponentList( root ).values()):
				if com.FLAG_INTERNAL: continue 
				result.append( com )
			return result
		else:
			return []

	def updateItemContent( self, item, node, **option ):
		if isMockInstance( node, 'Entity' ):
			item.setText( 0, getMockClassName( node ) )
			item.setText( 1, node.getName( node ) )
		else:
			item.setText( 0, getMockClassName( node ) )
			alias = node._alias
			if alias:
				item.setText( 1, alias )
			else:
				item.setText( 1, '-' )

	def onItemSelectionChanged( self ):
		self.parent().editor.updateSelection()


##----------------------------------------------------------------##
class CompactEntityEditorWidget( QtWidgets.QWidget ):
	def __init__( self, *args ):
		super( CompactEntityEditorWidget, self ).__init__( *args )
		self.editor = None
		self.target = None
		layout = QtWidgets.QVBoxLayout( self )
		self.tree = CompactEntityEditorTreeWidget( self )
		layout.addWidget( self.tree )
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
	
		self.tree.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Fixed
		)
		self.setMinimumSize( 30, 30 )
		self.setFixedHeight( 70 )
		

	def setTarget( self, target ):
		self.target = target
		self.rebuild()

	def rebuild( self ):
		self.tree.rebuild()

##----------------------------------------------------------------##
class CompactEntityEditor( ObjectEditor ):
	def initWidget( self, container, objectContainer ):
		introspector = self.getIntrospector()
		self.headerWidget = CompactEntityEditorWidget( )
		self.headerWidget.editor = self
		introspector.addHeaderWidget( self.headerWidget )
		return None
		
	def setTarget( self, target ):
		self.target = target
		self.headerWidget.setTarget( target )

	def refresh( self ):
		self.headerWidget.rebuild()

	def updateSelection( self ):
		introspector = self.getIntrospector()
		for obj in self.headerWidget.tree.getSelection():
			if obj == self.target:
				introspector.addObjectEditor(
					obj,
					context_menu = 'entity_context',
					editor_class = EntityEditor,
					show_after_add = False
				)
			else:
				introspector.addObjectEditor(
					obj,
					context_menu = 'component_context',
					editor_class = ComponentEditor,
					show_after_add = False
				)

	def unload( self ):
		self.target = None
		self.headerWidget.setTarget( None )


##----------------------------------------------------------------##
def EntityEditorFactory():
	return CompactEntityEditor()

registerMOCKObjectEditor( 'Scene',       SceneObjectEditor )
# registerMOCKObjectEditor( 'Entity',      CompactEntityEditor  )
registerMOCKObjectEditor( 'Entity',      EntityEditor      )
registerMOCKObjectEditor( 'EntityGroup', EntityGroupEditor )

registerMOCKObjectEditor( 'ScriptedBehaviour', ScriptedComponentEditor )
registerMOCKObjectEditor( 'ScriptedFSMController', ScriptedComponentEditor )

