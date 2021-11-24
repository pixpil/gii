#! /usr/bin/env python
# encoding: utf-8
# WARNING! Do not edit! http://waf.googlecode.com/git/docs/wafbook/single.html#_obtaining_the_waf_file

import os,sys
from waflib import Configure,Options,Utils
from waflib.Tools import ccroot,ar
from waflib.Configure import conf
@conf
def find_emcc(conf):
	cc=conf.find_program(['emcc'],var='CC')
	cc=conf.cmd_to_list(cc)
	conf.env.CC_NAME='emcc'
	conf.env.CC=cc
@conf
def emcc_common_flags(conf):
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
def emcc_modifier_browser(conf):
	v=conf.env
	v['cprogram_PATTERN']='%s.html'
	v['cshlib_PATTERN']='%s.js'
	v['implib_PATTERN']='lib%s.js.a'
	v['IMPLIB_ST']='-Wl,--out-implib,%s'
	v['CFLAGS_cshlib']=[]
	v.append_value('LINKFLAGS',['-Wl,--enable-auto-import'])
@conf
def emcc_modifier_platform(conf):
	emcc_modifier_func=getattr(conf,'emcc_modifier_'+conf.env.TARGET_OS,None)
	if emcc_modifier_func:
		emcc_modifier_func()
def configure(conf):
	conf.find_emcc()
	conf.load('emar', tooldir="waf-tools")
	conf.emcc_common_flags()
	conf.emcc_modifier_platform()
	conf.cc_load_tools()
	conf.cc_add_flags()
	conf.link_add_flags()
