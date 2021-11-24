from gii.core                 import *

##----------------------------------------------------------------#
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


##----------------------------------------------------------------##
from mock  import MOCKEditCanvas
from gii.qt.helpers           import addWidgetWithLayout

from qtpy import uic
from qtpy import QtWidgets, QtGui

from gii.AssetEditor import AssetPreviewer
from qtpy import QtWidgets, QtGui, QtCore

##----------------------------------------------------------------##
class ImagePreviewer( AssetPreviewer ):
	def createWidget(self, container):
		self.image = None
		self.scale = 1.0
		self.state = 'fit'

		self.container = uic.loadUi( _getModulePath( 'ImagePreview.ui' ) )			
		self.container.scrollArea.setStyleSheet('''
			background-color: rgb( 30, 30, 30 );
			'''
		)
		self.container.labelImage.setBackgroundRole( QtGui.QPalette.Base )
		self.container.labelImage.setSizePolicy( QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored )
		self.container.labelImage.setScaledContents( True )
		self.container.scrollArea.resizeEvent = self.onContainerResize			

		self.container.buttonFit.clicked.connect( self.fitSize )
		self.container.buttonActual.clicked.connect( self.actualSize )


		return self.container

	def accept(self, assetNode):
		return assetNode.getType() in ( 'texture' )

	def onStart(self, assetNode):
		filepath = assetNode.getObjectFile( 'tex' )
		image = QtGui.QImage( filepath )
		if image.isNull():
			self.container.labelImage.hide()
			return
		self.container.labelImage.show()
		self.container.labelImage.setPixmap( QtGui.QPixmap.fromImage(image) )
		self.image = image
		
		self.fitSize()

	def onStop(self):
		pass

	def fitSize( self ):
		if not self.image: return

		areaSize = self.container.scrollArea.size()
		aw = areaSize.width()
		ah = areaSize.height()
		imgSize = self.image.size()
		iw = imgSize.width()
		ih = imgSize.height()
		
		if ah * iw/ih < aw:
			w = ah * iw/ih
			h = ah
		else:
			w = aw	
			h = aw * ih/iw
		x = (aw - w)/2
		y = (ah - h)/2
		self.container.scrollInner.resize( x+w, y+h )
		self.container.labelImage.setGeometry( x, y,  w, h )
		self.state = 'fit'
		self.scale = w/iw

	def actualSize( self ):
		if not self.image: return
		
		areaSize = self.container.scrollArea.size()
		aw = areaSize.width()
		ah = areaSize.height()
		imgSize = self.image.size()
		iw = imgSize.width()
		ih = imgSize.height()
		w = iw
		h = ih
		if iw > aw:
			x = 0
		else:
			x = (aw - w)/2

		if ih > ah:
			y = 0
		else:
			y = (ah - h)/2

		self.container.labelImage.setGeometry( x, y,  w, h )
		self.container.scrollInner.resize( x + w, y + h )

		self.scale = 1.0
		self.state = 'actual'

	def onContainerResize( self, size ):
		if self.state=='actual':
			self.actualSize()
		else:
			self.fitSize()


ImagePreviewer().register()
