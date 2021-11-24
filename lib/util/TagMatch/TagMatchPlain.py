# -*- coding: utf-8 -*-
import re, fnmatch
from functools import cmp_to_key

##----------------------------------------------------------------##
_REObjectCache = {}
def _wildcard2RO( pattern ):
	ro = _REObjectCache.get( pattern, None )
	if not ro:
		regex = fnmatch.translate( pattern )
		ro = re.compile( regex )
		_REObjectCache[ pattern ] = ro
	return ro

##----------------------------------------------------------------##
class TagMatchNode( object ):
	MODE_ADD        = 0
	MODE_FILTER     = 1
	MODE_FILTERNOT  = 2
	MODE2NAME = {
		MODE_ADD       : "*",
		MODE_FILTER    : "+",
		MODE_FILTERNOT : "-",
	}
	def __init__( self, pattern, matchAll = False ):
		self.parent = None
		self.matchMode = TagMatchNode.MODE_ADD
		self.pattern   = pattern
		self.matchAll  = matchAll

	def getMode( self ):
		return self.matchMode

	def setMode( self, mode ):
		self.matchMode = mode
		if self.parent:
			self.parent.needResort = True

	def getEvaluateTargets( self, data ):
		return []

	def evaluate( self, data ):
		ro = _wildcard2RO( self.pattern )
		if self.matchAll:
			for target in self.getEvaluateTargets( data ):
				if not isinstance( target, str ): return False
				if not ro.match( target ): return False
			return True
		else:
			for target in self.getEvaluateTargets( data ):
				if not isinstance( target, str ): continue
				if ro.match( target ): return True
			return False

	def __repr__( self ):
		opName = TagMatchNode.MODE2NAME.get( self.matchMode, '??' )
		return '<%s>%s'%( opName, str(self.pattern) )

##----------------------------------------------------------------##
class TagMatchRule(object):
	def __init__( self ):
		self.nodes = []
		self.needResort = False
	
	def addNode( self, node, sorting = True ):
		node.parent = self
		self.nodes.append( node )
		self.needResort = True

	def removeNode( self, node ):
		node.parent = None
		self.nodes.remove( node )

	def sortNodes( self ):
		if not self.needResort: return
		def _sortFunc( x, y ):
			m1 = x.getMode()
			m2 = y.getMode()
			r = m1 < m2
			return r

		self.nodes = sorted( self.nodes, key = cmp_to_key( _sortFunc ) )
		self.needResort = False

	def evaluate( self, data ):
		self.sortNodes()
		result = None
		for node in self.nodes:
			r = node.evaluate( data )
			mode = node.getMode()
			if mode == TagMatchNode.MODE_ADD: #will check before FILTER/FITLER_NOT
				if r:
					result = True
			elif mode == TagMatchNode.MODE_FILTER:
				result = result and r
			elif mode == TagMatchNode.MODE_FILTERNOT:
				result = result and ( not r )
			# print'checking against', node, r, result
			if result == False: return False
		return result and True or False


##----------------------------------------------------------------##
class TagMatchNodeFactory( object ):
	def create( self, mode, tag, data, **options ):
		return None

_TagMatchNodeFactories = []
def registerTagMatchFactory( fac, prepend = True ):
	if prepend:
		_TagMatchNodeFactories.insert( 0, fac )
	else:
		_TagMatchNodeFactories.append( fac )

def createTagMatchNode( mode, tag, data, **options ):
	if options.get( 'uppercase', False ):
		data = data.upper()
	for fac in _TagMatchNodeFactories:
		node = fac.create( mode, tag, data, **options )
		if node: return node
	return None

##----------------------------------------------------------------##
_ROSplitPattern = re.compile( '[^\s]+' )
_ROTermPattern  = re.compile( '(?P<op>[~+-]?)((?P<tag>\w*):)?(?P<data>.+)' )
_OP2Mode = {
	""  : TagMatchNode.MODE_ADD,
	"+" : TagMatchNode.MODE_FILTER,
	"-" : TagMatchNode.MODE_FILTERNOT,
	"~" : TagMatchNode.MODE_FILTERNOT,
}

def parseTagMatch( src, **options ):
	rule = TagMatchRule()
	parts = _ROSplitPattern.findall( src ) #split
	for part in parts:
		mo = _ROTermPattern.match( part )
		if not mo: continue
		t = mo.groupdict()
		op   = t.get( 'op'   )
		tag  = t.get( 'tag'  )
		data = t.get( 'data' )
		mode = _OP2Mode.get( op, TagMatchNode.MODE_ADD )
		node = createTagMatchNode( mode, tag, data, **options )
		if node:
			rule.addNode( node )
	return rule


##----------------------------------------------------------------##
class TagMatchNodeTag( TagMatchNode ):
	def getEvaluateTargets( self, data ):
		v = data.get( 'tag' )
		if isinstance( v, list ): return v
		return [ v ]

class TagMatchNodeName( TagMatchNode ):
	def getEvaluateTargets( self, data ):
		v = data.get( 'name' )
		if isinstance( v, list ): return v
		return [ v ]

class TagMatchNodeType( TagMatchNode ):
	def getEvaluateTargets( self, data ):
		v = data.get( 'type' )
		if isinstance( v, list ): return v
		return [ v ]

class TagMatchNodeComponents( TagMatchNode ):
	def getEvaluateTargets( self, data ):
		v = data.get( 'components' )
		if isinstance( v, list ): return v
		return [ v ]

class CommonTagMatchNodeFactory( TagMatchNodeFactory ):
	def create( self, mode, tag, data, **options ):
		node = None
		if tag in ['t', 'tag']:
			node = TagMatchNodeTag( data )
		elif tag in ['T', 'type']:
			node = TagMatchNodeType( data )
		elif tag in ['c', 'com', 'component' ]:
			node = TagMatchNodeComponents( data )
		elif tag in ['n', 'name','', None ]:
			node = TagMatchNodeName( data )
		else:
			return None
		node.setMode( mode )
		return node

registerTagMatchFactory( CommonTagMatchNodeFactory() )

##----------------------------------------------------------------##
##TEST
##---------------------------------------utf-------------------------##	
if __name__ == '__main__':
	# matchNode = bracketTree2TagMatch( 'or( tag(damhill), tag(common) )' )
	pattern = 't:dam* t:common +t:furniture ~T:proto'
	rule = parseTagMatch( pattern )

	testDataSet = [
		{ "tag" : ['damhill', 'furniture'], "type" : "texture" },
		{ "tag" : ['common', 'furniture'],  "type" : "proto" },
		{ "tag" : ['common', 'tool'],       "type" : "texture" },
		{ "tag" : ['damhill', 'NPC'],       "type" : "texture" },
	]
	
	print(rule.nodes)
	print('matching pattern:', pattern)

	for data in testDataSet:
		print(data, rule.evaluate( data ))
