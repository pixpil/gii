#include "freejoyWrapper.h"
#include "stdio.h"
#include "stdlib.h"
#include "string.h"
//----------------------------------------------------------------//
//State
//----------------------------------------------------------------//
FreeJoyState::FreeJoyState() {
	mPort       = 0;
	mPollTime   = 0;
	memset( mHitCounts,  0, sizeof( mHitCounts ) );
	memset( mAxisStates, 0, sizeof( mAxisStates ) );
}

void FreeJoyState::Flush() {
	memset( mHitCounts,  0, sizeof( mHitCounts ) );
	memset( mAxisStates, 0, sizeof( mAxisStates ) );
}

void FreeJoyState::Poll( FreeJoyManager* manager ) {
	int buttonStates0;
	int buttonStates1;
	float axisStates1[ MAX_JOYSTICK_AXIS_COUNT ];
	memset( axisStates1, 0, sizeof( axisStates1 ) );

	ReadJoy( mPort, &buttonStates1, &axisStates1[ 0 ] );
		// if( axisId == 0 ) printf( "%.2f\n", v1) ;

	buttonStates0 = mButtonStates;
	if ( buttonStates1 != buttonStates0 ) {
		for( int btnId = 0; btnId < MAX_JOYSTICK_BUTTON_COUNT; ++btnId ) {
			int mask = 1 << btnId;
			bool b0 = (buttonStates0 & mask) != 0;
			bool b1 = (buttonStates1 & mask) != 0;
			if( b0 != b1 ) manager->SendButtonEvent( mId, btnId, b1 );
		}
		mButtonStates = buttonStates1;
	}

	for ( int axisId = 0; axisId < MAX_JOYSTICK_AXIS_COUNT; ++axisId ) {
		float v0 = mAxisStates[ axisId ];
		float v1 = axisStates1[ axisId ];
		float diff = v0 - v1;
		if( diff < -0.01f || diff > 0.01f ) {
			mAxisStates[ axisId ] = v1;
			manager->SendAxisEvent( mId, axisId, v1 );
		}
	}
}

//----------------------------------------------------------------//
//Manager
//----------------------------------------------------------------//
FreeJoyManager::FreeJoyManager() {
	mButtonListener = 0;
	mAxisListener   = 0;
	mJoystickCount  = 0;
}

void FreeJoyManager::Refresh() {
	mJoystickCount = JoyCount();
	for( int i = 0; i < this->mJoystickCount; ++i ) {
		this->mJoysticks[ i ].mPort = i;
		this->mJoysticks[ i ].mId   = i;
	}
	printf("found joy: %d\n", mJoystickCount );
}

void FreeJoyManager::Update() {
	for( int i = 0; i < this->mJoystickCount; ++i ) {
		this->mJoysticks[ i ].Poll( this );
	}
}

void FreeJoyManager::SetButtonListener ( FreeJoyButtonListener listener  ) {
	this->mButtonListener = listener;
}

void FreeJoyManager::SetAxisListener ( FreeJoyAxisListener listener  ) {
	this->mAxisListener = listener;
}


void FreeJoyManager::SendButtonEvent ( int joyId, int btnId, bool down ) {
	if( !this->mButtonListener ) return ;
	this->mButtonListener( joyId, btnId, down );
}

void FreeJoyManager::SendAxisEvent ( int joyId, int axisId, float value ) {
	if( !this->mAxisListener ) return ;
	this->mAxisListener( joyId, axisId, value );
}

