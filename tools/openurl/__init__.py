import os
import logging
import argparse
import socket
# from gii.core import *
from gii.core.InstanceHelper import send_to_server

import syslog


cli = argparse.ArgumentParser(
	prog = 'gii openurl',
	description = 'Send command to current Gii IDE'
)

cli.add_argument( 'url', 
	type = str, 	
	help = 'URL to send'
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
	msg = 'open_url ' + args.url
	#start gii?
	# Define identifier
	syslog.openlog("Gii")
	# Record a message
	syslog.syslog( syslog.LOG_ALERT, "msg:" + msg )

	# try:
	# 	response = send_to_server( host, port, msg, connect_timeout = 1 )

	# except socket.error, e:
	# 	logging.error( 'no Gii IDE running at the host' )
	# 	exit( 1 )
	# exit( 0 )

