import os
import time

##----------------------------------------------------------------##
from gii.core     import *
from gii.SearchView   import requestSearchView, registerSearchEnumerator

from .SceneEditor  import SceneEditorModule
from util.IDPool  import IDPool

from gii.qt.controls.PropertyEditor import PropertyEditor
from gii.qt.controls.Menu           import MenuManager
from gii.qt.helpers                 import addWidgetWithLayout, repolishWidget
from gii.qt.IconCache               import getIcon

from qtpy        import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore import Qt, QEventLoop, QEvent, QObject, Signal, Slot


##----------------------------------------------------------------##
def getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path
##----------------------------------------------------------------##
ObjectContainerBase,BaseClass = uic.loadUiType(getModulePath('ObjectContainer.ui'))

##----------------------------------------------------------------##
class ObjectContainer( QtWidgets.QWidget ):
	foldChanged  = Signal( bool )
	def __init__( self, *args ):
		super( ObjectContainer, self ).__init__( *args )
		self.ui = ObjectContainerBase()
		self.ui.setupUi( self )

		self.setSizePolicy( 
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Fixed
			)
		# self.setAttribute( Qt.WA_NoSystemBackground, True )
		self.mainLayout = QtWidgets.QVBoxLayout(self.getInnerContainer())
		self.mainLayout.setSpacing(0)
		self.mainLayout.setContentsMargins(0,0,0,0)
		self.contextObject = None

		self.folded = False
		self.toggleFold( False, True )
		
		self.ui.buttonFold.clicked.connect( lambda x: self.toggleFold( None ) )
		
		self.ui.buttonContext.clicked.connect( lambda x: self.openContextMenu() )
		self.ui.buttonContext.setIcon( getIcon( 'menu' ) )
		
		self.ui.buttonName.clicked.connect( lambda x: self.toggleFold( None ) )
		self.ui.buttonName.setIcon( getIcon( 'component' ) )
		self.ui.buttonName.setToolButtonStyle( Qt.ToolButtonTextBesideIcon )
		
		self.ui.buttonKey.setIcon( getIcon( 'key' ) )
		self.ui.buttonKey.hide()

		self.ui.buttonFold.setIcon( getIcon( 'node_folded' ) )


	def getButtonKey( self ):
		return self.ui.buttonKey

	def getButtonContext( self ):
		return self.ui.buttonContext

	def setContextObject( self, context ):
		self.contextObject = context

	def addWidget(self, widget, **layoutOption):
		if isinstance( widget, list):
			for w in widget:
				self.addWidget( w, **layoutOption )
			return
		# widget.setParent(self)		
		if layoutOption.get('fixed', False):
			widget.setSizePolicy(
				QtWidgets.QSizePolicy.Fixed,
				QtWidgets.QSizePolicy.Fixed
				)
		elif layoutOption.get('expanding', True):
			widget.setSizePolicy(
				QtWidgets.QSizePolicy.Expanding,
				QtWidgets.QSizePolicy.Expanding
				)		
		self.mainLayout.addWidget(widget)
		return widget

	def setContextMenu( self, menuName ):
		menu = menuName and MenuManager.get().find( menuName ) or None
		self.contextMenu = menu
		if not menu:
			self.ui.buttonContext.hide()
		else:
			self.ui.buttonContext.show()

	def getInnerContainer( self ):
		return self.ui.ObjectInnerContainer

	def getHeader( self ):
		return self.ui.ObjectHeader

	def repolish( self ):
		repolishWidget( self.ui.ObjectInnerContainer )
		repolishWidget( self.ui.ObjectHeader )
		repolishWidget( self.ui.buttonContext )
		repolishWidget( self.ui.buttonKey )
		repolishWidget( self.ui.buttonFold )
		repolishWidget( self.ui.buttonName )

	def toggleFold( self, folded = None, notify = True ):
		if folded == None:
			folded = not self.folded
		self.folded = folded
		if folded:
			# self.ui.buttonFold.setText( '+' )
			self.ui.buttonFold.setIcon( getIcon( 'node_folded' ) )
			self.ui.ObjectInnerContainer.hide()
		else:
			# self.ui.buttonFold.setText( '-' )
			self.ui.buttonFold.setIcon( getIcon( 'node_unfolded' ) )
			self.ui.ObjectInnerContainer.show()
		if notify:
			self.foldChanged.emit( self.folded )

	def setTitle( self, title ):
		self.ui.buttonName.setText( title )

	def openContextMenu( self ):
		if self.contextMenu:
			self.contextMenu.popUp( context = self.contextObject )

##----------------------------------------------------------------##
_OBJECT_EDITOR_CACHE = {} 

def pushObjectEditorToCache( typeId, editor ):
	pool = _OBJECT_EDITOR_CACHE.get( typeId, None )
	if not pool:
		pool = []
		_OBJECT_EDITOR_CACHE[ typeId ] = pool
	editor.container.setUpdatesEnabled( False )
	pool.append( editor )
	return True

def popObjectEditorFromCache( typeId ):
	pool = _OBJECT_EDITOR_CACHE.get( typeId, None )
	if pool:
		editor = pool.pop()
		if editor:
			editor.container.setUpdatesEnabled( True )
		return editor

def clearObjectEditorCache( typeId ):
	if typeId in _OBJECT_EDITOR_CACHE:
		del _OBJECT_EDITOR_CACHE[ typeId ]

##----------------------------------------------------------------##
class ObjectEditor( object ):	
	def __init__( self ):
		self.parentIntrospector = None
		self.typeName = 'Unknown'

	def getContainer( self ):
		return self.container

	def getInnerContainer( self ):
		return self.container.ObjectInnerContainer()

	def getIntrospector( self ):
		return self.parentIntrospector
		
	def initWidget( self, container, objectContainer ):
		pass

	def getContextMenu( self ):
		pass

	def setTarget( self, target ):
		self.target = target

	def getTarget( self ):
		return self.target

	def getTargetRepr( self ):
		return self.typeName

	def getTargetTypeRepr( self ):
		return self.typeName

	def getTargetIcon( self ):
		return None

	def unload( self ):
		pass

	def needCache( self ):
		return True

	def setFocus( self ):
		pass

	def refreshTitle( self ):
		self.getContainer().setTitle( self.typeName )

	def refresh( self ):
		pass

		
##----------------------------------------------------------------##
class CommonObjectEditor( ObjectEditor ): #a generic property grid 
	def initWidget( self, container, objectContainer ):
		self.grid = PropertyEditor(container)
		self.grid.propertyChanged.connect( self.onPropertyChanged )
		return self.grid

	def setTarget( self, target ):
		self.target = target
		self.grid.setTarget( target )

	def refresh( self ):
		self.grid.refreshAll()

	def unload( self ):
		self.grid.clear()
		self.target = None

	def onPropertyChanged( self, obj, id, value ):
		pass

##----------------------------------------------------------------##
def registerObjectEditor( typeId, editorClas ):
	app.getModule('introspector').registerObjectEditor( typeId, editorClas )


##----------------------------------------------------------------##
class HeaderContainer( QtWidgets.QFrame ):
	def __init__( self, *args ):
		super(HeaderContainer, self).__init__( *args )
		self.mainLayout = layout = QtWidgets.QVBoxLayout( self )
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )

##----------------------------------------------------------------##
class IntrospectorInstance(object):
	def __init__(self, id):
		self.id = id

		self.rebuilding = False
		self.locked    = False

		self.target    = None
		self.container = None
		self.body      = None
		self.editors   = []

	def createWidget(self, container):
		self.container = container
		self.container.setObjectName( 'IntrospectorContainer' )
		
		self.header = container.addWidgetFromFile(
			getModulePath( 'Introspector.ui' ),
			expanding = False )

		self.header.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Fixed
		)

		iconSize = QtCore.QSize( 12, 12 )
		self.header.setObjectName( 'IntrospectorHeader' )
		self.header.buttonLock.setObjectName( 'ButtonLock' )
		self.header.buttonLock.setIcon( getIcon('unlock') )
		self.header.buttonLock.setIconSize( iconSize )

		self.header.buttonSync.setIcon( getIcon('in') )
		self.header.buttonSync.setIconSize( iconSize )

		self.header.buttonNew.setIcon( getIcon('add') )
		self.header.buttonNew.setIconSize( iconSize )

		self.header.buttonSelect.setIcon( getIcon('find') )
		self.header.buttonSelect.setIconSize( iconSize )

		self.header.buttonFold.setIcon( getIcon('collapse') )
		self.header.buttonFold.setIconSize( iconSize )

		self.header.buttonUnfold.setIcon( getIcon('expand') )
		self.header.buttonUnfold.setIconSize( iconSize )

		# self.header.buttonFind.setIcon( getIcon('find') )
		self.header.buttonFind.setIconSize( iconSize )

		self.header.buttonSync   .clicked .connect( self.onSyncSelection )
		self.header.buttonLock   .clicked .connect( self.onToggleLock )
		self.header.buttonNew    .clicked .connect( self.onRequestInstance )
		self.header.buttonSelect .clicked .connect( self.onLocateSelection )
		self.header.buttonFind   .clicked .connect( self.onFindEditor )
		self.header.buttonFold   .clicked .connect( self.foldAll )
		self.header.buttonUnfold .clicked .connect( self.unfoldAll)
		# self.header.buttonLock.setToolButtonStyle( Qt.ToolButtonTextBesideIcon )
		

		self.header.groupMultiple.hide()
		# self.header.buttonSelect.setToolButtonStyle( Qt.ToolButtonTextBesideIcon )

		self.headerContainer = container.addWidget( HeaderContainer( container ) )
		self.headerContainer.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Fixed
		)

		self.scroll = scroll = container.addWidget( QtWidgets.QScrollArea( container ) )
		self.body   = body   = QtWidgets.QWidget( container )
		scroll.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Expanding
			)
		
		self.scroll.verticalScrollBar().setStyleSheet('width:6px')
		scroll.setWidgetResizable( True )
		body.mainLayout = layout = QtWidgets.QVBoxLayout( body )
		layout.setSpacing(0)
		layout.setContentsMargins(0,0,0,0)
		layout.addStretch()
		scroll.setWidget( body )

		self.updateTimer = self.container.startTimer( 5, self.onUpdateTimer )
		self.updatePending = False
	
	def isLocked( self ):
		return self.locked

	def setLocked( self, locked = True ):
		self.locked = locked
		self.header.buttonLock.setIcon( 
			getIcon( locked and 'lock' or 'unlock' )
		)
		self.header.buttonLock.setChecked( self.locked )
		if not locked:
			parent = app.getModule('introspector')
			self.setTarget( parent.currentTarget )


	def onRequestInstance( self ):
		parent = app.getModule('introspector')
		instance = parent.requestInstance()
		instance.setTarget( [self.target], True )

	def onToggleLock( self ):
		locked = self.header.buttonLock.isChecked()
		if locked == self.locked: return
		self.setLocked( locked )

	def onSyncSelection( self ):
		sceneGraphEditor = app.getModule( 'scenegraph_editor' )
		if sceneGraphEditor:
			self.setTarget( sceneGraphEditor.getSelection(), True )

	def onLocateSelection( self ):
		sceneGraphEditor = app.getModule( 'scenegraph_editor' )
		if not sceneGraphEditor: return
		if not self.target: return
		sceneGraphEditor.changeSelection( self.target )

	def onFindEditor( self ):
		requestSearchView(
			info    = 'select target entity class to replace with',
			on_search    = self.listSubEditors,
			on_selection = self.focusTargetSolo,
			sort_method  = 'none'
		)

	def foldAll( self ):
		for editor in self.editors:
			container = editor.container
			if container:
				container.toggleFold( True )

	def unfoldAll( self ):
		for editor in self.editors:
			container = editor.container
			if container:
				container.toggleFold( False )

	def listSubEditors( self, typeId, context, option ):
		entries = []
		for editor in self.editors:
			target     = editor.getTarget()
			targetRepr = editor.getTargetRepr()
			typeRepr   = editor.getTargetTypeRepr()
			iconName   = editor.getTargetIcon()
			entry = ( target, targetRepr, typeRepr, iconName )
			entries.append( entry )
		return entries

	def getTarget(self):
		return self.target

	def rebuild(self):
		self.setTarget( [self.target], True )

	def setTarget(self, t, forceRefresh = False ):
		if self.target == t and not forceRefresh: return
		app.getModule( 'qt' ).onUpdate()
		self.rebuilding = True
		self.container.setUpdatesEnabled( False )
		self.scroll.setVisible( False )
		if self.target:
			self.clear()
		
		if not t: 
			self.target=None
			self.rebuilding = False
			self.container.setUpdatesEnabled( True )
			self.scroll.setVisible( True )
			self.header.groupMultiple.hide()
			return

		if len(t)>1:
			self.header.groupMultiple.show()
			self.header.textMultipleTargetInfo.setText('Multiple object selected...')
			self.target = t[0] #TODO: use a multiple selection proxy as target
		else:
			self.header.groupMultiple.hide()
			self.target = t[0]

		self.addObjectEditor( self.target, root = True )
		self.rebuilding = False
		self.container.setUpdatesEnabled( True )
		self.scroll.setVisible( True )

	def hasTarget( self, target ):
		if self.getObjectEditor( target ): return True
		return False

	def focusTarget( self, target ):
		editor = self.getObjectEditor( target )
		if not editor: return
		#scroll to editor
		editorContainer = editor.getContainer()
		y = editorContainer.y()
		scrollBar = self.scroll.verticalScrollBar()
		scrollBar.setValue( y - 5 )
		editor.setFocus()
		return editor

	def focusTargetSolo( self, target ):
		editor = self.focusTarget( target )
		if not editor: return
		self.foldAll()
		editor.container.toggleFold( False )

	def getObjectEditor( self, targetObject ):
		for editor in self.editors:
			if editor.getTarget() == targetObject: return editor
		return None

	def addWidget( self, widget, **option ):
		widget.setParent( self.body )
		count = self.body.mainLayout.count()
		self.body.mainLayout.insertWidget( count - 1, widget )
		return widget

	def addHeaderWidget( self, widget, **option ):
		self.headerContainer.hide()
		widget.setParent( self.headerContainer )
		self.headerContainer.layout().addWidget( widget )
		self.headerContainer.show()
		return widget

	def addObjectEditor( self, target, **option ):
		showAfterAdded = option.get( 'show_after_add', True )
		isRoot = option.get( 'root', False )
		parent = app.getModule('introspector')
		typeId = ModelManager.get().getTypeId( target )
		if not typeId:
			if showAfterAdded: self.scroll.show()
			return

		#create or use cached editor
		cachedEditor = popObjectEditorFromCache( typeId )
		if cachedEditor:
			editor = cachedEditor
			editor.parentIntrospector = self
			container = editor.container
			count = self.body.mainLayout.count()
			assert count>0
			self.body.mainLayout.insertWidget( count - 1, container )
			container.show()
			container.setContextObject( target )
			self.editors.append( editor )

		else:
			defaultEditorClas = option.get( 'editor_class', None )
			editorClas = parent.getObjectEditorByTypeId( typeId, defaultEditorClas )

			editor = editorClas()
			editor.parentIntrospector = self

			editor.targetTypeId = typeId
			self.editors.append( editor )
			container = ObjectContainer( self.body )
			editor.container = container
			widget = editor.initWidget( container.getInnerContainer(), container )
			container.setContextObject( target )

			if widget:
				if isinstance( widget, list ):
					for w in widget:
						container.addWidget( w )
				else:
					container.addWidget( widget )

				model = ModelManager.get().getModelFromTypeId( typeId )

				if model:
					typeName = model.getShortName()
				else:
					typeName = repr( typeId )
					#ERROR
				count = self.body.mainLayout.count()
				assert count>0
				self.body.mainLayout.insertWidget( count - 1, container )
				menuName = option.get( 'context_menu', editor.getContextMenu() )
				container.setContextMenu( menuName )
				container.ownerEditor = editor
				editor.typeName = typeName
				
			else:
				container.hide()
		editor.setTarget( target )
		editor.refreshTitle()
		if showAfterAdded:
			size = self.body.sizeHint()
			size.setWidth( self.scroll.width() )
			self.body.resize( size )
			self.scroll.show()
		return editor


	def clear(self):		
		for editor in self.editors:
			editor.container.setContextObject( None )
			cached = False
			if editor.needCache():
				cached = pushObjectEditorToCache( editor.targetTypeId, editor )
			if not cached:
				editor.unload()
			editor.target = None

		#remove headerWidgets
		headerLayout = self.headerContainer.layout()
		for count in reversed( list(range(headerLayout.count())) ):
			child = headerLayout.takeAt( count )
			w = child.widget()
			if w:
				w.setParent( None )

		#remove containers
		mainLayout = self.body.mainLayout
		for count in reversed( list(range(mainLayout.count())) ):
			child = mainLayout.takeAt( count )
			w = child.widget()
			if w:
				w.setParent( None )
		mainLayout.addStretch()
		
		self.target = None
		self.editors = []

	def refresh(self, target = None):
		if self.rebuilding: return False
		self.scroll.setUpdatesEnabled( False )
		for editor in self.editors:
			if not target or editor.getTarget() == target:
				editor.refresh()
		self.scroll.setUpdatesEnabled( True )
		return True

	def onUpdateTimer( self ):
		if self.updatePending == True:
			if self.refresh():
				self.updatePending = False

	def scheduleUpdate( self ):
		self.updatePending = True


##----------------------------------------------------------------##
class SceneIntrospector( SceneEditorModule ):
	"""docstring for SceneIntrospector"""
	def __init__(self):
		super(SceneIntrospector, self).__init__()
		self.instances      = []
		self.instanceCache  = []
		self.idPool         = IDPool()
		self.objectEditorRegistry = TypeIdDict()
		self.currentTarget  = None
		self.updatePaused   = False

	def getName(self):
		return 'introspector'

	def getDependency(self):
		return ['qt', 'scene_editor']
	
	def onLoad(self):		
		self.requestInstance()
		signals.connect( 'selection.changed', self.onSelectionChanged )
		signals.connect( 'component.added',   self.onComponentAdded )
		signals.connect( 'component.removed', self.onComponentRemoved )
		signals.connect( 'component.renamed', self.onComponentRenamed )
		signals.connect( 'component.reordered', self.onComponentReordered )
		signals.connect( 'entity.modified',   self.onEntityModified ) 
		self.widgetCacheHolder = QtWidgets.QWidget()
		
	def onStart( self ):
		pass

	def requestInstance(self):
		#todo: pool
		id   = self.idPool.request()
		container = self.requestDockWindow('SceneIntrospector-%d'%id,
				title   = 'Introspector',
				dock    = 'right',
				minSize = (200,100)
		)
		instance = IntrospectorInstance(id)
		instance.createWidget( container )
		self.instances.append( instance )
		return instance

	def findInstances(self, target):
		res=[]
		for instance in self.instances:
			if instance.target==target:
				res.append(instance)
		return res

	def getInstances(self):
		return self.instances

	def registerObjectEditor( self, typeId, editorClas ):
		assert typeId, 'null typeid'
		self.objectEditorRegistry[ typeId ] = editorClas

	def getObjectEditorByTypeId( self, typeId, defaultClass = None ):
		if not defaultClass:
			defaultClass = CommonObjectEditor
		return self.objectEditorRegistry.get( typeId, defaultClass )

	def pauseUpdate( self, paused = True ):
		self.updatePaused = paused
		if not paused:
			self.updateTarget()

	def updateTarget( self ):
		if self.updatePaused: return
		target = self.currentTarget
		for instance in self.instances:
			if instance.isLocked(): continue
			instance.setTarget( target )

	def onSelectionChanged( self, selection, key ):
		if key != 'scene': return
		target = None
		if isinstance( selection, list ):
			target = selection
		elif isinstance( selection, tuple ):
			(target) = selection
		else:
			target=selection
		#first selection only?
		self.currentTarget = target
		self.updateTarget()

	def onComponentAdded( self, com, entity ):
		for instance in self.instances:
			if instance.target == entity:
				instance.rebuild()
				instance.focusTarget( com )

	def onComponentRemoved( self, com, entity ):
		for instance in self.instances:
			if instance.target == entity:
				instance.rebuild()

	def onComponentRenamed( self, com, entity ):
		for instance in self.instances:
			if instance.target == entity:
				editor = instance.getObjectEditor( com )
			if editor:
				editor.refreshTitle()

	def onComponentReordered( self, com, entity ):
		for instance in self.instances:
			if instance.target == entity:
				instance.rebuild()

	def onEntityModified( self, entity, context=None ):
		if context != 'introspector' :
			self.refresh( entity, context )

	def refresh( self, target = None, context = None ):
		for instance in self.instances:
			if not target or instance.hasTarget( target ):
				instance.scheduleUpdate()


##----------------------------------------------------------------##

SceneIntrospector().register()

