import sys
import math

from qtpy import QtWidgets, QtGui, QtCore, QtOpenGL, uic
from qtpy.QtCore import Qt, QObject, QEvent, Signal
from qtpy.QtCore import QPoint, QRect, QSize
from qtpy.QtCore import QPointF, QRectF, QSizeF
from qtpy.QtWidgets import QMessageBox
from qtpy.QtGui import QColor, QTransform, qRgb
from qtpy.QtWidgets import QStyle, QMessageBox

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

ColorPickerForm,BaseClass = uic.loadUiType( _getModulePath('ColorPicker.ui') )

def requestConfirm(title, msg, level='normal'):
	f = None
	if level == 'warning':
		f = QMessageBox.warning
	elif level == 'critical':
		f = QMessageBox.critical
	else:
		f = QMessageBox.question
	res = f(None, title, msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
	if res == QMessageBox.Yes:    return True
	if res == QMessageBox.Cancel: return None
	if res == QMessageBox.No:     return False

def unpackQColor( c ):
	return ( c.redF(), c.greenF(), c.blueF(), c.alphaF() )

def QColorF( r, g, b, a =1 ):
	return QtGui.QColor( r*255, g*255, b*255, a*255)

def clampOne( v ):
	return min( 1.0, max( 0.0, v ) )

def generateHSVImage( w, h, hue, img = None ):
	if not img:
		img = QtGui.QImage( w, h, QtGui.QImage.Format_RGB32 )
	du = 1.0/w
	dv = 1.0/h
	c = QColor()
	for y in range( 0, h ):
		for x in range( 0, w ):
			s = du * x
			v = 1.0 - dv * y
			c.setHsvF( hue, s, v )
			img.setPixel( x, y, c.rgb() )
	return img

##----------------------------------------------------------------##
_DefaultPaletteProvider = None
class PaletteProvider(object):
	def setDefault( self ):
		global _DefaultPaletteProvider
		_DefaultPaletteProvider = self

	def pullPalettes( self ):
		return []

	def pushPalettes( self, palettes ):
		pass

class SimplePaletteProvider(PaletteProvider):
	def __init__( self ):
		self.palettes = []

	def pullPalettes( self ):
		return self.palettes

	def pushPalettes( self, palettes ):
		self.palettes = palettes[:]

SimplePaletteProvider().setDefault()

##----------------------------------------------------------------##
class ColorBlock( QtWidgets.QToolButton ):
	def __init__(self, parent, color = None, **option ):
		super(ColorBlock, self).__init__( parent )
		self.setColor( color or QtGui.QColor( 1,1,1,1 ) )
		self.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Fixed
			)

		self.title = option.get( 'title', 'Color' )
		self.pen = QtGui.QPen()
		self.brush = QtGui.QBrush()
		self.brush.setStyle( Qt.SolidPattern )
		self.setCursor( Qt.PointingHandCursor )
		

	def sizeHint( self ):
		return QtCore.QSize( 60, 20 )

	def getColor( self ):
		return self.color

	def setColor( self, color ):
		self.color = color
		self.update()

	def paintEvent( self, event ):
		painter = QtGui.QPainter()
		color = self.color
		painter.begin( self )
		margin = 2
		x = margin
		y = margin
		w = self.width() - margin * 2
		h = self.height() - margin * 2
		gridSize = 5
		gridPart = gridSize * 1
		painter.translate( margin, margin )
		painter.setPen( Qt.black )
		painter.setBrush( Qt.white )
		painter.drawRect( 0,0,w,h )
		painter.setPen( Qt.NoPen )
		painter.setBrush( QColor.fromRgbF( 0.5, 0.5, 0.5 ) )
		painter.setClipRect( 0,0,w,h )
		for y in range( int(h/gridSize+1) ):
				for x in range( int(w/gridSize+1) ):
					if (x % 2) == (y % 2):
						painter.drawRect( x * gridSize, y * gridSize, gridSize, gridSize )
		painter.setBrush( color )
		painter.drawRect( 0,0,w,h )
		colorFull = QColor( color )
		colorFull.setAlpha( 255 )
		painter.setBrush( colorFull )
		painter.drawRect( 0,0, w/2, h )
		painter.end()

class ColorItemDelegate( QtWidgets.QStyledItemDelegate ):
	def sizeHint( self, option, index ):
		return QtCore.QSize( 50, 25 )

	def createEditor( *args ):
		return None

	def paint( self, painter, option, index ):
		self.initStyleOption(option,index)

		style = option.widget.style() or QApplication.style()

		#draw icon
		option.text = ""
		style.drawControl( QStyle.CE_ItemViewItem, option, painter,option.widget)

		painter.save()
		item = self.tree.itemFromIndex( index )
		colorData = item.userdata
		color = QColorF( *colorData.get( 'color', (1,1,1,1) ) )
		rect = option.rect
		margin = 2
		rect.adjust( margin,0,-margin,-margin*2 )
		w = rect.width()
		h = rect.height()
		
		gridSize = 5
		gridPart = gridSize * 1
		painter.translate( rect.x(), rect.y() )
		painter.translate( margin, margin )
		painter.setPen( Qt.black )
		painter.setBrush( Qt.white )
		painter.drawRect( 0,0,w,h )
		painter.setPen( Qt.NoPen )
		painter.setBrush( QColor.fromRgbF( 0.5, 0.5, 0.5 ) )
		painter.setClipRect( 0,0,w,h )
		for y in range( int(h/gridSize+1) ):
				for x in range( int(w/gridSize+1) ):
					if (x % 2) == (y % 2):
						painter.drawRect( x * gridSize, y * gridSize, gridSize, gridSize )
		painter.setBrush( color )
		painter.drawRect( 0,0,w,h )
		colorFull = QColor( color )
		colorFull.setAlpha( 255 )
		painter.setBrush( colorFull )
		painter.drawRect( 0,0, w/2, h )
		# painter.fillRect( rect, color )
		# if option.state & QStyle.State_Selected:
		# 	painter.setPen  ( Qt.white )
		# 	painter.setBrush( Qt.NoBrush )
		# 	painter.drawRect( rect )
		painter.restore()

	def paintEvent( self, event ):
		painter = QtGui.QPainter()
		color = self.color
		painter.begin( self )
		margin = 2
		x = margin
		y = margin
		w = self.width() - margin * 2
		h = self.height() - margin * 2
		gridSize = 5
		gridPart = gridSize * 1
		painter.translate( margin, margin )
		painter.setPen( Qt.black )
		painter.setBrush( Qt.white )
		painter.drawRect( 0,0,w,h )
		painter.setPen( Qt.NoPen )
		painter.setBrush( Qt.black )
		painter.setClipRect( 0,0,w,h )
		for y in range( int(h/gridSize+1) ):
				for x in range( int(w/gridSize+1) ):
					if (x % 2) == (y % 2):
						painter.drawRect( x * gridSize, y * gridSize, gridSize, gridSize )
		painter.setBrush( color )
		painter.drawRect( 0,0,w,h )
		colorFull = QColor( color )
		colorFull.setAlpha( 255 )
		painter.setBrush( colorFull )
		painter.drawRect( 0,0, w/2, h )
		painter.end()
		
##----------------------------------------------------------------##
class PaletteList( QtWidgets.QListWidget ):
	def __init__(self, *args ):
		super(PaletteList, self).__init__( *args )
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
		self.setAttribute(Qt.WA_MacShowFocusRect, False)
		self.owner = None
		self.itemSelectionChanged.connect( self.onItemSelectionChanged )
		self.itemChanged          .connect( self.onItemChanged )

	def addPalette( self, pal ):
		name = pal.get( 'name', 'unnamed' )
		item = QtWidgets.QListWidgetItem( name )
		self.addItem( item )
		item.palette = pal
		item.setFlags( Qt.ItemIsEditable|Qt.ItemIsSelectable|Qt.ItemIsEnabled )
		return item

	def onItemChanged( self, item ):
		text = str(item.text())
		item.palette['name'] = text
		self.owner.onPaletteChange()

	def onItemSelectionChanged( self ):
		selectedItems = self.selectedItems()
		if selectedItems:
			item = selectedItems[0]
			palette = item.palette
			self.owner.onPaletteSelected( palette )
		else:
			self.owner.onPaletteSelected( None )


class PaletteItemList( QtWidgets.QTreeWidget ):
	def __init__(self, *args ):
		super(PaletteItemList, self).__init__( *args )
		self.owner = None
		self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
		self.setColumnCount( 2 )
		self.setColumnWidth( 0, 60 )
		self.setColumnWidth( 1, -1 )
		self.setIndentation( 0 )

		self.setAttribute(Qt.WA_MacShowFocusRect, False)
		self.setHeaderHidden( True )
		self.setIconSize( QtCore.QSize( 16, 16 ) )
		self.colorItemDelegate = ColorItemDelegate()
		self.colorItemDelegate.tree = self
		self.setItemDelegateForColumn( 0, self.colorItemDelegate )
		self.dataToItem = {}

		self.itemSelectionChanged .connect( self.onItemSelectionChanged )
		self.itemClicked          .connect( self.onItemClicked )
		self.itemChanged          .connect( self.onItemChanged )

		
	def addColorData( self, data ):
		name = data.get( 'name', None )
		colorTuple = data.get( 'color', (1,1,1,1) )
		( r,g,b,a ) = colorTuple
		color = QColorF( r,g,b,a )
		item = QtWidgets.QTreeWidgetItem()
		self.addTopLevelItem( item )
		item.setText( 1, name )
		item.setFlags( Qt.ItemIsEditable|Qt.ItemIsSelectable|Qt.ItemIsEnabled )
		# self.dataToItem[ data ] = item
		item.userdata = data
		return item

	def refreshItem( self, item ):
		data = item.userdata
		item.setText( 1, data.get( 'name', 'unamed' ) )
		colorTuple = data.get( 'color', (1,1,1,1) )
		( r,g,b,a ) = colorTuple
		self.update()
	
	def setPalette( self, palette ):
		self.palette = palette
		self.rebuild()
	
	def rebuild( self ):
		self.hide()
		self.clear()
		self.dataToItem = {}
		if not self.palette: return
		items = self.palette.get( 'items', [] )
		for data in items:
			self.addColorData( data )
		self.show()

	def onItemSelectionChanged( self ):
		for item in self.selectedItems():
			data = item.userdata
			self.owner.setColor( QColorF( *data.get('color',(1,1,1,1) ) ) )

	def onItemChanged( self, item, col ):
		if col != 1: return
		if not hasattr( item, 'userdata' ) : return
		userdata = item.userdata
		if not userdata: return
		text = item.text( col )
		userdata[ 'name' ] = text
		self.owner.onPaletteChange()

	def onDClicked(self, item, col):
		if col == 0:
			self.owner.applyPaletteSelection()

	def onItemClicked( self, item, col ):
		self.owner.applyPaletteSelection()

#####
class ColorPreviewWidget( QtWidgets.QToolButton ):
	def __init__( self, parent ):
		super( ColorPreviewWidget, self ).__init__( parent )
		self.setFixedSize( parent.width(), parent.height() )
		self.previewColor = Qt.red
		self.originalColor = Qt.black

	def setColor( self, color ):
		self.previewColor = color

	def setOriginalColor( self, color ):
		self.originalColor = color

	def paintEvent( self, event ):
		painter = QtGui.QPainter( self )
		painter.setPen( Qt.NoPen )
		w = self.width()
		h = self.height()
		painter.setBrush( self.originalColor )
		painter.drawRect( 0,   0, w, h/2    )
		cSolid = QColor( self.previewColor )
		cSolid.setAlphaF( 1 )
		#left 1/2 for solid color
		painter.setBrush( cSolid )
		painter.drawRect( 0, h/2, w/2, h/2 + 1 )
		#draw chekerGrid
		x0 = w/2
		y0 = h/2
		w2 = w/2
		h2 = h/2
		painter.setBrush( Qt.white )
		painter.drawRect( x0, y0, w2, h2 )
		painter.setBrush( QColor.fromRgbF( 0.5, 0.5, 0.5 ) )
		for y in range( 4 ):
			for x in range( int(w2/10) ):
				if (x % 2) == (y % 2):
					painter.drawRect( x0 + x * 10, y0 + y * 10, 10, 10 )

		#right 2/3 for color with alpha
		painter.setBrush( self.previewColor )
		painter.drawRect( x0, y0, w2+1, h2 + 1 )

#####
class ColorPlaneWidget( QtWidgets.QWidget ):
	valueXChanged = Signal( float )
	valueYChanged = Signal( float )
	valueZChanged = Signal( float )
	valueChanged = Signal( float, float, float )

	def __init__( self, parent ):
		super( ColorPlaneWidget, self ).__init__( parent )
		self.setFixedSize( parent.width(), parent.height() )
		self.setCursor( Qt.PointingHandCursor )
		self.valueX = 0.0
		self.valueY = 0.0
		self.valueZ = 0.0 #Hue for hsv; 

		self.dragging = False

		self.updateImage()

	def setValue( self, x, y, z ):
		x = clampOne( x )
		y = clampOne( y )
		z = clampOne( z )
		self.valueX = x
		self.valueY = y
		if z != self.valueZ:
			self.valueZ = z
			self.updateImage()
		self.update()
		self.valueChanged.emit( self.valueX, self.valueY, self.valueZ )

	def getValue( self ):
		return ( self.valueX, self.valueY, self.valueZ )

	def setValueZ( self, value ):
		if self.valueZ != value:
			self.setValue( self.valueX, self.valueY, value )

	def setValueXY( self, x, y ):
		return self.setValue( x, y, self.valueZ )

	def getValueXY( self ):
		return ( self.valueX, self.valueY )

	def getValueZ( self ):
		return self.valueZ

	def updateImage( self ):
		self.colorImage = generateHSVImage( 20, 20, self.valueZ )
		self.colorImage = self.colorImage.scaled( 100, 100, Qt.IgnoreAspectRatio, Qt.SmoothTransformation )

	def paintEvent(self, event):
		painter = QtGui.QPainter(self)
		# painter.setRenderHint( QtGui.QPainter.Antialiasing, True )
		painter.setRenderHint( QtGui.QPainter.SmoothPixmapTransform, True )
		painter.drawImage( event.rect(), self.colorImage )
		x = self.valueX * self.width()
		y = self.valueY * self.height()
		painter.setBrush( Qt.NoBrush )
		painter.setPen( Qt.black )
		painter.drawRect( x-4, y-4, 8, 8 )
		painter.setPen( Qt.white )
		painter.drawRect( x-3, y-3, 6, 6 )

	def mousePressEvent( self, event ):
		if event.button() == Qt.LeftButton:
			self.grabMouse()
			vx = float(event.x())/float(self.width())
			vy = float(event.y())/float(self.height())
			self.setValueXY( vx, vy )
			self.dragging = True

	def mouseReleaseEvent( self, event ):
		if event.button() == Qt.LeftButton:
			self.releaseMouse()
			self.dragging = False

	def mouseMoveEvent( self, event ):
		if not self.dragging: return
		vx = float(event.x())/float(self.width())
		vy = float(event.y())/float(self.height())
		self.setValueXY( vx, vy )

#####
class AlphaSliderWidget( QtWidgets.QWidget ):
	valueChanged = Signal( float )

	def __init__( self, parent ):
		super( AlphaSliderWidget, self ).__init__( parent )
		self.setFixedSize( parent.width(), parent.height() )
		self.setCursor( Qt.PointingHandCursor )
		self.value = 0
		size = 100
		self.colorImage = QtGui.QImage( size, 1, QtGui.QImage.Format_RGB32 )
		c = QColor()
		for x in range( 0, size ):
			k = x/float(size)
			c.setHsvF( 1.0, 0.0, k )
			self.colorImage.setPixel( x, 0, c.rgb() )

	def setValue( self, value ):
		value = clampOne( value )
		if value == self.value: return
		self.value = value
		self.valueChanged.emit( value )
		self.update()

	def paintEvent(self, event):
		painter = QtGui.QPainter(self)
		painter.setRenderHint( QtGui.QPainter.SmoothPixmapTransform, True )
		painter.drawImage( event.rect(), self.colorImage )
		#draw cursor
		h = self.height()
		x = self.value * self.width()
		painter.setBrush( Qt.NoBrush )
		painter.setPen( Qt.black )
		painter.drawRect( x-3, 0, 6, h-1 )
		painter.setPen( Qt.white )
		painter.drawRect( x-2, 0, 4, h-1 )

	def mousePressEvent( self, event ):
		if event.button() == Qt.LeftButton:
			self.grabMouse()
			x = float(event.x())
			k = x/float(self.width())
			self.setValue( k )

	def mouseReleaseEvent( self, event ):
		if event.button() == Qt.LeftButton:
			self.releaseMouse()

	def mouseMoveEvent( self, event ):
		if self.mouseGrabber() != self: return
		x = float(event.x())
		k = x/float(self.width())
		self.setValue( k )


#####
class HueSliderWidget( QtWidgets.QWidget ):
	valueChanged = Signal( float )

	def __init__( self, parent ):
		super( HueSliderWidget, self ).__init__( parent )
		self.setFixedSize( parent.width(), parent.height() )
		self.value = 0
		size = 100
		self.colorImage = QtGui.QImage( 1, size, QtGui.QImage.Format_RGB32 )
		c = QColor()
		for y in range( 0, size ):
			k = y/float(size)
			c.setHsvF( k, 1.0, 1.0 )
			self.colorImage.setPixel( 0, y, c.rgb() )
		self.setCursor( Qt.PointingHandCursor )

	def setValue( self, value ):
		value = clampOne( value )
		if value == self.value: return
		self.value = value
		self.valueChanged.emit( value )
		self.update()

	def paintEvent(self, event):
		painter = QtGui.QPainter(self)
		painter.setRenderHint( QtGui.QPainter.SmoothPixmapTransform, True )
		painter.drawImage( event.rect(), self.colorImage )
		#draw cursor
		w = self.width()
		y = self.value * self.height()
		painter.setBrush( Qt.NoBrush )
		painter.setPen( Qt.black )
		painter.drawRect( 0, y-3, w -1, 6 )
		painter.setPen( Qt.white )
		painter.drawRect( 0, y-2, w -1, 4 )

	def mousePressEvent( self, event ):
		if event.button() == Qt.LeftButton:
			self.grabMouse()
			y = float(event.y())
			k = y/float(self.height())
			self.setValue( k )

	def mouseReleaseEvent( self, event ):
		if event.button() == Qt.LeftButton:
			self.releaseMouse()

	def mouseMoveEvent( self, event ):
		if self.mouseGrabber() != self: return
		y = float(event.y())
		k = y/float(self.height())
		self.setValue( k )


class ScreenColorPicker( QtWidgets.QWidget ):
	def __init__( self, parent = None ):
		super(ScreenColorPicker, self).__init__( parent )
		self.setFixedSize( 5, 5 )
		self.setMouseTracking( True )
		self.setFocusPolicy( Qt.StrongFocus )
		self.setWindowFlags( Qt.Popup )
		
		self.setWindowModality( Qt.ApplicationModal )

		self.timer = QtCore.QTimer( self )
		self.timer.setInterval( 10 )
		self.timer.timeout.connect( self.onTimer )
		self.timer.start()
		self.setCursor( Qt.CrossCursor)

		self.pixmap = QtGui.QPixmap.grabWindow( QtWidgets.QApplication.desktop().winId() )
		self.image  = self.pixmap.toImage()
		self.owner = False

	def setOwner( self, owner ):
		self.owner = owner

	def onTimer( self ):
		pos = QtGui.QCursor.pos()
		self.move( pos.x()-2, pos.y()-2 )

	def mouseMoveEvent( self, event ):
		pos = event.globalPos()
		rgb = self.image.pixel( pos )
		color = QColor.fromRgb( rgb )
		if self.owner:
			self.owner.setColor( color )

	def mousePressEvent( self, event ):
		self.close()
		self.deleteLater()

	def paintEvent( self, event ):
		painter = QtGui.QPainter( self )
		color = QColor.fromRgbF( 0, 0, 0 )
		# color.setAlphaF( 0.5 )
		painter.setPen( Qt.NoPen )
		painter.setBrush( color )
		painter.drawRect( event.rect() )
		

#####
class ColorPickerWidget( QtWidgets.QWidget ):
	def __init__( self, *args ):
		super(ColorPickerWidget, self).__init__( *args )
		self.updating = False
		self.updatingAlpha = False
		self.ui = ColorPickerForm()
		self.ui.setupUi( self )

		# self.setWindowFlags( Qt.Popup )

		self.preview     = ColorPreviewWidget( self.ui.containerPreview )
		self.hueSlider   = HueSliderWidget( self.ui.containerHueSlider )
		self.alphaSlider = AlphaSliderWidget( self.ui.containerAlphaSlider )

		self.colorPlane  = ColorPlaneWidget( self.ui.containerColorPlane )

		self.hueSlider   .valueChanged .connect( self.onHueChanged )
		self.alphaSlider .valueChanged .connect( self.onAlphaSliderChanged )
		self.colorPlane  .valueChanged .connect( self.onColorBaseChanged )

		self.preview.clicked.connect( self.onColorPreviewClicked )

		self.ui.buttonOK      .clicked .connect( self.onButtonOK )
		self.ui.buttonCancel  .clicked .connect( self.onButtonCancel )
		self.ui.buttonCopyHEX .clicked .connect( self.onButtonCopyHEX )
		self.ui.buttonCopyRGB .clicked .connect( self.onButtonCopyRGBA )
		self.ui.buttonCopyHSV .clicked .connect( self.onButtonCopyHSV )

		self.ui.buttonScreenPick.clicked.connect( self.onButtonScreenPick )

		self.ui.numR.valueChanged.connect( self.onTextRGBChanged )
		self.ui.numG.valueChanged.connect( self.onTextRGBChanged )
		self.ui.numB.valueChanged.connect( self.onTextRGBChanged )

		self.ui.numH.valueChanged.connect( self.onTextHSVChanged )
		self.ui.numS.valueChanged.connect( self.onTextHSVChanged )
		self.ui.numV.valueChanged.connect( self.onTextHSVChanged )

		self.ui.textHex.textChanged.connect( self.onTextHexChanged )
		self.ui.textHex.returnPressed.connect( self.onTextHexEntered )
		# self.ui.textHex.installEventFilter( self )

		self.ui.numA.valueChanged.connect( self.onAlphaSliderChanged )

		self.originalColor = QColor.fromRgbF( 0.0, 0.0, 0.0 )
		self.currentColor  = QColor.fromRgbF( 1.0, 1.0, 0.0 )

		self.preview.setColor( self.currentColor )
		self.preview.setOriginalColor( self.originalColor )

		self.updateAlphaWidgets()
		self.updateTextWidgets()
		self.updateColorPlane()

		self.paletteToolbar = toolbar = QtWidgets.QToolBar( self.ui.containerToolbar )
		toolbar.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Minimum)
		toolbar.setIconSize( QtCore.QSize( 16, 16 ) )
		toolbar.setToolButtonStyle( Qt.ToolButtonTextOnly )

		layout = QtWidgets.QHBoxLayout( self.ui.containerToolbar )
		layout.addWidget( toolbar )
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		self.actionAddPalette    = toolbar.addAction( '+ Pal' )
		self.actionRemovePalette = toolbar.addAction( '- Pal' )
		toolbar.addSeparator()
		self.actionUpdateColor  = toolbar.addAction( 'Update' )
		self.actionMatchColor  = toolbar.addAction( 'Match' )
		toolbar.addSeparator()
		self.actionAddColor     = toolbar.addAction( '+' )
		self.actionRemoveColor  = toolbar.addAction( '-' )
		# self.screenPicker.grabMouse()

		self.listPalettes = PaletteList( self.ui.containerCategory )
		self.listPaletteItems    = PaletteItemList( self.ui.containerItems )
		self.listPalettes.owner = self
		self.listPaletteItems.owner = self
		
		# self.listPaletteItems.addColorData( {} )
		#palette data
		self.palettes = []
		self.currentPalette = None

		self.actionAddPalette.triggered.connect( self.onAddPalette )
		self.actionRemovePalette.triggered.connect( self.onRemovePalette )
		self.actionAddColor.triggered.connect( self.onAddColor )
		self.actionRemoveColor.triggered.connect( self.onRemoveColor )
		self.actionUpdateColor.triggered.connect( self.onUpdateColor )
		self.actionMatchColor.triggered.connect( self.onMatchColor )
		self.paletteProvider = None
		self.refreshPalettes()

	def setPaletteProvider( self, provider ):
		self.paletteProvider = provider
		self.refreshPalettes()

	def getPaletteProvider( self ):
		provider = self.paletteProvider
		if not provider: return _DefaultPaletteProvider
		return provider

	def refreshPalettes( self ):
		provider = self.getPaletteProvider()
		self.clearPalettes()
		if not provider: return
		paletteList = provider.pullPalettes()

		self.palettes = paletteList[ : ]
		self.rebuildPaletteList()
		count = self.listPalettes.count()
		if count > 0:
			item = self.listPalettes.item( 0 )
			self.listPalettes.setCurrentItem( item )

	def eventFilter( self, obj, event ):
		if obj == self.ui.textHex:
			if event.type() == QEvent.MouseButtonPress:
				if event.button() == Qt.LeftButton:
					if obj.hasFocus(): return False
					obj.selectAll()
					obj.setFocus( Qt.TabFocusReason )
				return True
		return False

	def setColor( self, color ):
		self.currentColor = color
		self.updateTextWidgets()
		self.updateColorPlane()
		self.updateAlphaWidgets()
		self.onColorChange( color )

	def setOriginalColor( self, color ):
		self.originalColor = QColor( color )
		self.preview.setOriginalColor( self.originalColor )

	def setAlpha( self, alpha ):
		self.currentColor.setAlphaF( alpha )
		self.updateAlphaWidgets()
		self.onColorChange( self.currentColor )

	def updateAlphaWidgets( self ):
		if self.updatingAlpha: return
		self.updatingAlpha = True
		alpha = self.currentColor.alphaF()
		self.ui.numA.setValue( alpha )
		self.alphaSlider.setValue( alpha )
		self.preview.update()
		self.updatingAlpha = False

	def updateColorPlane( self ):
		if self.updating: return
		self.updating = True
		color = self.currentColor
		s = color.saturationF()
		v = color.valueF()
		h = color.hueF()
		self.colorPlane.setValue( s, 1.0 - v, h )
		self.hueSlider.setValue( h )
		self.updating = False

	def updateTextWidgets( self ):
		if self.updating: return
		self.updating = True

		color = self.currentColor

		self.preview.setColor( color )
		self.preview.update()
		#update fields
		if not self.ui.numR.hasFocus():
			self.ui.numR.setValue( color.redF() )
		if not self.ui.numG.hasFocus():
			self.ui.numG.setValue( color.greenF() )
		if not self.ui.numB.hasFocus():
			self.ui.numB.setValue( color.blueF() )

		if not self.ui.numH.hasFocus():
			self.ui.numH.setValue( color.hueF() * 360 )
		if not self.ui.numS.hasFocus():
			self.ui.numS.setValue( color.saturationF() )
		if not self.ui.numV.hasFocus():
			self.ui.numV.setValue( color.valueF() )

		if not self.ui.textHex.hasFocus():
			self.ui.textHex.setText( color.name() )

		self.updating = False

	def onButtonOK( self ):
		pass

	def onButtonCancel( self ):
		pass

	def onColorPreviewClicked( self ):
		self.setColor( self.originalColor )

	def onColorChange( self, color ):
		pass

	def onButtonCopyHEX( self ):
		clip = QtWidgets.QApplication.clipboard()
		clip.setText( self.ui.textHex.text() )

	def onButtonCopyRGBA( self ):
		color = self.currentColor
		output = '%.1f, %.1f, %.1f, %.1f'%( color.redF(), color.greenF(), color.blueF(), color.alphaF() )
		QtWidgets.QApplication.clipboard().setText( output )

	def onButtonCopyHSV( self ):
		color = self.currentColor
		h = float( self.ui.numH.value() ) / 360.0
		s = self.ui.numS.value()
		v = self.ui.numV.value()
		output = '%.1f, %.1f, %.1f'%( h, s, v )
		QtWidgets.QApplication.clipboard().setText( output )

	def onButtonScreenPick( self ):
		self.screenPicker = ScreenColorPicker( None )
		self.screenPicker.setOwner( self )
		self.screenPicker.show()
		self.screenPicker.raise_()

	def onHueChanged( self, value ):
		if self.updating: return
		self.colorPlane.setValueZ( value )

	def onAlphaSliderChanged( self, value ):
		self.setAlpha( value )

	def onColorBaseChanged( self, x,y,z ):
		if self.updating: return
		hue, s, v = z, x, 1.0 - y
		color = QColor.fromHsvF( hue, s, v )
		color.setAlphaF( self.currentColor.alphaF() )
		self.setColor( color )

	def onTextRGBChanged( self, value ):
		if self.updating: return
		r = self.ui.numR.value()
		g = self.ui.numG.value()
		b = self.ui.numB.value()
		color = QColor.fromRgbF( r,g,b )
		color.setAlphaF( self.currentColor.alphaF() )
		self.setColor( color )
		self.updateColorPlane()

	def onTextHSVChanged( self, value ):
		if self.updating: return
		h = float( self.ui.numH.value() ) / 360.0
		s = self.ui.numS.value()
		v = self.ui.numV.value()
		color = QColor.fromHsvF( h, s, v )
		color.setAlphaF( self.currentColor.alphaF() )
		self.setColor( color )
		self.updateColorPlane()

	def onTextHexChanged( self, value ):
		if self.updating: return
		hexText = value
		color = QColor( value )
		color.setAlphaF( self.currentColor.alphaF() )
		self.setColor( color )
		self.updateColorPlane()

	def onTextHexEntered( self ):
		self.onButtonOK()

	#palette
	def clearPalettes( self ):
		self.palettes = []
		self.rebuildPaletteList()

	def rebuildPaletteList( self ):
		self.listPalettes.clear()
		for pal in self.palettes:
			self.listPalettes.addPalette( pal )

	def rebuildPaletteItems( self ):
		self.listPaletteItems.clear()
		if not self.currentPalette: return
		self.listPaletteItems.setPalette( self.currentPalette )

	def onPaletteSelected( self, palette ):
		self.currentPalette = palette
		self.rebuildPaletteItems()

	def applyPaletteSelection( self ):
		for item in self.listPaletteItems.selectedItems():
			colorData = item.userdata
			color = QColorF( *colorData.get( 'color', (1,1,1,1) ) ) 
			self.setColor( color )

	def onAddPalette( self ):
		newPalette = { 'name':'unnamed', 'items':[] }
		self.palettes.append( newPalette )
		item = self.listPalettes.addPalette( newPalette )
		self.listPalettes.setCurrentItem( item )
		self.listPalettes.editItem( item )

	def onRemovePalette( self ):
		if QMessageBox.question( 
			self, 'Confirm', 'Remove Palette?', 
			QMessageBox.Yes | QMessageBox.No
			) != QMessageBox.Yes:
			return
		for item in self.listPalettes.selectedItems():
			self.palettes.remove( item.palette )
		self.onPaletteChange()
		self.rebuildPaletteList()

	def onAddColor( self ):
		if not self.currentPalette: return
		c = self.currentColor
		data = { 
			'name' : self.ui.textHex.text(), 
			'color': ( c.redF(), c.greenF(), c.blueF(), c.alphaF() )
		}
		self.currentPalette['items'].append( data )
		item = self.listPaletteItems.addColorData( data )
		self.listPaletteItems.setCurrentItem( item )
		self.onPaletteChange()

	def onRemoveColor( self ):
		if not self.currentPalette: return
		colorItems = self.currentPalette['items']
		for item in self.listPaletteItems.selectedItems():
			colorItems.remove( item.userdata )
		self.listPaletteItems.rebuild()
		self.onPaletteChange()

	def onUpdateColor( self ):
		c = self.currentColor
		for item in self.listPaletteItems.selectedItems():
			item.userdata['color'] = ( c.redF(), c.greenF(), c.blueF(), c.alphaF() )
			self.listPaletteItems.refreshItem( item )
		self.onPaletteChange()

	def onMatchColor( self ):
		c = self.currentColor
		d = 100000000
		found = None
		root = self.listPaletteItems.invisibleRootItem()
		r,g,b,a = c.redF(), c.greenF(), c.blueF(), c.alphaF()
		count = root.childCount()
		for i in range( count ):
			item = root.child( i )
			r1,g1,b1,a1 = item.userdata['color']
			dr = r - r1
			dg = g - g1
			db = b - b1
			da = a - a1
			d2 = dr*dr + dg*dg + db*db + da*da
			if d2 < d:
				found = item
				d = d2
		if found:
			self.listPaletteItems.setCurrentItem( found )
		self.applyPaletteSelection()
	
	def onPaletteChange( self ):
		provider = self.getPaletteProvider()
		if not provider: return
		provider.pushPalettes( self.palettes )

######TEST
if __name__ == '__main__':
	import sys
	app = QtWidgets.QApplication( sys.argv )
	styleSheetName = 'gii.qss'
	app.setStyleSheet(
			open( '/Users/tommo/prj/gii/data/theme/' + styleSheetName ).read() 
		)
	provider = SimplePaletteProvider()
	provider.pushPalettes([
		{	'name':'test',
			'items':[
				{'name':'black', 'color':(0,0,0,1) },
				{'name':'red', 'color':(1,0,0,1) },
				{'name':'black', 'color':(0,0,0,1) },
				{'name':'red', 'color':(1,0,0,1) },{'name':'black', 'color':(0,0,0,1) },
				{'name':'red', 'color':(1,0,0,1) },{'name':'black', 'color':(0,0,0,1) },
				{'name':'red', 'color':(1,0,0,1) },{'name':'black', 'color':(0,0,0,1) },
				{'name':'red', 'color':(1,0,0,1) },
			]
		},
		{	'name':'test2',
			'items':[
				{'name':'black', 'color':(0,0,0,1) },
				{'name':'red', 'color':(1,0,0,1) },
			]
		},
		])
	widget = ColorPickerWidget()
	widget.setPaletteProvider( provider )
	widget.show()
	widget.raise_()

	app.exec_()

