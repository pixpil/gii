import os.path
import logging
import argparse

import gii
from gii.core.project import ProjectException


cli = argparse.ArgumentParser(
	prog = 'gii init',
	description = 'Initialize GII project'
)

cli.add_argument( 'name', 
	type = str, 
	)

def main( argv ):
	args = cli.parse_args( argv[1:] )
	project = gii.Project.get()
	try:
		project.initEmptyProject( os.path.abspath(''), args.name )
	except ProjectException as e:
		logging.error( 'initialization failed: \n%s' % str( e ) )
		return False
	print('done!')
	return True
