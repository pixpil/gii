cdef extern from *:
	ctypedef char* const_char_ptr "const char*"

ctypedef void (*funcOpenWindow)( const_char_ptr title, int width, int height)
ctypedef void (*funcEnterFullscreen)()
ctypedef void (*funcExitFullscreen)()


cdef extern from "moai-core/host.h" nogil:
	# moai-core
	# context api
	void		AKUClearMemPool				()
	int			AKUCreateContext			()
	void		AKUDeleteContext			( int context )
	int			AKUGetContext				()
	void*		AKUGetUserdata				()
	void		AKUFinalize				()
	void		AKUInitMemPool				( size_t sizeInBytes )
	void		AKUSetContext				( int context )
	void		AKUSetUserdata				( void* user )

	#management
	lua_State*		AKUGetLuaState				()
	char*		AKUGetMoaiVersion       		( char* buffer, int length )
	char*		AKUGetWorkingDirectory  		( char* buffer, int length )
	int			AKUMountVirtualDirectory		( const_char_ptr virtualPath, const_char_ptr archive )
	
	void		AKULoadFuncFromBuffer   	( void* data, size_t size, int dataType, int compression )
	void		AKULoadFuncFromFile				( const char* filename )
	void		AKULoadFuncFromString			( const char* script )
	void		AKUCallFunc						()
 	# void		AKUCallFuncWithArgArray			( char* exeName, char* scriptName, int argc, char** argv, int asParams );
 	# void		AKUCallFuncWithArgString		( char* exeName, char* scriptName, char* args, int asParams );

	int			AKUSetWorkingDirectory		( const_char_ptr path )
	

cdef extern from "moai-sim/host.h" nogil:
	ctypedef struct lua_State:
		pass
		
	#...
	# void		AKUFinalizeSim	   		()
	# void		AKUInitializeSim			()
	void    AKUAppInitialize()
	void    AKUAppFinalize()

	#....
	void		AKUSetOrientation			( int orientation )
	void		AKUSetScreenDpi				( int dpi )
	void		AKUSetScreenSize			( int width, int height )
	void		AKUSetViewSize				( int width, int height )
	void		AKUSoftReleaseGfxResources		( int age )
	void		AKUUpdate				()


	# call back
	void AKUSetFunc_OpenWindow(funcOpenWindow func)
	void AKUSetFunc_EnterFullscreenMode(funcEnterFullscreen func)
	void AKUSetFunc_ExitFullscreenMode(funcExitFullscreen func)


	#moai-sim
	void		AKUDetectGfxContext			()
	double		AKUGetSimStep				()
	void		AKUPause				( bint pause )
	void		AKUReleaseGfxContext		()
	void		AKURender				()

	# input device api
	void		AKUReserveInputDevices		( int total )
	void		AKUReserveInputDeviceSensors	( int deviceID, int total )
	void		AKUSetInputConfigurationName	( const_char_ptr name )
	void		AKUSetInputDevice			( int deviceID, const_char_ptr name )
	void		AKUSetInputDeviceActive		( int deviceID, bint active )
	void		AKUSetInputDeviceButton		( int deviceID, int sensorID, const_char_ptr name )
	void		AKUSetInputDeviceCompass		( int deviceID, int sensorID, const_char_ptr name )
	void		AKUSetInputDeviceKeyboard		( int deviceID, int sensorID, const_char_ptr name )
	void		AKUSetInputDeviceLevel		( int deviceID, int sensorID, const_char_ptr name )
	void		AKUSetInputDeviceLocation		( int deviceID, int sensorID, const_char_ptr name )
	void		AKUSetInputDevicePointer		( int deviceID, int sensorID, const_char_ptr name )
	void		AKUSetInputDeviceTouch		( int deviceID, int sensorID, const_char_ptr name )
	void		AKUSetInputDeviceWheel		( int deviceID, int sensorID, const_char_ptr name )

	# input events api
	void		AKUEnqueueButtonEvent		( int deviceID, int sensorID, bint down )
	void		AKUEnqueueCompassEvent		( int deviceID, int sensorID, float heading )
	void		AKUEnqueueKeyboardKeyEvent		( int deviceID, int sensorID, int keyID, bint down )
	void		AKUEnqueueKeyboardTextEvent		( int deviceID, int sensorID, const_char_ptr text )
	void		AKUEnqueueKeyboardCharEvent		( int deviceID, int sensorID, int char )
	void		AKUEnqueueLevelEvent		( int deviceID, int sensorID, float x, float y, float z )
	void		AKUEnqueueLocationEvent		( int deviceID, int sensorID, double longitude, double latitude, double altitude, float hAccuracy, float vAccuracy, float speed )
	void		AKUEnqueuePointerEvent		( int deviceID, int sensorID, int x, int y )
	void		AKUEnqueueTouchEvent		( int deviceID, int sensorID, int touchID, bint down, float x, float y )
	void		AKUEnqueueTouchEventCancel		( int deviceID, int sensorID )
	void		AKUEnqueueWheelEvent		( int deviceID, int sensorID, float value )

cdef extern from "moai-fmod-designer/host.h" nogil:
	void    AKUFmodDesignerUpdate()

cdef extern from "aku_modules.h" nogil:
	void		AKUModulesAppFinalize       ()
	void		AKUModulesAppInitialize     ()
	void		AKUModulesContextInitialize ()
	void		AKUModulesRunLuaAPIWrapper  ()
	void		AKUModulesUpdate            ()

cdef extern from "extensionClasses.h" nogil:
	void registerExtensionClasses()

cdef extern from "helpers.h" nogil:
	void registerHelpers()

