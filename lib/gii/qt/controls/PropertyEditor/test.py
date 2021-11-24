import sip
sip.setapi("QString", 2)
sip.setapi('QVariant', 2)

from .__init__ import *

from qtpy import QtCore, QtWidgets, QtGui

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

class TestWindow(QtWidgets.QWidget):
	def __init__( self, parent = None ):
		super( TestWindow, self ).__init__( parent )
		self.setMinimumSize( 100, 100 )
		self.setWindowTitle('Prop Test')
		self.editor = addWidgetWithLayout( PropertyEditor( self ) )
		self.layout().addStretch()
		self.editor._buildSubEditor( 'name', StringFieldEditor ).set('tommo')
		self.editor._buildSubEditor( 'age', IntFieldEditor ).set( 31 )
		self.editor._buildSubEditor( 'balance', FloatFieldEditor ).set( 0.5 )
		self.editor._buildSubEditor( 'ready', BoolFieldEditor ).set(True)
		self.editor._buildSubEditor( 'category', EnumFieldEditor ).set(1)
		self.editor._buildSubEditor( 'color', ColorFieldEditor ).set( (1,1,0,0.5) )


app = QtWidgets.QApplication([])

styleSheetName = 'xn.qss'
QtCore.QDir.setSearchPaths( 'theme', [ '/prj/moai/gii/data/theme' ] )
app.setStyleSheet(
		open( '/prj/moai/gii/data/theme/' + styleSheetName ).read() 
	)
test = TestWindow()
test.show()
test.raise_()

app.exec_()