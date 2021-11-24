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
		).encode('utf-8')
	fp = open( path, 'w' )
	fp.write( outputString )
	fp.close()
	return True

def trySaveJSON( data, path, dataName = None, **option ):
	try:
		saveJSON( data, path, **option )
		return True
	except Exception as e:
		logging.warn( 'failed to save %s: %s' % ( dataName or 'JSON', path ) )
		logging.exception( e )
		return False


class StoryGraphParser(object):
	def __init__( self ):
		self.rootScope = [] 
		self.nodes = []
		self.edges = []
		self.parsed = {}

	def parse( self, filePath ):
		try:
			self.parseGraph( filePath )

		except Exception as e:
			print(filePath)
			print('error parsing story graph', e)
			logging.exception( e )
			return False
		return True

	def saveScopeData( self, scope ):
		output = []
		for node in scope:
			nodeData = {
				'id'    : node.id,
				'fullId': node.fullId,
				'type'  : node.storyNodeType or False,
				'text'  : node.getAttr( 'label', '' ),
				'group' : node.group and node.group.fullId or False,
				'visual': {} #TODO: visual
			}
			if node.storyNodeType in [ 'GROUP', 'REF' ]:
				subScopeData = self.saveScopeData( node.children )
				nodeData['children'] = subScopeData

			output.append( nodeData )
		return output

	def saveToData( self ):
		rootScopeData = self.saveScopeData( self.rootScope )
		edgeDatas = []
		for edge in self.edges:
			edgeType = 'NORMAL'
			#___YED has some issue keeping meta data from edge template, we have use style
			if edge.getAttr( 'color' ) == '#FF0000':
				edgeType = 'NOT'
			elif edge.getAttr( 'style' ) == 'dashed':
				edgeType = 'COMMENT'
			# if edge.getAttr( 'description' ) == 'COMMENT':
			# 	edgeType = 'COMMENT'
			# elif edge.getAttr( 'description' ) == 'NOT':
			# 	edgeType = 'NOT'

			edgeData = {
				'src':    edge.nodeSrc.fullId,
				'dst':    edge.nodeDst.fullId,
				'text':   edge.getAttr( 'label', '' ),
				'type':   edgeType,
				'visual': {} #TODO: visual
			}
			edgeDatas.append( edgeData )
		output = {
			'rootNodes' : rootScopeData,
			'edges'     : edgeDatas
		}
		return output

	def saveToJson( self, path ):
		data = self.saveToData()
		trySaveJSON( data, path )

	def parseGraph( self, graphFile ):
		graphFile = graphFile.replace( '\\', '/' )
		parser = YEdGraphMLParser()
		g = parser.parse( graphFile )
		#get story node type

		for node in list(g.nodes.values()):
			if not node.group:
				self.rootScope.append( node )

			nodeDesc = node.getAttr( 'description' )
			storyNodeType = None
			if nodeDesc:
				mo = _DataTypeMatch.match( nodeDesc )
			else:
				mo = None
			if mo :
				storyNodeType = mo.groups()[0]
				node.setAttr( 'story-node-type', storyNodeType )
				# if storyNodeType == 'REF':
				# 	url = graphDir + '/' + node.getAttr('url')
				# 	if self.parsed.has_key( url ):
				# 		print 'ERROR: duplicated sub graph reference', url
				# 	else:
				# 		node.children = []
				# 		self.parsed[ url ] = True
				# 		self.parseGraph( url, rootFolder, node )

			if not storyNodeType and isinstance( node, YEdGraphGroup ):
				node.setAttr( 'story-node-type', 'GROUP' )
				storyNodeType = 'GROUP'
			if not storyNodeType:
				print('WARNING: unknown story node type', graphFile, node.id, node.getAttr( 'label' ))

			node.fullId = node.id
			node.storyNodeType = storyNodeType
			self.nodes.append( node )

		for edge in list(g.edges.values()):
			self.edges.append( edge )

		
if __name__ == '__main__':
	parser = StoryGraphParser()
	parser.parse( 'basic.story' )
	parser.saveToJson( 'test.story.json' )
	

	