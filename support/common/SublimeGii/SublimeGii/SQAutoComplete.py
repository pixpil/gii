import sublime_plugin
import sublime
import re
import time
from os.path import basename

import sys

from .RemoteCommands import send_to_server

# limits to prevent bogging down the system
MIN_WORD_SIZE = 5
MAX_WORD_SIZE = 500

def _buildREPattern( term ):
	pat = '.*'.join(map(re.escape, term))
	regex = re.compile( pat, re.IGNORECASE )
	return regex

wordRe = re.compile( '^[_a-zA-Z0-9.:/!]+$' )
def _isWord( w ):
	return True
	# return wordRe.match( w )


def get_preceding_symbol(view, prefix, locations):
	index = locations[0]
	symbol_region = sublime.Region(index - 1 - len(prefix), index - len(prefix))
	symbol = view.substr(symbol_region)
	return symbol

def get_current_line(view, prefix, locations):
	index = locations[ 0 ]
	line = view.line( index )
	return view.substr( line )

def proc_result( prefix, result, incl, excl ):
	inclP = incl and re.compile( incl, re.IGNORECASE )
	exclP = excl and re.compile( excl, re.IGNORECASE )
	pattern = _buildREPattern( prefix )
	if result:
		output = []
		if sys.version_info >= (3,0):
			result = str( result, 'utf-8' )
		for entry in result.split( '\n' ):
			if entry \
			and _isWord( entry ) \
			and ( len( entry ) in range( MIN_WORD_SIZE, MAX_WORD_SIZE)) \
			and ( not inclP or inclP.match( entry ) ) \
			and ( not exclP or not( exclP.match( entry ) ) ) \
			and pattern.search( entry ):
				item = ( '%s\t(SQ)' % entry, entry )
				output.append( item )
		return output
	else:
		return []


def filterInclude( result, expr ):
	output = []
	patt = re.compile( expr, re.IGNORECASE )
	for item in result:
		if patt.match( item ):
			output.append( item )
	return output

def filterExclude( result, expr ):
	output = []
	patt = re.compile( expr, re.IGNORECASE )
	for item in result:
		if not patt.match( item ):
			output.append( item )
	return output

##----------------------------------------------------------------##
class SQAutocomplete(sublime_plugin.EventListener):
	def on_query_completions(self, view, prefix, locations):
		if not view.match_selector(locations[0], "source.sq_script -comment"):
			return []
		
		result = []
		line = get_current_line( view, prefix, locations )
		mode = 'normal'
		minSize = 2
		inclPattern = None
		exclPattern = None

		if re.match( r'\s*scene\s+open\s*', line ):
			mode = 'scene'
			minSize = 1
		if re.match( r'^\s*#group', line ):
			mode = 'group'
			inclPattern = '.*\!\w+$'
			exclPattern = '^\!wasted.*'
			minSize = 1
		if re.match( r'\s*@\s*', line ):
			mode = 'entity'
			minSize = 1
		if len(prefix) < minSize: return []
		try:
			if mode == 'scene':
				result = send_to_server( 'get_scene_auto_completion scene' )
			elif mode == 'entity':
				result = send_to_server( 'get_scene_auto_completion entity' )
			elif mode == 'group':
				result = send_to_server( 'get_scene_auto_completion entity_full' )
			elif mode == 'normal':
				result = send_to_server( 'get_scene_auto_completion entity quest' )

		except Exception as e:
			print( e )
			return []

		return proc_result( prefix, result, inclPattern, exclPattern )
