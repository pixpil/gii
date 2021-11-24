import os.path
import logging
import click

from gii import app, Project

@click.command()
@click.option( '--target', flag_value = True, help = 'help me' )
def start( target ):
	print('TODO: deploy!!!!')
	print('target is:', target)

def main( argv ):
	# app.openProject()
	return start( argv[1:], 'gii deploy' )
	