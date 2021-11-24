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

import os

def build_shader(task):
	src = task.inputs[0].abspath()
	tgt = task.outputs[0].abspath()
	
	shaderFile = open(src, "r")
	headerFile = open(tgt, "w")
	
	headerFile.write("namespace oak {\n")
	
	# deduce variable name from filename
	split = os.path.splitext(os.path.basename(src))
	variableName = split[0] + split[1].upper()[1:]
	
	headerFile.write("const char *" + variableName + "String = \"")
	for line in shaderFile:
		# escape '\' and '"'
		line = line.replace("\\", "\\\\")
		line = line.replace("\"", "\\\"")
		
		# content, with \n between lines
		headerFile.write(line.strip() + "\\n")
	
	headerFile.write("\";\n")
	
	headerFile.write("} // oak namespace\n")
	
	shaderFile.close()
	headerFile.close()
	
	return 0

from waflib import TaskGen
TaskGen.declare_chain(name = "vertex_shader", rule = build_shader, ext_in = ".vs", ext_out = ".vs.h")
TaskGen.declare_chain(name = "fragment_shader", rule = build_shader, ext_in = ".fs", ext_out = ".fs.h")
