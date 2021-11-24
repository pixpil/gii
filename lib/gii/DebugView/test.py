 #!/usr/bin/env python
 
import sys
from qtpy import Qt
from qtpy           import QtCore, QtWidgets, QtGui, uic
 
class HelloApplication( Qt.QApplication ):

 	def __init__( self, args ):
 		Qt.QApplication.__init__( self, args )
 		self.addWidgets()
 		self.exec_()

 	def addWidgets( self ):
 		self.helloButton = Qt.QPushButton( "hello" , None)
 		self.connect( self.helloButton, Qt.SIGNAL("clicked()"), self.slotSayHello )
 		self.helloButton.show()

 	def slotSayHello( self ):
 		print( "Hello, World !" )

if __name__ == "__main__":
	app = HelloApplication( sys.argv )

#  # We instantiate a QApplication passing the arguments of the script to it:
# a = Qt.QApplication(sys.argv)
 
#  # Add a basic widget to this application:
#  # The first argument is the text we want this QWidget to show, the second
#  # one is the parent widget. Since Our "hello" is the only thing we use (the 
#  # so-called "MainWidget", it does not have a parent.
# hello = Qt.QLabel("Hello, World")
 
#  # ... and that it should be shown.


# def sayHello():
# 	print( "Hello, World" )

# helloButton = Qt.QPushButton( "say 'hello'", None )

# a.connect( helloButton, Qt.SIGNAL( "clicked()" ), sayHello )

# helloButton.show()

 
#  # Now we can start it.
# a.exec_()