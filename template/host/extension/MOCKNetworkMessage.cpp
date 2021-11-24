#include "MOCKNetworkMessage.h"


void MOCKNetworkMessage::Init( MOCKNetworkMessageType msgType, MOCKNetworkPeer *sender, MOCKNetworkStream* stream ) {
	mType   = msgType;
	mSender = sender;
	mReliable = true;
	mChannel	= 0;
	mDataStream = stream;
}

MOCKNetworkMessage::MOCKNetworkMessage() {
	Init( NETWORK_MESSAGE_UNKNOWN, NULL, NULL );	
}

MOCKNetworkMessage::MOCKNetworkMessage( MOCKNetworkMessageType msgType, MOCKNetworkPeer *sender ) {
	Init( msgType, sender, NULL );
}

MOCKNetworkMessage::MOCKNetworkMessage( MOCKNetworkMessageType msgType, MOCKNetworkPeer *sender, MOCKNetworkStream* stream ) {
	Init( msgType, sender, stream );
}

MOCKNetworkMessage::~MOCKNetworkMessage() {
	if( mDataStream ) {
		delete mDataStream;
	}
}

//----------------------------------------------------------------//
ENetPacket* MOCKNetworkMessage::BuildPacket () {
	//todo
	MOCKNetworkStream stream;
	u32 flags = 0;
	if( mReliable ) { 
		flags |= ENET_PACKET_FLAG_RELIABLE;
	} else {
		flags |= ENET_PACKET_FLAG_UNSEQUENCED;
	}
	stream.WriteMessage( this );
	ENetPacket *packet = enet_packet_create( stream.GetBuffer(), stream.GetByteSize(), flags );
	return packet;
}

//----------------------------------------------------------------//
MOCKNetworkMessage* MOCKNetworkMessage::Clone() {
	MOCKNetworkMessage* msg = new MOCKNetworkMessage();
	if( mDataStream )
		msg->mDataStream = mDataStream->Clone();
	msg->mType     = mType;
	msg->mSender   = mSender;
	msg->mReliable = mReliable;
	msg->mChannel  = mChannel;
	return msg;
}