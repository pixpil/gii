from gii.core import app
from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtCore import Qt


class ListStackModel(QtCore.QAbstractListModel):
	def __init__(self, stacks):
		super(ListStackModel,self).__init__()
		self.stacks=stacks

	def rowCount(self, parent):
		return len(self.stacks)

	def data(self, idx, role=Qt.DisplayRole):
		if not idx.isValid(): return None
		row=idx.row()
		level=self.stacks[row]
		if role==Qt.DisplayRole:
			return level['string']
		if role==Qt.UserRole:
			return level

		return None

class ListStackView(QtWidgets.QListView):
	def __init__(self):
		super(ListStackView, self).__init__()
		self.setModel(ListStackModel([]))
		self.clicked.connect(self.onClicked)
		self.doubleClicked.connect(self.onDClicked)

	def loadStackData(self,data):
		self.model().beginResetModel()
		self.model().stacks=data
		self.model().endResetModel()
		idx=self.selectRow(0)
		self.onClicked(idx)
		self.onDClicked(idx)

	def selectRow(self, row):
		idx=self.model().index(row,0)
		if idx.isValid(): self.setCurrentIndex(idx)		
		return idx

	def onClicked(self, idx):
		if not idx.isValid(): return
		id=idx.row()
		app.getModule('script_view').debuggerHandler.getScopeInfo(id+1)

	def onDClicked( self, idx ):
		if not idx.isValid(): return
		level = self.model().data(idx, Qt.UserRole)
		if level['file']:
			highLight = ( idx.row() == 0 )
			app.getModule('script_view').locateFile(
				level['file'], level['line'], highLight and 'normal' or False)


