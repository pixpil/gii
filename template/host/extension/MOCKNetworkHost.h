#ifndef	MOCKNETWORKHOST_H
#define	MOCKNETWORKHOST_H

#include <enet/enet.h>

#include <moai-core/pch.h>
#include <moai-sim/pch.h>
#include <moai-sim/MOAIAction.h>
#include <moai-core/MOAILogMessages.h>

#include "MOCKNetworkMessage.h"
#include "MOCKNetworkPeer.h"
#include "MOCKNetworkRPC.h"

#include "MOCKNetworkBroadcast.h"

class MOCKNetworkMessage;
class MOCKNetworkPeer;

enum MOCKNetworkLogMessages {
	MOCKNETWORK_LOG_BASE = 0x3000,
	MOCKNETWORK_LOG_RPCRegisterFailed	
};

enum MOCKNetworkChannelID {
	MOCK_NETWORK_CHANNEL_SYSTEM,
	MOCK_NETWORK_CHANNEL_RPC,
	MOCK_NETWORK_CHANNEL_GENERAL,
	MOCK_NETWORK_CHANNEL_SERIALIZATION,
	MOCK_NETWORK_CHANNEL_LIMIT
};


//----------------------------------------------------------------//
class MOCKNetworkHost:
	public MOAIAction, 
	public virtual MOAINode
{
friend class MOCKNetworkPeer;
private:

	static int _getStat        ( lua_State *L ) ;
	static int _getLocalPeer   ( lua_State *L ) ;
	static int _getServerPeer  ( lua_State *L ) ;
	static int _setPassword    ( lua_State *L ) ;

	static int _startServer    ( lua_State *L ) ;
	static int _connectServer  ( lua_State *L ) ;
	static int _shutdown       ( lua_State *L ) ;
	static int _disconnectPeer ( lua_State *L ) ;

	static int _registerRPC    ( lua_State *L ) ;
	static int _sendRPC        ( lua_State *L ) ;
	static int _sendRPCTo      ( lua_State *L ) ;


	MOCKNetworkPeer    *mLocalPeer;
	MOCKNetworkPeer    *mServerPeer;
	ENetHost           *mHost;
	bool                mRPCReady;//RPC ready?
	
	//Settings
	u32                 mMaxSlots;
	u32                 mUsedSlots;
	STLString           mPassword;
	bool                mPasswordRequired;
	float               mConnectionTime;

	//Update Routine
	bool IsDone ();

	void OnUpdate       ( float dt );
	void OnUpdateServer ();
	void OnUpdateClient ();

	bool Init( ENetAddress localAddr, u32 peerCount );	

	void ProcessMessage   ( MOCKNetworkMessage *msg );
	bool BroadcastMessage ( MOCKNetworkMessage *msg, bool deleteMsg = true );

	//Peers
	void RemovePeer       ( MOCKNetworkPeer *peer );
	void AcceptClientPeer ( MOCKNetworkPeer *peer );

	bool CheckPassword    ( STLString password );

	typedef STLMap < u64, MOCKNetworkPeer* >::iterator PeerMapIt;
	STLMap < u64, MOCKNetworkPeer* > mPeerMap;

	typedef ZLLeanList < MOCKNetworkPeer* >::Iterator PeerIt;
	ZLLeanList < MOCKNetworkPeer* > mPeerList;

	//RPC
	// typedef STLMap < u64, MOCKNetworkRPC* >::iterator RPCMapIt;
	typedef ZLLeanList < MOCKNetworkRPCInstance* >::Iterator RPCInstanceIt;
	STLMap < STLString, MOCKNetworkRPC* >    mRPCMap;
	ZLLeanArray < MOCKNetworkRPC* >          mRPCList;
	ZLLeanList < MOCKNetworkRPCInstance* >   mRPCBuffer;
	
	u16 mCurrentRPCId;
	u16 mSyncedRPCId;

	void SendRPCMapping    ();
	void ReceiveRPCMapping ( MOCKNetworkMessage* msg );

	void ProcessRPCServer ( MOCKNetworkRPCInstance* instance );
	void ProcessRPCClient ( MOCKNetworkRPCInstance* instance );

	void SendRPCMessage   ( MOCKNetworkRPCInstance* instance );

	void PushRPCBuffer    ( MOCKNetworkRPCInstance* instance );
	void ClearRPCBuffer   ();
	// void QueueRPC         ( MOCKNetworkRPCInstance* instance );

public:
	MOCKNetworkHost();
	~MOCKNetworkHost();

	enum {
		EVENT_CONNECTION_ACCEPTED = MOAIAction::TOTAL_EVENTS,
		EVENT_CONNECTION_DISCONNECTING,
		EVENT_CONNECTION_CLOSED,
		EVENT_CONNECTION_FAILED,
		EVENT_REMOTE_CONNECTED,
		EVENT_REMOTE_DISCONNECTED,

		EVENT_BROADCAST_FOUND,

		TOTAL_EVENTS
	};

	DECL_LUA_FACTORY ( MOCKNetworkHost )

	void RegisterLuaClass ( MOAILuaState& state );
	void RegisterLuaFuncs ( MOAILuaState& state );

	MOCKNetworkPeer*    GetPeer ( u32 ip, u16 port, bool registerIfNotFound );
	MOCKNetworkPeer*    GetPeer ( ENetPeer* peer, bool registerIfNotFound );

	bool IsStarted ();
	bool IsClient  ();
	bool IsServer  ();	

	bool StartServer    ( u32 host, u32 port, u32 peerCount );
	bool StartServer    ( const char* hostName, u32 port, u32 peerCount );
	bool StartServer    ( ENetAddress localAddr, u32 peerCount );
	
	bool ConnectServer  ( u32 host, u32 port, u32 localPort );
	bool ConnectServer  ( const char* hostName, u32 port, u32 localPort );
	bool ConnectServer  ( ENetAddress serverAddr, ENetAddress localAddr );

	bool Shutdown       ();
	bool DisconnectPeer ( MOCKNetworkPeer* peer );

	bool HasEmptySlot   () { return mUsedSlots < mMaxSlots; } ;

	GET ( MOCKNetworkPeer*, ServerPeer, mServerPeer )
	GET ( MOCKNetworkPeer*, LocalPeer,  mLocalPeer )

	//----------------------------------------------------------------//
	//RPC
	//----------------------------------------------------------------//
	bool RegisterRPC    ( MOCKNetworkRPC* rpc );

	MOCKNetworkRPC* FindRPC ( u32 id );
	MOCKNetworkRPC* FindRPC ( STLString name );

	// MOCKNetworkRPCInstance* SendRPC ( MOCKNetworkRPC rpc, MOCKRPCParamList params );
	MOCKNetworkRPCInstance* SendRPC ( MOCKNetworkRPC* rpc, MOCKNetworkPeer* target, MOAILuaState &state );
	MOCKNetworkRPCInstance* SendRPC ( MOCKNetworkRPC* rpc, MOAILuaState &state );

};

#endif