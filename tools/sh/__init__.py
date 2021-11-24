import os
import os.path
import argparse
import logging
import subprocess

from gii.core import Project, app

cli = argparse.ArgumentParser(
	prog = 'gii sh',
	description = 'run shell script from env/shell path'
)

def main( argv ):
	try:
		proj = app.openProject()
	except Exception as ex:
		print(ex)
		return -1

	projPath  = proj.getPath()
	shellPath = projPath + '/env/shell'
	args = argv[1:]
	if len( args ) < 1:
		print('no script specified')
		return 0
	
	execName = shellPath + '/' + args[0]
	l = [ execName ] + args[ 1: ]
	if not os.path.exists( execName ):
		print('script not found')
		return -1

	try:
		code = subprocess.call( l, cwd = projPath )
	except Exception as ex:
		print(ex)
		return -1

	return code
