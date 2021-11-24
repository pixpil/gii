import os.path
import logging
import click

from gii.core import Project, app


@click.command( help = 'start gii IDE' )
@click.option( '--stop-other-instance', flag_value = True, default = False,
	help = 'stop other running instance' )
@click.option( '--load-compiled-project', flag_value = True, default = False,
	help = 'load compiled project from current path' )
def run( 
		**kwargs
	):
	app.openProject()
	import sip
	try:
		sip.setapi("QString", 2)
		sip.setapi('QVariant', 2)
	except Exception as e:
		pass
	       
	options = {}
	options[ 'stop_other_instance' ] = kwargs.get( 'stop_other_instance', False )
	options[ 'load_compiled_project'  ] = kwargs.get( 'load_compiled_project', False )

	print('starting gii IDE...')
	print('------------------------')
	
	app.run( **options )		
	
	print('------------------------')
	print('bye!')

def main( argv ):
	return run( argv[1:], 'gii ide' )
	
