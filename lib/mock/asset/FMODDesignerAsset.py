import os.path
import logging
import subprocess
import shutil

from gii.core import AssetManager, AssetLibrary, getProjectPath, app
# import xml.parsers.expat
import xml.etree.ElementTree

##----------------------------------------------------------------##

_FMOD_DESIGNER_CL = 'fmod_designercl'
_SETTING_KEY_FMOD_DESIGNER_PATH = 'fmod_designer_path'

##----------------------------------------------------------------##
def _parseFDPGroup( node ):
	groups = {}
	for groupItem in node.iterfind( 'eventgroup' ):
		name = groupItem.find('name').text
		g = {}
		groups[ name ] = g
		events = {}
		g['events'] = events
		for eventItem in groupItem.iterfind( 'event' ):
			eventName = eventItem.find('name').text
			events[ eventName ] = {
				'mode'    : eventItem.find('mode').text,
				'oneshot' : eventItem.find('oneshot').text,
			}
		for simpleEventItem in groupItem.iterfind( 'simpleevent' ):
			eventItem = simpleEventItem.find('event')
			eventName = eventItem.find('name').text
			events[ eventName ] = {
				'mode'    : eventItem.find('mode').text,
				'oneshot' : eventItem.find('oneshot').text,
			}
		g['groups'] = _parseFDPGroup( groupItem )
	return groups

def parseFDP( path ):
	try:
		fp = open( path, 'r' )
		data = fp.read()
		fp.close()
	except Exception as e :
		return False
	root = xml.etree.ElementTree.fromstring( data )
	groups = _parseFDPGroup( root )

	banks = {}
	for bankItem in root.iterfind( 'soundbank' ):
		name = bankItem.find('name').text
		banks[ name ] = {}

	return {
		'groups' : groups,
		'banks'  : banks
	}

	
##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


class FmodAssetManager(AssetManager):
	def getName(self):
		return 'asset_manager.fmod'

	def acceptAssetFile(self, filepath):
		if not os.path.isfile(filepath): return False		
		name, ext = os.path.splitext(filepath)
		if not ext in ['.fdp']: return False
		return True

	def _traverseGroup( self, node, data ):
		groups = data.get( 'groups', None )
		if groups:
			for name, group in list(groups.items()):
				groupNode = node.affirmChildNode( name, 'fmod_group', manager = self )
				groupNode.groupType = 'package'
				events    = group['events']
				for name, event in list(events.items()):
					eventNode = groupNode.affirmChildNode( name, 'fmod_event', manager = self )
				self._traverseGroup( groupNode, group )

	def importAsset(self, node, reload = False ):
		if node.isVirtual(): return
		
		node.assetType = 'fmod_project'
		node.groupType = 'package'
		
		project = parseFDP( node.getAbsFilePath() )

		fmodDesignerPath = app.getUserSetting( _SETTING_KEY_FMOD_DESIGNER_PATH )
		output = node.getCacheFile( 'export', is_dir = True )
		node.setObjectFile( 'export', output )
		# target = '-ios'
		target = '-pc'
		arglist = [ 
				fmodDesignerPath + '/' + _FMOD_DESIGNER_CL,
				target,
				'-p',
				'-b', output,
				node.getAbsFilePath()
			]
		try:
			subprocess.call( arglist )
		except Exception as e:
			logging.exception( e )

		#TODO:check bank files( delete banks unavailable )
		banks = project['banks']
		for name, bank in list(banks.items()):
			pass

		self._traverseGroup( node, project )
		return True

FmodAssetManager().register()

AssetLibrary.get().setAssetIcon( 'fmod_project',   'fmod' )
AssetLibrary.get().setAssetIcon( 'fmod_group',     'fmod_group' )
AssetLibrary.get().setAssetIcon( 'fmod_event',     'audio' )


