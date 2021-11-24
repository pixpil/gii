# -*- coding: utf-8 -*-
import re
from parsimonious.grammar import Grammar, TokenGrammar
from parsimonious.exceptions import ParseError, IncompleteParseError
import io


InlineDirectivePattern = re.compile( '\$(\w+)(\(([^\(\)]*)\))?')

class SQSyntaxError( Exception ):
	def __init__( self, msg, line ):
		self.msg  = msg
		self.line = line

	def __str__( self ):
		return self.__repr__()

	def __repr__( self ):
		return 'syntax error: %s ( line %d )' % ( self.msg, self.line )

##----------------------------------------------------------------##
class SQNode( object ):
	def __init__( self ):
		self.nodeType = None
		self.children = []
		self.parent   = None
		self.indent   = -1
		self.depth    = 0
		self.lineNumber = 0
		self.lineCount  = 0
		self.name     = None
		self.subnode  = False
		self.inlineDirectives = []

	def addChild( self, n ):
		n.parent = self
		self.children.append( n )
		n.depth	 = self.depth + 1
		return n

	def getFirstChild( self ):
		if self.children:
			return self.children[ 0 ]
		else:
			return None

	def getLastChild( self ):
		if self.children:
			return self.children[ -1 ]
		else:
			return None

	def toJSON( self ):
		data = {
			'type' : self.getType(),
			'children' : [ child.toJSON() for child in self.children ],
			'line' : self.lineNumber,
			'lineCount' : self.lineCount,
		}
		if self.inlineDirectives:
			data[ 'inlineDirectives' ] = self.inlineDirectives
		return data

	def getType( self ):
		return 'SQNode'

##----------------------------------------------------------------##
class SQRootNode( SQNode ):
	def __init__( self ):
		super( SQRootNode, self ).__init__()
		self.tags = []
		self.file = ''

	def getType( self ):
		return 'root'

	def toJSON( self ):
		data = super( SQRootNode, self ).toJSON()
		data[ 'file' ] = self.file
		return data

##----------------------------------------------------------------##
class SQLabelNode( SQNode ):
	def __init__( self ):
		super( SQLabelNode, self ).__init__()
		self.id = ''

	def toJSON( self ):
		data = super( SQLabelNode, self ).toJSON()
		data[ 'id' ] = self.id
		return data

	def getType( self ):
		return 'label'

##----------------------------------------------------------------##
class SQContextNode( SQNode ):
	def __init__( self ):
		super( SQContextNode, self ).__init__()
		self.name = '__context__'
		self.names = []

	def toJSON( self ):
		data = super( SQContextNode, self ).toJSON()
		data[ 'names' ] = self.names
		return data

	def getType( self ):
		return 'context'

##----------------------------------------------------------------##
class SQTagNode( SQNode ):
	def __init__( self ):
		super( SQTagNode, self ).__init__()
		self.tags = []		

	def toJSON( self ):
		data = super( SQTagNode, self ).toJSON()
		data[ 'tags' ] = self.tags
		return data

	def getType( self ):
		return 'tag'

##----------------------------------------------------------------##
class SQDirectiveNode( SQNode ):
	def __init__( self ):
		super( SQDirectiveNode, self ).__init__()
		self.name = ''
		self.value = ''

	def toJSON( self ):
		data = super( SQDirectiveNode, self ).toJSON()
		data[ 'name' ] = self.name
		data[ 'value' ] = self.value
		return data

	def getType( self ):
		return 'directive'

##----------------------------------------------------------------##
class SQActionNode( SQNode ):
	def __init__( self ):
		super( SQActionNode, self ).__init__()
		self.name = ''
		self.args = []

	def toJSON( self ):
		data = super( SQActionNode, self ).toJSON()
		data[ 'name' ] = self.name
		data[ 'args' ] = self.args
		data[ 'sub'  ] = self.subnode
		return data

	def getType( self ):
		return 'action'

##----------------------------------------------------------------##
def _getNodeTexts( n, tt ):
	l = []
	for child in n.children:
		if child.expr_name == tt:
			l.append( child.text )
		else:
			if child.children:
				for cc in child.children:
					l += _getNodeTexts( cc, tt )
	return l

def _getChildNodes( n, tt ):
	result = []
	for child in n.children:
		if child.expr_name == tt:
			result.append( child )
		if child.children:
				for cc in child.children:
					result += _getChildNodes( cc, tt )
	return result

##----------------------------------------------------------------##
class SQScriptCompiler(object):
	LineGrammar = Grammar(
		'''
		line                = comment_line / stmt_line
		comment_line        = ws comment
		stmt_line           = indentation ws stmt ws comment?
		stmt                = directive / context / tag / label / node_switch / node_case / node_default / node_if / node_elseif / node_else / node_long / node
		tag_head            = "#"
		context_head        = "@"
		directive_head      = "$"
		comma               = ","
		context             = context_head identifier ( ws comma? ws identifier )*
		directive           = directive_head identifier ( ws ":" trail )?
		tag                 = &tag_head (tag_item ws)+
		label               = "!" identifier
		node_case           = "case" ws trail
		node_default        = "default"
		node_switch         = "switch" ws trail
		node_assert         = "assert" ws trail
		node_if             = "if" ws trail
		node_elseif         = "elseif" ws trail
		node_else           = "else"
		node_long           = dot? identifier ws ":" trail
		node                = dot? identifier (ws span)*
		tag_item            = tag_head identifier (ws tag_item_param)?
		tag_item_param      = "(" ws tag_item_param_value ws ")"
		tag_item_param_value= ~"[^\)]*"i
		indentation         = ~"\t*"
		identifier          = ~"[A-Z_]+[A-Z0-9_\.]*"i
		ws                  = ~"[\s]*"
		span                = ~"[^\s]+"
		comment             = ~"//.*"
		trail               = ~".*"
		dot                 = ~"\."
		'''
	)


	def __init__( self ):
		pass

	def parseFile( self, path, name = None ):
		fp = io.open( path, 'rt', encoding = 'utf-8' )
		source = fp.read()
		fp.close()
		name = name or path
		return self.parse( source, name )

	def reset( self ):
		self.parsingLongNode = False
		self.rootNode = SQRootNode()
		self.rootNode.name = '__root__'
		self.rootNode.indent = -1
		self.contextNode = self.rootNode
		self.prevNode    = None
		self.lineId      = 0
		self.indentSize  = None

	def parse( self, source, fileName = None ):
		if not fileName:
			fileName = '<noname>'
		self.reset()
		try:
			for line in source.split( '\n' ):
				self.lineId += 1
				if not line.strip(): continue
				self.indentSize  = None
				
				inlineDirectives = None
				commentPos = line.find( '//' )
				if commentPos >=0 :
					comment = line[ commentPos: ]
					line = line[ :commentPos ]
					#find inline directive
					results = InlineDirectivePattern.findall( comment )
					if results:
						inlineDirectives = []
						for entry in results:
							inlineDirectives.append({
									'name' : entry[0],
									'value': entry[2],
								})

				if self.parsingLongNode:
					if self.parseLongNodeLine( line, inlineDirectives ):
						continue
				sublines = line.split( ';' )
				for subline in sublines:
					self.parseStmtLine( subline, inlineDirectives )

		except SQSyntaxError as e:
			raise e

		except ParseError as e:
			e.line_offset = self.lineId - 1
			raise e

		except IncompleteParseError as e:
			e.line_offset = self.lineId - 1
			raise e

		self.rootNode.file = fileName
		return self.rootNode

	def parseLongNodeLine( self, line, inlineDirectives = None ):
		indentSize = 0
		for i, c in enumerate( line ):
			if c == '\t':
				indentSize += 1
			elif c == ' ':
				raise SQSyntaxError( 'space detected in indentation', self.lineId -1 )
			else:
				break
		if indentSize > self.prevNode.indent:
			text = line[ indentSize: ]
			self.prevNode.args.append( text )
			if inlineDirectives: self.prevNode.inlineDirectives += inlineDirectives
			self.prevNode.lineCount = self.prevNode.lineCount + 1
			return True
		else:
			self.parsingLongNode = False
			return False

	def parseStmtLine( self, line, inlineDirectives = None ):
		indentSize = 0
		if not line.strip(): return False
		lineNode = SQScriptCompiler.LineGrammar.parse( line ).children[ 0 ]
		if lineNode.expr_name == 'comment_line':
			return False
		indentNode = lineNode.children[ 0 ]
		stmtNode   = lineNode.children[ 2 ].children[ 0 ]
		if not self.indentSize:
			indentSize = indentNode.end - indentNode.start
			self.indentSize = indentSize
		else:
			indentSize = self.indentSize
		stmtNodeType = stmtNode.expr_name
		
		if self.prevNode:
			if indentSize == self.prevNode.indent:
				pass #do nothing

			elif indentSize > self.contextNode.indent: #INCINDENT
				self.contextNode = self.prevNode

			else:
				while indentSize <= self.contextNode.indent:
					self.contextNode = self.contextNode.parent

		if stmtNodeType == 'node_long':
			self.parsingLongNode = True
		node = self.loadNode( stmtNodeType, stmtNode )
		node.indent = indentSize
		if inlineDirectives: node.inlineDirectives += inlineDirectives
		self.contextNode.addChild( node )
		self.prevNode = node

	def loadNode( self, nodeType, stmtNode ):
		parent      = self.contextNode
		prevSibling = parent.getLastChild() 
		pname       = parent.name
		if pname == 'switch':
			if not nodeType in ( 'node_case', 'node_default' ):
				raise SQSyntaxError( '"switch" only accepts "case" or "default" as child node, given:' + nodeType, self.lineId -1 )

		if nodeType == 'node':
			node = SQActionNode()
			if stmtNode.children[0].text == '.':
				if pname == '__root__':
					raise SQSyntaxError( 'invalid subnode usage', self.lineId -1 )
				else:
					node.name = pname + '.' + _getNodeTexts( stmtNode, 'identifier' )[0]
			else:
				node.name = _getNodeTexts( stmtNode, 'identifier' )[0]
			node.args += _getNodeTexts( stmtNode, 'span' )

		elif nodeType == 'node_long':
			node = SQActionNode()
			if stmtNode.children[0].text == '.':
				if pname == '__root__':
					raise SQSyntaxError( 'invalid subnode usage', self.lineId -1 )
				else:
					node.name = pname + '.' + _getNodeTexts( stmtNode, 'identifier' )[0]
			else:
				node.name = _getNodeTexts( stmtNode, 'identifier' )[0]
			trails = _getNodeTexts( stmtNode, 'trail' )
			if trails and trails[0]:
				node.args += trails

		elif nodeType == 'directive':
			node = SQDirectiveNode()
			node.name = _getNodeTexts( stmtNode, 'identifier' )[0]
			trails = _getNodeTexts( stmtNode, 'trail' )
			if trails:
				node.value = trails[0]
			else:
				node.value = None

		elif nodeType == 'context':
			node = SQContextNode()
			node.names = _getNodeTexts( stmtNode, 'identifier' )

		elif nodeType == 'tag':
			node = SQTagNode()
			tags = []
			for tagItemNode in _getChildNodes( stmtNode, 'tag_item' ):
				tagName = _getNodeTexts( tagItemNode, 'identifier' )[0]
				tagParam = None
				params = _getChildNodes( tagItemNode, 'tag_item_param' )
				if params:
					tagParam = _getNodeTexts( params[ 0 ], 'tag_item_param_value' )[ 0 ]
					tagParam = tagParam.strip()
				tags.append( (tagName, tagParam) )

			node.tags = tags

		elif nodeType == 'label':
			node = SQLabelNode()
			node.id = _getNodeTexts( stmtNode, 'identifier' )[0]
		
		elif nodeType == 'node_assert':
			node = SQActionNode()
			node.name = 'assert'
			trails = _getNodeTexts( stmtNode, 'trail' )
			if trails and trails[0]:
				node.args += trails
			else:
				raise SQSyntaxError( '"assert" without condition expr', self.lineId -1 )

		elif nodeType == 'node_if':
			node = SQActionNode()
			node.name = 'if'
			trails = _getNodeTexts( stmtNode, 'trail' )
			if trails and trails[0]:
				node.args += trails
			else:
				raise SQSyntaxError( '"if" without condition expr', self.lineId -1 )

		elif nodeType == 'node_elseif':
			if prevSibling and prevSibling.name in ( 'if', 'elseif' ):
				node = SQActionNode()
				node.name = 'elseif'
				trails = _getNodeTexts( stmtNode, 'trail' )
				if trails and trails[0]:
					node.args += trails
				else:
					raise SQSyntaxError( '"elseif" without condition expr', self.lineId -1 )
			else:
				raise SQSyntaxError( '"elseif" without "if"', self.lineId -1 )

		elif nodeType == 'node_else':
			if prevSibling and prevSibling.name in ( 'if', 'elseif' ):
				node = SQActionNode()
				node.name = 'else'
			else:
				raise SQSyntaxError( '"else" without "if"', self.lineId -1 )

		elif nodeType == 'node_switch':
			node = SQActionNode()
			node.name = 'switch'
			trails = _getNodeTexts( stmtNode, 'trail' )
			if trails and trails[0]:
				node.args += trails
			else:
				raise SQSyntaxError( '"switch" without condition variable', self.lineId -1 )

		elif nodeType == 'node_case':
			if parent.name == 'switch':
				node = SQActionNode()
				node.name = 'case'
				trails = _getNodeTexts( stmtNode, 'trail' )
				if trails and trails[0]:
					node.args += trails
				else:
					raise SQSyntaxError( '"case" without condition expr', self.lineId -1 )
			else:
				raise SQSyntaxError( '"case" without "switch"', self.lineId -1 )

		elif nodeType == 'node_default':
			if parent.name == 'switch':
				node = SQActionNode()
				node.name = 'default'
			else:
				raise SQSyntaxError( '"default" without "switch"', self.lineId -1 )

		node.lineNumber = self.lineId
		node.lineCount = 1
		return node

__all__ = [
	'SQNode',
	'SQLabelNode',
	'SQContextNode',
	'SQTagNode',
	'SQActionNode',
	'SQScriptCompiler',
]


if __name__ == '__main__':
	text = '''
//sqscript
!start
@Jasper,John Sam,Recard,Charlie
	run;go;die
	anim loop run; wait 0.5
	questlog
		.name 你好
		.desc 我不知道
	on interaction_talk //#sound(ra)
		if talked
			#title(!VisitingDay/!Crisis 111) #large
			#big #small
			$id:100
			$deprectaed
			say: Talked //$music_play( John, here ) $xxx $ddd( ) $goo() 
				nice
			say: don't //comment on this line
		else
			say: Hello
			
		switch talk_count
			case 1
				do

'''
	
	text2 = '''
//sqscript
questlog
	.name 你好
	.desc 我不知道
'''

	import logging
	import json

	def saveJSON( data, path, **option ):
		outputString = json.dumps( data , 
				indent    = option.get( 'indent' ,2 ),
				sort_keys = option.get( 'sort_keys', True ),
				ensure_ascii=False
			).encode('utf-8')
		fp = open( path, 'w' )
		fp.write( outputString )
		fp.close()
		return True

	node = SQScriptCompiler().parse( text )
	data = node.toJSON()

	saveJSON( data, 'test.json' )

