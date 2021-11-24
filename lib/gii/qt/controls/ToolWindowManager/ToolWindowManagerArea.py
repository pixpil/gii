from qtpy        import QtCore, QtWidgets, QtGui, uic
from qtpy.QtWidgets  import QApplication, QTabWidget
from qtpy.QtGui  import QCursor
from qtpy.QtCore import qWarning, QEvent, Qt

class ToolWindowManagerArea( QTabWidget ):
	"""docstring for ToolWindowManagerArea"""
	def __init__( self, manager, parent = None ):
		super( ToolWindowManagerArea, self ).__init__( parent )
		self.manager         = manager
		self.dragCanStart    = False
		self.tabDragCanStart = False
		self.setMovable( True )
		self.setTabsClosable( True )
		# self.setTabPosition( QTabWidget.South )
		self.tabBar().installEventFilter( self )
		self.tabBar().setExpanding( True )
		self.manager.areas.append( self )

	def addToolWindow( self, toolWindow ):
		self.addToolWindows( [toolWindow] )

	def addToolWindows( self, toolWindows ):
		index = 0
		for toolWindow in toolWindows:
			icon = toolWindow.windowIcon()
			title = toolWindow.windowTitle()
			index = self.addTab( toolWindow, icon, title )
		self.setCurrentIndex( index )
		self.manager.lastUsedArea = self

	def toolWindows( self ):
		result = []
		for i in range( self.count() ):
			result.append( self.widget( i ) )
		return result

	def mousePressEvent( self, event ):
		if event.buttons() == Qt.LeftButton:
			self.dragCanStart = True

	def mouseReleaseEvent( self, event ):
		self.dragCanStart = False
		self.manager.updateDragPosition()

	def mouseMoveEvent( self, event ):
		self.check_mouse_move( event )

	def eventFilter( self, obj, event ):
		if obj == self.tabBar():
			if event.type() == QEvent.MouseButtonPress and event.buttons() == Qt.LeftButton:
				# can start tab drag only if mouse is at some tab, not at empty tabbar space
				if self.tabBar().tabAt( event.pos() ) >= 0:
					self.tabDragCanStart = True
				else:
					self.dragCanStart = True

			elif event.type() == QEvent.MouseButtonRelease:
				self.tabDragCanStart = False
				self.dragCanStart = False
				self.manager.updateDragPosition()

			elif event.type() == QEvent.MouseMove:
				self.manager.updateDragPosition()
				if self.tabDragCanStart:
					if self.tabBar().rect().contains( event.pos() ):
						return False
					if event.buttons() != Qt.LeftButton:
						return False
					toolWindow = self.currentWidget()
					if not ( toolWindow and self.manager.hasToolWindow( toolWindow ) ):
						return False
					self.tabDragCanStart = False
					#stop internal tab drag in QTabBar
					releaseEvent = QtGui.QMouseEvent( 
							QEvent.MouseButtonRelease,
							event.pos(), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier
						)
					QApplication.sendEvent( self.tabBar(), releaseEvent )
					self.manager.startDrag( [toolWindow] )

				elif self.dragCanStart:
					self.check_mouse_move( event )

		return QTabWidget.eventFilter( self, obj, event )

	def saveState( self ):
		result = {}		
		objectNames = []
		for i in range( self.count() ):
			name = self.widget( i ).objectName()
			if name:
				objectNames.append( name )
			else:
				qWarning("cannot save state of tool window without object name")
		result["type"] = "area"
		result["currentIndex"] = self.currentIndex()
		result["objectNames"] = objectNames
		return result

	def restoreState( self, data ):
		for objectName in data.get( 'objectNames', [] ):
			found = False
			for window in self.manager.toolWindows():
				if window.objectName() == objectName:
					self.addToolWindow( window )
					found = True
					break
			if not found:
				qWarning("tool window with name '%s' not found" % objectName )
		self.setCurrentIndex( data.get( "currentIndex", 0 ) )

	def check_mouse_move( self, event ):
		self.manager.updateDragPosition()
		if event.buttons() == Qt.LeftButton \
		and	not self.rect().contains( self.mapFromGlobal( QCursor.pos() ) ) \
		and	self.dragCanStart:
			self.dragCanStart = False
			toolWindows = []
			for i in range( self.count() ):
				toolWindow = self.widget(i)
				if self.manager.hasToolWindow( toolWindow ):
					toolWindows.append( toolWindow )
				else:
					qWarning("tab widget contains unmanaged widget")
			self.manager.startDrag(toolWindows)
