import os
import os.path
import sys

from xml.dom import minidom, Node



##----------------------------------------------------------------##
def _getTexts( node, tag ):
	nodes = node.getElementsByTagName( tag )
	if not nodes: return None
	output = []
	for node in nodes:
		node = nodes[ 0 ]
		if node.firstChild and node.firstChild.nodeType == node.TEXT_NODE:
			output.append( node.firstChild.data )
	return output

def _getText( node, tag ):
	nodes = node.getElementsByTagName( tag )
	if not nodes: return None
	node = nodes[ 0 ]
	if node.firstChild and node.firstChild.nodeType == node.TEXT_NODE:
		return node.firstChild.data
	return None


##----------------------------------------------------------------##
class FMODStudioProjectItem(object):
	def __init__( self, project, id, objectClass ):
		self.project     = project
		self.id          = id
		self.objectClass = objectClass
		self.properties  = {}
		self.refs        = {}
		self.children    = []
		self.parent      = None

	def getChildren( self ):
		return self.children

	def getParent( self ):
		return self.parent

	def setParent( self, parent ):
		# if self in parent.children:
		# 	return
		self.parent = parent
		if parent:
			parent.children.append( self )

	def setChildren( self, children ):
		if not children:
			self.children = []
			return
		self.children = children
		for child in children:
			child.parent = self

	def getProperty( self, key, default = None ):
		return self.properties.get( key, default )

	def getFirstRef( self, key ):
		refs = self.getRef( key )
		if not refs: return None
		return refs[ 0 ]

	def getRef( self, key ):
		ids = self.refs.get( key, None )
		if not ids: return None
		proj = self.project
		return [ proj.getObject[ id ] for id in ids ]

	def __repr__( self ):
		return '%s:%s' % ( self.objectClass, self.id )

##----------------------------------------------------------------##
class FMODStudioProject(object):
	def __init__( self ):
		self.items = {}
		self.events = {}
		self.snapshots = {}
		self.assets = {}
		self.groups = {}
		self.folders = {}
		self.banks = {}
		self.masterEventFolder = None
		self.masterSnapshotGroup = None
		self.masterBankFolder  = None

	def getObject( self, guid ):
		return self.items.get( guid, None )

	def buildIndex( self ):
		for id, item in list(self.items.items()):
			clas = item.objectClass
			if clas == 'Event':
				self.events[ id ] = item
				item.setParent( item.getFirstRef( 'folder' ) )
		
			elif clas == 'Bank':
				self.banks[ id ] = item
				item.setParent( item.getFirstRef( 'folder' ) )

			elif clas == 'Snapshot':
				self.snapshots[ id ] = item

			elif clas == 'EncodableAsset':
				self.assets[ id ] = item

			elif clas == 'EventFolder':
				item.setParent( item.getFirstRef( 'folder' ) )

			elif clas == 'BankFolder':
				item.setParent( item.getFirstRef( 'folder' ) )

			elif clas == 'SnapshotGroup':
				item.setChildren( item.getRef( 'items' ) )

			elif clas == 'MasterBankFolder':
				self.masterBankFolder = item

			elif clas == 'MasterEventFolder':
				self.masterEventFolder = item

			elif clas == 'SnapshotList':
				self.masterSnapshotGroup = item
				item.setChildren( item.getRef( 'items' ) )


##----------------------------------------------------------------##
class FMODStudioParser():
	def parse( self, path ):
		self.project = FMODStudioProject()
		self.targetPath = path
		self.targetFolder = folder = os.path.dirname( path )
		metaDataPath = self.targetFolder + '/MetaData'
		for fileName in os.listdir( metaDataPath ):
			fullPath = metaDataPath + '/' + fileName
			if os.path.isfile( fullPath ):
				if fileName.endswith( '.xml' ):
					self.parseDataFile( fullPath )
			else:
				self.parseDataFolder( fullPath )
		self.project.buildIndex()
		return self.project

	def parseDataFolder( self, folder ):
		for fileName in os.listdir( folder ):
			fullPath = folder + '/' + fileName
			if os.path.isfile( fullPath ) and fileName.endswith( '.xml' ):
				self.parseDataFile( fullPath )

	def parseDataFile( self, path ):
		basename = os.path.basename( path )
		name, ext = os.path.splitext( basename )
		dom = minidom.parse( open( path, 'r' ) )
		project = self.project
		for objNode in dom.getElementsByTagName( "object" ):
			objClass = objNode.getAttribute( 'class' )
			id = objNode.getAttribute( 'id' )
			item = FMODStudioProjectItem( project, id, objClass )
			project.items[ id ] = item
			for propertyNode in objNode.getElementsByTagName( 'property' ):
				pname = propertyNode.getAttribute( 'name' )
				item.properties[ pname ] = _getText( propertyNode, 'value' )

			for propertyNode in objNode.getElementsByTagName( 'replationship' ):
				pname = propertyNode.getAttribute( 'name' )
				item.refs[ pname ] = _getTexts( propertyNode, 'destination' )

		
if __name__ == '__main__':
	testFile = '/Applications/FMOD Studio/examples/Examples.fspro'
	parser = FMODStudioParser()
	project = parser.parse( testFile )
	from gii.core import JSONHelper

	
