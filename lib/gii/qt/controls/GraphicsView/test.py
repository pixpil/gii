from gii.qt.controls.GraphicsView.TimelineWidget import *
from random import random
from qtpy import QtOpenGL

_spanid = 1
class TestSpan():
	def __init__( self, track ):
		global _spanid
		_spanid += 1
		self.name = 'span - %d' % _spanid
		self.length = 100
		self.pos    = random()*1000 + 50
		self.track  = track

class TestTrack():
	def __init__( self, name ):
		self.name = name
		self.spans = [
			TestSpan( self ),
			TestSpan( self ),
			TestSpan( self ),
			TestSpan( self )
		]

class TestEvent():
	def __init__( self ):
		self.name = 'event'

dataset = [
	TestTrack( 'track' ),
	TestTrack( 'track0' ),
	TestTrack( 'track1' ),
	TestTrack( 'track2' ),
	TestTrack( 'track3' ),
	TestTrack( 'track1' ),
	TestTrack( 'track2' ),
	TestTrack( 'track3' ),
	TestTrack( 'track1' ),
	TestTrack( 'track2' ),
	TestTrack( 'track3' )
]

class TestTimeline( TimelineWidget ):
	def getTrackNodes( self ):
		return dataset

	def getSpanNodes( self, trackNode ):
		return trackNode.spans

	def getSpanParam( self, spanNode ): #pos, length, resizable
		return spanNode.pos, spanNode.length, True

	def getParentTrackNode( self, spanNode ):
		return spanNode.track

	def updateTrackContent( self, track, trackNode, **option ):
		track.getHeader().setText( trackNode.name )

	def updateSpanContent( self, span, spanNode, **option ):
		pass

	def formatPos( self, pos ):
		i = int( pos/1000 )
		f = int( pos - i*1000 )
		return '%d:%02d' % ( i, f/10 )

	def getRulerParam( self ):
		return dict( zoom = 1 )
		# return dict( zoom = 5 )


class TestFrame( QtWidgets.QWidget ):
	def __init__( self ):
		pass

app = QtWidgets.QApplication( sys.argv )
styleSheetName = 'gii.qss'
app.setStyleSheet(
		open( '/Users/tommo/prj/gii/data/theme/' + styleSheetName ).read() 
	)
timeline = TestTimeline()
timeline.resize( 600, 300 )
timeline.show()
timeline.raise_()
timeline.rebuild()
# timeline.setZoom( 10 )
# timeline.selectTrack( dataset[1] )
timeline.selectSpan( dataset[1].spans[0] )

app.exec_()
