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
from .wirservice import *
import uuid
import json


# Talk to safari using:
# https://developers.google.com/chrome-developer-tools/docs/protocol/1.0/index
# https://webkit.googlesource.com/WebKit/+/825dea3b415c86cc86ff4a4dabe4ebc9b1ab9b75/Source/WebKit/mac/WebInspector/remote/WebInspectorServerWebViewConnectionController.mm
class WebKitInspector(WIRService):
	def __init__(self, amdevice):
		WIRService.__init__(self, amdevice, [AMSVC_WEBINSPECTOR])

	def uniqueid(self):
		retval = str(uuid.uuid1())
		if isinstance(retval, str):
			# get round a bug in safari's implementation of 'forwardSocketSetup'
			# they don't check the type/convert WIRConnectionIdentifierKey
			# Thus if we send a string, it converts to a CFData and Safari goes
			# pop when it tries to call compare on the CFData
			retval = retval.decode('utf-8') 
		return retval

	# register a connection_uuid
	def reportIdentifier(self, connection_uuid):
		self._sendmsg(
			'_rpc_reportIdentifier:',
			{ 
				'WIRConnectionIdentifierKey': connection_uuid,
			}
		)
		retval = self._recvmsg()
		retval = self._recvmsg() # get the getConnectedApplications response
		return retval[1]

	# list avaliable applications
	def getConnectedApplications(self, connection_uuid):
		self._sendmsg(
			'_rpc_getConnectedApplications:',
			{
				'WIRConnectionIdentifierKey': connection_uuid
			}
		)
		retval = self._recvmsg()
		return retval[1]

	# get info about an applications e.g. pages in mobilesafari
	def forwardGetListing(self, connection_uuid, appid):
		self._sendmsg(
			'_rpc_forwardGetListing:',
			{
				'WIRConnectionIdentifierKey': connection_uuid,
				'WIRApplicationIdentifierKey': appid
			}
		)
		retval = self._recvmsg()
		while retval[0] != '_rpc_applicationSentListing:':
			retval = self._recvmsg()
		return retval[1]

	# highlight a webview page
	def forwardIndicateWebView(self, connection_uuid, appid, pageid, enable):
		self._sendmsg(
			'_rpc_forwardIndicateWebView:',
			{
				'WIRConnectionIdentifierKey': connection_uuid,
				'WIRApplicationIdentifierKey': appid,
				'WIRPageIdentifierKey': pageid,
				'WIRIndicateEnabledKey': enable
			}
		)
		return self._recvmsg()[1]

	# setup a webkit protocol connection
	def forwardSocketSetup(self, connection_uuid, appid, pageid, sender_uuid):
		self._sendmsg(
			'_rpc_forwardSocketSetup:',
			{ 
				'WIRConnectionIdentifierKey':  connection_uuid,
				'WIRApplicationIdentifierKey': appid,
				'WIRPageIdentifierKey': pageid,
				'WIRSenderKey': sender_uuid
			}
		)
		#self._recvmsg() # throw away the forwardGetListing response

	# send webkit protocol message
	def forwardSocketData(self, connection_uuid, appid, pageid, sender_uuid, msg):
		self._sendmsg(
			'_rpc_forwardSocketData:',
			{ 
				'WIRConnectionIdentifierKey': connection_uuid,
				'WIRApplicationIdentifierKey': appid,
				'WIRPageIdentifierKey': pageid,
				'WIRSenderKey': sender_uuid,
				'WIRSocketDataKey': msg
			}
		)

	def forwardDidClose(self, connection_uuid, appid, pageid, sender_uuid):
		self.sendmsg(
			'_rpc_forwardDidClose:',
			{ 
				'WIRConnectionIdentifierKey': connection_uuid,
				'WIRApplicationIdentifierKey': appid,
				'WIRPageIdentifierKey': pageid,
				'WIRSenderKey': sender_uuid
			}
		)
		print(self._recvmsg())

	def navigate(self, url):
		conn = self.uniqueid()
		app = 'com.apple.mobilesafari'

		self.reportIdentifier(conn)
		# XXX: why does lockdownd show as a connected app?
		self.forwardGetListing(conn, app)

		session = self.uniqueid()
		listing = self.forwardIndicateWebView(conn, app, 1, session)

		pages = listing['WIRListingKey']
		ident = 1 #int(pages.values()[0][u'WIRPageIdentifierKey'])
		self.forwardSocketSetup(conn, app, ident, session)
		self.forwardSocketData(conn, app, ident, session, {
			'id': 1,
			'method': 'Inspector.enable'
		})
		self.forwardSocketData(conn, app, ident, session, {
			'id': 2,
			'method': 'CSS.getSupportedCSSProperties'
		})
		self.forwardSocketData(conn, app, ident, session, {
			'id': 3,
			'method': 'Page.enable'
		})
		self.forwardSocketData(conn, app, ident, session, {
			'id': 4,
			'method': 'Network.enable'
		})		
		self.forwardSocketData(conn, app, ident, session, {
			'id': 5,
			'method': 'Page.navigate',
			'params': {
				'url': (
					url
				)
			}
		})
		print('recv')
		self._recvmsg()



def register_argparse_webinspector(cmdargs):
	import argparse
	import sys
	import mimetypes
	import base64

	def cmd_load(args, dev):
		mimetype = mimetypes.guess_type(args.path)
		f = open(args.path, 'rb')
		content = f.read()
		f.close()
		
		# wakeup device
		# switch to safari?
		wi = WebKitInspector(dev)
		wi.navigate('data:' + mimetype[0] + ';base64,' + base64.b64encode(content))
		wi.disconnect()


	def cmd_navigate(args, dev):
		# wakeup device
		# switch to safari?
		wi = WebKitInspector(dev)
		wi.navigate(args.url.decode('utf-8'))
		wi.disconnect()

	webparser = cmdargs.add_parser(
		'web', 
		help='webinspector actions; requires settings->safari->advanced->web-inspector be enabled'
	)
	webcmd = webparser.add_subparsers()

	# load command
	loadcmd = webcmd.add_parser(
		'load',
		help='loads a single safari window with the specified file'
	)
	loadcmd.add_argument(
		'path',
		help='the file to load (as a data: url) into the first page of mobilesafari'
	)
	loadcmd.set_defaults(func=cmd_load)


	# navigate command
	navigatecmd = webcmd.add_parser(
		'navigate',
		help='navigate a single safari window with the specified url'
	)
	navigatecmd.add_argument(
		'url',
		help='the url to navigate the first page of mobilesafari to'
	)
	navigatecmd.set_defaults(func=cmd_navigate)



		

