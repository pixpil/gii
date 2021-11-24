#include "MOCKNetworkRPC.h"
#include "MOCKNetworkHost.h"

char RPCArgTypeToTag( MOCKRPCArgType type ) {
	switch ( type ) {
		case RPC_ARG_INT     : return 'i';
		case RPC_ARG_FLOAT   : return 'f';
		case RPC_ARG_BOOLEAN : return 'b';
		case RPC_ARG_STRING  : return 's';
		case RPC_ARG_PEER    : return 'p';
		case RPC_ARG_ID      : return '#';
		case RPC_ARG_VAR     : return '?';
		default:
			return 0;
	}
}

MOCKRPCArgType RPCArgTypeFromTag( char tag ) {	
	switch ( tag ) {
		case 'i' : return RPC_ARG_INT;
		case 'f' : return RPC_ARG_FLOAT;
		case 'b' : return RPC_ARG_BOOLEAN;
		case 's' : return RPC_ARG_STRING;
		case 'p' : return RPC_ARG_PEER;
		case '#' : return RPC_ARG_ID;
		case '?' : return RPC_ARG_VAR;
		default  :
			return RPC_ARG_NIL;
	}
}

//----------------------------------------------------------------//
// RPC arg
//----------------------------------------------------------------//
bool MOCKRPCArg::ReadFromStream ( MOCKNetworkHost* host, MOCKNetworkStream* stream ) {
	u16 strSize;
	char* data;
	MOCKRPCArgType type = (MOCKRPCArgType) stream->ReadValue <u8> ();	
	switch( type ) {
		case RPC_ARG_INT:
			SetInt( stream->ReadValue< long >() );
			break;

		case RPC_ARG_FLOAT:
			SetFloat( stream->ReadValue< double >() );
			break;

		case RPC_ARG_BOOLEAN:
			SetBool( stream->ReadOneBit() );
			break;

		case RPC_ARG_NIL:
			SetNil();
			break;

		case RPC_ARG_STRING:
			strSize = stream->ReadValue< u16 >();
			data    = (char*) malloc( strSize ); //to be free by MOCKRPCArg
			stream->ReadAlignBytes( (u8*)data, strSize );
			mType = type;
			mBody.string.str = data;
			mBody.string.size = strSize;
			break;

		case RPC_ARG_ID:
			//TODO
			break;

		case RPC_ARG_PEER:
			SetPeer( stream->ReadPeer( host ) );
			break;

		default:
			//ERROR?
			break;
	}
	return true;
}

bool MOCKRPCArg::WriteToStream  ( MOCKNetworkHost* host, MOCKNetworkStream* stream ) {
	STLString str;
	stream->WriteValue( (u8) mType );
	switch( mType ) {
		case RPC_ARG_INT:
			stream->WriteValue( mBody.i );
			break;

		case RPC_ARG_FLOAT:
			stream->WriteValue( mBody.f );
			break;

		case RPC_ARG_BOOLEAN:
			stream->WriteOneBit( mBody.b );
			break;

		case RPC_ARG_STRING:
			stream->WriteValue( (u16)mBody.string.size );
			stream->WriteAlignBytes( (byte*)mBody.string.str, mBody.string.size );
			break;

		case RPC_ARG_NIL:
			//nothing to write			
			break;

		case RPC_ARG_ID:
			//TODO
			break;

		case RPC_ARG_PEER:
			stream->WritePeer( host, mBody.peer );
			break;

		default:
			//ERROR?
			break;
	}
	return true;
}

bool MOCKRPCArg::ReadFromState  ( MOAILuaState &state, int idx ) {
	return ReadFromState( state, idx, RPC_ARG_VAR );	
}

bool MOCKRPCArg::ReadFromState  ( MOAILuaState &state, int idx, MOCKRPCArgType refType ) {
	int tt = lua_type( state, idx );
	switch ( refType ) {
		case RPC_ARG_INT:
			switch( tt ) {
				case LUA_TNUMBER: SetInt( lua_tointeger( state, idx ) ); break;
				default:          SetInt( 0 );
			}
			break;

		case RPC_ARG_FLOAT:
			switch( tt ) {
				case LUA_TNUMBER: SetFloat( lua_tonumber( state, idx ) ); break;
				default:          SetFloat( 0.0f );
			}
			break;

		case RPC_ARG_BOOLEAN:
			switch( tt ) {
				case LUA_TBOOLEAN: SetBool( lua_toboolean( state, idx ) ); break;
				case LUA_TNIL:     SetBool( false ); break;
				default:           SetBool( true );
			}			
			break;

		case RPC_ARG_STRING:
			switch( tt ) {
				case LUA_TSTRING:  SetString( lua_tostring( state, idx ) ); break;
				default:           SetNil();
			}
			break;
		
		case RPC_ARG_ID:
			//TODO
			break;

		case RPC_ARG_PEER:
			switch( tt ) {
				case LUA_TUSERDATA:
					SetPeer( state.GetLuaObject< MOCKNetworkPeer >( idx, true ) );
					break;
				default: SetPeer( NULL );
			}
			break;
		
		case RPC_ARG_VAR:
			switch( tt ) {
				case LUA_TNUMBER:  SetFloat( lua_tonumber( state, idx ) ); break;
				case LUA_TBOOLEAN: SetBool( lua_toboolean( state, idx ) ); break;
				case LUA_TSTRING:  SetString( lua_tostring( state, idx ) ); break;
				case LUA_TNIL:     SetNil(); break;
				default:           SetNil();
			}			
			break;

		case RPC_ARG_NIL:
			SetNil();
			break;

		default:
			SetNil();
			break;	
	}

	return true;
}

bool MOCKRPCArg::PushToState ( MOAILuaState &state ) {
	PushToState( state, RPC_ARG_VAR );
	return true;
}

bool MOCKRPCArg::PushToState ( MOAILuaState &state, MOCKRPCArgType type ) {
	//may need conversion
	switch( mType ) {
		case RPC_ARG_INT:
			lua_pushinteger( state, mBody.i );
			break;

		case RPC_ARG_FLOAT:
			state.Push( mBody.f );
			break;

		case RPC_ARG_BOOLEAN:			
			state.Push( (bool) mBody.b );
			break;

		case RPC_ARG_STRING:
			lua_pushlstring( state, mBody.string.str, mBody.string.size );
			break;

		case RPC_ARG_NIL:
			state.Push();
			break;

		case RPC_ARG_PEER:
			if ( mBody.peer ) {
				mBody.peer->PushLuaUserdata( state );
			} else {
				state.Push();
			}
			break;

		case RPC_ARG_ID:
			state.Push();
			break;
		
		default:
			state.Push();
	}

	return true;
}



//----------------------------------------------------------------//
//RPC Type
//----------------------------------------------------------------//
int MOCKNetworkRPC::_init ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkRPC, "USFN" )
	self->mName    = lua_tostring( L, 2 );
	self->mOnExec.SetRef ( *self, state, 3 );
	self->mMode    = state.GetValue< u32 >( 4, 0 );
	self->mChannel = state.GetValue< u32 >( 5, 0 );	
	return 0;
}

int MOCKNetworkRPC::_setArgs ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkRPC, "U" )	
	if( lua_isstring( L, 2 ) ) {
		cc8* argPattern = lua_tostring( L, 2 );
		u32 size = strlen( argPattern );
		self->mArgTypes.Init( size );
		MOCKRPCArgType atype;
		for( int i = 0; i < size; i++ ){			
			self->mArgTypes[ i ] = RPCArgTypeFromTag( argPattern[i] );
		}
	}
	self->mVarArg = false;
	return 0;
}

//----------------------------------------------------------------//
MOCKNetworkRPC::MOCKNetworkRPC () :
	mId       ( 0 ),
	mGlobalId ( 0 ),
	mChannel  ( 0 ),
	mMode     ( 0 ),
	mHost     ( NULL ),
	mVarArg   ( true )
{
	RTTI_BEGIN
		RTTI_SINGLE( MOCKNetworkRPC )
	RTTI_END
}

MOCKNetworkRPC::~MOCKNetworkRPC () {
}

void	MOCKNetworkRPC::RegisterLuaClass	( MOAILuaState& state ){
	state.SetField ( -1, "RPC_MODE_SERVER",         ( u32 )RPC_MODE_SERVER         );
	state.SetField ( -1, "RPC_MODE_OTHER",          ( u32 )RPC_MODE_OTHER          );
	state.SetField ( -1, "RPC_MODE_ALL",            ( u32 )RPC_MODE_ALL            );
	state.SetField ( -1, "RPC_MODE_OTHER_BUFFERED", ( u32 )RPC_MODE_OTHER_BUFFERED );
	state.SetField ( -1, "RPC_MODE_ALL_BUFFERED",   ( u32 )RPC_MODE_ALL_BUFFERED   );
}

void	MOCKNetworkRPC::RegisterLuaFuncs	( MOAILuaState& state ){	
	luaL_Reg regTable [] = {
		{ "init",    _init    },
		{ "setArgs", _setArgs },
		{ NULL, NULL }
	};

	luaL_register( state, 0, regTable );

}

//----------------------------------------------------------------//
MOCKRPCArgType MOCKNetworkRPC::GetArgType ( u16 idx ) {
	if( mVarArg ) return RPC_ARG_VAR;
	if( idx < mArgTypes.Size() ) return mArgTypes[ idx ];
	return RPC_ARG_NIL; //ignore
}

//----------------------------------------------------------------//
STLString MOCKNetworkRPC::GetSignature () {	
	return "";
}

//----------------------------------------------------------------//
MOCKNetworkRPCInstance* MOCKNetworkRPC::BuildInstance( MOAILuaState& state, int idx ) {
	return BuildInstance( NULL, state, idx );
}

MOCKNetworkRPCInstance* MOCKNetworkRPC::BuildInstance( MOCKNetworkPeer* target, MOAILuaState& state, int idx ) {
	MOCKNetworkRPCInstance* instance = new MOCKNetworkRPCInstance();
	instance->mRPC    = this;
	instance->mSender = mHost->GetLocalPeer();
	instance->mTarget = target;
	
	int top = state.GetTop();
	u8  argSize = top - idx;
	if( !mVarArg && argSize > mArgTypes.Size() ) argSize = mArgTypes.Size();

	instance->mArgs.Init( argSize );	
	for( int i = 0; i < argSize; i++ ) {
		instance->mArgs[ i ].ReadFromState( state, idx + i + 1, GetArgType( i ) );
	}
	return instance;
}

//----------------------------------------------------------------//
void MOCKNetworkRPC::OnExec ( MOCKNetworkRPCInstance* instance ) {
	if ( this->mOnExec ) {
		MOAIScopedLuaState state = MOAILuaRuntime::Get ().State ();
		if ( this->mOnExec.PushRef ( state )) {
			u8 argSize = instance->mArgs.Size();
			for( int i = 0; i < argSize; i++ ) {
				instance->mArgs[ i ].PushToState( state );
			}
			state.DebugCall ( argSize, 0 );
		}
	}
}


//----------------------------------------------------------------//
//INSTANCE
//----------------------------------------------------------------//
MOCKNetworkRPCInstance::MOCKNetworkRPCInstance () {
	mLinkInBuffer.Data( this );
	mTarget = NULL;
}


MOCKNetworkMessage* MOCKNetworkRPCInstance::ToMessage ( MOCKNetworkHost* host ) {
	MOCKNetworkStream* stream = new MOCKNetworkStream();
	u8 argSize = mArgs.Size();

	stream->WritePeer( host, mSender    ); //RPC sender
	stream->WritePeer( host, mTarget    ); //RPC target
	stream->WriteValue( mRPC->mGlobalId ); //RPC ID
	stream->WriteValue( argSize );         //Arg Size

	for( int i = 0; i < argSize; i++ ) { // Args
		mArgs[ i ].WriteToStream( host, stream );
	}

	MOCKNetworkMessage* msg   = new MOCKNetworkMessage( NETWORK_RPC, mSender, stream );
	return msg;
}


bool MOCKNetworkRPCInstance::FromMessage ( MOCKNetworkHost* host, MOCKNetworkMessage* msg ) {
	assert( msg->mType == NETWORK_RPC );
	assert( msg->mDataStream );
	MOCKNetworkStream* stream = msg->mDataStream;

	mSender    = stream->ReadPeer( host );    //RPC sender
	mTarget    = stream->ReadPeer( host );    //RPC sender
	u16 RPCId  = stream->ReadValue< u16 > (); //RPC ID
	u8 argSize = stream->ReadValue< u8 >();   //Arg Size	
	mRPC       = host->FindRPC( RPCId );

	mArgs.Init( argSize );
	for( int i = 0; i < argSize; i++ ) {
		mArgs[ i ].ReadFromStream( host, stream );
	}
	return true;
}

//----------------------------------------------------------------//
bool MOCKNetworkRPCInstance::Exec () {
	assert( mRPC );
	assert( mRPC->mHost );

	mRPC->OnExec( this );
	return true;
}
