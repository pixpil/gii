#ifndef AKU_MODULES_CONFIG_H
#define AKU_MODULES_CONFIG_H

    #ifndef AKU_WITH_APPLE
		#define AKU_WITH_APPLE 0
	#endif

	#ifndef AKU_WITH_BOX2D
		#define AKU_WITH_BOX2D 1
	#endif

	#ifndef AKU_WITH_CRYPTO
		#define AKU_WITH_CRYPTO 1
	#endif

	#ifndef AKU_WITH_FMOD_DESIGNER
		#ifdef MOAI_OS_HTML
			#define AKU_WITH_FMOD_DESIGNER 0
		#else
			#define AKU_WITH_FMOD_DESIGNER 1
		#endif
	#endif

	#ifndef AKU_WITH_FMOD_EX
		#ifdef MOAI_OS_HTML
			#define AKU_WITH_FMOD_EX 0
		#else
			#define AKU_WITH_FMOD_EX 0
		#endif
	#endif

	#ifndef AKU_WITH_HARNESS
		#define AKU_WITH_HARNESS 0
	#endif

	#ifndef AKU_WITH_HTTP_CLIENT
		#define AKU_WITH_HTTP_CLIENT 1
	#endif

	#ifndef AKU_WITH_HTTP_SERVER
		#define AKU_WITH_HTTP_SERVER 0
	#endif

	#ifndef AKU_WITH_LUAEXT
		#define AKU_WITH_LUAEXT 1
	#endif

	#ifndef AKU_WITH_PLUGINS
		#define AKU_WITH_PLUGINS 0
	#endif

	#ifndef AKU_WITH_SDL
		#define AKU_WITH_SDL 0
	#endif

	#ifndef AKU_WITH_SIM
		#define AKU_WITH_SIM 1
	#endif

	#ifndef AKU_WITH_STEER
		#define AKU_WITH_STEER 1
	#endif

	#ifndef AKU_WITH_TURBOBADGER
		#define AKU_WITH_TURBOBADGER 1
	#endif
	
	#ifndef AKU_WITH_IMGUI
		#define AKU_WITH_IMGUI 1
	#endif

	#ifndef AKU_WITH_UNTZ
		#ifdef MOAI_OS_HTML
			#define AKU_WITH_UNTZ 1
		#else
			#define AKU_WITH_UNTZ 0
		#endif
	#endif

	#ifndef AKU_WITH_UTIL
		#define AKU_WITH_UTIL 1
	#endif

#endif
