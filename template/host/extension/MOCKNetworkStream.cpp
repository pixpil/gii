#include "MOCKNetworkHost.h"
#include "MOCKNetworkStream.h"


void MOCKNetworkStream::Init( byte* buffer, u32 bufferSize, u32 bitLength = 0 ) {
	byte* newBuffer = (byte*) malloc( bufferSize );
	mBuffer     = newBuffer;
	mBufferSize = bufferSize;
	memcpy( newBuffer, buffer, bufferSize );
	if( bitLength == 0 ) bitLength = BYTE2BIT( bufferSize );
	mBitSize    = bitLength;
	mBitPos     = 0;
}

//----------------------------------------------------------------//
MOCKNetworkStream::MOCKNetworkStream() {
	mBuffer     = NULL;
	mBufferSize = 0;
	mBitSize    = 0;
	mBitPos     = 0;
}

MOCKNetworkStream::MOCKNetworkStream( byte* buffer, u32 bufferSize ) {
	Init( buffer, bufferSize, 0 );
}

MOCKNetworkStream::MOCKNetworkStream( byte* buffer, u32 bufferSize, u32 bitLength = 0 ) {
	Init( buffer, bufferSize, bitLength );
}

MOCKNetworkStream::~MOCKNetworkStream () {
	if( mBuffer ) free( mBuffer );
}

//----------------------------------------------------------------//
MOCKNetworkStream* MOCKNetworkStream::Clone() {
	MOCKNetworkStream* stream = new MOCKNetworkStream();
	stream->mBufferSize = mBufferSize;
	stream->mBuffer  = (byte*) malloc( mBufferSize );
	stream->mBitSize = mBitSize;
	stream->mBitPos  = 0;
	memcpy( stream->mBuffer, mBuffer, BIT2BYTE( mBitSize ) );
	return stream;
}

//----------------------------------------------------------------//
void MOCKNetworkStream::AffirmBuffer( u32 newBits ) {
	if( newBits == 0 ) return;
	u32 newBufferSize = BIT2BYTE( mBitSize + newBits );
	if( newBufferSize > mBufferSize ) {
		newBufferSize *= 2;
		byte* newBuffer = ( byte* )malloc( newBufferSize );
		if( mBuffer ) {
			memcpy ( newBuffer, mBuffer, BIT2BYTE( mBitSize ) );
			free( mBuffer );
		}
		mBuffer = newBuffer;
		mBufferSize = newBufferSize;
	}
}

//----------------------------------------------------------------//
void MOCKNetworkStream::WriteBits  ( const byte* data, u32 bitLength, bool align = false ) {
	if( bitLength == 0 ) return;
	AffirmBuffer( bitLength );

	u32 bytePos = mBitSize >> 3;
	u32 fullBytes = bitLength >> 3;
	u32 tail   = bitLength & 7;
	u32 mod8   = mBitSize & 7;
	if( mod8 == 0 ) { //start from head of a new byte
		for ( u32 i = 0; i < fullBytes; i++ ) {
			mBuffer[ bytePos ] = data[ i ];
			bytePos += 1;
		}
		//write tail
		if( tail > 0 ) {
			byte b = data[ fullBytes ];
			if( align ) {
				b = b << ( 8 - tail );
			} else {
				b = b & ( 0xff << ( 8 - tail ) );
			}
			mBuffer[ bytePos ] = b;
		}
	} else {
		for ( u32 i = 0; i < fullBytes; i++ ) {
			byte b = data[ i ];
			mBuffer[ bytePos     ] |= ( b >> mod8 );
			mBuffer[ bytePos + 1 ] = ( b << ( 8 - mod8 ) );
			bytePos += 1;
		}
		if( tail > 0 ) {
			byte b = data[ fullBytes ];
			if( align ) {
				b = b << ( 8 - tail );
			} else {
				b = b & ( 0xff << ( 8 - tail ) );
			}
			mBuffer[ bytePos ] |= ( b >> mod8 );
			if( mod8 + tail > 8 ) {
				mBuffer[ bytePos + 1 ] = ( b << ( 8 - mod8 ) );
			}
		}
	}
	mBitSize += bitLength;
}


//----------------------------------------------------------------//
bool MOCKNetworkStream::ReadBits ( byte* data, u32 bitLength, bool align = false ) {
	if( bitLength == 0 ) return true;
	if( mBitPos + bitLength > mBitSize ) return false;
	u32 bytePos   = mBitPos >> 3;
	u32 fullBytes = bitLength >> 3;
	u32 tail      = bitLength & 7;
	u32 mod8      = mBitPos & 7;
	
	if ( mod8 == 0 ) {
		for ( u32 i = 0; i < fullBytes; i++ ) {
			data[ i ] = mBuffer[ bytePos ];
			bytePos += 1;
		}
		if ( tail > 0 ) {
			byte b = mBuffer[ bytePos ];
			if( align ) {
				b = b >> ( 8 - tail );
			} else {
				b = b & ( 0xff << ( 8 - tail ) );
			}
			data[ fullBytes ] = b;
		} 

	} else {
		for ( u32 i = 0; i < fullBytes; i++ ) {
			u8 b0 = mBuffer[ bytePos ] << mod8;
			u8 b1 = mBuffer[ bytePos + 1 ] >> ( 8-mod8 );
			u8 byte = b0 | b1;
			data[ i ] = byte;
			bytePos += 1;
		}
		if ( tail > 0 ) {
			byte b = mBuffer[ bytePos ] << mod8;
			if( mod8 + tail > 8 ) { b = b|( mBuffer[ bytePos+1 ] >> ( 8 - mod8 ) ); }
			if( align ) {
				data[ fullBytes ] = b >> ( 8 - tail );
			} else {
				data[ fullBytes ] = b & ( 0xff << ( 8 - tail) );
			}
		}

	}
	mBitPos += bitLength;
}

//----------------------------------------------------------------//
void MOCKNetworkStream::SkipBits ( u32 bitLength ) {
	mBitPos = min( mBitPos + bitLength, mBitSize );
}

//----------------------------------------------------------------//
void MOCKNetworkStream::AlignRead () {
	u32 mod8 = mBitPos & 7;
	if( mod8 > 0 ) SkipBits( 8 - mod8 );
}

void MOCKNetworkStream::AlignWrite () {
	u32 mod8 = mBitSize & 7;
	if( mod8 > 0 ) {
		byte i = 0;
		WriteBits( &i, 8 - mod8, false );
	}
}

//----------------------------------------------------------------//
bool MOCKNetworkStream::ReadOneBit () {
	if( mBitPos + 1 > mBitSize ) return false;
	bool result = ( ( mBuffer[ mBitPos >> 3 ] & ( 0x80 >> ( mBitPos & 7 ) ) ) != 0 );
	mBitPos += 1;
	return result;
}

//----------------------------------------------------------------//
bool MOCKNetworkStream::WriteOneBit ( bool b = true ) {
	AffirmBuffer( 1 );
	u32 mod8 = mBitSize & 7;	
	if( b ) { //true
		if( mod8 == 0 ) {
			mBuffer[ mBitSize >> 3 ] = 0x80;
		} else {
			mBuffer[ mBitSize >> 3 ] |= ( 0x80 >> mod8 );
		}
	} else { //false
		if( mod8 == 0 ) mBuffer[ mBitSize >> 3 ] = 0;
	}
	mBitSize += 1;
	return true;
}


//----------------------------------------------------------------//
void MOCKNetworkStream::WriteAlignBytes ( const byte* data, u32 byteLength ) {
	AlignWrite();
	u32 bitLength = byteLength << 3;
	AffirmBuffer( bitLength );
	memcpy( mBuffer + ( mBitSize >> 3 ), data, byteLength );
	mBitSize += bitLength;
}

bool MOCKNetworkStream::ReadAlignBytes ( byte* data, u32 byteLength ) {
	AlignRead();
	if( mBufferSize < ( mBitPos >> 3 ) + byteLength ) return false; //eof
	memcpy( data, mBuffer + ( mBitPos >> 3 ), byteLength );
	mBitPos += (byteLength << 3);
	return true;
}

//----------------------------------------------------------------//
//Common values
void MOCKNetworkStream::WriteTrue  () { WriteOneBit( true ); }
void MOCKNetworkStream::WriteFalse () { WriteOneBit( false ); }

void MOCKNetworkStream::WriteString ( STLString str ) {
	u16 length = str.length();
	WriteValue( length );
	const char* buffer = str.data();
	WriteAlignBytes( (byte*)buffer, length );
}

STLString MOCKNetworkStream::ReadString() {
	STLString str;
	u16 length = ReadValue < u16 >();
	const unsigned int MAX_HEAP_ALLOC = 1024;
	if ( length ) {
		byte* buffer;
		if ( length > MAX_HEAP_ALLOC ) {
			buffer = ( byte* )malloc ( length + 1 );
		}
		else {
			buffer = ( byte* )alloca ( length + 1 );
		}
		this->ReadAlignBytes ( buffer, length );
		buffer [ length ] = 0;
		str = ( char* )buffer;
		if ( length > MAX_HEAP_ALLOC ) {
			free ( buffer );
		}
	}
	return str;
}

void MOCKNetworkStream::WriteData ( char* buf, u16 length ) {
	WriteValue( length );
	WriteAlignBytes( (byte*)buf, length );
}

int MOCKNetworkStream::ReadData ( char* buf, u16 bufSize ) {
	u16 length = ReadValue < u16 >();
	char* buf1 = (char*) malloc( length );
	this->ReadAlignBytes ( (byte*)buf1, length );
	memcpy( buf, buf1, min( bufSize, length ) );
	return min( bufSize, length );
}
//----------------------------------------------------------------//
//SUB Stream
//<16> stream size (<64kb)
// !align
//< datasize >
void MOCKNetworkStream::WriteStream ( MOCKNetworkStream* stream ) {
	unsigned short size = ( unsigned short ) stream->GetByteSize();
	//todo: limit stream size
	WriteValue( size );
	WriteAlignBytes( stream->mBuffer, size );
}

MOCKNetworkStream* MOCKNetworkStream::ReadStream () {
	unsigned short size = ReadValue< unsigned short >();
	byte* data = (byte*) malloc( size );
	MOCKNetworkStream* stream = new MOCKNetworkStream();
	ReadAlignBytes( data, size );
	stream->mBuffer = data;
	stream->mBufferSize = size;
	stream->mBitSize = BYTE2BIT( size );
	return stream;
}

//----------------------------------------------------------------//
/* MESSAGES
<1> message flag
<8> message type id
<1> data flag
[... data body( child bit stream )]
*/
void MOCKNetworkStream::WriteMessage ( MOCKNetworkMessage* msg ) {
	WriteOneBit();
	byte t = (byte) msg->mType;
	WriteValue( t );
	if( msg->mDataStream ) {
		WriteOneBit( true );
		WriteStream( msg->mDataStream );
	} else {
		WriteOneBit( false );
	}
}

MOCKNetworkMessage* MOCKNetworkStream::ReadMessage () {
	if( !ReadOneBit() ) return NULL;
	MOCKNetworkMessage* msg = new MOCKNetworkMessage();	
	msg->mType = ( MOCKNetworkMessageType ) ReadValue< byte >();
	if( ReadOneBit() ) {
		msg->mDataStream = ReadStream();
	}
	return msg;
}

//----------------------------------------------------------------//
//Peer
void MOCKNetworkStream::WritePeer ( MOCKNetworkHost *host, MOCKNetworkPeer *peer ) {
	if( !peer ) { 
		WriteFalse();
		return;
	}
	WriteTrue(); //non-null
	assert( host == peer->mHost );
	//by address
	WriteTrue();
	WriteValue( peer->mHostIP );
	WriteValue( (u16)peer->mPort );	
	//TODO: short id
	//WriteFalse()
}

MOCKNetworkPeer* MOCKNetworkStream::ReadPeer ( MOCKNetworkHost *host ) {
	if( !ReadOneBit() )  //non null ?
		return NULL;

	if( ReadOneBit() ) { //send by address ?
		u32 ip   = ReadValue< u32 >();
		u16 port = ReadValue< u16 >();
		return host->GetPeer( ip, port, true );
	} else { //send by id ?
	//TODO

	}
	return NULL;
}

//----------------------------------------------------------------//
//RPC


//----------------------------------------------------------------//
//Helpers
//----------------------------------------------------------------//
// float32
// Martin Kallman
//
// Fast half-precision to single-precision floating point conversion
//  - Supports signed zero and denormals-as-zero (DAZ)
//  - Does not support infinities or NaN
//  - Few, partially pipelinable, non-branching instructions,
//  - Core opreations ~6 clock cycles on modern x86-64
void float32(float* __restrict out, const uint16_t in) {
		uint32_t t1;
		uint32_t t2;
		uint32_t t3;

		t1 = in & 0x7fff;                       // Non-sign bits
		t2 = in & 0x8000;                       // Sign bit
		t3 = in & 0x7c00;                       // Exponent
		
		t1 <<= 13;                              // Align mantissa on MSB
		t2 <<= 16;                              // Shift sign bit into position

		t1 += 0x38000000;                       // Adjust bias

		t1 = (t3 == 0 ? 0 : t1);                // Denormals-as-zero

		t1 |= t2;                               // Re-insert sign bit

		*((uint32_t*)out) = t1;
};

// float16
// Martin Kallman
//
// Fast single-precision to half-precision floating point conversion
//  - Supports signed zero, denormals-as-zero (DAZ), flush-to-zero (FTZ),
//    clamp-to-max
//  - Does not support infinities or NaN
//  - Few, partially pipelinable, non-branching instructions,
//  - Core opreations ~10 clock cycles on modern x86-64
void float16(uint16_t* __restrict out, const float in) {
		uint32_t inu = *((uint32_t*)&in);
		uint32_t t1;
		uint32_t t2;
		uint32_t t3;

		t1 = inu & 0x7fffffff;                 // Non-sign bits
		t2 = inu & 0x80000000;                 // Sign bit
		t3 = inu & 0x7f800000;                 // Exponent
		
		t1 >>= 13;                             // Align mantissa on MSB
		t2 >>= 16;                             // Shift sign bit into position

		t1 -= 0x1c000;                         // Adjust bias

		t1 = (t3 > 0x38800000) ? 0 : t1;       // Flush-to-zero
		t1 = (t3 < 0x8e000000) ? 0x7bff : t1;  // Clamp-to-max
		t1 = (t3 == 0 ? 0 : t1);               // Denormals-as-zero

		t1 |= t2;                              // Re-insert sign bit

		*((uint16_t*)out) = t1;
};