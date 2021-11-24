import logging
from gii.core.tmpfile import TempDir

from qtpy import QtWidgets, QtGui,QtCore
from qtpy.QtCore import Qt

from gii.qt.controls.PropertyEditor import PropertyEditor

##----------------------------------------------------------------##
class PropertyDialog( QtWidgets.QDialog ):
	def __init__(self, prompt, *args, **options):
		super(PropertyDialog, self).__init__(*args)
		self.setWindowTitle( prompt )
		btnOK     = QtWidgets.QPushButton('OK')
		btnCancel = QtWidgets.QPushButton('Cancel')
		
		buttonBox=QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal)
		buttonBox.addButton(btnOK, QtWidgets.QDialogButtonBox.AcceptRole)
		if options.get( 'cancel_button', True ):
			buttonBox.addButton(btnCancel, QtWidgets.QDialogButtonBox.RejectRole)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)
			

		box = QtWidgets.QVBoxLayout( self )
		box.setContentsMargins( 10, 10, 10, 10 )
		box.setSpacing( 5 )

		propertyEditor = PropertyEditor( self )
		box.addWidget(propertyEditor)
		box.addWidget(buttonBox)

		self.propertyEditor = propertyEditor

	def setTarget( self, target ):
		self.propertyEditor.setTarget( target )


##----------------------------------------------------------------##		
def requestProperty( prompt, target, **option ):
	dialog = PropertyDialog( prompt, **option )
	dialog.setTarget( target )
	dialog.move( QtGui.QCursor.pos() )

	if dialog.exec_():
		return True
	else:
		return False

