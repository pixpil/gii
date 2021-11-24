import logging

def getSuperType( t ):
	if isinstance( t, DataType ):
		return t.getSuperType()
		
	m = ModelManager._singleton.getModelFromTypeId( t )
	if m:
		return m.getSuperType()
	return None

def _makeShortName( n ):
	blobs = n.split('.')
	return blobs[len(blobs)-1]

##----------------------------------------------------------------##
class DataType(object):
	
	def getName(self):
		return None

	def getSuperType( self ):
		return None

	def getDefaultValue(self):
		return None
	
	def repr(self, value):
		return repr(value)

	def check(self, value):
		return value

	def serialize(self, value):
		raise NotImplementedError( 'serialize not implemented' )

	def deserialize(self, data):
		raise NotImplementedError( 'deserialize not implemented' )

	def register( self ):
		raise NotImplementedError( 'register not implemented' )

##----------------------------------------------------------------##
class ReferenceType(DataType):
	pass


##----------------------------------------------------------------##
class PythonValueType(DataType):
	def __init__(self ,t, defaultValue):
		self._type = t
		name = repr(t)
		self._defaultValue=defaultValue

	def getName(self):
		return repr(self._type)

	def check(self, value):
		if value is self._type:
			return value
		return None

	def register( self, typeId ):
		ModelManager.get().registerPythonModel( typeId, self )
		return self


##----------------------------------------------------------------##
class EnumType( DataType ):
	def __init__( self, name, enum, defaultValue = None ):
		#validation
		self.name = name
		itemDict = {}

		self.itemDict = itemDict
		for item in enum:
			( name, value ) = item
			itemDict[ name ] = value
		self._defaultValue = defaultValue
		self.itemList = enum[:]

	def getName( self ):
		return self.name

	def getSuperType( self ):
		return EnumType

	def repr( self, value ):
		return '<%s> %s' %( self.name, repr( value ) )

	def fromIndex( self, idx ):
		if idx < 0 or idx >= len( self.itemList ):
			return None
		( name, value ) = self.itemList[ idx ]
		return value

	def toIndex( self, value ):
		for i, item in enumerate( self.itemList ):
			( k, v ) = item
			if value == v: return i
		return None

	def getItemList( self, contextObject ):
		return self.itemList
		

##----------------------------------------------------------------##

class CollectionType( DataType ):
	def __init__(self, name, itemType, defaultValue = None ):
		self.name = name
		self.itemType = itemType	
		
	def getName( self ):
		return self.name

	def getSuperType( self ):
		return CollectionType

	def repr( self, value ):
		return '<%s> %s' %( self.name, repr( value ) ) 


##----------------------------------------------------------------##
class ArrayType(DataType):
	def __init__(self,name,itemType,defaultValue = []):
		self.name = name
		self.itemType = itemType

	def getName(self):
		return self.name

	def getSuperType(self):
		return ArrayType

	def repr(self,value):
		return '<%s> %s' %( self.name, repr( value ) ) 
##----------------------------------------------------------------##

class AssetRefType( DataType ):
	def __init__( self, assetType ):
		self.assetType = assetType

	def getName( self ):
		return self.assetType

	def getAssetType( self, contextObject ):
		atype = self.assetType
		if isinstance( atype, str ):
			return atype
		else: #asset type getter function
			return atype( contextObject )

	def getSuperType( self ):
		return AssetRefType

	def repr( self, value ):
		return '<%s> %s' % ( self.assetType, value )
		

##----------------------------------------------------------------##
class FlagsValueType( DataType ):
	def __init__( self, flags, defaultValue ):
		super(FlagsValueType, self).__init__()
		self.arg = arg

##----------------------------------------------------------------##
class ActionType( DataType ):
	def __init__(self, name, actionName, defaultValue = None ):
		self.name = name
		self.actionName = actionName	
		
	def getName( self ):
		return self.name

	def getSuperType( self ):
		return ActionType

	def repr( self, value ):
		return '<%s> %s' %( self.name, repr( value ) ) 

##----------------------------------------------------------------##
class ObjectModel( DataType ):
	@staticmethod
	def fromList( name, fieldList, **option ):
		model = ObjectModel( name, **option )
		for dataTuple in fieldList:
			if len(dataTuple) == 3:
				(key, typeId, fieldOption ) = dataTuple
			else:
				(key, typeId) = dataTuple
				fieldOption = {}
			model.addFieldInfo( key, typeId, **fieldOption )
		return model

	def getName(self):
		return self.name

	def getShortName( self ):
		return self.shortName		

	def getSuperType(self):
		return self.superType

	def setSuperType( self , typeInfo ):
		self.superType = typeInfo
		#TODO: check circular reference

	def isSubTypeOf(self, superType):
		s = self.getSuperType()
		while s:
			if superType == s : return True
			s = s.getSuperType()
		return False
		
	def isSuperTypeOf(self, subType):
		return subType.isSubTypeOf( self )

	def __init__(self, name, superType = None, **option):
		self.name      = name
		self.shortName = _makeShortName( name )
		self.fieldMap  = {}
		self.fieldList = []
		self.superType = None
		if superType: self.setSuperType( superType )
		if not option: return
		self.defaultRefWidget = option.get('defaultRefWidget',None)
		self.defaultSubWidget = option.get('defaultSubWidget',None)
		self.reference = option.get('reference',None)
		self.subobject = option.get('subobject',None)

	def addFieldInfo(self, id, t, **option):
		f = self.createField(id, t, **option)
		self.fieldMap[id] = f
		self.fieldList.append(f)
		return f

	def createField( self, id, t, **option ):
		return Field(self, id, t, **option)

	def getFieldInfo(self, id):
		return self.fieldMap.get(id, None)

	def getFieldValue(self, obj, id):
		f=self.getFieldInfo(id)
		return f.getValue(obj)

	def setFieldValue(self, obj, id, value):
		f=self.getFieldInfo(id)
		f.setValue(obj, value)

	def isFieldOverrided( self, obj, id ):
		return False

	def serialize( self, obj, objMap = None ):
		data = {}
		if not objMap: objMap = {}
		for field in self.fieldList:
			field.serialize( obj, data, objMap )
		return data

	def deserialize( self, obj, data, objMap = None ):
		for field in self.fieldList:
			field.deserialize( obj, data, objMap )

##----------------------------------------------------------------##
class Field(object):
	"""docstring for Field"""
	def __init__(self, model, id, _type, **option):
		self._type = _type
		self.model = model
		self.id    = id

		option = option or {}

		self.label	   = option.get( 'label',    id )
		
		self.default   = option.get( 'default',  None )
		self.getter	   = option.get( 'get',      True )
		self.setter	   = option.get( 'set',      True )
		self.readonly  = option.get( 'readonly', False )
		if self.setter == False: self.readonly = True
		option[ 'readonly' ] = self.readonly
		self.option    = option

	def __repr__( self ):
		return 'field: %s <%s>' % ( self.id, repr(self._type) )

	def getType( self ):
		return self._type

	def getOption( self, key, default = None ):
		return self.option.get( key, default )

	def getValue( self, obj, defaultValue = None ):
		getter = self.getter
		if getter == False: return None
		#indexer
		if getter == True:
			if isinstance( obj, dict ):
				return obj.get( self.id, defaultValue )
			else:
				return getattr( obj, self.id, defaultValue )
		#caller
		v = self.getter( obj, self.id )
		if v is None: return defaultValue
		return v

	def setValue( self, obj, value ):
		if self.readonly: return 
		if self.setter == True:
			if isinstance( obj, dict ):
				obj[ self.id ] = value
			else:
				setattr(obj, self.id, value)
		else:
			self.setter(obj, value)
	
	def isOverrided( self, obj ):
		return self.model.isFieldOverrided( obj, self.id )

	def serialize( self, obj, data, objMap ):
		_type = self._type
		if _type in ( int, float, str, str, bool ):
			v = self.getValue( obj )
			data[ self.id ] = v
		else:
			model = ModelManager.get().getModelFromTypeId( _type )
			if not model: return
			#TODO
			#ref? subobj?
			if v:
				subData = model.serialize( v, objMap )
				if v:
					data[ self.id ] = subData
			else:
				data[ self.id ] = None

	def deserialize( self, obj, data, objMap ):
		_type = self._type
		value = data.get( self.id, None )
		if _type in ( int, float, str, str, bool ):
			self.setValue( obj, value )
		else:
			model = ModelManager.get().getModelFromTypeId( _type )
			if not model: return
			if value:
				#TODO
				#ref? subobj?
				subObj = model.deserialize( obj, objMap )
				self.setValue( obj, subObj )
			else:
				self.setValue( obj, None )

##----------------------------------------------------------------##
class ArrayItemVirtualField( Field ):
	def __init__(self,field,index):
		self.parentField = field
		self._type = self.parentField._type.itemType
		self.index = index
		self.option = self.parentField.option
		self.id = self.parentField.id

	def setIndex( self, index ):
		self.index = index

	def setArrayField( self, field ):
		self.parentField = field

	def getOption( self, key, default = None ):
		return self.parentField.getOption( key, default )

	def setValue( self, obj, value ):
		arrayObject = self.parentField.getValue( obj )
		arrayObject[ self.index ] = value
		self.parentField.setValue( obj, arrayObject )

	def getValue( self, obj, defaultValue = None ):
		arrayObject = self.parentField.getValue( obj )
		value = arrayObject[ self.index ]
		return value

	def getType(self):
		return self._type


##----------------------------------------------------------------##
class TypeIdGetter(object):
	"""docstring for TypeInfoGetter"""
	def getTypeId(self, obj):
		return None

##----------------------------------------------------------------##
## ModelManager
##----------------------------------------------------------------##
class ModelProvider(object):
	def getModel( self, obj ):
		return None

	def getTypeId( self, obj ):
		return None

	def getModelFromTypeId( self, typeId ):
		return None

	def createObject( self, typeId ):
		return None

	#the bigger the first
	def getPriority( self ):
		return 0

##----------------------------------------------------------------##
class ObjectEnumerator(object):
	def getName( self ):
		return 'enumerator'
		
	def enumerateObjects( self, typeId, context = None, options = None ):
		return None

	def getObjectRepr( self, obj ):
		return None

	def getObjectTypeRepr( self, obj ):
		return None
		
	
##----------------------------------------------------------------##
class PythonModelProvider(ModelProvider):
	def __init__(self):
		self.typeMapV           = {}
		self.typeMapN           = {}

		self.registerModel( int,   PythonValueType( int,    0 ) )
		self.registerModel( float, PythonValueType( float,  0 ) )
		self.registerModel( str,   PythonValueType( str,    '' ) )
		self.registerModel( bool,  PythonValueType( bool,   False ) )

	def registerModel(self, t, model):
		self.typeMapV[t]=model
		self.typeMapN[model.getName()]=model
		return model

	def unregisterModel(self, t, Model):
		del self.typeMapV[t]
		del self.typeMapN[Model.getName()]

	def getModel( self, obj ):
		return self.getModelFromTypeId( self.getTypeId(obj) )

	def getTypeId( self, obj ):
		typeId = type(obj)
		return typeId

	def getModelFromTypeId( self, typeId ):
		if typeId:
			return self.typeMapV.get( typeId, None )
		return None

	def getPriority( self ):
		return 0
		

##----------------------------------------------------------------##
class ModelManager(object):
	_singleton=None

	@staticmethod
	def get():
		return ModelManager._singleton

	def __init__(self):
		assert(not ModelManager._singleton)
		ModelManager._singleton=self

		self.modelProviders     = []
		self.objectEnumerators  = []
	
		self.pythonModelProvider = self.RegisterModelProvider( PythonModelProvider() )
		#build python types
	
	def RegisterModelProvider( self, provider ):
		priority = provider.getPriority()
		for i, p in enumerate( self.modelProviders ):
			if priority >= p.getPriority() :
				self.modelProviders.insert( i, provider )
				return provider
		self.modelProviders.append( provider )
		return provider

	def unregisterModelProvider( self, provider ):
		idx = self.modelProviders.index( provider )
		self.modelProviders.pop( idx )

	def registerObjectEnumerator(self, enumerator):
		assert isinstance( enumerator, ObjectEnumerator )
		self.objectEnumerators.append( enumerator )
		return enumerator

	def unregisterObjectEnumerator(self, enumerator):
		newList = []
		for enumerator1 in self.objectEnumerators:
			if enumerator1 != enumerator: newList.append( enumerator1 )
		self.objectEnumerators = newList
	
	def getTypeId(self, obj):
		for provider in self.modelProviders:
			typeId = provider.getTypeId( obj )
			if typeId: return typeId			
		return None

	def getModel(self, obj):
		for provider in self.modelProviders:
			model = provider.getModel( obj )
			if model: return model			
		return None

	def getModelFromTypeId(self, typeId):
		for provider in self.modelProviders:
			model = provider.getModelFromTypeId( typeId )
			if model: return model
		return None

	def enumerateObjects(self, targetTypeId, context = None, option = None ):
		res=[]
		for enumerator in self.objectEnumerators:
			objectEntries = enumerator.enumerateObjects( targetTypeId, context, option ) 
			if objectEntries:
				res += objectEntries
		return res

	def getObjectRepr( self, obj ):
		for enumerator in self.objectEnumerators:
			name = enumerator.getObjectRepr( obj )
			if name is not None:
				return name
		return repr(obj)

	def getObjectTypeRepr( self, obj ):
		for enumerator in self.objectEnumerators:
			typeName = enumerator.getObjectTypeRepr( obj )
			if typeName is not None:
				return typeName
		return repr( type(obj) )

	def registerPythonModel(self, typeId, model):
		self.pythonModelProvider.registerModel( typeId, model)

	def serialize( self, obj, **kw ):
		model = kw.get( 'model', ModelManager.get().getModel( obj ) )
		if not model: 
			logging.warn( '(serialize) no model detected for %s' % repr(obj) )
			return None
		objMap = {}
		data = model.serialize( obj, objMap )
		return {
			'body':  data,
			'model': model.getName(),
			'map':   objMap
		}

	def deserialize( self, obj, data, **kw ):
		model = kw.get( 'model', ModelManager.get().getModel( obj ) )
		if not model: 
			logging.warn( '(deserialize) no model detected for %s' % repr(obj) )
			return None
		objMap = {}
		model.deserialize( obj, data, objMap )
		return obj

##----------------------------------------------------------------##
ModelManager()


##----------------------------------------------------------------##
def serializeObject( obj, **kw ):
	return ModelManager.get().serialize( obj, **kw )

def deserializeObject( data, **kw ):
	return ModelManager.get().deserialize( data, **kw )

def getTypeId( obj ):
	return ModelManager.get().getTypeId( obj )


##----------------------------------------------------------------##
class TypeIdDict( object ):
	def __init__( self ):
		self._dict = {}
		self._cached = {}

	def get( self, typeId, default = None ):
		v = self._cached.get( typeId )
		if v: return v
		while True:
			value = self._dict.get( typeId, None )
			if value:
				self._cached[ typeId ] = value
				return value
			typeId = getSuperType( typeId )
			if not typeId: break
		return default

	def set( self, typeId, value ):
		self._cached = {}
		self._dict[ typeId ] = value

	def __setitem__( self, key, value ):
		self.set( key, value )

	def __getitem__( self, key ):
		return self.get( key, None )

