#C++ original by Pavel Strakhov ( https:#github.com/Riateche/toolwindowmanager )

from .ToolWindowManagerWrapper import ToolWindowManagerWrapper
from .ToolWindowManagerArea import ToolWindowManagerArea
from qtpy        import QtCore, QtWidgets, QtGui, uic, QT_VERSION
from qtpy.QtWidgets  import QApplication, QSplitter, QWidget
from qtpy.QtGui import QCursor
from qtpy.QtCore import qWarning, QPoint, QRect, QSize, Signal, Qt
  

def cast( obj, clas ):
	if type( obj ) == clas: return obj
	if isinstance( obj, clas ): return obj
	return None

def findClosestParent( widget, clas ):
	while widget != None:
		if isinstance( widget, clas ):
			return widget
		widget = widget.parentWidget()
	return None

##----------------------------------------------------------------##
class AreaReference( object ):
	'''The AreaReference class represents a place where tool windows should be moved'''	
	def __init__( self, type, widget = None ):
		self.type = type
		self.setWidget( widget )

	def setWidget( self, widget ):
		if self.type in [ 
		ToolWindowManager.LastUsedArea,
		ToolWindowManager.NewFloatingArea,
		ToolWindowManager.NoArea,
		ToolWindowManager.EmptySpace ]:
			if widget:
				qWarning( 'area parameter ignored for this type' )
			self.widget = None

		elif self.type == ToolWindowManager.AddTo:
			if isinstance( widget, ToolWindowManagerArea ):
				self.widget = widget
			else:
				qWarning( 'only ToolWindowManagerArea can be used with this type' )

		else:
			if isinstance( widget, ToolWindowManagerArea ) or	isinstance( widget, QSplitter ):
				self.widget = widget
			else:
				qWarning( 'only ToolWindowManagerArea or splitter can be used with this type' )
				self.widget = None

	def area( self ):
		if isinstance( self.widget, ToolWindowManagerArea ):
			return self.widget
		return None
		

##----------------------------------------------------------------##
class ToolWindowManager( QtWidgets.QWidget ):
	'''docstring for ToolWindowManager'''
	#! The area tool windows has been added to most recently.
	LastUsedArea = 1
	#! New area in a detached window.
	NewFloatingArea = 2
	#! Area inside the manager widget (only available when there is no tool windows in it).
	EmptySpace = 3
	#! Tool window is hidden.
	NoArea = 4
	#! Existing area specified in AreaReference argument.
	AddTo = 5
	#! New area to the left of the area specified in AreaReference argument.
	LeftOf = 6
	#! New area to the right of the area specified in AreaReference argument.
	RightOf = 7
	#! New area to the top of the area specified in AreaReference argument.
	TopOf = 8
	#! New area to the bottom of the area specified in AreaReference argument.
	BottomOf = 9

	#signal
	toolWindowVisibilityChanged = Signal( QWidget, bool )

	def __init__( self, parent = None ):
		super( ToolWindowManager, self ).__init__( parent )
		self.lastUsedArea = None
		self.suggestions = []
		self.wrappers    = []
		self.areas       = []
		self.draggedToolWindows = []
		#----
		self.borderSensitivity = 12
		testSplitter = QSplitter()
		self.rubberBandLineWidth = testSplitter.handleWidth()
		self.dragIndicator = QtWidgets.QLabel( None, Qt.ToolTip)
		self.dragIndicator.setAttribute( Qt.WA_ShowWithoutActivating)
		mainLayout = QtWidgets.QVBoxLayout( self )
		mainLayout.setContentsMargins( 0, 0, 0, 0 )
		
		wrapper = ToolWindowManagerWrapper( self )
		wrapper.setWindowFlags( wrapper.windowFlags() & ~Qt.Window )
		mainLayout.addWidget( wrapper )

		self.dropSuggestionSwitchTimer = QtCore.QTimer( self )
		self.dropSuggestionSwitchTimer.timeout.connect( self.showNextDropSuggestion )
		self.dropSuggestionSwitchTimer.setInterval( 800 )
		self.dropCurrentSuggestionIndex = 0

		palette = QtGui.QPalette()
		color = QtGui.QColor( Qt.blue )
		color.setAlpha(80)
		palette.setBrush( QtGui.QPalette.Highlight, QtGui.QBrush( color ) )
		
		self.rectRubberBand = QtWidgets.QRubberBand( QtWidgets.QRubberBand.Rectangle, self )
		self.lineRubberBand = QtWidgets.QRubberBand( QtWidgets.QRubberBand.Line, self )
		self.rectRubberBand.setPalette( palette )
		self.lineRubberBand.setPalette( palette )
		self.toolWindowList = []

	def hideToolWindow( self, toolWindow ):
		self.moveToolWindow( toolWindow, ToolWindowManager.NoArea )

	def toolWindows( self ):
		return self.toolWindowList

	def hasToolWindow( self, toolWindow ):
		return toolWindow in self.toolWindowList

	def addToolWindow( self, toolWindow, area ):
		return self.addToolWindows( [toolWindow], area )

	def addToolWindows( self, toolWindows, area ):
		for toolWindow in toolWindows:
			if self.hasToolWindow( toolWindow ): continue
			toolWindow.hide()
			toolWindow.setParent( None )
			self.toolWindowList.append( toolWindow )
		self.moveToolWindows( toolWindows, area )

	def areaOf( self, toolWindow ):
		return findClosestParent( toolWindow, ToolWindowManagerArea )

	def moveToolWindow( self, toolWindow, area ):
		self.moveToolWindows( [ toolWindow ], area )

	def moveToolWindows( self, toolWindows, area ):
		if type( area ) == int:
			area = AreaReference( area )

		for toolWindow in toolWindows:
			if not self.hasToolWindow( toolWindow ): return
			if toolWindow.parentWidget():
				self.releaseToolWindow( toolWindow )

		areaType = area.type

		if areaType == ToolWindowManager.LastUsedArea and not self.lastUsedArea:
			foundArea = self.findChild( ToolWindowManagerArea )
			if foundArea:
				area = AreaReference( ToolWindowManager.AddTo, foundArea )
			else:
				area = ToolWindowManager.EmptySpace

		if areaType == ToolWindowManager.NoArea:
			#do nothing
			pass

		elif areaType == ToolWindowManager.NewFloatingArea:
			area = self.createArea()
			area.addToolWindows( toolWindows )
			wrapper = ToolWindowManagerWrapper( self )
			wrapper.layout().addWidget( area )
			wrapper.move( QCursor.pos() )
			wrapper.show()

		elif areaType == ToolWindowManager.AddTo:
			area.area().addToolWindows( toolWindows )

		elif areaType in ( ToolWindowManager.LeftOf, ToolWindowManager.RightOf, ToolWindowManager.TopOf, ToolWindowManager.BottomOf ):
			parentSplitter = cast( area.widget.parentWidget(), QSplitter )
			wrapper = cast( area.widget.parentWidget(), ToolWindowManagerWrapper )
			if not ( parentSplitter or wrapper ):
				qWarning( 'unknown parent type' )
				return
			# import pudb; pu.db
			useParentSplitter = False
			indexInParentSplitter = 0
			if parentSplitter:
				indexInParentSplitter = parentSplitter.indexOf( area.widget )
				if parentSplitter.orientation() == Qt.Vertical:
					useParentSplitter = areaType in ( ToolWindowManager.TopOf, ToolWindowManager.BottomOf )
				else:
					useParentSplitter = areaType in ( ToolWindowManager.LeftOf, ToolWindowManager.RightOf )

			if useParentSplitter:
				if areaType in ( ToolWindowManager.BottomOf , ToolWindowManager.RightOf ):
					indexInParentSplitter += 1
				newArea = self.createArea()
				newArea.addToolWindows( toolWindows )
				parentSplitter.insertWidget( indexInParentSplitter, newArea )

			else:
				area.widget.hide()
				area.widget.setParent( None )
				splitter = self.createSplitter()
				if areaType in ( ToolWindowManager.TopOf, ToolWindowManager.BottomOf ):
					splitter.setOrientation(Qt.Vertical)
				else:
					splitter.setOrientation(Qt.Horizontal)

				splitter.addWidget( area.widget )
				area.widget.show()
				newArea = self.createArea()
				if areaType in ( ToolWindowManager.TopOf, ToolWindowManager.LeftOf ):
					splitter.insertWidget( 0, newArea )
				else:
					splitter.addWidget( newArea )

				if parentSplitter:
					parentSplitter.insertWidget( indexInParentSplitter, splitter )
				else:
					wrapper.layout().addWidget( splitter )
				newArea.addToolWindows( toolWindows )

		elif areaType == ToolWindowManager.EmptySpace:
			wrapper = self.findChild( ToolWindowManagerWrapper )
			if wrapper.isOccupied():
				self.lastUsedArea.addToolWindows( toolWindows )
			else:
				newArea = self.createArea()
				wrapper.layout().addWidget( newArea )
				newArea.addToolWindows( toolWindows )

		elif areaType == ToolWindowManager.LastUsedArea:
			self.lastUsedArea.addToolWindows( toolWindows )

		else:
			qWarning( 'invalid type' )

		self.simplifyLayout()
		for toolWindow in toolWindows:
			self.toolWindowVisibilityChanged.emit( toolWindow, toolWindow.parent() != None )

	def removeToolWindow( self, toolWindow ):
		if not self.toolWindowList.contains(toolWindow):
			qWarning( 'unknown tool window' )
			return
		self.moveToolWindow( toolWindow, ToolWindowManager.NoArea )
		self.toolWindowList.removeOne(toolWindow)

	def setSuggestionSwitchInterval( self, msec ):
		self.dropSuggestionSwitchTimer.setInterval(msec)

	def suggestionSwitchInterval( self ):
		return self.dropSuggestionSwitchTimer.interval()

	def setBorderSensitivity( self, pixels ):
		self.borderSensitivity = pixels

	def setRubberBandLineWidth( self, pixels ):
		self.rubberBandLineWidth = pixels

	def saveState( self ):
		result = {}
		result[ 'toolWindowManagerStateFormat' ] = 1
		mainWrapper = self.findChild( ToolWindowManagerWrapper )
		if not mainWrapper:
			qWarning( 'can not find main wrapper' )
			return {}

		result[ 'mainWrapper' ] = mainWrapper.saveState()
		floatingWindowsData = []
		for wrapper in self.wrappers:
			if not wrapper.isWindow(): continue
			floatingWindowsData.append( wrapper.saveState() )
		result['floatingWindows'] = floatingWindowsData
		return result

	def restoreState( self, data ):
		if not isinstance( data, dict ): return
		if data[ 'toolWindowManagerStateFormat' ] != 1:
			qWarning( 'state format is not recognized' )
			return
		self.moveToolWindows( self.toolWindowList, ToolWindowManager.NoArea )
		mainWrapper = self.findChild( ToolWindowManagerWrapper )
		if not mainWrapper:
			qWarning( 'can not find main wrapper' )

		mainWrapper.restoreState( data['mainWrapper'] )
		for windowData in data['floatingWindows']:
			wrapper = ToolWindowManagerWrapper( self )
			wrapper.restoreState( windowData )
			wrapper.show()

		self.simplifyLayout()
		for toolWindow in self.toolWindowList:
			self.toolWindowVisibilityChanged.emit( toolWindow, toolWindow.parentWidget() != None )

	def createArea( self ):
		area = ToolWindowManagerArea( self, None )
		area.tabCloseRequested.connect( self.tabCloseRequested )
		return area

	def handleNoSuggestions( self ):
		self.rectRubberBand.hide()
		self.lineRubberBand.hide()
		self.lineRubberBand.setParent(self)
		self.rectRubberBand.setParent(self)
		self.suggestions = []
		self.dropCurrentSuggestionIndex = 0
		if self.dropSuggestionSwitchTimer.isActive():
			self.dropSuggestionSwitchTimer.stop()

	def releaseToolWindow( self, toolWindow ):
		previousTabWidget = findClosestParent( toolWindow, ToolWindowManagerArea )
		if not previousTabWidget:
			qWarning( 'cannot find tab widget for tool window' )
			return
		previousTabWidget.removeTab( previousTabWidget.indexOf(toolWindow) )
		toolWindow.hide()
		toolWindow.setParent( None )

	def removeArea( self, area ):
		area.manager = None
		area.deleteLater()

	def removeWrapper( self, wrapper ):
		wrapper.deleteLater()
		self.wrappers.remove( wrapper )

	def simplifyLayout( self ):
		newAreas = []
		currentAreas = self.areas
		for area in currentAreas:
			if area.parentWidget() is None:
				if area.count() == 0:
					if area == self.lastUsedArea: self.lastUsedArea = None
					self.removeArea( area )
				continue

			splitter = cast( area.parentWidget(), QSplitter )
			validSplitter   = None # least top level splitter that should remain
			invalidSplitter = None #most top level splitter that should be deleted
			while( splitter ):
				if splitter.count() > 1:
					validSplitter = splitter
					break
				else:
					invalidSplitter = splitter
					splitter = cast( splitter.parentWidget(), QSplitter )
			if not validSplitter:
				wrapper = findClosestParent( area, ToolWindowManagerWrapper )
				if not wrapper:
					qWarning( 'can not find wrapper' )
					print((findClosestParent( area, ToolWindowManagerWrapper )))
					print((type( area.parentWidget() ) == ToolWindowManagerWrapper))
					return
				if area.count() == 0 and wrapper.isWindow():
					wrapper.hide()
					wrapper.setParent( None )
					# can not deleteLater immediately (strange MacOS bug)
					self.removeWrapper( wrapper )
					
				elif area.parent() != wrapper:
					wrapper.layout().addWidget( area )

			else:
				if area.count() > 0:
					if validSplitter and area.parent() != validSplitter:
						index = validSplitter.indexOf( invalidSplitter )
						validSplitter.insertWidget( index, area )

			if not invalidSplitter is None:
				invalidSplitter.hide()
				invalidSplitter.setParent( None )
				invalidSplitter.deleteLater()

			if area.count() == 0:
				area.hide()
				area.setParent( None )
				if area == self.lastUsedArea: self.lastUsedArea = None
				self.removeArea( area )
				continue

			newAreas.append( area )
		#keep
		self.areas = newAreas

	def dragInProgress( self ):
		return len( self.draggedToolWindows ) > 0

	def startDrag( self, toolWindows ):
		if self.dragInProgress():
			qWarning( 'ToolWindowManager::execDrag: drag is already in progress' )
			return
		if not toolWindows: return
		self.draggedToolWindows = toolWindows
		self.dragIndicator.setPixmap( self.generateDragPixmap( toolWindows ) )
		self.updateDragPosition()
		self.dragIndicator.show()

	def saveSplitterState( self, splitter ):
		result = {}
		result['state'] = splitter.saveState()
		result['type'] = 'splitter'
		
		items = []
		for i in range( splitter.count() ):
			item = splitter.widget(i)
			area = cast( item, ToolWindowManagerArea )
			if area:
				items.append( area.saveState() )
			else:
				childSplitter = cast( item, QSplitter )
				if childSplitter:
					items.append( self. saveSplitterState( childSplitter ) )
				else:
					qWarning( 'unknown splitter item' )
		result['items'] = items
		return result

	def restoreSplitterState( self, data ):
		if len( data[ 'items' ] )< 2:
			qWarning( 'invalid splitter encountered' )

		splitter = self.createSplitter()

		for itemData in data[ 'items' ]:
			itemType = itemData['type']
			if itemType == 'splitter':
				splitter.addWidget( self.restoreSplitterState( itemData ) )
			elif itemType == 'area':
				area = self.createArea()
				area.restoreState( itemData )
				splitter.addWidget( area )
			else:
				qWarning( 'unknown item type' )
		splitter.restoreState( data['state'] )
		return splitter

	def generateDragPixmap( self, toolWindows ):
		widget = QtWidgets.QTabBar()
		widget.setDocumentMode(True)
		for toolWindow in toolWindows:
			widget.addTab(toolWindow.windowIcon(), toolWindow.windowTitle())
		if QT_VERSION >= 0x050000: # Qt5
			return widget.grab()
		else: #Qt4
			return QtGui.QPixmap.grabWidget( widget )
		#endif

	def showNextDropSuggestion( self ):
		if len( self.suggestions ) == 0:
			qWarning( 'showNextDropSuggestion called but no suggestions' )
			return

		self.dropCurrentSuggestionIndex += 1
		if self.dropCurrentSuggestionIndex >= len( self.suggestions ):
			self.dropCurrentSuggestionIndex = 0
		
		suggestion = self.suggestions[ self.dropCurrentSuggestionIndex ]
		if suggestion.type in ( ToolWindowManager.AddTo , ToolWindowManager.EmptySpace ):
			if suggestion.type == ToolWindowManager.EmptySpace:
				widget = self.findChild( ToolWindowManagerWrapper )
			else:
				widget = suggestion.widget
			
			if widget.window() == self.window():
				placeHolderParent = self
			else:
				placeHolderParent = widget.window()

			placeHolderGeometry = widget.rect()
			placeHolderGeometry.moveTopLeft(
				widget.mapTo( placeHolderParent, placeHolderGeometry.topLeft() )
			)
			self.rectRubberBand.setGeometry( placeHolderGeometry )
			self.rectRubberBand.setParent( placeHolderParent )
			self.rectRubberBand.show()
			self.lineRubberBand.hide()

		elif suggestion.type in (
			ToolWindowManager.LeftOf , ToolWindowManager.RightOf,
			ToolWindowManager.TopOf , ToolWindowManager.BottomOf ):
			if suggestion.widget.window() == self.window():
				placeHolderParent = self
			else:
				placeHolderParent = suggestion.widget.window()

			placeHolderGeometry = self.sidePlaceHolderRect( suggestion.widget, suggestion.type )
			placeHolderGeometry.moveTopLeft(
				suggestion.widget.mapTo( placeHolderParent, placeHolderGeometry.topLeft() )
			)
			self.lineRubberBand.setGeometry(placeHolderGeometry)
			self.lineRubberBand.setParent(placeHolderParent)
			self.lineRubberBand.show()
			self.rectRubberBand.hide()

		else:
			qWarning( 'unsupported suggestion type' )

	def findSuggestions( self, wrapper ):
		self.suggestions = []
		self.dropCurrentSuggestionIndex = -1
		globalPos  = QCursor.pos()
		candidates = []
		for splitter in wrapper.findChildren( QSplitter ):
			candidates.append( splitter )

		for area in self.areas:
			if area.window() == wrapper.window():
				candidates.append( area )

		for widget in candidates:
			splitter = cast( widget, QSplitter )
			area = cast( widget, ToolWindowManagerArea )
			if not ( splitter or area ):
				qWarning( 'unexpected widget type' )				
				continue

			parentSplitter = cast( widget.parentWidget(), QSplitter )
			lastInSplitter = parentSplitter and \
					parentSplitter.indexOf(widget) == parentSplitter.count() - 1

			allowedSides = []
			if not splitter or splitter.orientation() == Qt.Vertical:
				allowedSides.append( ToolWindowManager.LeftOf )

			if not splitter or splitter.orientation() == Qt.Horizontal:
				allowedSides.append( ToolWindowManager.TopOf )

			if not parentSplitter or parentSplitter.orientation() == Qt.Vertical or lastInSplitter:
				if not splitter or splitter.orientation() == Qt.Vertical:
					allowedSides.append( ToolWindowManager.RightOf )

			if not parentSplitter or parentSplitter.orientation() == Qt.Horizontal or lastInSplitter:
				if not splitter or splitter.orientation() == Qt.Horizontal:
					allowedSides.append( ToolWindowManager.BottomOf )
			for side in allowedSides:
				rect = self.sideSensitiveArea( widget, side )
				pos  = widget.mapFromGlobal( globalPos )
				if rect.contains( pos ):
					self.suggestions.append( AreaReference( side, widget ) )
			if area:
				rect = area.rect()
				pos  = area.mapFromGlobal( globalPos )
				if rect.contains( pos ):
					self.suggestions.append( AreaReference( ToolWindowManager.AddTo, area ) )

		#end of for
		if not candidates:
			self.suggestions.append( AreaReference( ToolWindowManager.EmptySpace ) )

		if len( self.suggestions ) == 0:
			self.handleNoSuggestions()
		else:
			self.showNextDropSuggestion()

	def sideSensitiveArea( self, widget, side ):
		widgetRect = widget.rect()
		if side == ToolWindowManager.TopOf:
			return QRect(QPoint(widgetRect.left(), widgetRect.top() - self.borderSensitivity),
									 QSize(widgetRect.width(), self.borderSensitivity * 2))
		elif side == ToolWindowManager.LeftOf:
			return QRect(QPoint(widgetRect.left() - self.borderSensitivity, widgetRect.top()),
									 QSize(self.borderSensitivity * 2, widgetRect.height()))

		elif side == ToolWindowManager.BottomOf:
			return QRect(QPoint(widgetRect.left(), widgetRect.top() + widgetRect.height() - self.borderSensitivity),
									 QSize(widgetRect.width(), self.borderSensitivity * 2))
		elif side == ToolWindowManager.RightOf:
			return QRect(QPoint(widgetRect.left() + widgetRect.width() - self.borderSensitivity, widgetRect.top()),
									 QSize(self.borderSensitivity * 2, widgetRect.height()))
		else:
			qWarning( 'invalid side' )
			return QRect()

	def sidePlaceHolderRect( self, widget, side ):
		widgetRect = widget.rect()
		parentSplitter = cast( widget.parentWidget(), QSplitter )
		if parentSplitter and parentSplitter.indexOf(widget) > 0:
			delta = parentSplitter.handleWidth() / 2 + self.rubberBandLineWidth / 2
			if side == ToolWindowManager.TopOf and parentSplitter.orientation() == Qt.Vertical:
				return QRect(QPoint( widgetRect.left(), widgetRect.top() - delta ),
										 QSize( widgetRect.width(), self.rubberBandLineWidth ) )
			elif side == ToolWindowManager.LeftOf and parentSplitter.orientation() == Qt.Horizontal:
				return QRect(QPoint(widgetRect.left() - delta, widgetRect.top()),
										 QSize(self.rubberBandLineWidth, widgetRect.height()))

		if side == ToolWindowManager.TopOf:
			return QRect(QPoint(widgetRect.left(), widgetRect.top()),
									 QSize(widgetRect.width(), self.rubberBandLineWidth))
		elif side == ToolWindowManager.LeftOf:
			return QRect(QPoint(widgetRect.left(), widgetRect.top()),
									 QSize(self.rubberBandLineWidth, widgetRect.height()))
		elif side == ToolWindowManager.BottomOf:
			return QRect(QPoint(widgetRect.left(), widgetRect.top() + widgetRect.height() - self.rubberBandLineWidth),
									 QSize(widgetRect.width(), self.rubberBandLineWidth))
		elif side == ToolWindowManager.RightOf:
			return QRect(QPoint(widgetRect.left() + widgetRect.width() - self.rubberBandLineWidth, widgetRect.top()),
									 QSize(self.rubberBandLineWidth, widgetRect.height()))
		else:
			qWarning( 'invalid side' )
			return QRect()

	def updateDragPosition( self ):
		if not self.dragInProgress(): return
		if not QApplication.mouseButtons() & Qt.LeftButton :
			self.finishDrag()
			return

		pos = QCursor.pos()
		self.dragIndicator.move( pos + QPoint(1, 1) )
		foundWrapper = False
		window = QApplication.topLevelAt( pos )
		for wrapper in self.wrappers:
			if wrapper.window() == window:
				if wrapper.rect().contains( wrapper.mapFromGlobal(pos) ):
					self.findSuggestions( wrapper )
					if len( self.suggestions ) > 0:
						#starting or restarting timer
						if self.dropSuggestionSwitchTimer.isActive():
							self.dropSuggestionSwitchTimer.stop()
						self.dropSuggestionSwitchTimer.start()
						foundWrapper = True
				break
		if not foundWrapper:
			self.handleNoSuggestions()

	def finishDrag( self ):
		if not self.dragInProgress():
			qWarning( 'unexpected finishDrag' )
			return

		if len( self.suggestions ) == 0:
			self.moveToolWindows( self.draggedToolWindows, ToolWindowManager.NewFloatingArea )
		else:
			if self.dropCurrentSuggestionIndex >= len( self.suggestions ):
				qWarning( 'invalid self.dropCurrentSuggestionIndex' )
				return
			suggestion = self.suggestions[ self.dropCurrentSuggestionIndex ]
			self.handleNoSuggestions()
			self.moveToolWindows( self.draggedToolWindows, suggestion )

		self.dragIndicator.hide()
		self.draggedToolWindows = []

	def tabCloseRequested( self, index ):
		if not isinstance( self.sender(), ToolWindowManagerArea ):
			qWarning( 'sender is not a ToolWindowManagerArea' )
			return
		area = self.sender()
		toolWindow = area.widget( index )
		if not self.hasToolWindow( toolWindow ):
			qWarning( 'unknown tab in tab widget' )
			return
		self.hideToolWindow( toolWindow )

	def createSplitter( self ):
		splitter = QSplitter()
		splitter.setChildrenCollapsible( False )
		return splitter


#TEST
if __name__ == '__main__':
	import sys
	app = QtWidgets.QApplication( sys.argv )
	styleSheetName = 'gii.qss'
	app.setStyleSheet(
			open( '/Users/tommo/prj/gii/data/theme/' + styleSheetName ).read() 
		)

	class Test( QtWidgets.QMainWindow ):
		def __init__(self, *args ):
			super(Test, self).__init__( *args )
			mgr = ToolWindowManager( self )
			self.setCentralWidget( mgr )
			widget = QtWidgets.QOpenGLWidget()
			widget.setWindowTitle( 'hello' )
			widget.setObjectName( 'hello' )
			mgr.addToolWindow( widget, ToolWindowManager.EmptySpace )
			widget = QtWidgets.QPushButton( 'world' )
			widget.setWindowTitle( 'world' )
			widget.setObjectName( 'world' )
			mgr.addToolWindow( widget, ToolWindowManager.NewFloatingArea )
			widget = QtWidgets.QPushButton( 'happy' )
			widget.setWindowTitle( 'happy' )
			widget.setObjectName( 'happy' )
			mgr.addToolWindow( widget, ToolWindowManager.EmptySpace )
			widget = QtWidgets.QPushButton( 'goodness' )
			widget.setWindowTitle( 'goodness' )
			widget.setObjectName( 'goodness' )
			mgr.addToolWindow( widget, ToolWindowManager.LastUsedArea )
			result = mgr.saveState()
			for w in mgr.toolWindows():
				mgr.moveToolWindow( w, ToolWindowManager.NewFloatingArea )
			mgr.restoreState( result )
			area = mgr.areaOf( widget )
			mgr.hideToolWindow( widget )
			area.addToolWindow( widget )

	window = Test()
	window.show()
	window.raise_()
	app.exec_()
