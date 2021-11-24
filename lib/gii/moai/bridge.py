import logging
# import json
import ujson as json
import weakref
import base64

from gii.core   import *

from gii.core.selection   import getSelectionManager

from .exceptions import *
from AKU        import _LuaTable, _LuaThread, _LuaObject, _LuaFunction
from time       import time as getTime
import uuid

import importlib


def wrapLuaCaller(func):
	def caller(*args):
			try:
				return func(*args)
			except Exception as e:
				logging.error( str(e) )
			return None
	return caller

####################################
#COMMON COMMUNICATION FUNCTIONS
####################################
_luaSignalConnections=[]
_luaSignalRegistration=[]

def emitPythonSignal(name, *args):	
	signals.emit(name, *args)

def emitPythonSignalNow(name, *args):	
	signals.emitNow(name, *args)

def connectPythonSignal(name, func, prepend=False):
	caller=wrapLuaCaller(func)
	signals.connect(name, caller, prepend)
	sig=signals.affirm(name)
	_luaSignalConnections.append((sig, caller))

def clearSignalConnections():
	global _luaSignalConnections
	for m in _luaSignalConnections:
		(sig , handler) = m
		sig.disconnect(handler)
	_luaSignalConnections=[]

def registerPythonSignal(name):
	signals.register(name)
	_luaSignalRegistration.append(name)

def clearLuaRegisteredSignals():
	global _luaSignalRegistration
	for name in _luaSignalRegistration:
		signals.unregister(name)

def throwPythonException(name, data=None):
	raise MOAIException(name)

##----------------------------------------------------------------##
def importModule( id ):
	return importlib.import_module( id )


####################################
#GUI BRIDGE
####################################
#todo
def GUIYield():
	app.doMainLoop()

def getSelection( key ):
	selectionManager = getSelectionManager( key )
	s = selectionManager.getSelection()
	return s

def changeSelection( key, targets = None ):
	selectionManager = getSelectionManager( key )
	selectionManager.changeSelection( targets )

def addSelection( key, targets = None ):
	selectionManager = getSelectionManager( key )
	selectionManager.addSelection( targets )

def toggleSelection( key, targets = None ):
	selectionManager = getSelectionManager( key )
	selectionManager.toggleSelection( targets )

def removeSelection( key, targets = None ):
	selectionManager = getSelectionManager( key )
	selectionManager.removeSelection( targets )

	
####################################
#COMMON DATA BRIDGE
####################################
def newDict():
	return {}
	
def getDict( d, key, default=None ):
	return d.get( key, default )

def setDict( d, key, value ):
	d[key] = value

def decodeDict(data):
	return json.loads(data)

def encodeDict(dict):
	return json.dumps(dict).encode('utf-8')

def luaTableToDict( luat, deepCopy = False ): #no deep conversion
	assert isinstance(luat , _LuaTable)
	res={}
	if deepCopy:
		for k in luat:
			v = luat[k]
			if isinstance( v, _LuaTable ):
				v = luaTableToDict( v, deepCopy )
			res[k] = v
	else:
		for k in luat:
			res[k] = luat[k]
	return res

def newPythonList(*arg):
	return list(arg)

def newPythonDict():
	return {}

def appendPythonList(list, data):
	list.append(data)

def deletePythonList(list, i):
	del list[i]

def sizeOfPythonObject(list):
	return len(list)

def tupleToList( t ):
	return list( t )

####################################
#MODEL BRIDGE
####################################
class LuaObjectModelProvider(ModelProvider):
	def __init__( self,  name, priority, getTypeId, getModel, getModelFromTypeId ):
		self.name        = name
		self.priority    = priority

		self._getTypeId          = getTypeId
		self._getModel           = getModel
		self._getModelFromTypeId = getModelFromTypeId

	def getPriority( self ):
		return self.priority

	def getTypeId( self, obj ):
		if isinstance( obj, _LuaObject ):
			return self._getTypeId( obj )
		else:
			return None

	def getModel( self, obj ):
		if isinstance( obj, _LuaObject ):
			return self._getModel( obj )
		else:
			return None

	def getModelFromTypeId( self, typeId ):
		return self._getModelFromTypeId( typeId )

	def getPriority( self ):
		return 1

	def clear( self ):
		pass


##----------------------------------------------------------------##
class LuaObjectEnumerator( ObjectEnumerator ):
	def __init__( self, name, enumerateObject, getObjectRepr, getObjectTypeRepr ):
		self.name     = name
		self._enumerateObject    = enumerateObject
		self._getObjectTypeRepr  = getObjectTypeRepr
		self._getObjectRepr      = getObjectRepr

	def getName( self ):
		return self.name

	def enumerateObjects( self, typeId, context, option ):
		result = self._enumerateObject( self, typeId, context, option )
		if not result: return None
		return [ obj for obj in list(result.values()) ]			

	def getObjectRepr( self, obj ):
		return self._getObjectRepr( self, obj )

	def getObjectTypeRepr( self, obj ):
		return self._getObjectTypeRepr( self, obj )


##----------------------------------------------------------------##
class LuaObjectField( Field ):
	def __init__( self, model, id, _type, **option ):
		super( LuaObjectField, self ).__init__( model, id, _type, **option )
		#init getter/setter
		if self.getter == False:
			self.getValue = self._getValueNone
		elif self.getter == True: 
			self.getValue = self._getValueRaw
		else:
			self.getValue = self._getValueGetter

		if self.readonly:
			self.setValue = self._setValueNone
		elif self.setter == True:
			self.setValue = self._setValueRaw
		else:
			self.setValue = self._setValueSetter

	def _getValueNone( self, obj, defaultValue = None ):
		return None

	def _getValueRaw( self, obj, defaultValue = None ):
		return getattr( obj, self.id, defaultValue )

	def _getValueGetter( self, obj, defaultValue = None ):
		#caller
		v = self.getter( obj, self.id )
		if v is None: return defaultValue
		return v

	def _setValueNone( self, obj, value ):
		pass

	def _setValueRaw( self, obj, value ):
		setattr( obj, self.id, value )

	def _setValueSetter( self, obj, value ):
		self.setter(obj, value)

##----------------------------------------------------------------##
class LuaObjectModel(ObjectModel):
	_EnumCache = weakref.WeakValueDictionary()
	# _AssetTypeCache = {}

	def createField( self, id, t, **option ):
		return LuaObjectField(self, id, t, **option)

	def isFieldOverrided( self, obj, id ):
		overridedFields = obj['__overrided_fields']
		if not overridedFields: return False
		if overridedFields[ id ]: return True
		return False

	def addLuaFieldInfo(self, name, typeId, data = None): #called by lua
		#convert lua-typeId -> pythontype
		typeId  = luaTypeToPyType( typeId )
		setting = data and luaTableToDict(data) or {}
		meta = setting.get( 'meta', None )
		if meta:
			del setting['meta']
			for k, v in list(meta.items()):
				if k not in setting:
					setting[k] = v
		return self.addFieldInfo( name, typeId, **setting )

	def addLuaEnumFieldInfo(self, name, enumItems, data = None): #called by lua
		enumType = LuaObjectModel._EnumCache.get( enumItems, None )
		if not enumType:
			tuples = []
			for item in list(enumItems.values()):
				itemName  = item[1]
				itemValue = item[2]
				tuples.append ( ( itemName, itemValue ) )
			enumType = EnumType( '_LUAENUM_', tuples )
			LuaObjectModel._EnumCache[ enumItems ] = enumType
		return self.addLuaFieldInfo( name, enumType, data )

	def addLuaAssetFieldInfo(self, name, assetType, data = None): #called by lua
		# typeId = LuaObjectModel._AssetTypeCache.get( assetType )
		# if not typeId:
		typeId = AssetRefType( assetType )
		# LuaObjectModel._AssetTypeCache[ assetType ] = typeId
		return self.addLuaFieldInfo( name, typeId, data )

	def addLuaActionFieldInfo(self, name, actionName, data = None): #called by lua
		actionType = ActionType( name, actionName )
		return self.addLuaFieldInfo( name, actionType, data )

	def addLuaCollectionFieldInfo( self, name, itemType, data = None ):
		collectionType = CollectionType( name, itemType )
		return self.addLuaFieldInfo( name, collectionType, data )

	def addLuaArrayFieldInfo(self,name,itemType,assetType,data = None):
		if itemType == '@asset':
			itemType = AssetRefType(assetType)
		else:
			itemType = luaTypeToPyType(itemType)
		arrayType = ArrayType(name, itemType)
		return self.addLuaFieldInfo(name, arrayType, data)

	def serialize( self, obj, objMap = None ):
		raise Exception('Serializing Lua object in python is not supported, yet')

	def deserialize( self, obj, data, objMap = None ):
		raise Exception('Deserializing Lua object in python is not supported, yet')


##----------------------------------------------------------------##

def luaTypeToPyType( tname ):
		if tname   == 'int':
			return int
		elif tname == 'string':
			return str
		elif tname == 'number':
			return float
		elif tname == 'boolean':
			return bool
		elif tname == 'nil':
			return None
		return tname #no conversion

##----------------------------------------------------------------##
class ModelBridge(object):
	_singleton=None

	@staticmethod
	def get():
		return ModelBridge._singleton

	def __init__(self):
		assert(not ModelBridge._singleton)
		ModelBridge._singleton=self
		self.modelProviders   = []
		self.enumerators      = []		
		self.registeredTypes  = {}
		signals.connect( 'moai.clean', self.cleanLuaBridgeReference )

	def newLuaObjectMoel(self, name):
		return LuaObjectModel(name)

	def buildLuaObjectModelProvider( self, name, priority, getTypeId, getModel, getModelFromTypeId ):
		provider = LuaObjectModelProvider( name, priority, getTypeId, getModel, getModelFromTypeId )
		ModelManager.get().RegisterModelProvider( provider )
		self.modelProviders.append( provider )
		return provider

	def buildLuaObjectEnumerator( self, name, enumerateObjects, getObjectRepr, getObjectTypeRepr ):
		enumerator = LuaObjectEnumerator( name, enumerateObjects, getObjectRepr, getObjectTypeRepr )
		ModelManager.get().registerObjectEnumerator( enumerator )
		self.enumerators.append( enumerator )
		return enumerator

	def getTypeId(self, obj):
		return ModelManager.get().getTypeId(obj)

	def cleanLuaBridgeReference(self):
		#clean type getter
		for provider in self.modelProviders:
			logging.info( 'unregister provider:%s'% repr(provider) )
			provider.clear()
			ModelManager.get().unregisterModelProvider( provider )

		for enumerator in self.enumerators:
			logging.info( 'unregister enumerator:%s'% repr(enumerator) )
			ModelManager.get().unregisterObjectEnumerator( enumerator )

		self.modelProviders = []
		self.enumerators    = []



ModelBridge()

##----------------------------------------------------------------##
class SafeDict(object):
	def __init__( self, dict ):
		self.__dict = dict

	def __setitem__( self, key, value ):
		self.__dict[key] = value

	def __getitem__( self, key ):
		return self.__dict.get( key, None )

	def __iter__( self ):
		return self.__dict

	def values( self ):
		return list(self.__dict.values())


def registerLuaEditorCommand( fullname, cmdCreator ):
	class LuaEditorCommand( EditorCommand ):	
		name = fullname
		def __init__( self ):
			self.luaCmd = cmdCreator()

		def init( self, **kwargs ):
			cmd = self.luaCmd
			return cmd.init( cmd, SafeDict( kwargs ) )

		def redo( self ):
			cmd = self.luaCmd
			return cmd.redo( cmd )

		def undo( self ):
			cmd = self.luaCmd
			return cmd.undo( cmd )

		def canUndo( self ):
			cmd = self.luaCmd
			return cmd.canUndo( cmd )

		def hasHistory( self ):
			cmd = self.luaCmd
			return cmd.hasHistory( cmd )

		def getResult( self ):
			cmd = self.luaCmd
			return cmd.getResult( cmd )

		def getLuaCommand( self ):
			return self.luaCmd

		def __repr__( self ):
			cmd = self.luaCmd
			return cmd.toString( cmd )
			
	return LuaEditorCommand


def doCommand( cmdId, argTable ):
	pyArgTable = luaTableToDict( argTable )
	return app.doCommand( cmdId, **pyArgTable )

def undoCommand( popOnly = False ):
	return app.undoCommand( popOnly )

####
#EXTRA
####
def generateGUID():
	# return str( uuid.uuid1() )
	return uuid.uuid1().hex

def getAssetNode( path ):
	return AssetLibrary.get().getAssetNode( path )


###
#GUI
###
def setClipboard( text ):
	from qtpy import QtWidgets
	QtWidgets.QApplication.clipboard().setText( text )

def getClipboard():
	from qtpy import QtWidgets
	return QtWidgets.QApplication.clipboard().getText()
