import os
import sys
import logging
import subprocess
import platform
import multiprocessing


from gii.core import Project, app

# WAF_NAME = 'waf-1.9.7'
WAF_NAME = 'waf-2.0.19'

def run( **option ):
	FNULL = open(os.devnull, 'wb')
	project = app.getProject()
	assert project.isLoaded()
	os.chdir( project.getHostPath() )
	# if option.get( 'clean-bin', False ):
	# 	if sys.platform == 'darwin':
	# 		pass	
	# 	else:
	# 		pass
	# 		#TODO	
	# 	return 0
	buildEnv = os.environ.copy()
	globalBuildEnv = app.getUserSetting( 'build_env', None )
	if globalBuildEnv:
		for k, v in globalBuildEnv.items():
			buildEnv[ k ] = v
	projectBuildEnv = project.getUserSetting( 'build_env', None )
	if projectBuildEnv:
		for k, v in projectBuildEnv.items():
			buildEnv[ k ] = v

	buildEnv[ 'JOBS' ] = '8'
	WAFCmd = [ app.getPythonPath(), app.getPath( 'support/common/%s/waf' % WAF_NAME ) ]
	def callWAF( cmd, *args, **kwargs ):
		kwargs[ "env" ] = buildEnv
		if isinstance( cmd, list ):
			arglist = WAFCmd + cmd + list( args )
		else:
			arglist = WAFCmd + [ cmd ] + list( args )
		return subprocess.call( arglist, **kwargs )

	#check configure
	# code = callWAF( 'list', stdout = FNULL, stderr = FNULL )
	# if code != 0:
	# 	code = callWAF( 'configure' )
	# 	if code != 0:
	# 		logging.error( 'cannot configure building ' )
	# 		return -1

	#main body
	building = True
	cmds = []
	args = []
	
	#misc settings
	if option.get( 'verbose', False ):
		args.append( '-v' )

	args.append( '-j%d' % max( 2, multiprocessing.cpu_count()) )
	#configure
	if option.get( 'configure', False ):
		return callWAF( 'configure', *args )

	#commands
	if option.get( 'clean', False ):
		cmds += [ 'clean' ]

	if option.get( 'dist', False ):
		cmds += [ 'dist' ]

	if option.get( 'project', False ):
		cmds += [ 'project' ]

	else:
		if option.get( 'build', True ):
			cmds += [ 'build' ]

		if option.get( 'install', True ):
			cmds += [ 'install' ]


	targets = option.get( 'targets', [ 'host' ] )		

	if isinstance( targets, str ):
		targets = [ targets ]

	#expand native
	if 'host' in targets:
		targets.remove( 'host' )
		if platform.system() == 'Darwin':
			if not ( 'osx' in targets ):
				targets.append( 'osx' )
				
		elif platform.system() == 'Windows':
			if not ( 'win' in targets ):
				targets.append( 'win' )

		elif platform.system() == 'Linux':
			if not ( 'linux' in targets ):
				targets.append( 'linux' )

	if 'native' in targets:
		targets.remove( 'native' )
		if platform.system() == 'Darwin':
			if not ( 'osx' in targets ):
				targets.append( 'osx' )
			if not ( 'python' in targets ):
				targets.append( 'python' )
				
		elif platform.system() == 'Windows':
			if not ( 'win' in targets ):
				targets.append( 'win' )
			if not ( 'python' in targets ):
				targets.append( 'python' )

		elif platform.system() == 'Linux':
			if not ( 'linux' in targets ):
				targets.append( 'linux' )

	build_type = option.get( 'build_type', 'debug' )

	cmdList = []
	for target in targets:
		contextName = '%s-%s' % ( target, build_type )
		suffix = '-' + contextName
		for cmd in cmds:
			cmdList += [ cmd + suffix ]
	print( cmdList )
	return callWAF( cmdList, *args )
