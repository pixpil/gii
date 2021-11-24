import os
import logging
import argparse
from gii.core import Project, app
from gii.core.tools import Build


cli = argparse.ArgumentParser(
	prog = 'gii path',
	description = 'Retrieve project path information'
)

def main( argv ):
	proj = app.openProject()
	args = cli.parse_args( argv[1:] )	
	print(proj.getPath())
	exit( 0 )
