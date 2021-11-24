from util.YEd import *

import os.path
import re
import json
import logging

_ROOT_ML = '_root.graphml'

_DataTypeMatch = re.compile('type\s*=\s*(\w+)')


def saveJSON( data, path, **option ):
	outputString = json.dumps( data , 
			indent    = option.get( 'indent' ,2 ),
			sort_keys = option.get( 'sort_keys', True ),
			ensure_ascii=False
		)
	with open( path, 'w', encoding = 'utf-8' ) as fp:
		fp.write( outputString )
	return True

def trySaveJSON( data, path, dataName = None, **option ):
	try:
		saveJSON( data, path, **option )
		return True
	except Exception as e:
		logging.warn( 'failed to save %s: %s' % ( dataName or 'JSON', path ) )
		logging.exception( e )
		return False


class QuestSchemeParser(object):
	def __init__( self ):
		self.nodes = []
		self.edges = []

	def saveToData( self ):
		output = {
			'nodes' : self.nodes,
			'connections' : self.edges
		}
		return output

	def saveToJson( self, path ):
		data = self.saveToData()
		trySaveJSON( data, path )

	def parse( self, graphFile ):
		graphFile = graphFile.replace( '\\', '/' )
		parser = YEdGraphMLParser()
		g = parser.parse( graphFile )
		#get story node type
		nodeDataMap = {}
		self.nodes = nodes = []
		self.edges = edges = []
		def _processNode( node ):
			name = node.getAttr( 'label', None )
			fullname = name
			group = node.group
			while group:
				gname = group.getAttr( 'label', None )
				if gname:
					fullname = gname + '.' + fullname
				group = group.group
			node.fullname = fullname
			
			if node.getAttr( 'border-style' )	== 'dotted':
				nodeType = 'comment'

			elif name == 'AND':
				nodeType = 'and'

			elif name == 'ABORT':
				nodeType = 'abort'

			elif name == 'RESET':
				nodeType = 'reset'

			elif name == 'RESUME':
				nodeType = 'resume'

			elif name == 'PAUSE':
				nodeType = 'pause'

			else:
				if name and name.startswith( '//' ):
					nodeType = 'comment'
				else:
					nodeType = 'node'

			nodeData = {
				'id'   : node.id,
				'name' : name,
				'fullname' : fullname,
				'type' : nodeType,
				'children' : [],
			}
			if nodeType == 'comment': return False
			if node.isGroup():
				nodeData[ 'children' ] = childrenData = []
				for child in node.children:
					data = _processNode( child )
					if data:
						childrenData.append( data )
			nodeDataMap[ node.id ] = nodeData
			return nodeData

		def _processEdge( edge ):
			cond = edge.getAttr( 'label', False )
			color = edge.getAttr( 'line-color' )
			style = edge.getAttr( 'line-style' )
			if cond and cond.startswith( '//' ): 
				edgeType = 'comment'
			elif style == 'dashed':
				edgeType = 'spawn'
			else:
				edgeType = 'move'

			if edgeType == 'comment': return False

			dataFrom = nodeDataMap[ edge.nodeSrc.id ]
			dataTo   = nodeDataMap[ edge.nodeDst.id ]
			typeFrom = dataFrom[ 'type' ] 
			typeTo   = dataTo[ 'type' ]
			if typeFrom != 'node' and	typeTo != 'node':
				print(dataFrom['name'], '->', dataTo['name'])
				logging.warn( 'invalid connection between two command nodes' )
				return False

			if typeFrom != 'node' and edgeType != 'move':
				print(dataFrom['name'], '->', dataTo['name'])
				logging.warn( 'invalid SPAWN connection from command node' )
				return False

			edgeData ={
				'from' : edge.nodeSrc.id,
				'to'   : edge.nodeDst.id,
				'cond' : cond,
				'type' : edgeType
				}
			return edgeData

		###
		for node in g.rootNodes.values():
			data = _processNode( node )
			if data:
				nodes.append( data )

		for edge in g.edges.values():
			data = _processEdge( edge )
			if data:
				edges.append( data )

		return True

		
if __name__ == '__main__':
	parser = QuestSchemeParser()
	parser.parse( 'test.quest.graphml' )
	parser.saveToJson( 'test.quest_scheme.json' )
	

	