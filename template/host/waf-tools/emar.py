#! /usr/bin/env python
# encoding: utf-8

from waflib.Configure import conf
@conf
def configure(conf):
	conf.find_program('emar',var='AR')
	conf.env.ARFLAGS='rcs'
