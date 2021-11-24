import sys
from qtpy import QtWidgets, QtGui, QtCore



if __name__ == '__main__':
	class TestFrame( QtWidgets.QFrame ):
		def tabletEvent( self, ev ):
			print((ev.pressure()))
			

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
