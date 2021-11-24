#ifndef MOAI_HOST_CONFIG_H
#define MOAI_HOST_CONFIG_H

	// // #define MOAI_WITH_ARES              0
	// // #define MOAI_HOST_USE_AUDIOSAMPLER  0
	#define MOAI_WITH_BOX2D             1
	// #define MOAI_WITH_CHIPMUNK          0
	// #define MOAI_WITH_EXPAT             1
	#ifdef MOAI_WITH_FMOD_DESIGNER
		#undef MOAI_WITH_FMOD_DESIGNER
		#define MOAI_WITH_FMOD_DESIGNER     1
	#endif
	// #define MOAI_WITH_FMOD_EX           0
	// #define MOAI_WITH_FOLDER_WATCHER    0
	// #define MOAI_WITH_FREETYPE          1
	// #define MOAI_WITH_GPB               1
	// #define MOAI_WITH_HARNESS           0
	// #define MOAI_WITH_HTTP_CLIENT       1
	// #define MOAI_WITH_JANSSON           1
	// #define MOAI_WITH_LIBCRYPTO         1
	// #define MOAI_WITH_LIBCURL           1
	// #define MOAI_WITH_LIBJPG            1
	// #define MOAI_WITH_LIBPNG            1
	// #define MOAI_WITH_LUAEXT            1
	// // #define MOAI_WITH_MONGOOSE          1
	// // #define MOAI_WITH_OGG               1
	// #define MOAI_WITH_OPENSSL           1
	// #define MOAI_WITH_TINYXML           1
	// #define MOAI_WITH_SFMT              1
	// #define MOAI_WITH_SQLITE            1
	// #define MOAI_WITH_TLSF              1
	// #define MOAI_WITH_UNTZ              0
	// #define MOAI_WITH_VORBIS            0
	// // #define MOAI_GFX_DUMMY              0
	// // #define MOAI_GFX_FLASCC             0
	// // #define MOAI_GFX_OPENGL             1	

#endif