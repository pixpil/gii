from xml.etree.ElementTree import ElementTree

groupSep  = '.'
actionSep = ':'

ML_NS = '{http://graphml.graphdrawing.org/xmlns}'
Y_NS  = '{http://www.yworks.com/xml/graphml}'

FSM_NODE_NAME_ANY = 'ANY'

allNodes = {}
allConnections = {}


class FSMParseException( Exception ):
	pass

def getTag( node ):
	tag = node.tag
	index = tag.find( '}' )
	if index != -1:
		return tag[ index+1: ]
	else:
		return tag

class FSMConnection(object):
	def loadFromXML( self, xmlNode ):
		self.id = xmlNode.attrib['id']
		label = xmlNode.find( './/'+ Y_NS +'EdgeLabel' )
		if label is not None:
			self.value = label.text.strip()
			if not self.value:
				self.values = False
		else:
			self.value = False
		self.nodeIdFrom = xmlNode.attrib['source']
		self.nodeIdTo   = xmlNode.attrib['target']
		allConnections[ self.id ] = self

	def findNodes( self ):
		self.nodeFrom = allNodes[ self.nodeIdFrom ]
		self.nodeTo   = allNodes[ self.nodeIdTo ]

class FSMNode(object):
	def __init__( self ):
		self.value = None
		self.fullname = None
		self.funcname = None
		self.connections = []
		self.parent = None
		self.id = ''
		self.name = ''
		self.jump = {}
		self.next = {}

	def isAny( self ):
		return self.name == FSM_NODE_NAME_ANY

	def loadFromXML( self, xmlNode ):
		if xmlNode.tag == ML_NS + 'graphml':
			self.id = 'root'
			self.name = ''
		else:
			self.id = xmlNode.attrib['id']
			label = xmlNode.find( './/'+ Y_NS+'NodeLabel' )
			self.name = label.text		
		allNodes[ self.id ] = self

	def getType( self ):
		return 'state'

	def isGroup( self ):
		return False

	def getName( self ):
		return self.name

	def getFullName( self ):
		if not self.fullname:
			if self.parent:
				pn = self.parent.getFullName()
				if pn:
					self.fullname = pn + groupSep + self.name
				else:
					self.fullname = self.name
			else:
				self.fullname = False
		return self.fullname

	def getFuncName( self ):
		if not self.funcname:
			self.funcname = '_FSM_' + str.replace( self.getFullName(), '.' , '_' )
		return self.funcname


	def __repr__( self ):
		return str(self.getFullName())


class FSMNodeGroup( FSMNode):
	def __init__( self ):
		super( FSMNodeGroup, self ).__init__()
		self.children = []

	def loadFromXML( self, xmlNode ):
		super( FSMNodeGroup, self ).loadFromXML( xmlNode )
		graphNode = xmlNode.find( ML_NS+'graph' )
		self.loadChildrenFromXML( graphNode )

	def isGroup( self ):
		return True

	def getType( self ):
		return 'group'

	def loadChildrenFromXML( self, xmlNode ):
		for childXml in xmlNode:
			tag = getTag( childXml )
			if tag == 'node':
				if childXml.attrib.get( 'yfiles.foldertype' ) == 'group':
					child = FSMNodeGroup()
				else:
					child = FSMNode()
				child.parent = self
				child.loadFromXML( childXml )
				self.children.append( child )

			elif tag == 'edge':
				conn = FSMConnection()
				conn.loadFromXML( childXml )
				self.connections.append( conn )

	def findChild( self, name ):
		for child in self.children:
			if child.name == name:
				return child
		return False

	def getAllChildren( self ):
		result = self.children[:]
		for c in self.children:
			if c.isGroup():
				result += c.getAllChildren()
		return result

class FSMParser():
	def __init__( self ):
		self.output = ''

	def parse( self, fileName ):
		global allNodes
		global allConnections
		allNodes = {}
		allConnections = {}

		tree     = ElementTree()
		rootNode = tree.parse( fileName )
		root     = FSMNodeGroup()
		root.loadFromXML( rootNode )

		self.root = root

		for conn in allConnections.values():
			conn.findNodes()
		##############-
		#generate jump table
		for e in allConnections.values():
			nodeFrom   = e.nodeFrom
			nodeTo     = e.nodeTo
			msg        = e.value
			jump       = nodeFrom.jump
			isGroup    = False
			if nodeTo.isGroup() :
				isGroup = True
				startState = nodeTo.findChild( 'start' )
				if startState :
					nodeTo = startState
				else:
					raise FSMParseException( "no 'start' state for group:" + nodeTo.getFullName() )

			if msg and msg != '' :
				jump[msg]=nodeTo

			else:
				if nodeFrom.isAny():
					raise FSMParseException( "cannot jump from ANY state without msg/condition: " + nodeTo.getFullName() )

				#validate group
				if nodeFrom.isGroup() :
					stopState = nodeFrom.findChild( 'stop' )
					if stopState :
						nodeFrom=stopState					
					else:
						raise FSMParseException( "no 'stop' state for group:" + nodeFrom.getFullName() )
				
				next = nodeFrom.next
				if not next :
					next = {}
					nodeFrom.next = next
				
				next[ nodeTo ] = isGroup and 'group' or 'node'
		
		####
		for node in allNodes.values():
			self.updateJump( node )

		return self.generateCode()
	
	def generateJumpTarget( self, nodeFrom, nodeTo ):
		if nodeTo.isAny():
			raise FSMParseException( "cannot jump into ANY state : <-" + nodeFrom.getFullName() )

		if nodeFrom.parent == nodeTo.parent :
			return ( '"%s"' % nodeTo.getFullName() )

		exits  = ""
		enters = ""
		node = nodeFrom.parent
		while True: #find group crossing path
			found = False
			enters = ""
			node1 = nodeTo.parent
			while node1 != self.root:
				if node1 == node :
					found = True
					break 
				enters = ( '"%s",' % (node1.getFuncName() + '__jumpin' ) ) + enters
				node1 = node1.parent				
			
			if found :
				break
			if node == self.root :
				break 

			exits = exits + ( '"%s",' % ( node.getFuncName() + '__jumpout') )
			node = node.parent	
		
		output = exits + enters
		#format: [ list of func needed nodeTo be called ] + 'next state name'
		return '{ %s"%s" }' % ( output, nodeTo.getFullName() )
	
	#overwrite according nodeTo parent-level-priority
	def updateJump( self, node, src = None ):
		if not node or node == self.root : return 
		if src :
			jump0 = src.jump
			jump  = node.jump
			for msg, target in jump.items():
				jump0[ msg ] = target
		else:
			src=node
		
		return self.updateJump( node.parent, src )

	def processAnyJump( self, anyNode ):
		for msg, target in anyNode.jump.items():
			if target.isAny(): continue
			sources = anyNode.parent.getAllChildren()
			for n in sources:
				if n == self.root: continue
				if n.isAny(): continue
				if n == target: continue
				if msg in n.jump:
					#warn?
					print( 'warning: multiple jump target in "%s" for msg "%s"' % ( n.getFullName(), msg ) )
				else:
					n.jump[ msg ] = target

	def generateCode( self ):
		self.output = ''
	
		def writef( pattern, *args ):
			self.output = self.output + ( pattern % args )
		
		def write(a):
			self.output = self.output+a

		#data code(jumptable) generation
		# file=io.open(fnout,'w')
		# if not file : 
		# 	print("cannot open file nodeTo write")
		# 	os.exit(1)
		# 
		write( 'return ' )
		write( '(function()\n' )
		write( 'nodelist={' )
		write( '\n' )
		for id, n in allNodes.items():
			if n == self.root: continue
			if n.isAny() :continue
			writef( '["%s"]={name="%s",localName="%s",id="%s",type="%s"};',n.getFullName(),n.getFullName(),n.getName(),n.getFuncName(),n.getType() )
			write( '\n' )
		
		write( '};' )
		write( '\n' )

		#ANY jump
		write( '-----------\n' )
		for id, n in allNodes.items():
			if n == self.root: continue
			if not n.isAny() :continue
			self.processAnyJump( n )

		for id, n in allNodes.items():
			if n == self.root: continue
			if n.isAny() :continue
			write( '-----------\n' )
			if len( n.jump ) > 0:
				writef( 'nodelist["%s"].jump={\n',n.getFullName() )
				for msg, target in n.jump.items():
					jumpto = target.getFullName()
					writef( '\t["%s"]=%s;\n', msg, self.generateJumpTarget( n, target ) )
				
				write( '}\n' )
			else:
				writef( 'nodelist["%s"].jump=false\n',n.getFullName() )
			
			if len( n.next ) > 0: #non-conditional jump
				writef( 'nodelist["%s"].next={\n', n.getFullName() )
				count = 0
				for target,targetType in n.next.items():
				# target=n.next
					jumpto = target.getFullName()
					targetName = target.getName()
					#add a symbol for better distinction
					if targetType == 'group' :
						targetName = target.parent.getName()
					writef('["$%s"]=%s;\n',targetName, self.generateJumpTarget( n, target ) ) 
					count += 1
				
				if count == 1 : #only one, give it a 'True' transition
					target = list(n.next.keys())[0]
					jumpto = target.getFullName()
					writef( '[true]=%s;\n', self.generateJumpTarget( n, target ) )
				
				writef( '}\n' )
		
		write( '-----------\n' )
		write( 'return nodelist\n' )
		write( 'end) ()\n' )
		write( '\n' )
		return self.output

def convertGraphMLToFSM( input, output ):
	parser = FSMParser()
	result = parser.parse( input )
	with open( output, 'w' ) as fp:
		fp.write( result )
	return True

if __name__ == '__main__':
	convertGraphMLToFSM( 'test.fsm.graphml', 'fsm_test_output.lua' )
