import os

##----------------------------------------------------------------##
MOAI_LIB_DEFAULT  = '/Users/feng_ye/Projects/moai-lib'
MOAI_ROOT_DEFAULT = '/Users/feng_ye/Projects/moai-dev'
FMOD_ROOT_DEFAULT = '/Users/feng_ye/DevLibrary/fmodex'
FMOD_ROOT         = '/Users/feng_ye/DevLibrary/fmodex'

##----------------------------------------------------------------##
#env path helpers
def setup_moai_env( ctx, target, config ):
	ctx.env.INCLUDES_MOAI = find_moai_includes()
	LIB_NAMES  = [ 
		'moai-%s',
		'moai-%s-sim',
		'moai-%s-3rdparty-core',
		'moai-%s-3rdparty-crypto',
		# 'moai-%s-3rdparty-curl',
		'moai-%s-luaext',
		'moai-%s-zl-vfs',
		'moai-%s-zl-core',
		'moai-%s-zl-crypto',
		'moai-%s-box2d',
		'moai-%s-untz',
		'moai-%s-crypto',
		# 'moai-%s-lua',
		'moai-%s-http-client',
		'moai-%s-steer',
		]

	if target == 'ios':
		LIB_NAMES += [
			'moai-%s-twitter',
			'moai-%s-crittercism'
		]
	else:
		LIB_NAMES += [
			'moai-%s-3rdparty-sdl'
		]

	if target == 'osx':
		LIB_NAMES += [
			'moai-%s-apple'
		]

	LIB_NAMES += [ 
		# 'moai-%s-fmod-ex',
		'moai-%s-fmod-designer'
		]
	
	MOAI_LIB  =  os.environ.get( 'MOAI_LIB', MOAI_LIB_DEFAULT )

	ctx.env.LIBPATH_MOAI  = [ MOAI_LIB + '/%s-%s' % ( config, target ) ]
	ctx.env.LIBPATH_MOAI  += [ MOAI_LIB ]
	ctx.env.LIB_MOAI      = [ n % target for n in LIB_NAMES ]
	ctx.env.CXXFLAGS_MOAI   = [
		'-DMOAI_WITH_LUAEXT', 
		'-DMOAI_WITH_BOX2D', 
		'-DMOAI_WITH_FMOD_DESIGNER',
		'-DMOAI_WITH_HTTP_CLIENT'
	]	
	
	ctx.env.LIBPATH_LUA = [ MOAI_LIB ]
	ctx.env.LIB_LUA     = [ 'lua' ]

	ctx.env.LIBPATH_LUAJIT = [ MOAI_LIB ]
	ctx.env.LIB_LUAJIT     = [ 'luajit' ]
	ctx.env.CXXFLAGS_LUAJIT  = [ '-DMOAI_WITH_LUAJIT' ]

##----------------------------------------------------------------##
def setup_moai_html5_env( ctx, target, config ):
	MOAI_LIB  =  os.environ.get( 'MOAI_LIB', MOAI_LIB_DEFAULT )
	ctx.env.MOAI_ROOT = find_moai_lib_root()
	ctx.env.MOAI_LIB  = os.environ.get( 'MOAI_LIB', MOAI_LIB_DEFAULT )
	ctx.env.INCLUDES_MOAIHTML5 = find_moai_includes()
	ctx.env.LIBPATH_MOAIHTML5  = [ MOAI_LIB + '/html5' ]
	ctx.env.LIB_MOAIHTML5 = [
		'png',
		'sfmt',
		'tess2',
		'tinyxml',
		'tlsf',
		'untz',
		'webp',
		'zlib',
		'box2d',
		'contrib',
		'crypto',
		'freetype',
		'jansson',
		'liblua-static',
		'zlvfs','zlcore',
		'moai-box2d',
		'moai-core',
		'moai-crypto',
		'moai-sim',
		'moai-untz',
		'moai-util',
		'host-modules'
		# 'moaishared'
	]
			
	ctx.env.CFLAGS_MOAIHTML5 = [ '-DMOAI_OS_HTML' ]
	ctx.env.CXXFLAGS_MOAIHTML5 = [
		'-DMOAI_OS_HTML',
		'-DGL_ES',
		'-DMOAI_WITH_BOX2D=1',
		'-DAKU_WITH_BOX2D=1',
		'-DMOAI_WITH_CHIPMUNK=0',
		'-DAKU_WITH_CHIPMUNK=0',
		'-DMOAI_WITH_LIBCURL=0',
		'-DMOAI_WITH_UNTZ=1',
		'-DAKU_WITH_UNTZ=1',
		'-DMOAI_WITH_TINYXML=1',
		'-DMOAI_WITH_HTTP_CLIENT=0',
		'-DAKU_WITH_HTTP_CLIENT=0',
		'-DMOAI_WITH_EXPAT=0',
		'-DMOAI_WITH_LIBCRYPTO=1',
		'-DMOAI_WITH_OPENSSL=0',
		'-DMOAI_WITH_FREETYPE=1',
		'-DAKU_WITH_LUAEXT=0',
		'-DMOAI_WITH_LUAEXT=0',
		'-DMOAI_WITH_SQLITE=0',
		'-DMOAI_WITH_JANSSON=1',
		'-DMOAI_WITH_SFMT=1',
		'-DMOAI_WITH_LIBPNG=1',
		'-DMOAI_WITH_LIBJPG=0',
		'-DMOAI_WITH_VORBIS=0',
		'-DMOAI_WITH_OGG=0',
		'-DMOAI_WITH_SDL=0',
		'-DMOAI_WITH_MONGOOSE=0',
		'-DMOAI_WITH_LUAJIT=0',
		'-DAKU_WITH_PLUGINS=0',
		'-DAKU_WITH_TEST=0',
		'-DAKU_WITH_HTTP_SERVER=0 ',
	]
	ctx.env.LINKFLAGS_MOAIHTML5 = [ 
		'-DMOAI_OS_HTML',
		'-DGL_ES',
		'-DMOAI_WITH_BOX2D=1',
		'-DAKU_WITH_BOX2D=1',
		'-DMOAI_WITH_CHIPMUNK=0',
		'-DAKU_WITH_CHIPMUNK=0',
		'-DMOAI_WITH_LIBCURL=0',
		'-DMOAI_WITH_UNTZ=1',
		'-DAKU_WITH_UNTZ=1',
		'-DMOAI_WITH_TINYXML=1',
		'-DMOAI_WITH_HTTP_CLIENT=0',
		'-DAKU_WITH_HTTP_CLIENT=0',
		'-DMOAI_WITH_EXPAT=0',
		'-DMOAI_WITH_LIBCRYPTO=1',
		'-DMOAI_WITH_OPENSSL=0',
		'-DMOAI_WITH_FREETYPE=1',
		'-DAKU_WITH_LUAEXT=0',
		'-DMOAI_WITH_LUAEXT=0',
		'-DMOAI_WITH_SQLITE=0',
		'-DMOAI_WITH_JANSSON=1',
		'-DMOAI_WITH_SFMT=1',
		'-DMOAI_WITH_LIBPNG=1',
		'-DMOAI_WITH_LIBJPG=0',
		'-DMOAI_WITH_VORBIS=0',
		'-DMOAI_WITH_OGG=0',
		'-DMOAI_WITH_SDL=0',
		'-DMOAI_WITH_MONGOOSE=0',
		'-DMOAI_WITH_LUAJIT=0',
		'-DAKU_WITH_PLUGINS=0',
		'-DAKU_WITH_TEST=0',
		'-DAKU_WITH_HTTP_SERVER=0 ',
	]
####----------------------------------------------------------------##
def find_moai_lib_root():
	MOAI_ROOT =  os.environ.get( 'MOAI_ROOT', MOAI_ROOT_DEFAULT )
	return MOAI_ROOT

####----------------------------------------------------------------##
def find_fmod_lib_root():
	FMOD_ROOT =  os.environ.get( 'FMOD_ROOT', FMOD_ROOT_DEFAULT )
	return FMOD_ROOT

##----------------------------------------------------------------##
def find_moai_includes():
	MOAI_ROOT =  find_moai_lib_root()
	
	moaiSources   = [
		MOAI_ROOT + '/src',
		MOAI_ROOT + '/src/moaicore',
		MOAI_ROOT + '/src/config-default'
	]

	MOAI_THRIDPARTY_PATH = MOAI_ROOT + '/3rdparty'
	thirdParties = [
		MOAI_THRIDPARTY_PATH,
		MOAI_THRIDPARTY_PATH + '/chipmunk-5.3.4/include',
		MOAI_THRIDPARTY_PATH + '/box2d-2.3.0',
		MOAI_THRIDPARTY_PATH + '/freetype-2.4.4/include',
		MOAI_THRIDPARTY_PATH + '/tinyxml',
		MOAI_THRIDPARTY_PATH + '/lua-5.1.3/src',
		MOAI_THRIDPARTY_PATH + '/jansson-2.1/src',
		MOAI_THRIDPARTY_PATH + '/sfmt-1.4',
		MOAI_THRIDPARTY_PATH + '/expat-2.0.1/lib',
		MOAI_THRIDPARTY_PATH + '/sdl2-2.0.0/include',
		MOAI_THRIDPARTY_PATH + '/zlib-1.2.3',
	]

	commons = [ '.' ]
	return commons + moaiSources + thirdParties

##----------------------------------------------------------------##
def setup_fmod_env( ctx, target, config ):
	FMOD_ROOT =  find_fmod_lib_root()

	ctx.env.LIBPATH_FMOD   = [ FMOD_ROOT + '/%s/api/lib' % target ]
	ctx.env.LIBPATH_FMOD  += [ FMOD_ROOT + '/%s/fmoddesignerapi/api/lib' % target ]
	ctx.env.INCLUDES_FMOD  = [ FMOD_ROOT + '/%s/api/inc' % target ]
	ctx.env.INCLUDES_FMOD += [ FMOD_ROOT + '/%s/fmoddesignerapi/api/inc' % target ]
	if target == 'ios':
		ctx.env.LIB_FMOD      = [ 
			'fmodex_iphoneos', 
			'fmodevent_iphoneos', 
			'fmodeventnet_iphoneos'
		]
	else:
		ctx.env.LIB_FMOD      = [ 
			'fmodex',
			'fmodevent',
			'fmodeventnet'
		]

