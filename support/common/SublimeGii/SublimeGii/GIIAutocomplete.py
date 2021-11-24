# Extends Sublime Text autocompletion to find matches in all open
# files. By default, Sublime only considers words from the current file.
import sublime_plugin
import sublime
import re
import time
from os.path import basename

import sys

from .RemoteCommands import send_to_server

# limits to prevent bogging down the system
MIN_WORD_SIZE = 5
MAX_WORD_SIZE = 30

def _buildREPattern( term ):
	pat = '.*'.join(map(re.escape, term))
	regex = re.compile( pat, re.IGNORECASE )
	return regex

wordRe = re.compile( '^[_a-zA-Z0-9.:!]+$' )
def _isWord( w ):
	return wordRe.match( w )
##----------------------------------------------------------------##
class GIIAutocomplete(sublime_plugin.EventListener):
	def on_query_completions(self, view, prefix, locations):
		if view.match_selector(locations[0], "source.sq_script" ):
			return []
		try:
			result = send_to_server( 'get_scene_auto_completion entity' )
		except Exception as e:
			return []

		pattern = _buildREPattern( prefix )
		if len(prefix) < 3: return []
		if result:
			output = []
			if sys.version_info >= (3,0):
				result = str( result, 'utf-8' )
			for entry in result.split( '\n' ):
				if entry \
				and _isWord( entry ) \
				and ( len( entry ) in range( MIN_WORD_SIZE, MAX_WORD_SIZE)) \
				and pattern.search( entry ):
					item = ( '%s\t(Gii)' % entry, entry )
					output.append( item )
			return output
		else:
			return []

