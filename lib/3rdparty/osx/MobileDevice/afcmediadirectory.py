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


from .amdevice import *
from .afc import *


class AFCMediaDirectory(AFC):
	def __init__(self, amdevice):
		s = amdevice.start_service(AMSVC_AFC)
		if s is None:
			raise RuntimeError('Unable to launch:', AMSVC_AFC)
		AFC.__init__(self, s)

	def transfer_application(self, path, progress=None):
		'''Transfers an application bundle to the device; into the 
		/PublicStaging directory

		Arguments:
		path -- the local path to the file to transfer
		progress -- the callback to get notified of the transfer process
		            (defaults to none)

		Error:
		Raises RuntimeError on error
		'''
		# Technically you could use this on any AFC connection but it only makes
		# sense to use it on the MediaDirectory - as it hard coded moves stuff 
		# to /PublicStaging.
		def callback(cfdict, arg):
			pass

		cfpath = CFTypeFrom(path)
		cb = AFCProgressCallback(callback)
		if progress is not None:
			cb = AFCProgressCallback(progress)
		err = AMDeviceTransferApplication(self.s, cfpath, None, cb, None)
		CFRelease(cfpath)
		if err != MDERR_OK:
			raise RuntimeError('Unable to transfer application')


def register_argparse_afc(cmdargs):
	import argparse
	import sys
	from . import afcapplicationdirectory
	from . import afccrashlogdirectory
	from . import afcmediadirectory
	from . import afcroot
	import time
	import posixpath
	import pprint

	def printdir(afc, path, recurse):
		dirlist = []
		rows = []
		colmax = [0, 0, 0, 0]
		print("afc: ", path)
		for name in afc.listdir(path):
			isdir = ''
			info = afc.lstat(posixpath.join(path, name))
			if info.st_ifmt == stat.S_IFDIR:
				isdir = '/'
				dirlist.append(posixpath.join(path, name))

			types = {
				stat.S_IFSOCK: 's',
				stat.S_IFLNK: 'l',
				stat.S_IFREG: '-',
				stat.S_IFBLK: 'b',
				stat.S_IFDIR: 'd',
				stat.S_IFCHR: 'c',
				stat.S_IFIFO: 'p'
			}
			modtime = int(info.st_mtime)
			if int(time.time()) - modtime > (60*60*24*365):
				# only show year if its over a year old (ls style)
				strtime = time.strftime('%d %b  %Y', time.gmtime(modtime))
			else:
				strtime = time.strftime('%d %b %H:%M', time.gmtime(modtime))
			islink = ''
			if info.st_ifmt == stat.S_IFLNK:
				islink = ' -> ' + afc.readlink(posixpath.join(path, name))

			row = (
				types[info.st_ifmt],
				info.st_size,
				strtime,
				name + isdir + islink
			)
			rows.append(row)
			for i in range(len(row)):
				if len(row[i]) > colmax[i]:
					colmax[i] = len(row[i])
	
		for row in rows:
			print((
				row[0].ljust(colmax[0]) + '  ' +
				row[1].rjust(colmax[1]) + '  ' + 
				row[2].ljust(colmax[2]) + '  ' + 
				row[3]))

		if recurse:
			for name in dirlist:
				print(('\n' + name))
				printdir(afc, name, recurse)

	def get_afc(args, dev):
		retval = None
		if args.path.startswith('/var/mobile/Media'):
			retval = afcmediadirectory.AFCMediaDirectory(dev)
			args.path = args.path[len('/var/mobile/Media'):]
		elif args.m:
			retval = afcmediadirectory.AFCMediaDirectory(dev)
		elif args.c:
			retval = afccrashlogdirectory.AFCCrashLogDirectory(dev)
		elif args.app is not None:
			retval = afcapplicationdirectory.AFCApplicationDirectory(
				dev, 
				args.app.decode('utf-8')
			)
		else:
			retval = afcroot.AFCRoot(dev)
		return retval

	def cmd_ls(args, dev):
		afc = get_afc(args, dev)
		printdir(afc, args.path.decode('utf-8'), args.r)
		afc.disconnect()

	def cmd_mkdir(args, dev):
		afc = get_afc(args, dev)
		afc.mkdir(args.path)
		afc.disconnect()

	def cmd_rm(args, dev):
		afc = get_afc(args, dev)
		afc.remove(args.path)
		afc.disconnect()

	def cmd_ln(args, dev):
		# XXX unable to make linking work?
		afc = get_afc(args, dev)
		# if we're using the default mediadirectory then adjust the link
		if args.link.startswith('/var/mobile/Media'):
			args.link = args.link[len('/var/mobile/Media'):]
		if args.s:
			afc.symlink(args.path, args.link)
		else:
			afc.link(args.path, args.link)
		afc.disconnect()

	def cmd_get(args, dev):
		dest = args.dest
		if dest[-1] == os.sep:
			# trailing seperator so dest has same name as src
			dest = posixpath.join(dest, posixpath.basename(args.path))

		afc = get_afc(args, dev)
		s = afc.open(args.path, 'r')
		d = open(dest, 'w+')
		d.write(s.readall())
		d.close()
		s.close()
		afc.disconnect()

	def cmd_put(args, dev):
		if args.path[-1] == os.sep:
			# trailing seperator so dest has same name as src
			args.path = posixpath.join(args.path, posixpath.basename(args.src))

		afc = get_afc(args, dev)
		d = afc.open(args.path, 'w')
		s = open(args.src, 'r')
		d.write(s.read())
		s.close()
		d.close()
		afc.disconnect()

	def preview_file(afc, path):
		s = afc.open(path, 'r')
		d = s.readall()
		s.close()
		p = dict_from_plist_encoding(d)
		if p is not None:
			pprint.pprint(p)
		else:
			print(d)
		# XXX add extra preview code for other common types

	def cmd_view(args, dev):
		afc = get_afc(args, dev)
		path = args.path.decode('utf-8')
		files = []
		try:
			# check for directory preview
			for f in afc.listdir(path):
				files.append(posixpath.join(path, f))
		except OSError:
			files = [path] # its not a directory

		for f in files:
			preview_file(afc, f)
		afc.disconnect()		

	# afc command
	afcparser = cmdargs.add_parser(
		'afc', 
		help='commands to manipulate files via afc'
	)
	afcgroup = afcparser.add_mutually_exclusive_group()
	afcgroup.add_argument(
		'-a',
		metavar='app',
		dest='app',
		help='reverse domain name of application; device paths become relative to app container'
	)
	afcgroup.add_argument(
		'-c',
		action='store_true',
		help='crashlogs; device paths become relative to crash log container'
	)
	afcgroup.add_argument(
		'-m',
		action='store_true',
		help='device paths become relative to /var/mobile/media (saves typing)'
	)
	afccmd = afcparser.add_subparsers()

	# ls command
	lscmd = afccmd.add_parser(
		'ls',
		help='lists the contents of the directory'
	)
	lscmd.add_argument(
		'-r',
		action='store_true',
		help='if specified listing is recursive'
	)
	lscmd.add_argument(
		'path',
		help='path on the device to list'
	)
	lscmd.set_defaults(func=cmd_ls)

	# mkdir command
	mkdircmd = afccmd.add_parser(
		'mkdir',
		help='creates a directory'
	)
	mkdircmd.add_argument(
		'path',
		help='path of the dir to create'
	)
	mkdircmd.set_defaults(func=cmd_mkdir)

	# rmdir / rm
	rmcmd = afccmd.add_parser(
		'rm',
		help='remove directory/file'
	)
	rmcmd.add_argument(
		'path',
		help='the path to delete'
	)
	rmcmd.set_defaults(func=cmd_rm)

	rmdircmd = afccmd.add_parser(
		'rmdir',
		help='remove directory/file'
	)
	rmdircmd.add_argument(
		'path',
		help='the path to delete'
	)
	rmdircmd.set_defaults(func=cmd_rm)

	# ln
	lncmd = afccmd.add_parser(
		'ln',
		help='create a link (symbolic or hard)'
	)
	lncmd.add_argument(
		'path',
		help='the pre-existing path to link to'
	)
	lncmd.add_argument(
		'link',
		help='the path for the link'
	)
	lncmd.add_argument(
		'-s',
		action='store_true',
		help='create a symbolic link'
	)
	lncmd.set_defaults(func=cmd_ln)

	# get
	getcmd = afccmd.add_parser(
		'get',
		help='retrieve a file from the device'
	)
	getcmd.add_argument(
		'path',
		help='path on the device to retrieve'
	)
	getcmd.add_argument(
		'dest',
		help='local path to write file to'
	)
	getcmd.set_defaults(func=cmd_get)

	# put
	putcmd = afccmd.add_parser(
		'put',
		help='upload a file from the device'
	)
	putcmd.add_argument(
		'src',
		help='local path to read file from'
	)
	putcmd.add_argument(
		'path',
		help='path on the device to write'
	)
	putcmd.set_defaults(func=cmd_put)

	# view
	viewcmd = afccmd.add_parser(
		'view',
		help='retrieve a file from the device and preview as txt'
	)
	viewcmd.add_argument(
		'path',
		help='path on the device to retrieve'
	)
	viewcmd.set_defaults(func=cmd_view)

