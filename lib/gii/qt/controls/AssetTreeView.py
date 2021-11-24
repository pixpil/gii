import random
from qtpy            import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore     import Qt

from gii.core         import *
from gii.qt           import QtEditorModule

from gii.qt.IconCache                  import getIcon
from gii.qt.controls.GenericTreeWidget import GenericTreeWidget, GenericTreeFilter


class AssetTreeView( GenericTreeWidget ):
	def __init__( self, *args, **options ):
		super( AssetTreeView, self ).__init__( *args, **options )

	def saveTreeStates( self ):
		for node, item in list(self.nodeDict.items()):
			node.setProperty( 'expanded', item.isExpanded() )

	def loadTreeStates( self ):
		for node, item in list(self.nodeDict.items()):
			item.setExpanded( node.getProperty( 'expanded', False ) )
		self.getItemByNode( self.getRootNode() ).setExpanded( True )
		
	def getRootNode( self ):
		return app.getAssetLibrary().getRootNode()

	def getNodeParent( self, node ): # reimplemnt for target node
		return node.getParent()

	def getNodeChildren( self, node ):
		result = []
		for node in node.getChildren():
			if node.getProperty( 'hidden', False ): continue
			if self.getOption( 'folder_only', False ):
				if not node.getGroupType() in ( 'folder', 'package' ) :continue
			result.append( node )
		return result

	def createItem( self, node ):
		return AssetTreeItem()

	def updateItemContent( self, item, node, **option ):
		if option.get('basic', True):
			assetType = node.getType()
			item.setText( 0, node.getName() )
			item.setText( 1, '' )
			if assetType in [ 'file', 'folder' ] :
				item.setText( 2, '' )
			else:
				item.setText( 2, assetType )

			iconName = app.getAssetLibrary().getAssetIcon( assetType )
			item.setIcon(0, getIcon(iconName,'normal'))

		if option.get('deploy', True):
			dstate=node.getDeployState()
			if   dstate is None:
				item.setIcon(1, getIcon(None))
			elif dstate == False:
				item.setIcon(1, getIcon('deploy_no'))
			elif dstate == True:
				item.setIcon(1, getIcon('deploy_yes'))
			else: #'dep' or 'parent'
				item.setIcon(1, getIcon('deploy_dep'))

	def onClipboardCopy( self ):
		clip = QtWidgets.QApplication.clipboard()
		out = None
		for node in self.getSelection():
			if out:
				out += "\n"
			else:
				out = ""
			out += node.getNodePath()
		clip.setText( out )
		return True

	def getHeaderInfo( self ):
		return [('Name',200), ('Deploy',30), ('Type',60)]

	def _updateItem(self, node, updateLog=None, **option):
		super( AssetTreeView, self )._updateItem( node, updateLog, **option )

		if option.get('updateDependency',False):
			for dep in node.dependency:
				self._updateItem(dep, updateLog, **option)
	
##----------------------------------------------------------------##
#TODO: allow sort by other column
class AssetTreeItem(QtWidgets.QTreeWidgetItem):
	def __lt__(self, other):
		node0 = self.node
		node1 = hasattr(other, 'node') and other.node or None
		if not node1:
			return True
		tree = self.treeWidget()

		# if not tree:
		# 	col = 0
		# else:
		# 	col = tree.sortColumn()		
		t0 = node0.getType()
		t1 = node1.getType()
		if t1!=t0:			
			if tree.sortOrder() == 0:
				if t0 == 'folder': return True
				if t1 == 'folder': return False
			else:
				if t0 == 'folder': return False
				if t1 == 'folder': return True
		return super( AssetTreeItem, self ).__lt__( other )
		# return node0.getName().lower()<node1.getName().lower()

##----------------------------------------------------------------##

class AssetTreeFilter( GenericTreeFilter ):
	pass
