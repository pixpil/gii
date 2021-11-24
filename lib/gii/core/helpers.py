import traceback
import time
import hashlib
import os.path
# def printTraceBack():
# 	try:
# 		1/0
# 	except Exception as e:
# 		traceback.print_stack()

def printTraceBack():
	traceback.print_stack()


# _timeRecords = {}
# def resetTiming():
# 	_timeRecords = {}

# def doTiming( id ):
# 	entry = _timeRecords.get( id, None ) 
# 	if not entry:
# 		entry = ( 0.0, time.time() )
# 	else:

_timeRecords = {}
def startTiming( id = 'default' ):
	_timeRecords[ id ] = time.process_time()

def stopTiming( id = 'default' ):
	if id not in _timeRecords:
		print(("no timing:", id))
		return
	t0 = _timeRecords.get( id, None )
	print(("time elapsed <%s>:%d" % ( id , ( time.process_time() - t0 ) * 1000 )))


##----------------------------------------------------------------##
def makeMangledFilePath( path ):
	name, ext = os.path.splitext( os.path.basename( path ) )
	m = hashlib.md5()
	m.update( path.encode('utf-8') )
	return name + '_' + m.hexdigest()
