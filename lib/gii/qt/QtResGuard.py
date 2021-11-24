from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import QEventLoop, QEvent, QObject

from gii.core import ResGuard

class ResGuardQWidget(object):
	
	target = QtWidgets.QWidget

	def onRelease( self, widget ):
		print(('releasing widget!!', widget))
		widget.setParent( None )
