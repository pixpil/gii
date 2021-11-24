#ifndef FREEJOYWRAPPER_H
#define FREEJOYWRAPPER_H
	
#include "freejoy.h"
	
#define MAX_JOYSTICK_COUNT 16
#define MAX_JOYSTICK_BUTTON_COUNT 16
#define MAX_JOYSTICK_AXIS_COUNT   16

class FreeJoyState;
class FreeJoyManager;

typedef void ( *FreeJoyButtonListener ) ( int joyId, int buttonId, bool down );
typedef void ( *FreeJoyAxisListener ) ( int joyId, int axisId, float value );

class FreeJoyState
	{
	friend class FreeJoyManager;
	private:
		int   mId;
		int   mPort;
		int   mPollTime;
		int   mButtonStates;
		int   mHitCounts  [ MAX_JOYSTICK_BUTTON_COUNT ];
		float mAxisStates [ MAX_JOYSTICK_AXIS_COUNT ];

	public:
		enum{
			JOY_X = 0,
			JOY_Y,
			JOY_Z,
			JOY_R,
			JOY_U,
			JOY_V,
			JOY_YAW,
			JOY_PITCH,
			JOY_ROLL,
			JOY_HAT,
			JOY_WHEEL
		};
		
		void Poll  ( FreeJoyManager* manager );
		void Flush ();
		// void GetName();

		inline float GetX() {
			return this->mAxisStates[ JOY_X ];
		};

		inline float GetY() {
			return this->mAxisStates[ JOY_Y ];
		};

		inline float GetZ() {
			return this->mAxisStates[ JOY_Z ];
		};
		
		inline float GetR() {
			return this->mAxisStates[ JOY_R ];
		};

		inline float GetU() {
			return this->mAxisStates[ JOY_U ];
		};

		inline float GetV() {
			return this->mAxisStates[ JOY_V ];
		};

		inline float GetYaw() {
			return this->mAxisStates[ JOY_YAW ];
		};

		inline float GetPitch() {
			return this->mAxisStates[ JOY_PITCH ];
		};

		inline float GetRoll() {
			return this->mAxisStates[ JOY_ROLL ];
		};

		inline float GetAxis( int i ) {
			if( i > MAX_JOYSTICK_COUNT - 1 ) i = MAX_JOYSTICK_COUNT - 1;
			return this->mAxisStates[ i ];
		};

		inline float IsDown( int button ) {
			return ( this->mButtonStates & ( 1 << button ) ) != 0;
		};

		FreeJoyState();

	};

class FreeJoyManager
{
private:
	int          mJoystickCount;
	FreeJoyState mJoysticks[ MAX_JOYSTICK_COUNT ];
	FreeJoyButtonListener  mButtonListener;
	FreeJoyAxisListener    mAxisListener;

public:
	void Refresh();
	void Update();

	int getJoystickCount() {
		return mJoystickCount;
	}

	void SetButtonListener  ( FreeJoyButtonListener listener  );
	void SetAxisListener    ( FreeJoyAxisListener listener  );

	void SendButtonEvent    ( int joyId, int btnId, bool down );
	void SendAxisEvent      ( int joyId, int axisId, float value );

	FreeJoyManager();
	// ~FreeJoyManager();

};

#endif