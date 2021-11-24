from gii.core import generateGUID
from util import TagMatch

##----------------------------------------------------------------##
class SearchFilterItem( object ):
	def __init__( self ):
		self.locked  = False
		self.active  = True
		self.alias   = ''
		self.citeria = ''
		self.rule    = None
		self.parent  = None

	def setLocked( self, locked ):
		self.locked = locked
		self.active = True

	def isLocked( self ):
		return self.locked

	def setActive( self, active ):
		self.active = active

	def isActive( self ):
		return self.active

	def setAlias( self, alias ):
		self.alias = alias

	def getAlias( self ):
		return self.alias

	def toString( self ):
		if self.alias: return self.alias
		return self.citeria

	def setCiteria( self, citeria ):
		self.citeria = citeria
		self.rule = TagMatch.parseTagMatch( citeria, uppercase = True )

	def getCiteria( self ):
		return self.citeria

	def evaluate( self, info ):
		if not self.rule: return False
		return self.rule.evaluate( info )

	def markDirty( self ):
		if self.parent:
			self.parent.markDirty()

	def save( self ):
		return {
			'locked'  : self.locked,
			'active'  : self.active,
			'alias'   : self.alias,
			'citeria' : self.citeria,
		}

	def load( self, data ):
		self.locked  = data.get( 'locked',  self.locked  )
		self.active  = data.get( 'active',  self.active  )
		self.alias   = data.get( 'alias',   self.alias   )
		self.citeria = data.get( 'citeria', self.citeria )

##----------------------------------------------------------------##
class SearchFilterNode( object ):
	def __init__( self ):
		self.parent   = None
		self.children = []
		self.id = None

		self.name     = 'node'
		self.comment  = ''

	def getType( self ):
		return 'filterNode'

	def getName( self ):
		return self.name

	def setName( self, name ):
		self.name = name

	def getComment( self ):
		return self.comment

	def setComment( self, comment ):
		self.comment = comment 

	def getId( self ):
		if not self.id:
			self.id = generateGUID()
		return self.id
	
	def getRoot( self ):
		if not self.parent: return self
		return self.parent.getRoot()

	def findChild( self, id ):
		for node in self.children:
			if node.id == id:
				return node
			found = node.findChild( id )
			if found: return found
		return None

	def getParent( self ):
		return self.parent

	def addChild( self, node ):
		if node.parent:
			node.remove()
		self.children.append( node )
		node.parent = self

	def getChildren( self ):
		return self.children

	def getAllChildren( self ):
		collection = self.children[:]
		for child in self.children:
			collection += child.getAllChildren()
		return collection

	def getParent( self ):
		return self.parent

	def removeChild( self, node ):
		self.children.remove( node )
		node.parent = None

	def remove( self ):
		if self.parent:
			return self.parent.removeChild( self )

	def save( self ):
		return {}

##----------------------------------------------------------------##
class SearchFilterGroup( SearchFilterNode ):
	def getType( self ):
		return 'group'

	def save( self ):
		return {
			'type'     : 'group',
			'id'       : self.getId(),
			'name'     : self.name,
			'comment'  : self.comment,
			'children' : [ child.save() for child in self.children ],
		}

	def load( self, data ):
		self.id      = data.get( 'id', None )
		self.name    = data.get( 'name', '' )
		self.comment = data.get( 'comment', '' )
		for childData in data.get( 'children', [] ):
			t = childData['type']
			if t == 'group':
				node = SearchFilterGroup()
				self.addChild( node )
				node.load( childData )
			
			elif t == 'filter':
				node = SearchFilter()
				self.addChild( node )
				node.load( childData )

			else:
				raise Exception( 'unkown filter node type %s' % t )


##----------------------------------------------------------------##
class SearchFilter( SearchFilterNode ):
	def __init__( self ):
		super( SearchFilter, self ).__init__()
		self.items = []
		self.compiledRule = None
		self.dirty = False

	def getType( self ):
		return 'filter'

	def evaluate( self, info ):
		if self.compiledRule:
			return self.compiledRule.evaluate( info )
		else:
			return False

	def updateRule( self ):
		if not self.dirty: return
		self.dirty = False
		compiledCiteria = ''
		for item in self.items:
			if item.isActive():
				compiledCiteria = compiledCiteria + ' ' + item.citeria
		if not compiledCiteria.strip():
			self.compiledRule = None
		else:
			self.compiledRule = TagMatch.parseTagMatch( compiledCiteria, uppercase = True )

	def markDirty( self ):
		self.dirty = True

	def addItem( self, item ):
		self.items.append( item )
		item.parent = self

	def removeItem( self, item ):
		self.items.remove( item )
		item.parent = None

	def getItems( self ):
		return self.items

	def hasItem( self ):
		return bool( self.items )

	def isFiltering( self ):
		if self.compiledRule: return True
		return False

	def save( self ):
		return {
			'type'   : 'filter',
			'id'     : self.getId(),
			'name'   : self.name,
			'comment': self.comment,
			'items'  : [ item.save() for item in self.items ],
		}

	def load( self, data ):
		self.id      = data.get( 'id', None )
		self.name    = data.get( 'name', '' )
		self.comment = data.get( 'comment', '' )
		self.items   = []
		for itemData in data.get( 'items', [] ):
			item = SearchFilterItem()
			item.load( itemData )
			self.addItem( item )
		self.dirty = True 


if __name__ == '__main__':
	#info[ 'tag'  ] = _toUpper( assetNode.getTagCache() , uppercase )
	#info[ 'type' ] = _toUpper( assetNode.getType() , uppercase )
	#info[ 'name' ] = _toUpper( assetNode.getName() , uppercase )
	rootGroup = SearchFilterGroup()
	rootGroup.setName( '__root__')
	f = SearchFilter()
	item = SearchFilterItem()
	item.setAlias( 'alias' )
	item.setCiteria( 'good' )
	f.addItem( item )
	rootGroup.addChild( f )
	print(rootGroup.save())