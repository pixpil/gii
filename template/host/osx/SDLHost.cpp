// Copyright (c) 2010-2011 Zipline Games, Inc. All Rights Reserved.
// http://getmoai.com

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <moai-core/host.h>

#include <aku_modules.h>
#include <aku_modules_custom.h>

#include <host-sdl/SDLHost.h>

#include <freejoyWrapper.h>
#include <extensionClasses.h>

#include <SDL.h>

#define UNUSED(p) (( void )p)

namespace InputDeviceID {
	enum {
		DEVICE,
		TOTAL,
	};
}

namespace InputSensorID {
	enum {
		KEYBOARD,
		POINTER,
		MOUSE_LEFT,
		MOUSE_MIDDLE,
		MOUSE_RIGHT,
		TOUCH,
		JOYSTICK_1,
		JOYSTICK_2,
		JOYSTICK_3,
		JOYSTICK_4,
		TOTAL,
	};
}



static SDL_Window* sWindow = 0;
static FreeJoyManager sJoystickManager;

typedef int ( *DisplayModeFunc ) (int, SDL_DisplayMode *);
static void SetScreenSize ( DisplayModeFunc func);


//================================================================//
// aku callbacks
//================================================================//

void	_AKUEnterFullscreenModeFunc		();
void	_AKUExitFullscreenModeFunc		();
void	_AKUOpenWindowFunc				( const char* title, int width, int height );
void    _AKUShowCursor ();
void    _AKUHideCursor ();


//----------------------------------------------------------------//
void _AKUEnterFullscreenModeFunc () {
    //videomode change
  SDL_SetWindowFullscreen(sWindow, SDL_WINDOW_FULLSCREEN);
	SetScreenSize( SDL_GetCurrentDisplayMode );
}

//----------------------------------------------------------------//
void _AKUExitFullscreenModeFunc () {

  SDL_SetWindowFullscreen(sWindow, 0);
	SetScreenSize( SDL_GetDesktopDisplayMode );
}


//----------------------------------------------------------------//
void _AKUShowCursor () {
	SDL_ShowCursor(1);
}

//----------------------------------------------------------------//
void _AKUHideCursor () {
	SDL_ShowCursor(0);
}


//----------------------------------------------------------------//
void _AKUOpenWindowFunc ( const char* title, int width, int height ) {
	
	if ( !sWindow ) {
		sWindow = SDL_CreateWindow ( title, SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, width, height, SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN | SDL_WINDOW_RESIZABLE );
		SDL_GL_SetAttribute(SDL_GL_DEPTH_SIZE, 32);
		SDL_GL_CreateContext ( sWindow );
		SDL_GL_SetSwapInterval ( 1 );
		// SDL_SetWindowGrab( sWindow, SDL_TRUE );
		AKUDetectGfxContext ();
		AKUSetScreenSize ( width, height );
		// AKUSdlSetWindow ( sWindow );

		// SDL_StartTextInput ();
	}
}

//----------------------------------------------------------------//
void SetScreenSize(DisplayModeFunc func ) {

    SDL_DisplayMode dm;

    if ( func != NULL && func( 0, &dm ) == 0 ) {
    	AKUSetScreenSize(dm.w, dm.h);
    }
}


//----------------------------------------------------------------//
static void _JoyButtonFunc ( int joyId, int buttonId, bool down ) {
	printf("%d,%d,%d\n", joyId, buttonId, down );
	if( joyId == 1 ) {
		AKUEnqueueJoystickExButtonEvent( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_1, buttonId, down );
	} else if( joyId == 2 ) {
		AKUEnqueueJoystickExButtonEvent( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_2, buttonId, down );
	} else if( joyId == 3 ) {
		AKUEnqueueJoystickExButtonEvent( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_3, buttonId, down );
	} else if( joyId == 4 ) {
		AKUEnqueueJoystickExButtonEvent( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_4, buttonId, down );
	}
}

static void _JoyAxisFunc ( int joyId, int axisId, float value ) {
	printf("%d,%d,%.2f\n", joyId, axisId, value );
	if( joyId == 1 ) {
		AKUEnqueueJoystickExAxisEvent( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_1, axisId, value );
	} else if( joyId == 2 ) {
		AKUEnqueueJoystickExAxisEvent( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_2, axisId, value );
	} else if( joyId == 3 ) {
		AKUEnqueueJoystickExAxisEvent( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_3, axisId, value );
	} else if( joyId == 4 ) {
		AKUEnqueueJoystickExAxisEvent( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_4, axisId, value );
	}
}

//================================================================//
// helpers
//================================================================//

static void	Finalize			();
static void	Init				( int argc, char** argv );
static void	MainLoop			();
static void	PrintMoaiVersion	();

//----------------------------------------------------------------//
void Finalize () {

	AKUModulesCustomAppFinalize ();
	AKUModulesAppFinalize ();
	AKUAppFinalize ();
	
	SDL_Quit ();
}

//----------------------------------------------------------------//
void Init ( int argc, char** argv ) {

	SDL_Init ( SDL_INIT_EVERYTHING );

	// PrintMoaiVersion ();

	#ifdef _DEBUG
		printf ( "DEBUG BUILD\n" );
	#endif

	AKUAppInitialize ();
	AKUModulesAppInitialize ();
	AKUModulesCustomAppInitialize ();

	AKUCreateContext ();
	AKUModulesContextInitialize ();
	AKUModulesCustomContextInitialize ();
	// AKUModulesRunLuaAPIWrapper ();
	registerExtensionClasses();

	AKUSetInputConfigurationName ( "SDL" );

	AKUReserveInputDevices			( InputDeviceID::TOTAL );
	AKUSetInputDevice				( InputDeviceID::DEVICE, "device" );
	
	AKUReserveInputDeviceSensors	( InputDeviceID::DEVICE, InputSensorID::TOTAL );
	AKUSetInputDeviceKeyboard		( InputDeviceID::DEVICE, InputSensorID::KEYBOARD,		"keyboard" );
	AKUSetInputDevicePointer		( InputDeviceID::DEVICE, InputSensorID::POINTER,		"pointer" );
	AKUSetInputDeviceButton			( InputDeviceID::DEVICE, InputSensorID::MOUSE_LEFT,		"mouseLeft" );
	AKUSetInputDeviceButton			( InputDeviceID::DEVICE, InputSensorID::MOUSE_MIDDLE,	"mouseMiddle" );
	AKUSetInputDeviceButton			( InputDeviceID::DEVICE, InputSensorID::MOUSE_RIGHT,	"mouseRight" );

	AKUSetInputDeviceJoystickEx			( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_1,	"joystick-1" );
	AKUSetInputDeviceJoystickEx			( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_2,	"joystick-2" );
	AKUSetInputDeviceJoystickEx			( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_3,	"joystick-3" );
	AKUSetInputDeviceJoystickEx			( InputDeviceID::DEVICE, InputSensorID::JOYSTICK_4,	"joystick-4" );

	//init joysticks
	sJoystickManager.Refresh();
	sJoystickManager.SetAxisListener( _JoyAxisFunc );
	sJoystickManager.SetButtonListener( _JoyButtonFunc );

	AKUSetFunc_EnterFullscreenMode ( _AKUEnterFullscreenModeFunc );
	AKUSetFunc_ExitFullscreenMode ( _AKUExitFullscreenModeFunc );

	AKUSetFunc_ShowCursor ( _AKUShowCursor );
	AKUSetFunc_HideCursor ( _AKUHideCursor );

	AKUSetFunc_OpenWindow ( _AKUOpenWindowFunc );
	
	AKUModulesCustomRunBefore ();
	AKUModulesParseArgs ( argc, argv );
	AKUModulesCustomRunAfter ();
	
	atexit ( Finalize ); // do this *after* SDL_Init
}

//----------------------------------------------------------------//
void MainLoop () {

	Uint32 lastFrame = SDL_GetTicks();
	
	bool running = true;
	while ( running ) {
	
		SDL_Event sdlEvent;
		
		while ( SDL_PollEvent ( &sdlEvent )) {  
				 
			switch ( sdlEvent.type )  {
			
				case SDL_QUIT:
				
					running = false;
					break;
				
				case SDL_KEYDOWN:
				case SDL_KEYUP:
					switch( sdlEvent.key.keysym.sym ) {
						default:
							if( !sdlEvent.key.repeat )
							AKUEnqueueKeyboardKeyEvent ( InputDeviceID::DEVICE, InputSensorID::KEYBOARD, sdlEvent.key.keysym.sym & 0xffff, sdlEvent.key.type == SDL_KEYDOWN );
					}
					break;
					
				case SDL_MOUSEBUTTONDOWN:
				case SDL_MOUSEBUTTONUP:
	
					switch ( sdlEvent.button.button ) {
					
						case SDL_BUTTON_LEFT:
							AKUEnqueueButtonEvent ( InputDeviceID::DEVICE, InputSensorID::MOUSE_LEFT, ( sdlEvent.type == SDL_MOUSEBUTTONDOWN ));
							break;
						
						case SDL_BUTTON_MIDDLE:
							AKUEnqueueButtonEvent ( InputDeviceID::DEVICE, InputSensorID::MOUSE_MIDDLE, ( sdlEvent.type == SDL_MOUSEBUTTONDOWN ));
							break;
						
						case SDL_BUTTON_RIGHT:
							AKUEnqueueButtonEvent ( InputDeviceID::DEVICE, InputSensorID::MOUSE_RIGHT, ( sdlEvent.type == SDL_MOUSEBUTTONDOWN ));
							break;
					}

					break;

				case SDL_MOUSEMOTION:
				
					AKUEnqueuePointerEvent ( InputDeviceID::DEVICE, InputSensorID::POINTER, sdlEvent.motion.x, sdlEvent.motion.y );
					break;

				case SDL_WINDOWEVENT:
						switch( sdlEvent.window.event ) {
							case SDL_WINDOWEVENT_RESIZED:
								AKUSetScreenSize ( sdlEvent.window.data1, sdlEvent.window.data2 );
								AKUSetViewSize ( sdlEvent.window.data1, sdlEvent.window.data2 );
								// AKURender ();
								// SDL_GL_SwapWindow ( sWindow );
								break;
						}
			}
		}
		
		AKUModulesUpdate ();
		sJoystickManager.Update();

		
		AKURender ();
		SDL_GL_SwapWindow ( sWindow );
		
		Uint32 frameDelta = ( Uint32 )( AKUGetSimStep () * 1000.0 );
		Uint32 currentFrame = SDL_GetTicks ();
		Uint32 delta = currentFrame - lastFrame;
		
		if ( delta < frameDelta ) {
			SDL_Delay ( frameDelta - delta );
		}
		lastFrame = SDL_GetTicks();
	}
}

//----------------------------------------------------------------//
void PrintMoaiVersion () {

	static const int length = 255;
	char version [ length ];
	AKUGetMoaiVersion ( version, length );
	printf ( "%s\n", version );
}

//================================================================//
// SDLHost
//================================================================//

//----------------------------------------------------------------//
int SDLHost ( int argc, char** argv ) {

	Init ( argc, argv );

	if ( sWindow ) {
		MainLoop ();
	}

	return 0;
}
