import logging
import os
import sarge
import time
import platform

from gii.core import Project, app

_terminating = False

##----------------------------------------------------------------##
def getExecutable( platformName ):
	project = app.getProject()
	executableName = 'moai'

	if platformName == 'native':
		if platform.system() == 'Darwin':
			platformName = 'osx'
		elif platform.system() == 'Windows':
			platformName = 'win' 
		elif platform.system() == 'Linux':
			platformName = 'linux' 

	if platformName == 'win':
		executableName = 'moai.exe'
	elif platformName == 'ns-win':
		executableName = 'moai.exe'
	elif platformName in ( 'linux', 'osx' ):
		executableName = 'moai'
	else:
		raise Exception( 'unknown target platform:' + platformName )

	path = project.getBinaryPath( '%s/%s' % ( platformName, executableName ) )

	#check if excutable exists
	if os.path.isfile( path ):
		return path
	else:
		raise Exception( 'No executable found:' + path )


def terminate():
	global _terminating
	_terminating = True

def run( target, *args, **options ):
	global _terminating
	_terminating = False
	project = app.getProject()
	assert project.isLoaded()
	platformName = options.get( 'platform', app.getPlatformName() )

	try:
		executable = getExecutable( platformName )
	except Exception as e:
		logging.exception( e )
		return 1

	arglist = [
		executable
	]


	defaultSteamSupport = False

	base = options.get( 'base', 'game' )
	
	if base == 'game':
		defaultSteamSupport = True
		os.chdir( project.getBasePath() )
		script = 'game/%s.lua' % target

	elif base == 'local':
		os.chdir( os.environ[ 'GII_CWD' ] )
		script = target

	else:
		return False

	# if options.get( 'steam_support', defaultSteamSupport ):
	# 	arglist += [ '--steam' ]

	arglist += [
		'-f',
		script
	]
	
	if args:
		arglist += [ '-p' ]
		arglist += args
		
	returncode = 0
	try:
		pipeline = sarge.run( arglist, async_ = True )
		while True:
			time.sleep( 0.05 )
			command = pipeline.commands[0]
			returncode = command.poll()
			if returncode != None:
				break
			if _terminating:
				command.kill()
				returncode = -1
				break
		# pipeline.close()
		# returncode = command.poll()
	except Exception as e:
		logging.error( 'cannot start host: %s ' % e)
		return 1
	return returncode
