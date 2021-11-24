import re

def parseMetaTag( text, **options ):
	if isinstance( text, bytes ):
		text = str( text, encoding = options.get( 'encoding', 'utf-8' ) )
	#find head
	headPattern = re.compile('^\s*([@\w_\-\./]+)')
	mo = headPattern.search( text )
	if not mo: return None
	suffix = text[ mo.end(): ]
	baseName = mo.group( 1 ).strip()

	tags = {}
	tagPattern = re.compile( '^\s*:([\w_]+)\s*(\(([\w_\.\-, ]*)\))?' )
	pos = 0
	while True:
		mo = tagPattern.search( suffix, pos )
		if not mo: break
		suffix = suffix[ mo.end(): ]
		tagName, tagArgText = mo.group( 1 ), mo.group( 3 )
		#parse arg
		if tagArgText:
			args = [ n.strip() for n in tagArgText.split( ',' ) ]
		else:
			args = []
		tags[ tagName ] = args
		
	return {
		'name' : baseName,
		'tags' : tags
	}


if __name__ == '__main__':
	print(( parseMetaTag( 'ABCD:xxx(12, 24 ) :fuck() :SHIT' ) ))
