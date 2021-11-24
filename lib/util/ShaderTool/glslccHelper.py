import sys
import io
import subprocess
import os
import os.path
import re
import logging
from simple_task_queue import task, Task, WorkerPool
import platform

from gii.core import app

##----------------------------------------------------------------##
@task( 'ConvertGLSL' )
def taslConvertGLSL( options ):
	# if target == 'hlsl':
	# 	options.vert = options.vert + '_hlsl'

	res = convertGLSL( **options )
	if res.returncode != 0:
		err = str( res.stderr, 'utf-8' ).strip()
		if len(err) > 0:
			logging.warning( err )


def convertGLSL( **kw ):
	SYSTEM = platform.system()
	if SYSTEM == 'Windows':
		glslccExe = app.getNativeSupportPath( 'glslcc/glslcc.exe' )
	else:
		glslccExe = app.getNativeSupportPath( 'glslcc/glslcc' )
	
	arglist = [ 
		glslccExe,
		'--silent',
	]

	target = kw.get( 'target', 'glsl' )
	profile = kw.get( 'profile', None )
	defines = kw.get( 'defines', None )

	if target == 'glsl3':
		target = 'glsl'
		profile = '330'

	elif target == 'glsl4':
		target = 'glsl'
		profile = '450'

	elif target == 'hlsl':
		#replace vertex input attributes
		pass

	if kw.get( 'vert' ):
		arglist += [ '--vert=' + kw['vert'] ]

	if kw.get( 'frag' ):
		arglist += [ '--frag=' + kw['frag'] ]

	if kw.get( 'compute' ):
		arglist += [ '--compute=' + kw['compute'] ]

	arglist += [ '--lang=' + target ]
	if profile:
		arglist += [ '--profile=' + profile ]	

	arglist += [ '-o', kw.get( 'output', 'output' ) ]
	
	if defines:
		arglist += [ '--defines={}'.format( ",".join( defines )) ]

	res = subprocess.run( arglist, capture_output  = True )
	return res

name2sem = {
	'position':"POSITION",
	'normal':"NORMAL",
	'color':"COLOR0",
	'uv':"TEXCOORD0",
}

def repl(m):
	sem = name2sem.get( m.group(3), 'TEXCOORD1' )
	return 'layout( location={SEM} ) in {TY} {ID}'.format( SEM = sem, TY = m.group(2), ID = m.group(3))

def generateHLSLInput( src, dst ):
	fs = open( src, 'r' )
	fd = open( dst, 'w' )
	lines = []
	for l in fs.readlines():
		#layout( location=POSITION ) in vec4 position;
		nl = re.sub( 'layout\(\s*location=(\w+)\s*\) in (\w+) (\w+)', repl, l )
		lines.append( nl )
	fd.writelines( lines )
	fs.close()
	fd.close()

def convertGLSLSet( **kw ):
	srcPath = kw.get( 'input', '.' )
	dstPath = kw.get( 'output', srcPath )

	targets = kw.get( 'targets', [ 'msl', 'hlsl', 'glsl3' ] )
	defines = kw.get( 'defines', [] )

	defaultDefines = {
		"none"   : [ "TEX_UP=1.0", "VIEW_Z_SCL=1.0" ],

		"msl"   : [ "TEX_UP=-1.0", "VIEW_Z_SCL=2.0" ],
		"hlsl"  : [ "TEX_UP=-1.0", "VIEW_Z_SCL=2.0" ],
		"glsl3" : [ "TEX_UP=1.0", "VIEW_Z_SCL=1.0"  ],
	}

	options = {}
	def addInputFile( stage, name ):
		filename = srcPath + '/' + name
		if os.path.isfile( filename ):
			options[ stage ] = filename

	addInputFile( 'vert', 'input_vs' )
	addInputFile( 'frag', 'input_fs' )
	addInputFile( 'compute', 'input_comp' )

	generateHLSLInput( srcPath + '/input_vs', srcPath + '/input_vs_hlsl' )

	options[ 'target' ] = 'none'
	options[ 'output' ] = dstPath + '/none'
	options[ 'defines' ] = defaultDefines.get( 'none', [] ) + defines

	#dry run
	res = convertGLSL( **options )
	if res.returncode != 0:
		err = str( res.stderr, 'utf-8' ).strip()
		if len(err) > 0:
			logging.warning( err )
			return False

	with WorkerPool( worker_num = 8 ):
		for target in targets:
			options[ 'target' ] = target
			options[ 'output' ] = dstPath + '/output_' + target
			options[ 'defines' ] = defaultDefines.get( target, [] ) + defines
			execOptions = options.copy()
			if target == 'hlsl':
				execOptions[ 'vert' ] = srcPath + '/input_vs_hlsl'
			Task( 'ConvertGLSL' ).promise( execOptions )
	return True

if __name__ == '__main__':
	convertGLSLSet( input = 'test' )

	# res = convertGLSL( 
	# 	vert = 'test.vert',
	# 	frag = 'test.frag',
	# 	output = 'output_hlsl',
	# 	target = 'hlsl'
	# )

	# print( str( res.stderr, 'utf-8' ) )
	# print( '----' )
	# print( str( res.stdout, 'utf-8' ) )