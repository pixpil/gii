import logging
from gii.core.tmpfile import TempDir

from qtpy import QtWidgets, QtGui, QtCore, QtGui
from qtpy.QtCore import Qt, QPoint
from qtpy.QtWidgets import QMessageBox
from qtpy.QtGui import QColor, QTransform

def unpackQColor( c ):
	return c.redF(), c.greenF(), c.blueF(), c.alphaF()

def QColorF( r, g, b, a =1 ):
	return QtGui.QColor( r*255, g*255, b*255, a*255)

def addWidgetWithLayout(child, parent = None, **option):
	#add a widget to parent along with a new layout
	direction = option.get('direction','vertical')
	if not parent:
		parent = child.parent()
	layout    = parent.layout()
	if layout == None:
		if   direction == 'vertical':
			layout = QtWidgets.QVBoxLayout()
		elif direction == 'horizontoal':
			layout = QtWidgets.QHBoxLayout()
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		parent.setLayout( layout )
		
	layout.addWidget( child )
	return child


def setClipboardText( text ):
	QtWidgets.QApplication.clipboard().setText( text )


def getClipboardText( default = None ):
	t = QtWidgets.QApplication.clipboard().text()
	if not t: return default
	return t


def restrainWidgetToScreen( widget ):
		screenRect = QtWidgets.QApplication.desktop().availableGeometry(widget.mapToGlobal( QPoint(0,0) ));
		widgetRect = widget.frameGeometry()
		pos = widget.pos()
		
		if widgetRect.left() < screenRect.left() :
			pos.setX( pos.x() + screenRect.left() - widgetRect.left() )
		elif widgetRect.right() > screenRect.right():
			pos.setX( pos.x() + screenRect.right() - widgetRect.right() )

		if widgetRect.top() < screenRect.top():
			pos.setY( pos.y() + screenRect.top() - widgetRect.top() )			
		elif widgetRect.bottom() > screenRect.bottom():
			pos.setY( pos.y() + screenRect.bottom() - widgetRect.bottom() )

		widget.move( pos )

def repolishWidget( widget ):
	style = widget.style()
	style.unpolish( widget )
	style.polish( widget )

def makeBrush( **option ):
	brush = QtGui.QBrush()
	brush.setStyle( option.get( 'style', Qt.SolidPattern ) )
	color = QColor( option.get( 'color', '#ffffff' ) )
	color.setAlphaF( option.get( 'alpha', 1 ) )
	brush.setColor( color )
	return brush

def makePen( **option ):
	pen = QtGui.QPen()
	pen.setStyle( option.get( 'style', Qt.SolidLine ) )
	color = QColor( option.get( 'color', '#ffffff' ) )
	color.setAlphaF( option.get( 'alpha', 1 ) )
	pen.setColor( color )
	pen.setWidth( option.get( 'width', .0 ) )
	return pen

def makeFont( **option ):
	font=QtGui.QFont()
	font.setPointSize( option.get( 'size', 11 ) )
	font.setBold( option.get( 'bold', False ) )
	font.setItalic( option.get( 'italic', False ) )
	font.setUnderline( option.get( 'underline', False ) )
	family = option.get( 'family', None )
	if family:
		font.setFamily( family )
	return font
