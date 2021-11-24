#include <moai-sim/headers.h>
#include "MOCKNetworkHost.h"

bool _ENetInitialized = false;

//----------------------------------------------------------------//
int MOCKNetworkHost::_getStat ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkHost, "U" )
	// todo
	return 0;
}

int MOCKNetworkHost::_getLocalPeer ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkHost, "U" )
	self->mLocalPeer->PushLuaUserdata( state );
	return 1;
}

int MOCKNetworkHost::_getServerPeer ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkHost, "U" )
	if( self->mServerPeer ) {
		self->mServerPeer->PushLuaUserdata( state );
		return 1;
	} else {
		return 0;
	}
}

int MOCKNetworkHost::_setPassword ( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkHost, "U" )
	if( lua_isstring( L, 2 ) ) {
		const char* str = lua_tostring( L, 2 );
		self->mPassword = str;
		self->mPasswordRequired = true;
	} else {
		self->mPassword = "";
		self->mPasswordRequired = false;
	}
	return 1;
}

int MOCKNetworkHost::_startServer( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkHost, "U" )

	u32 port       = state.GetValue< u32 >( 3, ENET_PORT_ANY );
	u32 peerCount  = state.GetValue< u32 >( 4, 16 );

	if( lua_isstring( L, 2 ) ) {
		const char* hostName = lua_tostring( L, 2 );
		state.Push( self->StartServer( hostName, port, peerCount ) );
	} else {
		u32 hostIP = state.GetValue< u32 >( 2, ENET_HOST_ANY );
		state.Push( self->StartServer( hostIP, port, peerCount ) );
	}
	return 1;
}

int MOCKNetworkHost::_connectServer( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkHost, "U" )

	u32 port = state.GetValue< u32 >( 3, 21103 );	
	u32 localPort = state.GetValue< u32 >( 4, ENET_PORT_ANY );	

	if( lua_type( L, 2 ) == LUA_TSTRING ) {
		const char* hostName = lua_tostring( L, 2 );
		state.Push( self->ConnectServer( hostName, port, localPort ) );
	} else {
		u32 hostIP = state.GetValue< u32 >( 2, 0 );
		state.Push( self->ConnectServer( hostIP, port, localPort ) );
	}
	return 1;
}

int MOCKNetworkHost::_shutdown( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkHost, "U" )
	state.Push( self->Shutdown() );
	return 1;
}

int MOCKNetworkHost::_disconnectPeer( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkHost, "UU" )
	MOCKNetworkPeer *peer = state.GetLuaObject < MOCKNetworkPeer > ( 2, true );
	if( peer ) {
		state.Push( self->DisconnectPeer( peer ) );
		return 1;
	} else {
		return 0;
	}
}

int MOCKNetworkHost::_registerRPC( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkHost, "UU" )
	MOCKNetworkRPC* rpc = state.GetLuaObject < MOCKNetworkRPC > ( 2, true );
	if( rpc ) {
		self->RegisterRPC( rpc );
	}
	return 0;
}

int MOCKNetworkHost::_sendRPC( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkHost, "UU" )
	MOCKNetworkRPC* rpc = state.GetLuaObject < MOCKNetworkRPC > ( 2, true );
	if( !rpc ) return 0;
	self->SendRPC( rpc, state );
	return 0;
}

int MOCKNetworkHost::_sendRPCTo( lua_State *L ) {
	MOAI_LUA_SETUP( MOCKNetworkHost, "UUU" )	
	MOCKNetworkPeer* target = state.GetLuaObject < MOCKNetworkPeer > ( 2, true );
	if( !target ) return 0;
	MOCKNetworkRPC* rpc = state.GetLuaObject < MOCKNetworkRPC > ( 3, true );
	if( !rpc ) return 0;
	self->SendRPC( rpc, target, state );
	return 0;
}

//----------------------------------------------------------------//
void MOCKNetworkHost::RegisterLuaClass ( MOAILuaState& state ) {
	MOAIAction::RegisterLuaClass( state );
	MOAINode::RegisterLuaClass( state );
	state.SetField ( -1, "EVENT_CONNECTION_ACCEPTED",   ( u32 )EVENT_CONNECTION_ACCEPTED  );
  state.SetField ( -1, "EVENT_CONNECTION_CLOSED",     ( u32 )EVENT_CONNECTION_CLOSED    );
  state.SetField ( -1, "EVENT_CONNECTION_FAILED",     ( u32 )EVENT_CONNECTION_FAILED    );
  state.SetField ( -1, "EVENT_REMOTE_CONNECTED",      ( u32 )EVENT_REMOTE_CONNECTED     );
  state.SetField ( -1, "EVENT_REMOTE_DISCONNECTED	",  ( u32 )EVENT_REMOTE_DISCONNECTED	);
  
  //Register Log Messages
  MOAILogMgr& log = MOAILogMgr::Get ();

	log.RegisterLogMessage ( 
		MOCKNETWORK_LOG_RPCRegisterFailed,
		MOAILogMgr::LOG_ERROR,
		"NET ERROR: cannot register RPC after host started" );

}

void MOCKNetworkHost::RegisterLuaFuncs ( MOAILuaState& state ) {
	MOAIAction::RegisterLuaFuncs( state );
	MOAINode::RegisterLuaFuncs( state );
	luaL_Reg regTable [] = {
		{ "getStat",		    	_getStat        },
		{ "getLocalPeer",			_getLocalPeer   },
		{ "getServerPeer",		_getServerPeer  },
		{ "setPassword",    	_setPassword    },
		{ "startServer",      _startServer    },
    { "connectServer",    _connectServer  },
    { "shutdown",         _shutdown       },
    { "disconnectPeer",   _disconnectPeer },

    { "registerRPC",      _registerRPC    },
    { "sendRPC",          _sendRPC        },
    { "sendRPCTo",        _sendRPCTo      },
		{ NULL, NULL }
	};

	luaL_register ( state, 0, regTable );
}

MOCKNetworkHost::MOCKNetworkHost() :
	mHost              ( NULL ),
	mServerPeer        ( NULL ),
	mMaxSlots          ( 1 ),
	mUsedSlots         ( 0 ),
	mPasswordRequired  ( false ),
	mCurrentRPCId      ( 0 ),
	mSyncedRPCId       ( 0 ),
	mRPCReady          ( false )
{
	RTTI_BEGIN
		RTTI_EXTEND( MOAIAction )
	RTTI_END

	if( !_ENetInitialized ) {
		enet_initialize();
		_ENetInitialized = true;
	}

	mLocalPeer = new MOCKNetworkPeer();
	mLocalPeer->mLocal = true;
	mLocalPeer->mState = MOCKNetworkPeer::PEER_STATE_DISCONNECTED;
	this->LuaRetain( mLocalPeer );
	mLocalPeer->mHost  = this;
	// mLocalPeer->LuaRetain( this );
	mLocalPeer->mPort = 0;
}

MOCKNetworkHost::~MOCKNetworkHost()
{
	Shutdown();
	//Clear Peers
	LuaRelease( mLocalPeer );
	PeerIt peerIt = mPeerList.Head ();
	while ( peerIt ) {
		MOCKNetworkPeer* peer = peerIt->Data ();
		peerIt = peerIt->Next ();
		LuaRelease( peer );
	}
	mPeerList.Clear();
}

//----------------------------------------------------------------//
//Initializer
//----------------------------------------------------------------//
bool MOCKNetworkHost::Init ( ENetAddress localAddr, u32 peerCount  ) {	
	if( mHost ) return false;	
	mHost = enet_host_create( &localAddr, peerCount, MOCK_NETWORK_CHANNEL_LIMIT, 0, 0 );
	if( !mHost ) return false ;
	enet_host_compress_with_range_coder( mHost );
	mLocalPeer->mHostIP = mHost->address.host;
	mLocalPeer->mPort   = mHost->address.port;
	return true;
}

//----------------------------------------------------------------//
bool MOCKNetworkHost::StartServer ( u32 host, u32 port, u32 peerCount ) {
	ENetAddress localAddr;
	localAddr.host = host;
	localAddr.port = port;
	return StartServer( localAddr, peerCount );
}

bool MOCKNetworkHost::StartServer ( const char* hostName, u32 port, u32 peerCount ) {
	ENetAddress localAddr;
	enet_address_set_host( &localAddr, hostName );
	localAddr.port = port;

	return StartServer( localAddr, peerCount );
}

bool MOCKNetworkHost::StartServer ( ENetAddress localAddr, u32 peerCount ) {
	if( mLocalPeer->mState == MOCKNetworkPeer::PEER_STATE_DISCONNECTED ){
		if( Init( localAddr, peerCount ) ) {
			mLocalPeer->mState = MOCKNetworkPeer::PEER_STATE_SERVER;
			mRPCReady = true;
			this->Start( MOAISim::Get ().GetActionMgr (), false );
			mServerPeer = mLocalPeer;
			return true;
		}
	}
	return false;
}

//----------------------------------------------------------------//
bool MOCKNetworkHost::ConnectServer( u32 host, u32 port, u32 localPort ) {
	ENetAddress serverAddr;
	serverAddr.host = host;
	serverAddr.port = port;

	ENetAddress localAddr;
	localAddr.host = 0;
	localAddr.port = localPort;

	return ConnectServer( serverAddr, localAddr );
}

bool MOCKNetworkHost::ConnectServer( const char* hostName, u32 port, u32 localPort ) {
	ENetAddress addr;
	enet_address_set_host( &addr, hostName );
	addr.port = port;

	ENetAddress localAddr;
	localAddr.host = 0;
	localAddr.port = localPort;

	return ConnectServer( addr, localAddr );
}

bool MOCKNetworkHost::ConnectServer( ENetAddress serverAddr, ENetAddress localAddr ) {
	if( mLocalPeer->mState == MOCKNetworkPeer::PEER_STATE_DISCONNECTED ){
		if( !Init( localAddr, 2 ) ) return false;		
		ENetPeer* peer = enet_host_connect( mHost, &serverAddr, MOCK_NETWORK_CHANNEL_LIMIT, 0 );
		if( !peer ) return false;
		MOCKNetworkPeer *serverPeer = GetPeer( peer, true );	
		mServerPeer = serverPeer;
		mLocalPeer->mState = MOCKNetworkPeer::PEER_STATE_CONNECTING;
		this->Start( MOAISim::Get ().GetActionMgr (), false );
		mConnectionTime = ZLDeviceTime::GetTimeInSeconds();
		return true;
	}
	return false;
}

//----------------------------------------------------------------//
bool MOCKNetworkHost::Shutdown() {
	if( mHost ) {
		if( IsClient() ) {
			mServerPeer->Send( NETWORK_CONNECTION_DISCONNECTING );
		} else {
			mRPCReady = false;
		}
		enet_host_destroy( mHost );
		mLocalPeer->mState = MOCKNetworkPeer::PEER_STATE_DISCONNECTED;
		mHost = NULL;
	}

	//clear RPC buffer
	ClearRPCBuffer();
	return true;
}

//----------------------------------------------------------------//
//States
//----------------------------------------------------------------//
bool MOCKNetworkHost::IsDone () {
	return mHost == NULL;
}

bool MOCKNetworkHost::IsStarted () {
	return mHost != NULL;
}

bool MOCKNetworkHost::IsClient () {
		return mLocalPeer->mState == MOCKNetworkPeer::PEER_STATE_CLIENT;
	}

bool MOCKNetworkHost::IsServer () {
	return mLocalPeer->mState == MOCKNetworkPeer::PEER_STATE_SERVER;
}


//----------------------------------------------------------------//
//Peer management
//----------------------------------------------------------------//
void MOCKNetworkHost::RemovePeer ( MOCKNetworkPeer* peer ) {
	// printf( "remove peer: %d:%d \n", peer->mHostIP, peer->mPort  );
	peer->mLinkInHost.Remove();
	if( peer->mPeer ) { //TODO
		enet_peer_reset( peer->mPeer );
		peer->mPeer->data = NULL;
	}	
	LuaRetain( peer );
}

//----------------------------------------------------------------//
MOCKNetworkPeer* MOCKNetworkHost::GetPeer ( ENetPeer* peer, bool registerIfNotFound ) {
	MOCKNetworkPeer* p = GetPeer( peer->address.host, peer->address.port, registerIfNotFound );
	if( !p->mPeer ) p->mPeer = peer;
	return p;
}

//----------------------------------------------------------------//
MOCKNetworkPeer* MOCKNetworkHost::GetPeer ( u32 ip, u16 port, bool registerIfNotFound ) {
	u64 fullAddress = (((u64) ip) << 16) | (u64) port;
	if( mPeerMap.contains( fullAddress ) ) {
		return mPeerMap[ fullAddress ];
	}

	if( !registerIfNotFound ) return NULL;

	MOCKNetworkPeer* p = new MOCKNetworkPeer();
	p->mHost   = this;
	p->mHostIP = ip;
	p->mPort   = port;
	p->mState  = MOCKNetworkPeer::PEER_STATE_CONNECTING;
	// printf( "add peer: %d:%d \n", p->mHostIP, p->mPort  );
	mPeerList.PushBack( p->mLinkInHost );	
	mPeerMap.insert( pair< u64, MOCKNetworkPeer* >( fullAddress, p ) );
	LuaRetain( p );

	return p;
}

//----------------------------------------------------------------//
void MOCKNetworkHost::AcceptClientPeer( MOCKNetworkPeer* client ) {
	MOAIScopedLuaState state = MOAILuaRuntime::Get ().State ();

	client->mState = MOCKNetworkPeer::PEER_STATE_CLIENT;
	// broadcast remote_connection
	PeerIt peerIt = this->mPeerList.Head ();
	while ( peerIt ) {
		MOCKNetworkPeer* peer = peerIt->Data ();
		peerIt = peerIt->Next ();
		if( peer != client ) {
			MOCKNetworkStream *stream = new MOCKNetworkStream();
			stream->WritePeer( this, client );
			peer->Send( NETWORK_REMOTE_CONNECTED, stream );
		}
	}
	client->Send( NETWORK_CONNECTION_ACCEPTED );

	if ( this->PushListenerAndSelf ( EVENT_CONNECTION_ACCEPTED, state ) ) {
		client->PushLuaUserdata( state );
		state.DebugCall ( 2, 0 );
	}

}

//----------------------------------------------------------------//
bool MOCKNetworkHost::CheckPassword ( STLString password ) {
	//TODO
	if( !mPasswordRequired ) return false;
	return ( mPassword.compare( password ) == 0 );
}

//----------------------------------------------------------------//
bool MOCKNetworkHost::DisconnectPeer( MOCKNetworkPeer *peer ) {
	if( IsServer() ){
		if( peer != mLocalPeer && peer->mPeer ) {
			enet_peer_disconnect( peer->mPeer, 0 );
			return true;
		} 
	}
	return false;
}


//----------------------------------------------------------------//
//Update Routine
//----------------------------------------------------------------//
void MOCKNetworkHost::OnUpdate ( float dt ) {	
	if( !mHost ) return;
	//Update ENet Service
	MOCKNetworkMessage *msg;
	MOCKNetworkPeer    *sender;
	MOCKNetworkStream  *stream;
	ENetEvent e;
	while( enet_host_service( mHost, &e, 0 ) > 0 ) {
		switch( e.type ) {
			case ENET_EVENT_TYPE_CONNECT:
				sender = GetPeer( e.peer, true );
				msg = new MOCKNetworkMessage( NETWORK_CONNECTION_REQUEST, sender );
				ProcessMessage( msg );
				delete msg;
				break;

			case ENET_EVENT_TYPE_DISCONNECT:
				sender = GetPeer( e.peer, false );
				if( sender ) {
					msg = new MOCKNetworkMessage( NETWORK_CONNECTION_CLOSED, sender );
					ProcessMessage( msg );
					delete msg;
				}
				break;

			case ENET_EVENT_TYPE_RECEIVE:
				//split packets
				sender = GetPeer( e.peer, false );
				if ( e.packet && sender ){ //dont process event from unkown peer
					stream = new MOCKNetworkStream( (byte*)e.packet->data, e.packet->dataLength );
					while( !stream->Eof() ) {
						msg = stream->ReadMessage();
						if( !msg ) break;
						msg->mSender = sender;
						ProcessMessage( msg );
						delete msg;
					}
					delete stream;
					enet_packet_destroy( e.packet );
				}
				break;
			
			case ENET_EVENT_TYPE_NONE:
				break;
				
		}
	}
	
	//todo: role-specified update routine
	if( mLocalPeer->mState == MOCKNetworkPeer::PEER_STATE_SERVER ) {
		OnUpdateServer();
	} else if( mLocalPeer->mState == MOCKNetworkPeer::PEER_STATE_CLIENT ) {
		OnUpdateClient();
	} else if( mLocalPeer->mState == MOCKNetworkPeer::PEER_STATE_CONNECTING ) {		
		float t = (float)ZLDeviceTime::GetTimeInSeconds();
		if( t - mConnectionTime > 5.0f ) {
			//timeout in 5 secons
			MOCKNetworkStream *stream =new MOCKNetworkStream();
			stream->WriteValue( (byte) NETWORK_ERROR_TIMEOUT );
			msg = new MOCKNetworkMessage( NETWORK_CONNECTION_FAILED, mServerPeer, stream );
			ProcessMessage( msg );
			delete msg;
		}
	}

	//flush message
	PeerIt peerIt = this->mPeerList.Head ();
	while ( peerIt ) {
		MOCKNetworkPeer* peer = peerIt->Data ();
		peerIt = peerIt->Next ();
		peer->FlushMessages();
	}

	if( mLocalPeer->mState != MOCKNetworkPeer::PEER_STATE_DISCONNECTED )
		this->ScheduleUpdate();

}

//----------------------------------------------------------------//
void MOCKNetworkHost::ProcessMessage ( MOCKNetworkMessage* msg ) {
	MOAIScopedLuaState state = MOAILuaRuntime::Get ().State ();

	STLString testPassword;
	MOCKNetworkErrorType    err;
	MOCKNetworkStream       *stream;
	MOCKNetworkRPCInstance  *RPCInstance;

	// printf( "process msg :%d \n", msg->mType );

	switch( msg->mType ) {
		//-------------------------------------//
		//COMMON Message type
		//-------------------------------------//
		case NETWORK_RPC:
			RPCInstance = new MOCKNetworkRPCInstance();
			if ( RPCInstance->FromMessage( this, msg ) ) {
				if( IsServer() ) {
					ProcessRPCServer( RPCInstance );
				} else {
					ProcessRPCClient( RPCInstance );
				}
			}
			break;

		case NETWORK_ID_REGISTER:
			break;

		case NETWORK_ID_UNREGISTER:
			break;		

		case NETWORK_CONNECTION_DISCONNECTING:
			break;

		//-------------------------------------//
		//SERVER Message type
		//-------------------------------------//		
		case NETWORK_CONNECTION_REQUEST:			
			if( IsServer() ) {
				//todo: askfor password
				if( mPasswordRequired ) {
					msg->mSender->Send( NETWORK_CONNECTION_PASSWORD_REQUEST );
				} else {
					AcceptClientPeer( msg->mSender );
				}
			}
			break;
				

		case NETWORK_CONNECTION_PASSWORD_SEND:			
			if( CheckPassword( msg->mDataStream->ReadString() ) ) {
				AcceptClientPeer( msg->mSender );
			} else {
				stream = new MOCKNetworkStream();
				stream->WriteValue( (byte)NETWORK_ERROR_INVALID_PASSWORD );
				msg->mSender->Send( NETWORK_CONNECTION_FAILED, stream );
			}
			break;

		case NETWORK_CONNECTION_CLOSED:
			//broadcast remote disconnection
			// PeerIt peerIt = this->mPeerList.Head ();
			// while ( peerIt ) {
			// 	MOCKNetworkPeer* peer = peerIt->Data ();
			// 	peerIt = peerIt->Next ();
			// 	peer->Send( NETWORK_REMOTE_DISCONNECTED );
			// }
			break;

		//-------------------------------------//
		//CLIENT Message type
		//-------------------------------------//
		case NETWORK_RPC_REGISTER:
			ReceiveRPCMapping( msg );
			break;

		case NETWORK_REMOTE_CONNECTED:
			{	
				MOCKNetworkPeer *remotePeer = msg->mDataStream->ReadPeer( this );
				if ( this->PushListenerAndSelf ( EVENT_REMOTE_CONNECTED, state ) ) {
					remotePeer->PushLuaUserdata( state );
					state.DebugCall ( 2, 0 );
				}	
			}
			break;

		case NETWORK_REMOTE_DISCONNECTED:
			{	
				MOCKNetworkPeer *remotePeer = msg->mDataStream->ReadPeer( this );
				if ( this->PushListenerAndSelf ( EVENT_REMOTE_DISCONNECTED, state ) ) {
					remotePeer->PushLuaUserdata( state );
					state.DebugCall ( 2, 0 );
				}	
				remotePeer->mState = MOCKNetworkPeer::PEER_STATE_DISCONNECTED;
			}			
			break;

		case NETWORK_CONNECTION_PASSWORD_REQUEST:
			//todo: provide password
			stream = new MOCKNetworkStream();
			stream->WriteString( mPassword );
			testPassword = stream->ReadString();
			mServerPeer->Send( NETWORK_CONNECTION_PASSWORD_SEND, stream );
			break;

		case NETWORK_CONNECTION_ACCEPTED:
			if( mServerPeer == msg->mSender )
			{
				mServerPeer->mState = MOCKNetworkPeer::PEER_STATE_SERVER;
				mLocalPeer->mState = MOCKNetworkPeer::PEER_STATE_CLIENT;
				if ( this->PushListenerAndSelf ( EVENT_CONNECTION_ACCEPTED, state ) ) {
					mServerPeer->PushLuaUserdata( state );
					state.DebugCall ( 2, 0 );
				}	
			}
			break;

		case NETWORK_CONNECTION_READY: //receive this after all initialization done
			break;

		case NETWORK_CONNECTION_FAILED:
			err = (MOCKNetworkErrorType) msg->mDataStream->ReadValue< byte >();
			mLocalPeer->mState = MOCKNetworkPeer::PEER_STATE_DISCONNECTED;
			if ( this->PushListenerAndSelf ( EVENT_CONNECTION_FAILED, state ) ) {
				state.Push( (u32)err );
				state.DebugCall ( 2, 0 );
			}	
			RemovePeer( mServerPeer );
			mServerPeer = NULL;
			break;
		
		case NETWORK_MESSAGE_UNKNOWN:
			break;

	}
}

void MOCKNetworkHost::OnUpdateServer () {
	//RPC mapping sync
	SendRPCMapping();	

	//PEER state sync
	//TODO

	//Send Buffered RPC

}

void MOCKNetworkHost::OnUpdateClient () {

}

//----------------------------------------------------------------//
//broad message
//----------------------------------------------------------------//
bool MOCKNetworkHost::BroadcastMessage ( MOCKNetworkMessage* msg, bool deleteMsg ) {	
	if( !IsServer() ) {
		return false;
		printf( "ERROR:cannot register RPC after host started\n");
	}
	PeerIt peerIt = mPeerList.Head ();
	while ( peerIt ) {
		MOCKNetworkPeer* peer = peerIt->Data ();
		peerIt = peerIt->Next ();
		if( peer->mState == MOCKNetworkPeer::PEER_STATE_CLIENT ) {
			peer->Send( msg->Clone() ); //TODO: use ref count to avoid cloning?
		}
	}
	if( deleteMsg ) delete msg;

	return true;
}

//----------------------------------------------------------------//
//RPC
//----------------------------------------------------------------//
bool MOCKNetworkHost::RegisterRPC ( MOCKNetworkRPC* rpc ) {
	if( IsStarted() ) {
		MOAILog( 0, MOCKNETWORK_LOG_RPCRegisterFailed );
		return false;
	}
	mCurrentRPCId++;
	rpc->mHost = this;
	rpc->mId   = mCurrentRPCId; //alloc rpc id
	if( mCurrentRPCId >= mRPCList.Size() ) {
		mRPCList.Resize( mCurrentRPCId * 2 );
	}
	mRPCList[ mCurrentRPCId ] = rpc;	
	mRPCMap.insert( pair< STLString, MOCKNetworkRPC* >( rpc->mName, rpc ) );
	return false;
}


MOCKNetworkRPCInstance* MOCKNetworkHost::SendRPC ( MOCKNetworkRPC* rpc, MOAILuaState &state ) {
	return SendRPC( rpc, NULL, state );	
}

// MOCKNetworkRPCInstance* MOCKNetworkHost::SendRPC ( MOCKNetworkRPC rpc, MOCKRPCParamList params );
MOCKNetworkRPCInstance* MOCKNetworkHost::SendRPC ( MOCKNetworkRPC* rpc, MOCKNetworkPeer* target, MOAILuaState &state ) {
	MOCKNetworkRPCInstance* instance = rpc->BuildInstance( target, state, 2 );
	if( !instance ) return NULL;
	if( target == mLocalPeer ) {
		instance->Exec(); //TODO: push to execution queue
		delete instance;
		return NULL;
	}

	if( IsServer() ) {
		ProcessRPCServer( instance );
	} else {
		ProcessRPCClient( instance );
	}

	return instance;
}



MOCKNetworkRPC* MOCKNetworkHost::FindRPC ( u32 globalId ) {
	if( globalId <= mCurrentRPCId ) return mRPCList[ globalId ];
	return NULL;
}

MOCKNetworkRPC* MOCKNetworkHost::FindRPC ( STLString name ) {
	if( mRPCMap.contains( name ) ) {
		return mRPCMap[ name ];
	}
	return NULL;
}

void MOCKNetworkHost::ProcessRPCServer ( MOCKNetworkRPCInstance* instance ) {
	if( instance->mTarget ) {
		//----TARGETED RPC--//
		if( instance->mTarget == mLocalPeer ) {
			//send to self? exec & delete
			instance->Exec();
			delete instance;
		} else {
			//redirect & delete
			SendRPCMessage( instance );
			delete instance;
		}
		//End of targeted rpc

	} else {
		//----BROADCAST RPC--//
		u32 mode = instance->mRPC->mMode;
		bool needExec   = false;
		bool needSend   = false;
		bool needDrop   = false;
		bool needBuffer = ( mode & MOCKNetworkRPC::RPC_MODE_FLAG_BUFFERED ) != 0;

		if( mode == MOCKNetworkRPC::RPC_MODE_SERVER ) {
			//MODE_SERVER
			needExec = true;
			needDrop = true;
		} else {
			//OTHER/ALL
			if( instance->mSender == mLocalPeer ) { //send by self
				needExec = ( mode & MOCKNetworkRPC::RPC_MODE_FLAG_SELF ) != 0;	
			} else {
				needExec = ( mode & MOCKNetworkRPC::RPC_MODE_FLAG_OTHER ) != 0;
			}
			needDrop = !needBuffer;
		}

		//operation
		if( needExec   ) { instance->Exec();                        }
		if( needSend   ) { SendRPCMessage( instance );              }
		if( needBuffer ) { PushRPCBuffer ( instance );              }
		if( needDrop   ) { delete instance; assert( !needBuffer );  }
		//End of broacast rpc
	}
}

void MOCKNetworkHost::ProcessRPCClient ( MOCKNetworkRPCInstance* instance ) {
	if( instance->mTarget ) {
		//----TARGETED RPC--//
		if( instance->mTarget == mLocalPeer ) {
			//send to self? exec & delete
			instance->Exec();
			delete instance;
		} else {			
			if( instance->mSender == mLocalPeer )	SendRPCMessage( instance );
			delete instance;
		}

	} else {
		//----BROADCAST RPC--//
		u32 mode = instance->mRPC->mMode;
		if( instance->mSender == mLocalPeer ) {
			//send by self?
			if( ( mode & MOCKNetworkRPC::RPC_MODE_FLAG_SELF ) != 0 ) instance->Exec();
			SendRPCMessage( instance );
		}	else {
			//send by other
			assert( ( mode & MOCKNetworkRPC::RPC_MODE_FLAG_OTHER ) != 0 );
			instance->Exec();
		}
		delete instance;
	}

}

//----------------------------------------------------------------//
void MOCKNetworkHost::SendRPCMessage ( MOCKNetworkRPCInstance* instance ) {
	if( IsServer() ) {
		//boradcast
		PeerIt peerIt = mPeerList.Head ();
		MOCKNetworkMessage* msg = instance->ToMessage( this );

		while ( peerIt ) {
			MOCKNetworkPeer* peer = peerIt->Data ();
			peerIt = peerIt->Next ();
			if( (peer->mState == MOCKNetworkPeer::PEER_STATE_CLIENT)
				&& (peer != instance->mSender) )
			{
				peer->Send( msg->Clone() ); //TODO: use ref count to avoid cloning?
			}
		}
		delete msg;	

	} else {
		//send to server
		MOCKNetworkMessage* msg = instance->ToMessage( this );
		mServerPeer->Send( msg );
	}

}

//----------------------------------------------------------------//
void MOCKNetworkHost::PushRPCBuffer ( MOCKNetworkRPCInstance* instance ) {
	//TODO: should we push generated packet instead?????
	mRPCBuffer.PushBack( instance->mLinkInBuffer );
}

void MOCKNetworkHost::ClearRPCBuffer () {
	RPCInstanceIt it = mRPCBuffer.Head ();
	while ( it ) {
		MOCKNetworkRPCInstance* instance = it->Data ();
		it = it->Next ();
		delete instance;	
	}
	mRPCBuffer.Clear();
}

//----------------------------------------------------------------//
void MOCKNetworkHost::SendRPCMapping () {
	if( mSyncedRPCId < mCurrentRPCId ) {
		MOCKNetworkStream* stream = new MOCKNetworkStream();
		u16 count = mCurrentRPCId - mSyncedRPCId;
		stream->WriteValue( count ); //sync count
		for( int i = 1; i <= count; i++ ) {
			MOCKNetworkRPC *rpc = mRPCList[ mSyncedRPCId + i ];
			rpc->mGlobalId = rpc->mId;
			stream->WriteString ( rpc->mName     );
			stream->WriteValue  ( rpc->mGlobalId );
			stream->WriteValue  ( (u8)rpc->mMode );
			// stream->WriteString ( rpc->GetSignature() );
		}
		MOCKNetworkMessage* msg = new MOCKNetworkMessage();
		mSyncedRPCId = mCurrentRPCId;

		BroadcastMessage( msg, true ); //no need to keep
	}
}

void MOCKNetworkHost::ReceiveRPCMapping ( MOCKNetworkMessage* msg ) {
	// mCurrentRPCId
	MOCKNetworkStream* stream = msg->mDataStream;
	u16 count = stream->ReadValue < u16 > ();
	for( int i = 1; i <= count; i++ ) {
		STLString name = stream->ReadString();
		u16 globalId   = stream->ReadValue< u16 >();
		u8  mode       = stream->ReadValue< u8 >();
		// STLString sig  = stream->ReadString();
		//verify
		
		MOCKNetworkRPC* rpc = FindRPC( name );
		if( rpc ) {
			if( rpc->mMode != mode ) {} //TODO: error, not match!
			rpc->mGlobalId = globalId;
		}
	}

}
//----------------------------------------------------------------//

