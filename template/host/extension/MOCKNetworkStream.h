#ifndef MOCKNETWORKSTREAM_H
#define MOCKNETWORKSTREAM_H
#include "moai-core/pch.h"

#include "MOCKNetworkMessage.h"
#include "MOCKNetworkRPC.h"

#define BIT2BYTE( v ) ( (v + 7) >> 3 )
#define BYTE2BIT( v ) ( v << 3 )

class MOCKNetworkMessage;
class MOCKNetworkPeer;
class MOCKNetworkHost;

typedef unsigned char byte;

//----------------------------------------------------------------//
//Bit stream
class MOCKNetworkStream
{
private:
	byte* mBuffer;
	u32 mBufferSize;

	u32 mBitSize;
	u32 mBitPos;

	void AffirmBuffer( u32 newBits );
	void Init( byte* data, u32 dataSize, u32 bitLength );

public:
	MOCKNetworkStream();
	MOCKNetworkStream( byte* data, u32 dataSize );
	MOCKNetworkStream( byte* data, u32 dataSize, u32 bitLength );
	~MOCKNetworkStream();

	//----------------------------------------------------------------//
	MOCKNetworkStream* Clone();

	//----------------------------------------------------------------//	
	bool Eof()   { return mBitPos >= mBitSize; };
	void Reset() { mBitPos = 0; };

	u32 GetBitSize()  { return mBitSize; };
	u32 GetByteSize() { return BIT2BYTE( mBitSize ); };

	byte* GetBuffer() { return mBuffer; };	

	//----------------------------------------------------------------//
	void SkipBits    ( u32 bitLength );
	void WriteBits   ( const byte* data, u32 bitLength, bool align );
	bool ReadBits    ( byte* data, u32 bitLength, bool align );
	bool WriteOneBit ( bool b );
	bool ReadOneBit  ();

	void WriteAlignBytes  ( const byte* data, u32 byteLength );
	bool ReadAlignBytes   ( byte* data, u32 byteLength );

	void AlignRead   ();
	void AlignWrite  ();

	//----------------------------------------------------------------//
	//values
	template < typename T >
	T ReadValue() {
		T value;
		ReadBits( (byte*)&value, sizeof( T ) << 3, false );
		return value;
	}

	template < typename T >
	void WriteValue( T value ) {
		WriteBits( (byte*)&value, sizeof( T ) << 3, false );
	};

	void WriteFalse ();
	void WriteTrue  ();

	void WriteString( STLString str );
	STLString ReadString();

	void WriteData ( char* data, u16 size );
	int ReadData  ( char* data, u16 size );

	//----------------------------------------------------------------//
	// sub stream
	void WriteStream ( MOCKNetworkStream* stream );
	MOCKNetworkStream* ReadStream ();

	//----------------------------------------------------------------//
	//Message
	void WriteMessage ( MOCKNetworkMessage* msg );
	MOCKNetworkMessage* ReadMessage ();

	//----------------------------------------------------------------//
	//PEER
	void WritePeer ( MOCKNetworkHost* host, MOCKNetworkPeer* peer );
	MOCKNetworkPeer* ReadPeer ( MOCKNetworkHost* host );

	//----------------------------------------------------------------//
	//RPC

};

#endif