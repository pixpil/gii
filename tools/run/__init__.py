import os
import logging
import argparse
import platform
from gii.core import Project, app

cli = argparse.ArgumentParser(
	prog = 'gii run',
	description = 'Run GII desktop Host'
)

cli.add_argument( 'target', 
	type = str, 
	nargs = '?',
	default = 'main',
	help   = 'target name'
	)

cli.add_argument( '-b', 
	dest   = 'build',
	help   = 'Build host before running',
	action = 'store_true',
	default = False
)

cli.add_argument( '--steam', 
	dest   = 'steam_support',
	help   = 'Enable steam support',
	action = 'store_true',
	default = False
)

cli.add_argument( '-t, --build-type', 
	dest   = 'build_type',
	help   = 'Target build type (release|debug)', 
	default = 'debug'
)

cli.add_argument( '-p, --platform',
	dest = 'platform',
	help = 'running on which platform',
	default = 'native'
)

cli.add_argument( '-l', 
	dest   = 'local',
	help   = 'Run from current directory',
	action = 'store_true',
	default = False
)

cli.add_argument( 'arguments',  nargs = '*' )

def main( argv ):
	app.openProject()
	args = cli.parse_args( argv[1:] )	
	
	if args.build:
		buildTargetName = 'host'
		if args.platform != 'native':
			buildTargetName = args.platform

		from gii.core.tools import Build
		buildOptions = {
			'build_type' : args.build_type,
			'targets'    : [ buildTargetName ]
		}
		code = Build.run( **buildOptions )
		if code and code != 0:
			exit( code )

	from gii.core.tools import RunHost
	options = {
		'base' : args.local and 'local' or 'game',
		'platform' : args.platform,
		'steam_support' : args.steam_support
	}
	code = RunHost.run( args.target, *args.arguments, **options )
	exit( code )
