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


class PortalGraphParser(object):
	def __init__( self ):
		self.nodes = []
		self.edges = []
		self.groupMeta = {}

	def saveToData( self ):
		output = {
			'nodes' : self.nodes,
			'connections' : self.edges,
			'group_meta' : self.groupMeta
		}
		return output

	def saveToJson( self, path ):
		data = self.saveToData()
		trySaveJSON( data, path )

	def parse( self, graphFile ):
		def _getGroupName( node ):
			name = None
			group = node.group
			while group:
				gname = group.getAttr( 'label', None )
				if gname:
					if not name:
						name = gname
					else:
						name = gname + '.' + name
				group = group.group
			return name

		logging.info( 'parsing yed:%s', graphFile )
		graphFile = graphFile.replace( '\\', '/' )
		parser = YEdGraphMLParser()
		g = parser.parse( graphFile )
		#get story node type
		self.nodes = nodes = []
		self.edges = edges = []
		self.groupMeta = groupMeta = {}

		for node in g.nodes.values():
			if node.isGroup(): continue
			name = node.getAttr( 'label', None )
			if not name:
				#TODO: warning
				continue

			groupName = _getGroupName( node )
			if name.startswith( '@' ):
				if groupName:
					groupMeta[ groupName ] = name[1:]
				else:
					logging.warning( 'metadata outside group', name )
				continue

			if groupName:
				fullname = groupName + '.' + name
			else:
				fullname = name

			nodes.append( {
				'name' : name,
				'fullname' : fullname
			} )
			node.fullname = fullname

		for edge in g.edges.values():
			data = edge.getAttr( 'label', False )
			if edge.nodeSrc.isGroup() or edge.nodeDst.isGroup():
				logging.warning( 'connection to Group node:%s->%s', edge.nodeSrc.getAttr('label','???'), edge.nodeDst.getAttr('label','???'))
				continue
			edges.append(
				{
				'a' : edge.nodeSrc.fullname,
				'b' : edge.nodeDst.fullname,
				'data' : data
				}
			)

		return True

		
if __name__ == '__main__':
	parser = PortalGraphParser()
	parser.parse( 'test.portals.graphml' )
	parser.saveToJson( 'test.portal_graph.json' )
	

	