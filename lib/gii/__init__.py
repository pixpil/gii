from .core import *

##----------------------------------------------------------------##
def startup():
	import platform
	if platform.system() == 'Windows':
		import ctypes
		myappid = 'com.pixpil.gii:0.5'
		ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

	startupTool()

##----------------------------------------------------------------##
def startSubProcess( argv, **options ):
	from subprocess import PIPE, Popen
	from threading  import Thread
	import sys
	import os

	try:
		from queue import Queue, Empty
	except ImportError:
		from queue import Queue, Empty  # python 2.x

	defaultEncoding = os.environ[ 'GII_RPC_STDIO_ENCODING' ]
	encoding = options.get( 'encoding', defaultEncoding )
	def enqueue_output( out, queue, cc ):
		for line in iter(out.readline, b''):
			if cc: cc.write( line.decode( encoding ) )
			if encoding:
				try:
					line = line.decode( encoding )
				except Exception as e:
					pass
			queue.put(line)
		out.close()

	ON_POSIX = 'posix' in sys.builtin_module_names

	print( 'start gii sub process ( %s )' % ( encoding or 'no-encoding' ) )
	executable = sys.executable
	binPath = os.environ.get( 'GII_BASE_PATH' )  + '/gii_bin.py'
	argv = list( argv )
	cmd = [ executable, binPath ] + argv
	proc = Popen( cmd, stdout=PIPE, stderr=PIPE, bufsize=1, close_fds=ON_POSIX )
	queueStdOut = Queue()
	tthreadStdOut = Thread( target = enqueue_output, args = (proc.stdout, queueStdOut, sys.stdout) )
	tthreadStdOut.daemon = True # thread dies with the program
	tthreadStdOut.start()
	queueStdErr = Queue()
	tthreadStdErr = Thread( target = enqueue_output, args = (proc.stderr, queueStdErr, sys.stderr) )
	tthreadStdErr.daemon = True # thread dies with the program
	tthreadStdErr.start()
	return proc, queueStdOut, queueStdErr
