from .RemoteCommand import *
from .JSONHelper import *
from .guid import generateGUID
import base64
import logging

def encodeData( data ):
	return base64.b64encode( bytes( json.dumps( data ), encoding='utf-8') )

def decodeData( data ):
	return json.loads( str( base64.b64decode( bytes(data, encoding='ascii') ), encoding='utf-8') )

##----------------------------------------------------------------##
class RemoteSessionItemMeta( type ):
	def __init__( cls, name, bases, dict ):
		super( RemoteSessionItemMeta, cls ).__init__( name, bases, dict )
		fullname = dict.get( 'name', None )
		id = dict.get( 'id', None )
		if not fullname: return
		RemoteControlManager.get().registerCommand( id, cls )

##----------------------------------------------------------------##
class RemoteSessionItem( object, metaclass=RemoteSessionItemMeta ):
	def getName( self, context = None ):
		if hasattr( self, 'name' ):
			return getattr( self, 'name' )

		if hasattr( self.__class__, 'name' ):
			return getattr( self.__class__, 'name' )

		if hasattr( self.__class__, 'id' ):
			return getattr( self.__class__, 'id' )

		return None

	def run( self, session, context = None, inputContext = None ):
		pass

##----------------------------------------------------------------##
class RemoteControlSession(object):
	def __init__( self ):
		self.id = generateGUID()
		self.currentFrame = None
		self.sequence = 0
		self.currentItems = None
		self.history = {}
		self.pendingItems = []
		self.fileItems    = []
		self.answer = 'ok'

	def setAnswer( self, answer ):
		self.answer = answer

	def addFuncItem( self, name, func, context = None ):
		item = RemoteSessionItem()
		item.run = func
		item.name = name
		self.addItem( item, context )

	def addItem( self, item, context = None ):
		name = item.getName( context )
		self.pendingItems.append( ( name, item, context ) )

	def addFileItem( self, name, path ):
		self.fileItems.append( { 'name':name,'path':path } )

	def acceptInput( self, index, inputContext = None ):
		name, item, context = self.currentItems[ index ]
		return item.run( self, context, inputContext )

	def done( self ):
		self.done = True #TODO
		pass

	def flush( self ):
		self.currentItems = self.pendingItems
		fileItems = self.fileItems
		self.pendingItems = []
		self.fileItems = []
		outputItems = []
		for entry in self.currentItems:
			outputItems.append( {
					'name' : entry[ 0 ]
				}
			)
		frame = {
			'sequence' : self.sequence,
			'answer' : self.answer,
			'session_id' : self.id,
			'items' : outputItems,
			'files' : fileItems
		}
		self.answer = 'ok'
		self.currentFrame = frame
		self.history[ self.sequence ] = frame
		self.sequence = self.sequence + 1
		return frame

##----------------------------------------------------------------##
class RemoteControlManager( object ):
	_singleton = None
	@staticmethod
	def get():
		if not RemoteControlManager._singleton:
			return RemoteControlManager()
		return RemoteControlManager._singleton

	def __init__( self ):
		RemoteControlManager._singleton = self
		self.itemRegistry = {}
		self.sessions = {}

	def registerCommand( self, id, itemClas ):
		self.itemRegistry[ id ] = itemClas

	def getSession( self, id ):
		return self.sessions.get( id, None )

	def startSession( self ):
		session = RemoteControlSession()
		#init default
		for id, itemClas in list(self.itemRegistry.items()):
			item = itemClas()
			session.addItem( item, None )
		self.sessions[ session.id ] = session
		return session

RemoteControlManager()


##----------------------------------------------------------------##
class RemoteCommandControlSessionStart( RemoteCommand ):
	name = 'control_session_start'		
	def run( self, *args ):
		session = RemoteControlManager.get().startSession()
		response = session.flush()
		return encodeData( response )

		
##----------------------------------------------------------------##
class RemoteCommandControlSessionSend( RemoteCommand ):
	name = 'control_session_send'		
	def run( self, *args ):
		data = decodeData( args[0] or '' )
		sessionId = data[ 'session_id' ]
		session = RemoteControlManager.get().getSession( sessionId )
		if not session:
			response = {
				'answer' : 'error'
			}
		else:
			session.acceptInput( data[ 'index' ], data.get( 'context', None ) )
			response = session.flush()
		return encodeData( response )
