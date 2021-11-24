from gii.core import *
from gii.core.model import *

from gii.qt.controls.ColorPickerWidget import ColorPickerWidget
from gii.qt.controls.SimpleTitleBar import SimpleTitleBar
from gii.qt.helpers    import addWidgetWithLayout, restrainWidgetToScreen
from gii.qt.IconCache  import getIcon

from qtpy import QtWidgets, QtGui, QtCore, uic
from qtpy.QtCore import Qt
from qtpy.QtCore import QEventLoop, QEvent, QObject, QPoint
from qtpy.QtGui import QColor, QTransform, qRgb
from qtpy.QtWidgets import QStyle

##----------------------------------------------------------------##
class WindowAutoHideEventFilter(QObject):
	def eventFilter(self, obj, event):
		e = event.type()		
		if e == QEvent.KeyPress and event.key() == Qt.Key_Escape:
			obj.cancelled = True
			obj.hide()
		elif e == QEvent.WindowDeactivate:
			obj.hide()

		return QObject.eventFilter( self, obj, event )


class ColorPickerDialog( ColorPickerWidget ):
	def __init__( self, *args ):
		self.onCancel  = None
		self.onChange  = None
		self.onChanged = None
		self.cancelled = False
		self.prevActivatedWindow = None
		self.titleBar  = None

		super( ColorPickerDialog, self ).__init__( *args )
		self.setWindowFlags( Qt.Popup )
		self.titleBar = SimpleTitleBar( self )
		self.layout().insertWidget( 0, self.titleBar )
		self.installEventFilter( WindowAutoHideEventFilter( self ) )
		self.setWindowTitle( 'Colors' )
	
	def setWindowTitle( self, text ):
		if self.titleBar:
			self.titleBar.setTitle( text )
		super( ColorPickerDialog, self ).setWindowTitle( text )

	def request( self, **option ):
		self.prevActivatedWindow = QtWidgets.QApplication.activeWindow()
		self.onCancel  = None
		self.onChange  = None
		self.onChanged = None
		original = option.get( 'original_color', None )
		if original:
			self.setColor( QColor( original ) )
			self.setOriginalColor( original )

		self.onCancel  = option.get( 'on_cancel',  None )
		self.onChange  = option.get( 'on_change',  None )
		self.onChanged = option.get( 'on_changed', None )

		pos       = option.get( 'pos', QtGui.QCursor.pos() )
		self.move( pos + QPoint( -50, 0 ) )
		restrainWidgetToScreen( self )
		self.ui.buttonOK.setFocus()
		self.show()
		self.raise_()
		self.cancelled = False

	def onButtonOK( self ):
		if self.onChanged:
			self.onChanged( self.currentColor )
		self.hide()

	def onButtonCancel( self ):
		self.cancelled = True
		self.hide()

	def onColorChange( self, color ):
		if self.onChange:
			self.onChange( color )

	def hideEvent( self, ev ):
		if self.cancelled and self.onCancel:
			self.onCancel()
		if self.prevActivatedWindow:
			self.prevActivatedWindow.raise_()
			self.prevActivatedWindow = None
		self.onCancel  = None
		self.onChange  = None
		self.onChanged = None


##----------------------------------------------------------------##
_colorPickerDialog = None
def requestColorDialog( title = None, **option ):
	global _colorPickerDialog
	if not _colorPickerDialog:
		_colorPickerDialog = ColorPickerDialog( None )
	if title:
		_colorPickerDialog.setWindowTitle( title or 'Color Picker' )
	_colorPickerDialog.request( **option )
	return _colorPickerDialog
