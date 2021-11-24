#include "MOCKNetworkHost.h"
#include "MOCKNetworkPeer.h"


int MOCKNetworkPeer::_getState ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkPeer, "U" )
	state.Push( self->mState );
	return 1;
}

int MOCKNetworkPeer::_getContextHost ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkPeer, "U" )
	if ( self->mHost ){
		self->mHost->PushLuaUserdata( state );
	}
	return 1;
}


int MOCKNetworkPeer::_getHostIP ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkPeer, "U" )
	state.Push( self->mHostIP );
	return 1;
}

int MOCKNetworkPeer::_getPort ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkPeer, "U" )
	state.Push( self->mPort );
	return 1;
}

int MOCKNetworkPeer::_isLocal ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkPeer, "U" )
	state.Push( self->mLocal );
	return 1;
}

int MOCKNetworkPeer::_isConnected ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkPeer, "U" )
	state.Push( 
		self->mState == PEER_STATE_CLIENT || self->mState == PEER_STATE_SERVER
	);
	return 1;
}


//----------------------------------------------------------------//
void MOCKNetworkPeer::RegisterLuaClass ( MOAILuaState& state ) {

	state.SetField ( -1, "PEER_STATE_SERVER",       ( u32 )PEER_STATE_SERVER );
	state.SetField ( -1, "PEER_STATE_CLIENT",       ( u32 )PEER_STATE_CLIENT );
	state.SetField ( -1, "PEER_STATE_DISCONNECTED", ( u32 )PEER_STATE_DISCONNECTED );
	state.SetField ( -1, "PEER_STATE_CONNECTING",   ( u32 )PEER_STATE_CONNECTING );

	luaL_Reg regTable [] = {
		{ "new",							MOAILogMessages::_alertNewIsUnsupported },
		{ NULL, NULL }
	};
	
	luaL_register ( state, 0, regTable );
}

void MOCKNetworkPeer::RegisterLuaFuncs ( MOAILuaState& state ) {
	luaL_Reg regTable [] = {
		{ "getContextHost", _getContextHost  },
		{ "getHostIP",      _getHostIP   },
		{ "getPort",        _getPort     },
		{ "getState",			  _getState    },
		{ "isLocal",        _isLocal     },
		{ "isConnected",    _isConnected },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//

MOCKNetworkPeer::MOCKNetworkPeer():
	mHost    ( NULL ),
	mPeer    ( NULL ),
	mState   ( PEER_STATE_UNKNOWN ),
	mLocal   ( false ),
	mHostIP  ( 0 ),
	mPort    ( 0 ),
	mMessageCount  (0),
	mMessageCursor (0)
{
	RTTI_BEGIN
		RTTI_SINGLE( MOCKNetworkPeer )
	RTTI_END

	mLinkInHost.Data( this );
}

MOCKNetworkPeer::~MOCKNetworkPeer() {
	// if( mPeer ) {
	// 	enet_peer_reset( mPeer );
	// }
}

//----------------------------------------------------------------//
bool MOCKNetworkPeer::SendRaw ( char* data, u32 dataSize, u32 channel, bool reliable ) {
	if( !mPeer ) return false;
	
	u32 flags = 0;
	if( reliable ) { 
		flags |= ENET_PACKET_FLAG_RELIABLE;
	} else {
		flags |= ENET_PACKET_FLAG_UNSEQUENCED;
	}
	ENetPacket* packet = enet_packet_create( data, dataSize, flags );
	if( !packet ) return false;

	return enet_peer_send( mPeer, channel, packet );
}

//----------------------------------------------------------------//
bool MOCKNetworkPeer::Send( MOCKNetworkMessageType msgType ) {
	return Send( new MOCKNetworkMessage( msgType, mHost->mLocalPeer ) );
}

//----------------------------------------------------------------//
bool MOCKNetworkPeer::Send( MOCKNetworkMessageType msgType, MOCKNetworkStream *stream ) {
	return Send( new MOCKNetworkMessage( msgType, mHost->mLocalPeer, stream ) ) ;
}

//----------------------------------------------------------------//
bool MOCKNetworkPeer::Send( MOCKNetworkMessage* msg ) {
	mMessageQueue[ mMessageCount % MOCK_NETWORK_MESSAGE_QUEUE_SIZE ] = msg;
	mMessageCount++;
	//todo: check capacity
	return true;
}

//----------------------------------------------------------------//
bool MOCKNetworkPeer::SendMessagePacket ( MOCKNetworkMessage *msg ) {
	if ( !mPeer ) return false;
	ENetPacket *packet = msg->BuildPacket();
	if( packet ) {
		return enet_peer_send( mPeer, msg->mChannel, packet );
	} else {
		return false;
	}
}

//----------------------------------------------------------------//
void MOCKNetworkPeer::FlushMessages ( bool noSend = false ) {
	while( mMessageCursor < mMessageCount ) {
		MOCKNetworkMessage *msg = mMessageQueue[ mMessageCursor % MOCK_NETWORK_MESSAGE_QUEUE_SIZE ];
		if( !noSend )SendMessagePacket( msg );
		delete msg;
		mMessageCursor++;	
	}
	mMessageCount = 0;
	mMessageCursor = 0;
}

//----------------------------------------------------------------//
void MOCKNetworkPeer::ClearMessages () {
	FlushMessages( true );
}
