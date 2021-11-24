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


from .MobileDevice import *
from .amdevice import *
from .plistservice import *
import os


class FileRelay(PlistService):
	'''Provides access to the file relay service; allowing you to retrive 
	filesets from the device in cpio.gz format'''

	filesets = [
		'AppleSupport',
		'Network',
		'VPN',
		'WiFi',
		'UserDatabases',
		'CrashReporter',
		'tmp',
		'SystemConfiguration'
	]

	def __init__(self, amdevice):
		PlistService.__init__(
			self,
			amdevice, 
			[AMSVC_FILE_RELAY],
			kCFPropertyListXMLFormat_v1_0
		)

	def get_filesets(self, sources):
		'''retrieves the fileset/sets specified in sources; returns the data
		in cpio.gz format

		Arguments:
		sources -- an array of source names
		'''
		self._sendmsg({'Sources': sources})
		reply = self._recvmsg()
		if 'Status' in reply and reply['Status'] == 'Acknowledged':
			# now read the cpio.gz file it returns
			retval = ''
			while True:
				data = os.read(self.s, 1024)
				if data is None or len(data) == 0:
					break
				retval += data
		else:
			raise RuntimeError('Unable to retrieve filesets: %s' % reply)
		return retval


def register_argparse_filerelay(cmdargs):
	import argparse
	import sys

	def cmd_filerelay(args, dev):
		fr = FileRelay(dev)

		sets = FileRelay.filesets
		if args.s is not None:
			sets = []
			for s in args.s:
				sets.append(s.decode('utf-8'))
		f = open(args.dest.decode('utf-8'), 'wb')
		f.write(fr.get_filesets(sets))
		f.close()
		fr.disconnect()

	# filerelay command
	filerelaycmd = cmdargs.add_parser(
		'filerelay', 
		help='retrieves filesets from the device in .cpio.gz format'
	)
	filerelaycmd.add_argument(
		'-s',
		metavar='setname',
		action='append',
		help='the set name to retrieve; if no -s options are specified it retrieves all sets'
	)
	filerelaycmd.add_argument(
		'dest',
		help='destination filename; should really end in .cpio.gz'
	)
	filerelaycmd.set_defaults(func=cmd_filerelay)

