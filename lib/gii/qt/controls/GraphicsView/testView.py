from gii.qt.controls.GraphicsView.TimelineView import *
from random import random
from qtpy import QtOpenGL
from time import time

_keyid = 1
class TestKey():
	def __init__( self, track ):
		global _keyid
		_keyid += 1
		self.name = 'key - %d' % _keyid
		# self.length = random()*500/1000.0
		self.length = 1
		self.pos    = ( random()*1000 + 50 ) /1000.0
		self.track  = track
		self.value = 100
		self.mode = TWEEN_MODE_BEZIER
		self.preTPValue = (0.5, 0 )
		self.postTPValue = (0.5, 0 )

	def isResizable( self ):
		return False

class TestEventKey( TestKey ):
	def isResizable( self ):
		return True

_trackId = 0
class TestTrack():
	def __init__( self, name, pos = None ):
		global _trackId
		pos = _trackId * 25
		_trackId += 1
		self.name = name
		if self.isResizable():
			self.keys = [
				TestEventKey( self ),
				TestEventKey( self ),
				TestEventKey( self ),
				# TestKey( self )
			]
		else:
			self.keys = [
				TestKey( self ),
				TestKey( self ),
				TestKey( self ),
				TestKey( self )
			]
		self.pos = pos

	def isResizable( self ):
		return False

	def isCurve( self ):
		return True

class TestEventTrack( TestTrack ):
	def isResizable( self ):
		return True

	def isCurve( self ):
		return False

class TestEvent():
	def __init__( self ):
		self.name = 'event'

dataset = [
	TestTrack( 'track' ),
	TestTrack( 'track0' ),
	TestEventTrack( 'track1' ),
	TestTrack( 'track2' ),
	TestTrack( 'track3' ),
	TestTrack( 'track1' ),
	TestEventTrack( 'track2' ),
	TestTrack( 'track3' ),
	TestTrack( 'track1' ),
	TestEventTrack( 'track2' ),
	TestTrack( 'track3' )
]

class TestMarker(object):
	pass

class TestTimeline( TimelineView ):
	def getTrackNodes( self ):
		return dataset

	def getKeyNodes( self, trackNode ):
		return trackNode.keys

	def getKeyParam( self, keyNode ): #pos, length, resizable
		return keyNode.pos, keyNode.length, keyNode.isResizable()

	def getKeyBezierPoints( self, keyNode ):
		( tpx0, tpy0 ) = keyNode.preTPValue  
		( tpx1, tpy1 ) = keyNode.postTPValue 
		return tpx0, tpy0, tpx1, tpy1

	def getKeyCurveValue( self, keyNode ):
		return keyNode.value

	def getKeyMode( self, keyNode ):
		return keyNode.mode

	def getParentTrackNode( self, keyNode ):
		return keyNode.track

	def updateTrackContent( self, track, trackNode, **option ):
		# track.getHeaderItem().setText( trackNode.name )
		track.allowOverlap = True
		pass

	def updateKeyContent( self, key, keyNode, **option ):
		pass

	def isTrackVisible( self, track ):
		return True

	def isCurveTrack( self, track ):
		return track.isCurve()

	def getTrackPos( self, track ):
		return track.pos

	def formatPos( self, pos ):
		i = int( pos/1000 )
		f = int( pos - i*1000 )
		return '%d:%02d' % ( i, f/10 )

	def getRulerParam( self ):
		return dict( zoom = 1 )
		# return dict( zoom = 5 )

	def createTrackItem( self, node ):
		if node.isResizable():
			return TimelineEventTrackItem()
		else:
			return TimelineTrackItem()


class TestFrame( QtWidgets.QFrame ):
	def __init__( self ):
		super( TestFrame, self ).__init__()
		layout = QtWidgets.QVBoxLayout( self )
		# layout.setContentsMargins( 0 , 0 , 0 , 0 )
		timeline = TestTimeline()
		layout.addWidget( timeline )
		timeline.setRange( 0, 3.2 )
		timeline.rebuild()
		timeline.setTrackSelection( [ dataset[0] ] )
		self.testMarker = TestMarker()
		timeline.addMarker( self.testMarker )

		self.testMarker2 = TestMarker()
		mitem = timeline.addMarker( self.testMarker2 )
		mitem.setText( 'FightStart')
		mitem.setTimePos( 2.3 )

		timeline.keyChanged.connect( self.onKeyChanged )
		timeline.keyBezierPointChanged.connect( self.onKeyBezierPointChanged )
		timeline.keyCurveValueChanged.connect( self.onKeyCurveValueChanged )
		timeline.markerChanged.connect( self.onMarkerChanged )
		self.timer = QtCore.QTimer( self )
		self.timer.timeout.connect( self.onTimer )
		self.timer.setInterval( 100 )
		self.timer.start()
		self.t0 = time()


	def onKeyChanged( self, key, pos, length ):
		key.pos = pos
		key.length = length

	def onKeyCurveValueChanged( self, key, value ):
		key.value = value

	def onKeyBezierPointChanged( self, key, tpx0, tpy0, tpx1, tpy1 ):
		key.preTPValue  = ( tpx0, tpy0 )
		key.postTPValue = ( tpx1, tpy1 )

	def onMarkerChanged( self, marker, pos ):
		print(('marker changed', marker, pos))

	def onTimer( self ):
		t1 = time()
		# print '%.2f' % (t1- self.t0)
		self.t0 = t1
		

app = QtWidgets.QApplication( sys.argv )
styleSheetName = 'gii.qss'
app.setStyleSheet(
		open( '/Users/tommo/prj/gii/data/theme/' + styleSheetName ).read() 
	)
frame = TestFrame()

frame.resize( 600, 300 )
frame.show()
frame.raise_()

# # timeline.setZoom( 10 )
# # timeline.selectTrack( dataset[1] )
# timeline.selectKey( dataset[1].keys[0] )

app.exec_()
