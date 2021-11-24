import re
'''
A dead simple ( Lisp like ) bracketed tree parser
TODO: bracket matching
'''

##----------------------------------------------------------------##
def strToNum( v ):
	try:
		number_float = float(v)
		number_int = int(v)
		return number_int if number_float == number_int else number_float
	except ValueError:
		return v


##----------------------------------------------------------------##
class BracketTreeNode( object ):
	def __init__( self, parent ):
		self.parent = parent
		self.tag    = None
		self.value  = None
		self.children = None
		
	def initValue( self, v ):
		self.value = strToNum( v )

	def initObject( self, tag, children ):
		self.tag = tag
		self.children = children

	def isValue( self ):
		return not( self.value is None )
	
	def isObject( self ):
		return not( self.tag is None )

	def getValue( self ):
		return self.value

	def getChildren( self ):
		return self.children

	def getTag( self ):
		return self.tag
	
	def getParent( self ):
		return self.parent

	def getChild( self, idx ):
		if not self.children: return None
		return self.children[ idx ]

	def addChild( self, node ):
		self.children.append( node )
		node.parent = self
		return node

	def getChildValue( self, idx ):
		return self.getChild( idx ).getValue()

	def toData( self ):
		if self.isValue():
			return self.getValue()
		else:
			return {
				'tag': self.tag,
				'children': [ child.toData() for child in self.children ]
			}

##----------------------------------------------------------------##
_BracketRO = re.compile( '[,()]' )
class BracketTreeParser(object):
	def __init__( self ):
		self.nodeStack = []
		self.pointer = 0
		self.rootNode = BracketTreeNode( None )
		self.rootNode.initObject( '__root__', [] )
		self.currentNode = self.rootNode

	def pushTagNode( self, tag, pos ):
		node = BracketTreeNode( self.currentNode )
		node.initObject( tag, [] )
		self.currentNode.addChild( node )
		self.nodeStack.append( node )
		self.currentNode = node

	def popTagNode( self, pos ):
		if self.rootNode == self.currentNode:
			raise Exception( 'unexpected bracket at %d' % pos )
		node = self.nodeStack.pop()
		self.currentNode = node.parent

	def pushValueNode( self, content, pos ):
		node = BracketTreeNode( self.currentNode )
		node.initValue( content )
		self.currentNode.addChild( node )

	def parse( self, src ):
		p = 0
		while True:
			mo = _BracketRO.search( src, p )
			if not mo: break
			ch = mo.group(0)
			pos = mo.start()
			span = src[ p:pos ]
			span = span.strip()

			if ch == '(':
				self.pushTagNode( span, pos )

			elif ch == ')':
				if len(span) > 0:
					self.pushValueNode( span, pos )
				self.popTagNode( pos )

			elif ch == ',':
				if len(span) > 0:
					self.pushValueNode( span, pos )

			p = mo.end()

		return self.rootNode


##----------------------------------------------------------------##
def parseBracketTree( src ):
	parser = BracketTreeParser()
	node = parser.parse( src )
	return node

##----------------------------------------------------------------##
##TEST
##----------------------------------------------------------------##	
if __name__ == '__main__':
	# print parseBracketTree( 'and( tag( damhill ), tag( common ) )' ).toData()
	# print parseBracketTree( 'or( tag(damhill), tag(common) )' ).toData()
	# print parseBracketTree( 'and( or( tag(damhill), tag(common) ), tag(furniture) )' ).toData()
	x = 'and( or( tag(damhill+1), tag(common) ), tag(furniture) )'
	result = parseBracketTree( x )
	print(result.toData())