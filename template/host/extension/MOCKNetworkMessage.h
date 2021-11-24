#ifndef	MOCKNETWORKMESSAGE_H
#define	MOCKNETWORKMESSAGE_H

#include <moai-core/pch.h>
#include <moai-sim/pch.h>

#include "enet/enet.h"
#include "MOCKNetworkStream.h"

class MOCKNetworkPeer;
class MOCKNetworkStream;

//----------------------------------------------------------------//
typedef enum {
	
	NETWORK_MESSAGE_UNKNOWN,

	NETWORK_RPC,	

	NETWORK_ID_REGISTER,
	NETWORK_ID_UNREGISTER,

	NETWORK_RPC_REGISTER,

	NETWORK_CONNECTION_REQUEST,
	NETWORK_CONNECTION_PASSWORD_REQUEST,
	NETWORK_CONNECTION_PASSWORD_SEND,
	NETWORK_CONNECTION_CLOSED,
	NETWORK_CONNECTION_ACCEPTED,
	NETWORK_CONNECTION_READY,
	NETWORK_CONNECTION_FAILED,
	NETWORK_CONNECTION_DISCONNECTING,

	NETWORK_REMOTE_CONNECTED,
	NETWORK_REMOTE_DISCONNECTED
	
} MOCKNetworkMessageType;

//----------------------------------------------------------------//
typedef enum {
	NETWORK_ERROR_TIMEOUT,
	NETWORK_ERROR_ALREADY_CONNECTED,
	NETWORK_ERROR_BANNED,
	NETWORK_ERROR_INVALID_PASSWORD,
	NETWORK_ERROR_ATTEMPT_FAILED,
	NETWORK_ERROR_NO_FREE_SLOT,
	NETWORK_ERROR_UNKNOWN
} MOCKNetworkErrorType;

//----------------------------------------------------------------//
class MOCKNetworkMessage
{
friend class MOCKNetworkPeer;
friend class mDataStream;
private:
	ENetPacket* BuildPacket ();
	void Init ( MOCKNetworkMessageType type, MOCKNetworkPeer *sender, MOCKNetworkStream *stream );

public:
	MOCKNetworkMessageType mType;	
	MOCKNetworkPeer*       mSender;
	MOCKNetworkStream*     mDataStream;

	bool   mReliable;
	u32    mChannel; 

	MOCKNetworkMessage  ();
	MOCKNetworkMessage  ( MOCKNetworkMessageType type, MOCKNetworkPeer *sender );
	MOCKNetworkMessage  ( MOCKNetworkMessageType type, MOCKNetworkPeer *sender, MOCKNetworkStream *stream );
	~MOCKNetworkMessage ();
	
	MOCKNetworkMessage* Clone();
};


#endif