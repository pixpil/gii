from gii.core import app

from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtCore import Qt

class TreeScopeView(QtWidgets.QTreeWidget):
	"""docstring for TreeScopeView"""
	def __init__(self):
		super(TreeScopeView, self).__init__()
		self.varDict={}
		self.rootItem=self.invisibleRootItem()
		headerItem=QtWidgets.QTreeWidgetItem()		
		headerItem.setText(0,'Var')
		headerItem.setText(1,'Value')
		# headerItem.setText(2,'Type')
		self.setHeaderItem(headerItem)

		self.itemExpanded.connect(self.onExpandVar)

	def loadVarData(self, data, parentName):
		parentItem=None
		if not parentName:
			self.clear()
			self.varDict={}
			parentItem=self.rootItem
		else:
			parentItem=self.varDict.get(parentName, None)
			if not parentItem:
				return
			pdata=parentItem.data
			if pdata['expanded']!=True:
				pdata['expanded']=True
				parentItem.takeChildren()

		for var in data:
			vt=var['type']
			childItem=QtWidgets.QTreeWidgetItem()
			parentItem.addChild(childItem)
			childItem.setText(0,var['name'])
			childItem.setText(1,var['value'])
			# childItem.setText(2,var['type'])
			childItem.data=var
			
			if vt=='table': #expandable
				if parentName:
					var['index']=parentName+'.'+var['name']
				else:
					var['index']=var['name']
				dummy=QtWidgets.QTreeWidgetItem()
				dummy.setText(0,'...')
				childItem.addChild(dummy)
				self.varDict[var['index']]=childItem

	def onExpandVar(self, item):		
		var=item.data
		if var and not var.get('expanded',False):
			app.getModule('script_view').debuggerHandler.dumpVar(var['index'])
			var['expanded']='expanding'
