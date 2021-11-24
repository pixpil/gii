#ifndef MOCKNETWORKRPC_H
#define MOCKNETWORKRPC_H

#include "moai-core/pch.h"
#include "moai-sim/pch.h"
#include "MOCKNetworkMessage.h"
#include "MOCKNetworkStream.h"

class MOCKNetworkHost;
class MOCKNetworkStream;
class MOCKNetworkPeer;
class MOCKNetworkMessage;


class MOCKNetworkRPCInstance;
class MOCKNetworkRPC;

//----------------------------------------------------------------//
enum MOCKRPCArgType {
	//value
	RPC_ARG_NIL,
	RPC_ARG_BOOLEAN,

	RPC_ARG_INT,
	RPC_ARG_FLOAT,
	RPC_ARG_STRING,

	//network facility
	RPC_ARG_PEER, //network object id
	RPC_ARG_ID, //network object id
	// RPC_ARG_SHORT_ID, //network object id

	//collection type
	// RPC_ARG_ARRAY,
	// RPC_ARG_MAP,

	//compound type
	RPC_ARG_VEC2,
	RPC_ARG_VEC3,

	//var
	RPC_ARG_VAR, //variable type

	//--------
	RPC_ARG_LAST
};


//----------------------------------------------------------------//
struct MOCKRPCArg;
struct MOCKRPCArgKV;

//----------------------------------------------------------------//
// typedef struct {
// 	u32 size;
// 	struct MOCKRPCArg* ptr;
// } MOCKRPCArgArray;

// typedef struct {
// 	u32 size;
// 	struct MOCKRPCArgKV* ptr;
// } MOCKRPCArgMap;

typedef struct {
	u32 size;
	char* str;
} MOCKRPCArgString;

//----------------------------------------------------------------//
typedef union{
	bool   b;
	long   i;
	double f;
	MOCKNetworkPeer* peer;
	// MOCKRPCArgArray  array;
	// MOCKRPCArgMap    map;
	MOCKRPCArgString string;
} MOCKRPCArgUnion;

//----------------------------------------------------------------//
class MOCKRPCArg {
public:
	MOCKRPCArgType  mType;
	MOCKRPCArgUnion mBody;

	MOCKRPCArg() :mType( RPC_ARG_NIL ) {
	};

	~MOCKRPCArg() {
		if( mType == RPC_ARG_STRING ) {
			free( mBody.string.str );
		}
	};

	bool ReadFromStream ( MOCKNetworkHost* host, MOCKNetworkStream* stream );
	bool WriteToStream  ( MOCKNetworkHost* host, MOCKNetworkStream* stream );

	bool ReadFromState  ( MOAILuaState &state, int idx );
	bool ReadFromState  ( MOAILuaState &state, int idx, MOCKRPCArgType type );

	bool PushToState    ( MOAILuaState &state );
	bool PushToState    ( MOAILuaState &state, MOCKRPCArgType type );

	void SetString ( const char* str ) {
		size_t size = strlen( str );
		SetString( str, size );
	};

	void SetString ( const char* data, size_t size ) {		
		mType = RPC_ARG_STRING;
		char* s = ( char* ) malloc( size );
		memcpy( s, data, size );
		mBody.string.str = s;
		mBody.string.size = size;
	};

	void SetPeer   ( MOCKNetworkPeer* peer ) { mType = RPC_ARG_PEER; mBody.peer = peer; };

	void SetInt    ( int i )   { mType = RPC_ARG_INT;     mBody.i = i; };
	void SetFloat  ( float f ) { mType = RPC_ARG_FLOAT;   mBody.f = f; };
	void SetBool   ( bool b )  { mType = RPC_ARG_BOOLEAN; mBody.b = b; };
	void SetNil    ()          { mType = RPC_ARG_NIL; };


};

// typedef struct MOCKRPCArgKV {
// 	MOCKRPCArg key;
// 	MOCKRPCArg val;
// } MOCKRPCArgKV;

//----------------------------------------------------------------//
class MOCKNetworkRPC:
	public virtual MOAILuaObject
{
friend class MOCKNetworkRPCInstance;
friend class MOCKNetworkHost;
private:
	static int _init    ( lua_State *L ) ;
	static int _setArgs ( lua_State *L ) ;

	MOCKNetworkHost* mHost;

	u16 mId;
	u16 mGlobalId;
	STLString mName;

	u32 mChannel;
	u32 mMode;

	bool mVarArg;
	ZLLeanArray < MOCKRPCArgType > mArgTypes;

	MOAILuaMemberRef		mOnExec;//callback

protected:
	virtual void OnExec ( MOCKNetworkRPCInstance* instance );

public:
	static const u32 RPC_MODE_FLAG_SELF     = 0x01;
	static const u32 RPC_MODE_FLAG_OTHER    = 0x02;
	static const u32 RPC_MODE_FLAG_BUFFERED = 0x04;

	static const u32 RPC_MODE_SERVER         = 0;
	static const u32 RPC_MODE_OTHER          = RPC_MODE_FLAG_OTHER;
	static const u32 RPC_MODE_ALL            = RPC_MODE_FLAG_SELF | RPC_MODE_FLAG_OTHER;
	static const u32 RPC_MODE_OTHER_BUFFERED = RPC_MODE_OTHER | RPC_MODE_FLAG_BUFFERED;
	static const u32 RPC_MODE_ALL_BUFFERED   = RPC_MODE_ALL   | RPC_MODE_FLAG_BUFFERED;

	DECL_LUA_FACTORY ( MOCKNetworkRPC )

	MOCKNetworkRPC();
	~MOCKNetworkRPC();

	void    RegisterLuaClass		( MOAILuaState& state );
	void    RegisterLuaFuncs		( MOAILuaState& state );

	MOCKNetworkRPCInstance* BuildInstance ( MOAILuaState& state, int idx );
	MOCKNetworkRPCInstance* BuildInstance ( MOCKNetworkPeer* target, MOAILuaState& state, int idx );
	MOCKRPCArgType GetArgType ( u16 idx );

	STLString GetSignature();

};


//----------------------------------------------------------------//
class MOCKNetworkRPCInstance
{
friend class MOCKNetworkRPC;
friend class MOCKNetworkHost;
private:
	MOCKNetworkRPC*            mRPC;
	MOCKNetworkPeer*           mSender;
	MOCKNetworkPeer*           mTarget;
	ZLLeanArray < MOCKRPCArg > mArgs;
	ZLLeanLink < MOCKNetworkRPCInstance* > mLinkInBuffer;	
	bool Exec();

public:
	MOCKNetworkRPCInstance();

	MOCKNetworkMessage* ToMessage ( MOCKNetworkHost* host );
	bool FromMessage ( MOCKNetworkHost* host, MOCKNetworkMessage* msg );
};

#endif
