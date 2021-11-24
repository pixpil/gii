#ifndef	MOCKNETWORKPEER_H
#define	MOCKNETWORKPEER_H

#include "MOCKNetworkMessage.h"

class MOCKNetworkHost;
class MOCKNetworkMessage;

//----------------------------------------------------------------//
#define MOCK_NETWORK_MESSAGE_QUEUE_SIZE    256


//----------------------------------------------------------------//
class MOCKNetworkPeer:
	public MOAILuaObject
{
private:
	friend class MOCKNetworkHost;

	static int _getContextHost ( lua_State *L ) ;
	static int _getHostIP      ( lua_State *L ) ;
	static int _getPort        ( lua_State *L ) ;
	static int _getState       ( lua_State *L ) ;
	static int _isLocal        ( lua_State *L ) ;
	static int _isConnected    ( lua_State *L ) ;

	ENetPeer* mPeer;
	ZLLeanLink < MOCKNetworkPeer* > mLinkInHost;

	MOCKNetworkMessage *mMessageQueue[ MOCK_NETWORK_MESSAGE_QUEUE_SIZE ];
	u32                 mMessageCount;
	u32                 mMessageCursor;

	bool SendRaw ( char* data, u32 dataSize, u32 channel, bool reliable );
	bool SendMessagePacket ( MOCKNetworkMessage* msg );

public:
	bool mLocal;
	u32  mState;
	u32  mHostIP;
	u32  mPort;
	MOCKNetworkHost* mHost;

	enum {
		PEER_STATE_UNKNOWN,
		PEER_STATE_DISCONNECTED,
		PEER_STATE_CONNECTING,
		PEER_STATE_CLIENT,
		PEER_STATE_SERVER
	};

	DECL_LUA_FACTORY ( MOCKNetworkPeer )
	
	MOCKNetworkPeer  ();
	~MOCKNetworkPeer ();

	void RegisterLuaClass ( MOAILuaState& state );
	void RegisterLuaFuncs ( MOAILuaState& state );

	bool Send    ( MOCKNetworkMessage* msg );
	bool Send    ( MOCKNetworkMessageType msgType );
	bool Send    ( MOCKNetworkMessageType msgType, MOCKNetworkStream *stream );

	void FlushMessages ( bool noSend );
	void FlushMessages () { FlushMessages( false ); };
	void ClearMessages ();

};

#endif
