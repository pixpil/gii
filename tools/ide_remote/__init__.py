import os
import logging
import argparse
import socket
# from gii.core import *
from gii.core.InstanceHelper import send_to_server

cli = argparse.ArgumentParser(
	prog = 'gii remote',
	description = 'Send command to current Gii IDE'
)

cli.add_argument( 'cmd', 
	type = str, 	
	help = 'Command to send'
	)

cli.add_argument( 'args', 
	type = str, 	
	nargs = '*',
	help = 'Arguments to send along with the command'
	)

cli.add_argument( '--host',
	dest   = 'host',
	help   = 'IP of host running Gii IDE ',
	type   = str,
	default = '127.0.0.1'
	)

def main( argv ):
	args = cli.parse_args( argv[1:] )	
	host = args.host
	port = None
	msg = ' '.join( args.args )
	msg = args.cmd + ' ' + msg
	try:
		response = send_to_server( host, port, msg )
		print(response)
	except socket.error:
		logging.error( 'no Gii IDE running at the host' )
		exit( 1 )
	exit( 0 )

