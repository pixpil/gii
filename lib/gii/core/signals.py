from .dispatch import Signal
from .dispatch.idle_queue import idle_loop,idle_add
import logging

SIGNALS={}

def dispatchAll():
	if idle_loop.empty(): return False
	while not idle_loop.empty():
		c=idle_loop.get()
		c()
	return True

def dispatchPartial( count ):
	if idle_loop.empty(): return False
	while not idle_loop.empty():
		c=idle_loop.get()
		c()
		count -= 1
		if count <= 0: return True
	return True

def connect(name, handler, prepend=False):
	sig=SIGNALS.get(name,None)
	if sig is None: raise Exception('SIGNAL undefined: %s '%name)
	sig.connect(handler,prepend)

def disconnect(name,handler):
	sig=SIGNALS.get(name,None)
	if sig is None: raise Exception('SIGNAL undefined: %s '%name)
	sig.disconnect(handler)

def tryConnect(name, handler):
	sig=SIGNALS.get(name,None)
	if sig is None: return
	sig.connect(handler)

def emit(name, *args, **kwargs):
	sig=SIGNALS.get(name,None)
	if sig is None: raise Exception('SIGNAL undefined: %s '%name)
	sig.emit(*args,  **kwargs)

# def emitUpdate(name, *args, **kwargs):
# 	sig=SIGNALS.get(name,None)
# 	if sig is None: raise Exception('SIGNAL undefined: %s '%name)
# 	sig.emitUpdate(*args, **kwargs)

def emitNow(name,*args, **kwargs):
	sig=SIGNALS.get(name,None)
	if sig is None: raise Exception('SIGNAL undefined: %s '%name)
	sig.emitNow(*args,  **kwargs)

def register( name ):
	if not SIGNALS.get(name,None) is None :raise Exception('SIGNAL duplicated: %s '%name)
	logging.debug( 'register signal: %s ' % name )
	sig = Signal( name=name )
	# sig=Signal()
	# sig.description = description
	# sig.name=name
	SIGNALS[name]=sig
	return sig

def unregister(name):
	del SIGNALS[name]

def get(name):
	return SIGNALS.get(name,None)

def affirm(name):
	sig=SIGNALS.get(name,None)
	if sig is None: raise Exception('SIGNAL undefined: %s '%name)
	return sig

#call func at next dispatch
def callAfter(func, *args, **kwargs):
	idle_add(func, *args, **kwargs)


_callHolderTable = {}
def _makeOneshotCall( sig, func, *args, **kwargs ):
	def _call():
		disconnect( sig, _call )
		flag = _callHolderTable.get( _call, None )
		if flag:
			del _callHolderTable[ _call ]
			return func( *args, **kwargs )
	return _call

def callOnce( sig, func, *args, **kwargs ):
	_call = _makeOneshotCall( sig, func, *args, **kwargs )
	_callHolderTable[ _call ] = True
	connect( sig, _call )
	return _call

def dropCall( call ):
	if call in _callHolderTable:
		_callHolderTable[ call ] = False

##----------------------------------------------------------------##
#DECORATORS
def slot( sig ):
	def slot_decorator( handler ):
		connect( sig, handler )
		return handler
	return slot_decorator

