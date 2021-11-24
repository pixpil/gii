###############################################################################
 #
 # Oak game engine
 # Copyright (c) 2013 Remi Papillie
 #
 # Permission is hereby granted, free of charge, to any person obtaining a
 # copy of this software and associated documentation files (the "Software"),
 # to deal in the Software without restriction, including without limitation
 # the rights to use, copy, modify, merge, publish, distribute, sublicense,
 # and/or sell copies of the Software, and to permit persons to whom the
 # Software is furnished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 # THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 # FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 # DEALINGS IN THE SOFTWARE.
 # 
###############################################################################

#! /usr/bin/env python
# encoding: utf-8

import os,sys
from waflib import Configure,Options,Utils
from waflib.Tools import ccroot
from waflib.Configure import conf
@conf
def find_emxx(conf):
	cxx=conf.find_program(['em++'], var = "CXX")
	cxx=conf.cmd_to_list(cxx)
	conf.env.CXX_NAME='emcc'
	conf.env.CXX=cxx
@conf
def emxx_common_flags(conf):
	v=conf.env
	v['CXX_SRC_F']=[]
	v['CXX_TGT_F']=['-c','-o']
	if not v['LINK_CXX']:v['LINK_CXX']=v['CXX']
	v['CXXLNK_SRC_F']=[]
	v['CXXLNK_TGT_F']=['-o']
	v['CPPPATH_ST']='-I%s'
	v['DEFINES_ST']='-D%s'
	v['LIB_ST']='-l%s'
	v['LIBPATH_ST']='-L%s'
	# v['STLIB_ST']='lib%s.a'
	v['STLIB_ST']='-l%s'
	v['STLIBPATH_ST']='-L%s'
	v['RPATH_ST']='-Wl,-rpath,%s'
	v['SONAME_ST']='-Wl,-h,%s'
	v['SHLIB_MARKER']='-Wl,-Bdynamic'
	v['STLIB_MARKER']='-Wl,-Bstatic'
	v['cxxprogram_PATTERN']='%s'
	v['CXXFLAGS_cxxshlib']=['-fPIC']
	v['LINKFLAGS_cxxshlib']=['-shared']
	v['cxxshlib_PATTERN']='lib%s.js'
	v['LINKFLAGS_cxxstlib']=['-Wl,-Bstatic']
	v['cxxstlib_PATTERN']='lib%s.a'
	v['LINKFLAGS_MACBUNDLE']=['-bundle','-undefined','dynamic_lookup']
	v['CXXFLAGS_MACBUNDLE']=['-fPIC']
	v['macbundle_PATTERN']='%s.bundle'
@conf
def emxx_modifier_browser(conf):
	v=conf.env
	v['cxxprogram_PATTERN']='%s.html'
	v['cxxshlib_PATTERN']='%s.js'
	v['implib_PATTERN']='lib%s.js.a'
	v['IMPLIB_ST']='-Wl,--out-implib,%s'
	v['CXXFLAGS_cxxshlib']=[]
	v.append_value('LINKFLAGS',['-Wl,--enable-auto-import'])
@conf
def emxx_modifier_platform(conf):
	emxx_modifier_func=getattr(conf,'emxx_modifier_'+conf.env.TARGET_OS,None)
	if emxx_modifier_func:
		emxx_modifier_func()
def configure(conf):
	conf.find_emxx()
	conf.load('emcc', tooldir="waf-tools")
	conf.load('emar', tooldir="waf-tools")
	conf.emxx_common_flags()
	conf.emxx_modifier_platform()
	conf.cxx_load_tools()
	conf.cxx_add_flags()
	conf.link_add_flags()
