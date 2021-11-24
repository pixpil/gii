import os.path
import logging
import click

from gii.core import Project, app

@click.command( help = 'generate documentation for current project' )
def run():
	pass

def main( argv ):
	return run( argv[1:], 'gii doc' )
	
