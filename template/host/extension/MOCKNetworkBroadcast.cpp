#include "MOCKNetworkBroadcast.h"

ENetSocket _setupSocket( u16 port ) {
	ENetSocket socket = enet_socket_create( ENET_SOCKET_TYPE_DATAGRAM );
	ENetAddress addr;
	addr.host = ENET_HOST_ANY;
	addr.port = port;
	enet_socket_set_option( socket, ENET_SOCKOPT_REUSEADDR, 1 );
	if( enet_socket_bind( socket, &addr ) != 0 ) {
		enet_socket_destroy( socket );
		return -1;
	}	
	enet_socket_set_option( socket, ENET_SOCKOPT_BROADCAST, 1 );
	enet_socket_set_option( socket, ENET_SOCKOPT_NONBLOCK, 1 );
	return socket;
}

//----------------------------------------------------------------//
//SERVER
//----------------------------------------------------------------//

int MOCKNetworkBroadcastServer::_init ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkBroadcastServer, "UNS" )
	u16 port = state.GetValue< u16 >( 2, 0 );
	const char* identifier = lua_tostring( L, 3 );
	self->mIdentifier = identifier;
	self->mPort       = port;
	return 0;
}

//----------------------------------------------------------------//
void MOCKNetworkBroadcastServer::RegisterLuaClass ( MOAILuaState& state ) {
	MOAINode::RegisterLuaClass( state );
	MOAIAction::RegisterLuaClass( state );
}

void MOCKNetworkBroadcastServer::RegisterLuaFuncs ( MOAILuaState& state ) {
	MOAINode::RegisterLuaFuncs( state );
	MOAIAction::RegisterLuaFuncs( state );
	luaL_Reg regTable [] = {
		{ "init",			_init },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
MOCKNetworkBroadcastServer::MOCKNetworkBroadcastServer() :
	mStarted ( false ),
	mSocket  ( 0 ),
	mPort    ( 0 )
{
	RTTI_BEGIN
		RTTI_EXTEND( MOAINode )
		RTTI_EXTEND( MOAIAction )
	RTTI_END
}

MOCKNetworkBroadcastServer::~MOCKNetworkBroadcastServer() {

}

//----------------------------------------------------------------//
bool MOCKNetworkBroadcastServer::IsDone() {
	return !mStarted;	
}

void MOCKNetworkBroadcastServer::OnUpdate( float dt ) {
	if( !mStarted ) return;
	//receive message from client
	//if incoming message == identifier
	//reply with identifier
	//(optional) along with some host info?
	ENetBuffer buffer;
	ENetAddress addr;
	u8* data = (u8*) malloc( 1024 );
	buffer.data = data;
	buffer.dataLength = 1024;
	int recvLength = enet_socket_receive( mSocket, &addr, &buffer, 1 );
	if( recvLength == mIdentifier.length() + 1 ) {
		if(
			data[ 0 ] == MOCK_NETWORK_BROADCAST_HEADER
			&&
			memcmp( (char*)data + 1, mIdentifier.data(), recvLength - 1 ) == 0
		 ) { //respones
		 	//TODO: add extra data
		 	u32 extraLength = 0;
		 	buffer.dataLength = recvLength + extraLength;
			int sent = enet_socket_send( mSocket, &addr, &buffer, 1 );
			// printf( "responded with %d\n", sent );
		}
	}
	free( data );
	ScheduleUpdate();
}

void MOCKNetworkBroadcastServer::OnStart () {
	MOAIAction::OnStart();
	if( mPort > 0 ) {
		mSocket = _setupSocket( mPort );
		mStarted = mSocket > 0;
	}
}

void MOCKNetworkBroadcastServer::OnStop () {
	MOAIAction::OnStop();
	if( !mStarted ) return;
	enet_socket_shutdown( mSocket, ENET_SOCKET_SHUTDOWN_READ );
	enet_socket_destroy( mSocket );
	mStarted = false;
}


//----------------------------------------------------------------//
//CLIENT
//----------------------------------------------------------------//
int MOCKNetworkBroadcastClient::_init ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkBroadcastClient, "UNS" )
	u16 port = state.GetValue< u16 >( 2, 0 );
	const char* identifier = lua_tostring( L, 3 );
	self->mIdentifier = identifier;
	self->mTargetPort = port;
	self->mTimeout    = state.GetValue< float >( 4, 0 );
	self->mSubnetMask = state.GetValue< u32 >( 5, 0 );
	return 0;
}

void MOCKNetworkBroadcastClient::RegisterLuaClass ( MOAILuaState& state ) {
	MOAINode::RegisterLuaClass( state );
	MOAIAction::RegisterLuaClass( state );
	state.SetField ( -1, "EVENT_BROADCAST_RECEIVED",   ( u32 )EVENT_BROADCAST_RECEIVED  );
}

void MOCKNetworkBroadcastClient::RegisterLuaFuncs ( MOAILuaState& state ) {
	MOAINode::RegisterLuaFuncs( state );
	MOAIAction::RegisterLuaFuncs( state );
	luaL_Reg regTable [] = {
		{ "init",			_init },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

//----------------------------------------------------------------//
MOCKNetworkBroadcastClient::MOCKNetworkBroadcastClient() :
	mStarted      ( false ),
	mSocket       ( 0 ),
	mTargetPort   ( 0 ),
	mSubnetMask   ( 0 ),
	mTimeout      ( 0.0f ),
	mStartTime    ( 0.0f )	
{
	RTTI_BEGIN
		RTTI_EXTEND( MOAINode )
		RTTI_EXTEND( MOAIAction )
	RTTI_END
}

MOCKNetworkBroadcastClient::~MOCKNetworkBroadcastClient() {

}

//----------------------------------------------------------------//
bool MOCKNetworkBroadcastClient::IsDone() {
	return !mStarted;	
}

void MOCKNetworkBroadcastClient::OnStart () {
	MOAIAction::OnStart();
	if( mStarted ) return;
	if( mTargetPort == 0 ) return;

	mSocket = _setupSocket( ENET_PORT_ANY );
	if( mSocket <= 0 ) return;

	mStarted = true;
	mStartTime = ZLDeviceTime::GetTimeInSeconds();
	SendRequest();
}

void MOCKNetworkBroadcastClient::SendRequest () {
	ENetAddress broadcastAddr;
	if( mSubnetMask == 0 ) {
		broadcastAddr.host = ENET_HOST_BROADCAST;
	} else {
		broadcastAddr.host = mSubnetMask;
	}
	broadcastAddr.port = mTargetPort;

	u32 l = mIdentifier.length();
	ENetBuffer buffer;
	u8* data = (u8*)malloc( l + 1 );
	data[0] = MOCK_NETWORK_BROADCAST_HEADER;
	memcpy( data+1, mIdentifier.data(), l );
	buffer.data = data;
	buffer.dataLength = l + 1;

	int sendLength = enet_socket_send( mSocket, &broadcastAddr, &buffer, 1 );
	// printf( "sent length: %d\n", sendLength );

	free( data );
}

int MOCKNetworkBroadcastClient::Poll ( ENetAddress *addr, u8* extraBuffer, u32 extraBufferLength ) {
	if( !mStarted ) return -1;
	//receive message on specified port
	ENetBuffer buffer;
	u8* data = (u8*) malloc( 1024 );
	buffer.data = data;
	buffer.dataLength = 1024;

	int recvLength = enet_socket_receive( mSocket, addr, &buffer, 1 );
	if( recvLength <= 0 ) return -1;
	if( data[0] != MOCK_NETWORK_BROADCAST_HEADER ) return -1;
	if( 
		recvLength >= mIdentifier.length() + 1 
		&&
		memcmp( (char*)data + 1, mIdentifier.data(), recvLength - 1 ) == 0
		)
	{
		u32 extraLength = recvLength - 1 - mIdentifier.length();
		if( extraLength > 0) {
			memcpy( 
				(char*)extraBuffer,
				data + mIdentifier.length() + 1,
				min( extraLength, extraBufferLength )
			);
		}
		return extraLength;
	} else {
		free( data );
		return -1;
	}
	
}

void MOCKNetworkBroadcastClient::OnStop () {
	MOAIAction::OnStop();
	if( !mStarted ) return;
	enet_socket_shutdown( mSocket, ENET_SOCKET_SHUTDOWN_READ );
	enet_socket_destroy( mSocket );
	mStarted = false;
}

void MOCKNetworkBroadcastClient::OnUpdate ( float dt ) {	
	MOAIAction::OnUpdate( dt );
	if( !mStarted ) return;
	ENetAddress addr;
	u8* data = (u8*) malloc( 1024 );
	int length = Poll( &addr, data, 1024 );
	if( length >= 0 ) {
		MOAIScopedLuaState state = MOAILuaRuntime::Get ().State ();
		if ( this->PushListenerAndSelf ( EVENT_BROADCAST_RECEIVED, state ) ) {
			state.Push( (u32) addr.host );
			state.Push( (u32) addr.port );
			//todo: extra string
			state.DebugCall ( 3, 0 );
		}	
	}
	free( data );
	if( mTimeout > 0
			&& ( ZLDeviceTime::GetTimeInSeconds() - mStartTime <= mTimeout )
		) {
		Stop();
	} else {
		ScheduleUpdate();
	}
}
