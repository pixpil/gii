import platform
import os
import os.path
import argparse
import logging
import subprocess
import sys
import gii
from gii.core import Project, app

cli = argparse.ArgumentParser(
	prog = 'gii python',
	description = 'run python script with GII module environment'
)

def fixPath( p ):
	if platform.system() == 'Windows':
		return p.replace('/','\\')
	else:
		return p.replace('\\','/')

def addEnvPath( key, entry, prepend = False ):
	if not isinstance( entry, list ):
		entry = [ entry ]
	processedEntry = [ fixPath( p ) for p in entry ]

	try:
		path0 = os.environ[ key ]
		if prepend:
			processedEntry = processedEntry + [ path0 ]
		else:
			processedEntry = [ path0 ] + processedEntry
	except KeyError as e:
		processedEntry = processedEntry
	path1 = os.pathsep.join( processedEntry )
	os.environ[ key ] = path1
	os.putenv( key, path1 )
	return path1


def main( argv ):
	interpreter = sys.executable
	args = argv[1:]
	# if len( args ) < 1:
	# 	print 'no script specified'
	# 	return 0
	cwd = os.getcwd()
	try:
		app.openProject()
		projectExtPath = app.getProject().getBinaryPath( 'python' )
		addEnvPath( 'PYTHONPATH', projectExtPath, True )
		#add project binary into path
	except Exception as ex:
		pass
	
	os.chdir( cwd )
	
	l = [ interpreter ] + args
	if not os.path.exists( interpreter ):
		print('python interperter not found')
		return -1
	
	try:
		code = subprocess.call( l )
	except Exception as ex:
		print(ex)
		return -1

	return code
