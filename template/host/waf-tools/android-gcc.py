#! /usr/bin/env python
# encoding: utf-8
# WARNING! Do not edit! http://waf.googlecode.com/git/docs/wafbook/single.html#_obtaining_the_waf_file

import os,sys
from waflib import Configure,Options,Utils
from waflib.Tools import ccroot
from waflib.Configure import conf
@conf
def find_android_gcc(conf):
	exeDir = os.path.join(conf.options.ndk, "toolchains", "arm-linux-androideabi-4.6", "prebuilt", "windows-x86_64", "bin")
	cc=conf.find_program(['arm-linux-androideabi-gcc'], var = "CXX", path_list=[exeDir])
	cc=conf.cmd_to_list(cc)
	conf.get_cc_version(cc,gcc=True)
	conf.env.CC_NAME='gcc'
	conf.env.CC=cc
@conf
def gcc_common_flags(conf):
	v=conf.env
	v['CC_SRC_F']=[]
	v['CC_TGT_F']=['-c','-o']
	if not v['LINK_CC']:v['LINK_CC']=v['CC']
	v['CCLNK_SRC_F']=[]
	v['CCLNK_TGT_F']=['-o']
	v['CPPPATH_ST']='-I%s'
	v['DEFINES_ST']='-D%s'
	v['LIB_ST']='-l%s'
	v['LIBPATH_ST']='-L%s'
	v['STLIB_ST']='-l%s'
	v['STLIBPATH_ST']='-L%s'
	v['RPATH_ST']='-Wl,-rpath,%s'
	v['SONAME_ST']='-Wl,-h,%s'
	v['SHLIB_MARKER']='-Wl,-Bdynamic'
	v['STLIB_MARKER']='-Wl,-Bstatic'
	v['cprogram_PATTERN']='%s'
	v['CFLAGS_cshlib']=['-fPIC']
	v['LINKFLAGS_cshlib']=['-shared']
	v['cshlib_PATTERN']='lib%s.so'
	v['LINKFLAGS_cstlib']=['-Wl,-Bstatic']
	v['cstlib_PATTERN']='lib%s.a'
	v['LINKFLAGS_MACBUNDLE']=['-bundle','-undefined','dynamic_lookup']
	v['CFLAGS_MACBUNDLE']=['-fPIC']
	v['macbundle_PATTERN']='%s.bundle'
@conf
def android_gcc_modifier_android9(conf):
	v=conf.env
	v['CFLAGS']=[
		"-fPIC",
		"-ffunction-sections",
		"-funwind-tables",
		"-fstack-protector",
		"-D__ARM_ARCH_5__",
		"-D__ARM_ARCH_5T__",
		"-D__ARM_ARCH_5E__",
		"-D__ARM_ARCH_5TE__",
		"-Wno-psabi",
		"-mthumb",
		"-Os",
		"-fomit-frame-pointer",
		"-fno-strict-aliasing",
		"-finline-limit=64",
		"-DANDROID"
	]
	
	if v.TARGET_ARCH == "armv6":
		v.append_unique('CFLAGS', [
			"-march=armv5te",
			"-mtune=xscale",
			"-msoft-float"
		])
	elif v.TARGET_ARCH == "armv7":
		v.append_unique('CFLAGS', [
			"-march=armv7-a",
			"-mfloat-abi=softfp",
			"-mfpu=vfpv3-d16"
		])
		v.append_unique('LINKFLAGS', [
			"-march=armv7-a",
			"-Wl,--fix-cortex-a8"
		])
	
	android_arch = "arm"
	if conf.env.TARGET_ARCH == "mips":
		android_arch = "mips"
	elif conf.env.TARGET_ARCH == "x86":
		android_arch = "x86"
	
	sysroot = os.path.join(conf.options.ndk, "platforms/android-9/arch-" + android_arch)
	v.append_unique('CFLAGS', ["--sysroot=" + sysroot])
	v.append_unique('LINKFLAGS', ["--sysroot=" + sysroot])

@conf
def android_gcc_modifier_platform(conf):
	android_gcc_modifier_func=getattr(conf,'android_gcc_modifier_'+conf.env.TARGET_OS,None)
	if android_gcc_modifier_func:
		android_gcc_modifier_func()
def configure(conf):
	conf.find_android_gcc()
	conf.load('android-ar', tooldir="waf-tools")
	conf.gcc_common_flags()
	conf.android_gcc_modifier_platform()
	conf.cc_load_tools()
	conf.cc_add_flags()
	conf.link_add_flags()
