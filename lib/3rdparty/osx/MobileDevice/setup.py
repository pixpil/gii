#!/usr/bin/python
# coding: utf-8

# Copyright (c) 2013 Mountainstorm
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from distutils.core import setup
import os.path
import os
from subprocess import check_output


def readfile(filename):
	f = open(filename)
	text = f.read()
	f.close()
	return text

def getcommit():
	retval = ''
	try:
		retval = check_output(['git', 'rev-list', '--all', '--count'])
		retval = '.' + retval.strip()
	except:
		pass
	return retval


setup(
	name='Distutils',
	version='1.0' + getcommit(),
	description='A python package, and command line tool, which wraps Apple\'s MobileDevice API - providing access to iOS devices',
	long_description = readfile('README.md'),
	author='Cooper',
	url='https://github.com/mountainstorm/MobileDevice',
	classifiers = [
		'Development Status :: 5 - Production/Stable',
		'Environment :: Console',
		'Environment :: MacOS X',
		'Intended Audience :: Developers',
		'License :: OSI Approved :: MIT License',
		'Natural Language :: English',
		'Operating System :: MacOS :: MacOS X',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2.7',
		'Topic :: Security',
		'Topic :: Software Development :: Libraries :: Python Modules',
		'Topic :: Utilities',
	],
	license= readfile('LICENSE'),
	packages=['MobileDevice'],
	package_dir={'': '../'},
	scripts=['mdf']
)
