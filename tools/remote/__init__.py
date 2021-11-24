import os
import sys
import logging
import argparse
import socket
import locale
# from gii.core import *
from gii.core.InstanceHelper import send_to_server, start_rpc_server, send_to_rpc_server

cli = argparse.ArgumentParser(
	prog = 'gii remote',
	description = 'Execute command on remote Gii server'
)

cli.add_argument( '--server', 
	dest    = 'server_mode',
	help    = 'start Gii remote server.',
	default = False,
	action  = 'store_true'
)

cli.add_argument( '--encoding', 
	dest    = 'encoding',
	help    = 'specify stdio encoding',
	type    = str,
)

cli.add_argument( '--host',
	dest   = 'host',
	help   = 'target Gii remote server address',
	type   = str,
	default = '127.0.0.1'
)

cli.add_argument( 'messages', 
	type = str, 	
	nargs = argparse.REMAINDER,
	help = 'Message to send along with the command'
	)

def main( argv ):
	args, unknown = cli.parse_known_args( argv[1:] )	
	host = args.host
	port = None

	if args.server_mode:

		options = {
			'encoding' : args.encoding or locale.getpreferredencoding()
		}
		server = start_rpc_server( **options )
		
	else:		
		options = {
			'host': args.host,
			'messages': args.messages,
		}
		if not send_to_rpc_server( **options ):
			exit( 1 )
		else:
			exit( 0 )
		