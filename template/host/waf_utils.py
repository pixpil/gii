import commands
import glob
import os
import sys


from waflib import Build, Logs, Node, Options, Task, TaskGen, Utils

##----------------------------------------------------------------##
@TaskGen.extension('.mm')
def mm_hook(self, node):
	"Bind the c++ file extensions to the creation of a :py:class:`waflib.Tools.cxx.cxx` instance"
	return self.create_compiled_task('mm', node)
 
class mm(Task.Task):
	"Compile MM files into object files"
	run_str = '${CXX} ${ARCH_ST:ARCH} ${MMFLAGS} ${FRAMEWORKPATH_ST:FRAMEWORKPATH} ${CPPPATH_ST:INCPATHS} ${DEFINES_ST:DEFINES} ${CXX_SRC_F}${SRC} ${CXX_TGT_F}${TGT}'
	vars    = ['CXXDEPS'] # unused variable to depend on, just in case
	ext_in  = ['.h'] # set the build order easily by using ext_out=['.h']


# ##----------------------------------------------------------------##
_IOS_ARCH   = 'armv7'
_IOS_DEVICE = 'iPhoneOS'
def GetDevRootIOS():
	PLATFORMS_PATHS = [
		'/Applications/Xcode.app/Contents/Developer/Platforms',
		'/Developer/Platforms',
		]
	for pdir in PLATFORMS_PATHS:
		d = '%s/%s.platform/Developer' % (pdir, _IOS_DEVICE )
		if os.path.exists(d):
			return d
	return '/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain'
	
def prepareEnvIOS( ctx ):
	minimalVersion = '4.3'
	devRoot = GetDevRootIOS()
	ctx.env.IOS_DEV_ROOT = devRoot

	device  = ctx.env.IOS_DEVICE or _IOS_DEVICE
	arch    = ctx.env.IOS_ARCH   or _IOS_ARCH

	for ver in ['4.3','5.0', '5.1', '6.0', '6.1']:
		path = '{0}/SDKs/{1}{2}.sdk'.format( devRoot, device, ver )
		if os.path.isdir(path):  break

	ctx.env.IOS_SDK_ROOT = SDKRoot = path
	
	# Compiler and linker flags
	cflags = '-arch %s -pipe -miphoneos-version-min=%s -isysroot %s ' % ( arch, minimalVersion, SDKRoot )
	ctx.env.CC  = devRoot + '/usr/bin/gcc'
	ctx.env.CXX = devRoot + '/usr/bin/g++'
	ctx.env.LINK_CC  = devRoot + '/usr/bin/gcc'
	ctx.env.LINK_CXX = devRoot + '/usr/bin/g++'
	ctx.env.CXXFLAGS = Utils.to_list(cflags)  # -std=c++0x -no-cpp-precomp
	# ctx.env.CXXFLAGS.append += '-x object')
	ctx.env.CXXFLAGS.append('-I%s/usr/include' % SDKRoot )
	ctx.env.DEFINES.append('IOS')

	ctx.env.CXXFLAGS.append( '-F%s/System/Library/Frameworks' % SDKRoot )
	ctx.env.LINKFLAGS.append( '-F%s/System/Library/Frameworks' % SDKRoot )

	ctx.env.MMFLAGS = ctx.env.CXXFLAGS[:]
	# ctx.env.CXXFLAGS.append(
	# 	'-I%s/System/Library/Frameworks/OpenGLES.framework/Headers/ES1' % SDKRoot )
	# ctx.env.CXXFLAGS.append(
	# 	'-I%s/System/Library/Frameworks/OpenGLES.framework/Headers/ES2'	% SDKRoot )
	# ctx.env.DEFINES.append('WHISPER_DATA_MUTEX_POOL_SIZE=25')
	# ctx.env.LINKFLAGS += [ '-arch', arch ]
	# ctx.env.LINKFLAGS += [ '-isysroot',  SDKRoot ]
	# ctx.env.LINKFLAGS += [ '-miphoneos-version-min=' + minimalVersion ]
	ctx.env.CFLAGS       = ctx.env.CXXFLAGS
	ctx.env.LINKFLAGS    = ctx.env.CXXFLAGS
	# if device != 'iPhoneOS.Simulator':
	# 	ctx.env.LINKFLAGS.extend(['-syslibroot', SDKRoot])


# ##----------------------------------------------------------------##
# _ANDROID_NDK_PATH = '/Users/tommo/dev/android-ndk-r8'
# _ANDROID_NDK_VER  = '14'
# _ANDROID_NDK_ARCH = 'arm'
# def GetSDKRootAndroid():
# 	return _ANDROID_NDK_PATH + '/platforms/android-%s/arch-%s' % ( _ANDROID_NDK_VER, _ANDROID_NDK_ARCH )	


# ##----------------------------------------------------------------##