import logging
from gii.core.tmpfile import TempDir

from qtpy import QtWidgets, QtGui,QtCore
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QMessageBox

class StringDialog(QtWidgets.QDialog):
	def __init__(self, prompt, *args):
		super(StringDialog, self).__init__(*args)
		lineEdit=QtWidgets.QLineEdit(self)
		self.setWindowTitle(prompt)
		btnOK=QtWidgets.QPushButton('OK')
		btnCancel=QtWidgets.QPushButton('Cancel')
		
		buttonBox=QtWidgets.QDialogButtonBox(QtCore.Qt.Horizontal)
		buttonBox.addButton(btnOK, QtWidgets.QDialogButtonBox.AcceptRole)
		buttonBox.addButton(btnCancel, QtWidgets.QDialogButtonBox.RejectRole)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)

		box=QtWidgets.QVBoxLayout()
		self.setLayout(box)

		box.addWidget(lineEdit)
		box.addWidget(buttonBox)

		self.lineEdit=lineEdit

	def getText(self):
		return self.lineEdit.text()
	
def requestConfirm(title, msg, level='normal'):
	f = None
	if level == 'warning':
		f = QMessageBox.warning
	elif level == 'critical':
		f = QMessageBox.critical
	else:
		f = QMessageBox.question
	res = f(None, title, msg, QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
	if res == QMessageBox.Yes:    return True
	if res == QMessageBox.Cancel: return None
	if res == QMessageBox.No:     return False

def alertMessage(title, msg, level='warning'):
	f=None
	if level=='warning':
		f=QMessageBox.warning
		logging.warning( msg )

	elif level=='critical':
		f=QMessageBox.critical
		logging.error( msg )

	elif level=='question':
		f = QMessageBox.question

	else:
		f = QMessageBox.information
	res = f( None, title, msg	)

def requestString( title, prompt, defaultValue = '' ):
	text, ok = QtWidgets.QInputDialog.getText(None, title, prompt, QtWidgets.QLineEdit.Normal, defaultValue )
	# dialog=StringDialog(prompt)
	# dialog.move(QtGui.QCursor.pos())
	# if dialog.exec_():
	# 	return dialog.getText()
	# else:
	# 	return None
	if ok:
		return text
	else:
		return None

def requestColor(prompt, initColor = None, **kwargs):
	dialog = QtGui.QColorDialog( initColor or QtCore.Qt.white )
	dialog.move( QtGui.QCursor.pos() )
	dialog.setWindowTitle( prompt )
	onColorChanged = kwargs.get( 'onColorChanged', None )
	if onColorChanged:
		dialog.currentColorChanged.connect( onColorChanged )
	if dialog.exec_() == 1:
		col = dialog.currentColor()
		# dialog.destroy()
		if col.isValid(): return col
	return initColor

	# col = None
	# if initCol: 
	# 	col = QtGui.QColor(initCol)
	# else:
	# 	col = QtCore.Qt.white
	# 	if onColorChanged:
	# 		currentColorChanged
	# col = QtGui.QColorDialog.getColor( 
	# 	col, 
	# 	None,
	# 	prompt,
	# 	QtGui.QColorDialog.ShowAlphaChannel
	# 	)
	# if col.isValid(): return col
	# return None

