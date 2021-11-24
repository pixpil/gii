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


class AssertionAgent(PlistService):

	WIRELESS_SYNC = 'AMDPowerAssertionTypeWirelessSync'
	USER_IDLE_SLEEP = 'PreventUserIdleSystemSleep'
	SYSTEM_SLEEP = 'PreventSystemSleep'

	def __init__(self, amdevice):
		PlistService.__init__(self, amdevice, ['com.apple.mobile.assertion_agent'])

	def power_assert(self, type, name, timeout, details=None):
		msg = {
			'CommandKey': 'CommandCreateAssertion',
			'AssertionTypeKey': type,
			'AssertionNameKey': name,
			'AssertionTimeoutKey': timeout
		}

		if details is not None:
			msg['AssertionDetailKey'] = details

		self._sendmsg(msg)
		print(self._recvmsg())


def register_argparse_assertionagent(cmdargs):
	import argparse
	import time

	def cmd_assert(args, dev):
		# XXX check this actually works ... I'm not sure it is
		ass = AssertionAgent(dev)
		typ = None
		details = None
		timeout = int(args.timeout.decode('utf-8'))
		if args.w:
			typ = AssertionAgent.WIRELESS_SYNC
		elif args.u:
			typ = AssertionAgent.USER_IDLE_SLEEP
		elif args.s:
			typ = AssertionAgent.SYSTEM_SLEEP
		if args.details:
			details = args.details.decode('utf-8')
		ass.power_assert(
			typ, 
			args.name.decode('utf-8'), 
			timeout, 
			details
		)
		time.sleep(timeout)
		ass.disconnect()

	assertcmd = cmdargs.add_parser(
		'assert', 
		help='perform a power management assert'
	)
	me = assertcmd.add_mutually_exclusive_group(required=True)
	me.add_argument(
		'-w',
		action='store_true',
		help='perform a wireless sync assertion'
	)
	me.add_argument(
		'-u',
		action='store_true',
		help='perform a user idle sleep assertion'
	)
	me.add_argument(
		'-s',
		action='store_true',
		help='perform a system sleep assertion'
	)
	assertcmd.add_argument(
		'name',
		help='the name of the assertion'
	)
	assertcmd.add_argument(
		'timeout',
		help='the duration (in seconds) of the assertion'
	)
	assertcmd.add_argument(
		'details',
		nargs='?',
		help='the description of the assertion (optional)'
	)
	assertcmd.set_defaults(func=cmd_assert)




