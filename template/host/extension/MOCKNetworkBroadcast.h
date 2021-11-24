#ifndef MOCKNETWORKBROADCAST_H
#define MOCKNETWORKBROADCAST_H
#include "enet/enet.h"
#include "moai-core/pch.h"
#include "moai-sim/pch.h"

#include <moai-sim/MOAIAction.h>
#include <moai-core/MOAILogMessages.h>

//----------------------------------------------------------------//
#define MOCK_NETWORK_BROADCAST_HEADER 0x33


class MOCKNetworkBroadcastServer :
	public virtual MOAINode,
	public MOAIAction
{
private:
	ENetSocket mSocket;
	bool      mStarted;
	STLString mIdentifier;
	u16       mPort;

	static int _init ( lua_State* L );

	void OnStart  ();
	void OnUpdate ( float step );
	bool IsDone   ();
	void OnStop   ();

	void Update   ();

public:
	enum {
		BROADCAST_REQUEST
	};

	DECL_LUA_FACTORY ( MOCKNetworkBroadcastServer )
	void    RegisterLuaClass ( MOAILuaState& state );
	void    RegisterLuaFuncs ( MOAILuaState& state );

	MOCKNetworkBroadcastServer();
	~MOCKNetworkBroadcastServer();

};

//----------------------------------------------------------------//
class MOCKNetworkBroadcastClient :
	public virtual MOAINode,
	public MOAIAction
{
private:
	ENetSocket mSocket;
	STLString  mIdentifier;
	bool       mStarted;
	u16        mTargetPort;
	u32        mSubnetMask;

	float      mTimeout;
	float      mStartTime;

	static int _init ( lua_State* L );

	void OnStart  ();
	void OnUpdate ( float step );
	bool IsDone   ();
	void OnStop   ();
	void SendRequest ();

	int Poll     ( ENetAddress *address, u8* extraBuffer, u32 extraBufferLength );

public:
	enum {
		EVENT_BROADCAST_RECEIVED = MOAIAction::TOTAL_EVENTS,
		TOTAL_EVENTS
	};
	
	DECL_LUA_FACTORY ( MOCKNetworkBroadcastClient )
	void    RegisterLuaClass ( MOAILuaState& state );
	void    RegisterLuaFuncs ( MOAILuaState& state );

	MOCKNetworkBroadcastClient();
	~MOCKNetworkBroadcastClient();

};

#endif
