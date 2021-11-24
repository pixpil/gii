from gii.core                 import *
from mock  import MOCKEditCanvas
from gii.AssetEditor          import AssetPreviewer
from gii.qt.helpers           import addWidgetWithLayout

from qtpy import uic
from qtpy import QtWidgets, QtGui

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


class ParticlePreviewer(AssetPreviewer):
	def createWidget(self, container):
		self.canvas = MOCKEditCanvas(container)
		self.canvas.loadScript( _getModulePath('ParticlePreview.lua') )
		return self.canvas

	def accept(self, assetNode):
		return assetNode.getType() in [ 'particle_system', 'particle_pex', 'particle_simple'  ]

	def onStart(self, assetNode):
		atype = assetNode.getType()
		self.canvas.makeCurrentCanvas()
		self.canvas.safeCallMethod( 'preview', 'showParticle', assetNode.getPath() )
		self.canvas.startUpdateTimer( 60 )
		
	def onStop(self):
		self.canvas.stopUpdateTimer()
		self.canvas.safeCallMethod( 'preview', 'clearParticle' )

ParticlePreviewer().register()

