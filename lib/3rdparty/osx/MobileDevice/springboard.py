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
from .plistservice import *
import time


class Springboard(PlistService):
	PORTRAIT = 1
	PORTRAIT_UPSIDE_DOWN = 2 
	LANDSCAPE = 3 # home button to right
	LANDSCAPE_HOME_TO_LEFT = 4

	def __init__(self, amdevice):
		PlistService.__init__(
			self, 
			amdevice, 
			[AMSVC_SPRINGBOARD_SERVICES]
		)

	def get_iconstate(self):
		self._sendmsg({
			'command': 'getIconState',
			'formatVersion': '2'
		})
		return self._recvmsg()

	def set_iconstate(self, state):
		self._sendmsg({
			'command': 'setIconState',
			'iconState': state
		})
		# no response

	def get_iconpngdata(self, bundleid):
		self._sendmsg({
			'command': 'getIconPNGData',
			'bundleId': bundleid
		})
		return self._recvmsg()['pngData']

	def get_interface_orientation(self):
		self._sendmsg({'command': 'getInterfaceOrientation'})
		reply = self._recvmsg()
		if reply is None or 'interfaceOrientation' not in reply:
			raise RuntimeError('Unable to retrieve interface orientation')
		return reply['interfaceOrientation']

	def get_wallpaper_pngdata(self):
		self._sendmsg({'command': 'getHomeScreenWallpaperPNGData'})
		return self._recvmsg()['pngData']


def register_argparse_springboard(cmdargs):
	import argparse
	import pprint
	import sys

	def cmd_icon(args, dev):
		sb = Springboard(dev)
		data = sb.get_iconpngdata(args.appid.decode('utf-8'))
		sb.disconnect()
		f = open(args.path.decode('utf-8'), 'wb')
		f.write(data)
		f.close()

	def cmd_orient(args, dev):
		sb = Springboard(dev)
		orient = sb.get_interface_orientation()
		sb.disconnect()

		orient_str = {
			Springboard.PORTRAIT: '↑',
			Springboard.PORTRAIT_UPSIDE_DOWN: '↓',
			Springboard.LANDSCAPE: '←',
			Springboard.LANDSCAPE_HOME_TO_LEFT: '→'
		}
		print((orient_str[orient]))

	def cmd_wallpaper(args, dev):
		sb = Springboard(dev)
		data = sb.get_wallpaper_pngdata()
		sb.disconnect()
		f = open(args.path.decode('utf-8'), 'wb')
		f.write(data)
		f.close()

	def print_icons(state, pad=''):
		retval = ''
		rows = []
		colmax = [0, 0, 0, 0, 0]
		pageid = 0
		for page in state:
			iconid = 0
			for icon in page:
				displayname = icon['displayName']
				pos = '%u:%u' % (pageid, iconid)
				if len(pos) > colmax[0]:
					colmax[0] = len(pos)				
				bundleid = ''
				version = ''
				modtime = ''
				strtime = ''
				extras = ''
				if 'listType' in icon:
					# its a special type
					displayname += '/'
					if icon['listType'] == 'folder':
						extras = print_icons(icon['iconLists'], '  ')
					elif icon['listType'] == 'newsstand':
						extras = print_icons(icon['iconLists'], '  ')
					else:
						raise NotImplementedError('unsupported listType', icon)
				else:
					#print icon
					bundleid = icon['bundleIdentifier']
					if len(bundleid) > colmax[2]:
						colmax[2] = len(bundleid)
					version = icon['bundleVersion']
					if len(version) > colmax[3]:
						colmax[3] = len(version)
					modtime = time.mktime(icon['iconModDate'].timetuple()) * 1000
					if int(time.time()) - modtime > (60*60*24*365):
						# only show year if its over a year old (ls style)
						strtime = time.strftime('%d %b  %Y', time.gmtime(modtime))
					else:
						strtime = time.strftime('%d %b %H:%M', time.gmtime(modtime))
					if len(strtime) > colmax[4]:
						colmax[4] = len(strtime)
				if len(displayname) > colmax[1]:
					colmax[1] = len(displayname)
				rows.append((pos, displayname, bundleid, version, strtime, extras))
				iconid += 1
			pageid += 1
			if pageid != len(state):
				rows.append(('', '', '', '', '', ''))

		for row in rows:
			retval += (
				pad + 
				row[0].ljust(colmax[0]) + '  ' +
				row[1].ljust(colmax[1]) + '  ' +
				row[4].ljust(colmax[4]) + '  ' + 
				row[3].rjust(colmax[3]) + '  ' + 
				row[2].ljust(colmax[2]) + '\n'
				
			)
			retval += row[5]
		return retval

	def cmd_getstate(args, dev):
		sb = Springboard(dev)
		state = sb.get_iconstate()
		sb.disconnect()	
		print(print_icons(state))

	springboardparser = cmdargs.add_parser(
		'springboard',
		help='springboard related controls'
	)
	springboardcmds = springboardparser.add_subparsers()

	# icon command
	iconcmd = springboardcmds.add_parser(
		'icon',
		help='retrieves the icon png data'
	)
	iconcmd.add_argument(
		'appid',
		help='the application bundle id'
	)
	iconcmd.add_argument(
		'path',
		help='the file to write to'
	)
	iconcmd.set_defaults(func=cmd_icon)

	# orient command
	orientcmd = springboardcmds.add_parser(
		'orient',
		help='retrieves the orientation of the foreground app'
	)
	orientcmd.set_defaults(func=cmd_orient)

 	# wallpaper command
	wallpapercmd = springboardcmds.add_parser(
		'wallpaper',
		help='retrieves the wallpaper png data'
	)
	wallpapercmd.add_argument(
		'path',
		help='the file to write to'
	)
	wallpapercmd.set_defaults(func=cmd_wallpaper)

	# get icon state command
	statecmd = springboardcmds.add_parser(
		'get-state',
		help='get the state info for application icons'
	)
	statecmd.set_defaults(func=cmd_getstate)


