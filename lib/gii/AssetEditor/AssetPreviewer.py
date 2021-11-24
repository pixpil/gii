import random
from abc import ABCMeta, abstractmethod

from gii.core         import *
from gii.qt.dialogs   import requestString
from gii.qt.controls.AssetTreeView import AssetTreeView

from gii.SceneEditor      import SceneEditorModule


from qtpy            import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore     import Qt

##----------------------------------------------------------------##
class AssetPreviewerManager( SceneEditorModule ):
	name = 'asset_previewer'
	dependency = [ 'asset_browser' ]
	
	def __init__(self):
		# super(AssetPreviewerManager, self).__init__()
		self.previewers        = []
		self.activePreviewer   = None		
		self.target = None

	def onLoad( self ):
		self.container = self.requestDockWindow('AssetPreview',
				title   = 'Asset View',
				dock    = 'left',
				minSize = (100,100)
			)

		self.previewerContainer = QtWidgets.QStackedWidget()
		self.previewerContainer.setSizePolicy(
				QtWidgets.QSizePolicy.Expanding, 
				QtWidgets.QSizePolicy.Expanding
			)
		self.previewerContainer.setMinimumSize(100,100)
		self.container.addWidget( self.previewerContainer, expanding=False )
		self.nullPreviewer = self.registerPreviewer( NullAssetPreviewer() )		

		signals.connect( 'asset.imported', self.onAssetImported )
		signals.connect( 'app.activate',   self.onAppActivate )
		signals.connect( 'app.deactivate', self.onAppDeactivate )


	# def onAppReady( self ):
	# 	for previewer in self.previewers:
	# 		self._loadPreviewer(previewer)

	def setTarget( self, selection ):
		if self.activePreviewer:
			self.activePreviewer.onStop()
			self.target = None

		if selection and isinstance( selection[0], AssetNode ) :
			target = selection[0]
			for previewer in self.previewers:
				if previewer.accept(target):
					self._startPreview(previewer, target)
					return

		self._startPreview(self.nullPreviewer, None)

	def onAppActivate(self):
		if self.activePreviewer:
			self.activePreviewer.onPause( False )

	def onAppDeactivate(self):
		if self.activePreviewer:
			self.activePreviewer.onPause( True )


	def onAssetImported( self, assetNode ):
		if not self.target: return
		if assetNode == self.target or assetNode.isParentOf( self.target ):
			self.refreshPreviewr()

	def refreshPreviewr( self ):
		if self.activePreviewer:
			self.activePreviewer.onStop()
			self._startPreview( self.activePreviewer, self.target )

	def _startPreview(self, previewer, selection):
		if not previewer.initialized:
			self._loadPreviewer( previewer )

		idx = previewer._stackedId
		self.target = selection
		if selection:
			self.container.setWindowTitle( 'Asset View - %s' % selection.getPath() )
		else:
			self.container.setWindowTitle( 'Asset View' )
		self.previewerContainer.setCurrentIndex(idx)
		self.activePreviewer=previewer		
		previewer.onStart(selection)

	def _loadPreviewer(self, previewer):
		widget = previewer.createWidget(self.previewerContainer)
		assert isinstance(widget,QtWidgets.QWidget), 'widget expected from previewer'
		idx = self.previewerContainer.addWidget(widget)
		previewer._stackedId  = idx
		previewer._widget     = widget
		previewer.initialized = True

	def registerPreviewer(self, previewer):
		self.previewers.insert(0, previewer) #TODO: use some dict?
		# if self.alive: self._loadPreviewer(previewer)		
		previewer.initialized = False
		return previewer


##----------------------------------------------------------------##
class AssetPreviewer(object):
	def register( self ):
		return app.getModule('asset_previewer').registerPreviewer( self )

	def accept(self, selection):
		return False

	def createWidget(self):
		return None

	def onStart(self, selection):
		pass

	def onPause( self, paused ):
		pass

	def onStop(self):
		pass

##----------------------------------------------------------------##		
class NullAssetPreviewer(AssetPreviewer):
	def createWidget(self,container):
		self.label = QtWidgets.QLabel(container)
		self.label.setAlignment(QtCore.Qt.AlignHCenter)
		self.label.setText('NO PREVIEW')
		self.label.setSizePolicy(
				QtWidgets.QSizePolicy.Expanding,
				QtWidgets.QSizePolicy.Expanding
				)
		return self.label

	def onStart(self, selection):
		pass
		# self.label.setParent(container)

	def onStop(self):
		pass
