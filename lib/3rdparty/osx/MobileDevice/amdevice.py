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
import socket
import select
import os
import glob


class AMDevice(object):
	'''Represents a Apple Mobile Device; providing a wrapping around the raw
	MobileDeviceAPI.
	'''

	# XXX add recovery mode features - move them into anoher file

	INTERFACE_USB = 1
	INTERFACE_WIFI = 2

	BUDDY_SETID = 0x1
	BUDDY_WIFI = 0x2

	value_domains = [
		'com.apple.mobile.battery',
		'com.apple.mobile.iTunes',
		'com.apple.mobile.data_sync',
		'com.apple.mobile.sync_data_class',
		'com.apple.mobile.wireless_lockdown',
		'com.apple.mobile.internal',
		'com.apple.mobile.chaperone'
	]
	
	def __init__(self, dev):
		'''Initializes a AMDevice object

		Arguments:
		dev -- the device returned by MobileDeviceAPI
		'''
		self.dev = dev

	def activate(self, activation_record):
		'''Sends the activation record to the device - activating it for use

		Arguments:
		activation_record -- the activation record, this will be converted to 
							 a CFType

		Error:
		Raises RuntimeError on error
		'''
		record = CFTypeFrom(activation_record)
		retval = AMDeviceActivate(self.dev, record)
		CFRelease(record)
		if retval != MDERR_OK:
			raise RuntimeError('Unable to activate the device')

	def connect(self, advanced=False):
		'''Connects to the device, and starts a session

		Arguments:
		advanced -- if not set, this will create a pairing record if required 
					(default: false)

		Error:
		Raises RuntimeError describing the error condition
		'''
		if AMDeviceConnect(self.dev) != MDERR_OK: 
			raise RuntimeError('Unable to connect to device')

		if not advanced:
			self.pair()

		if AMDeviceStartSession(self.dev) != MDERR_OK: 
			if not advanced:
				raise RuntimeError('Unable to start session')

	def get_deviceid(self):
		'''Retrieves the device identifier; labeled "Identifier" in the XCode
		organiser; a 10 byte value as a string in hex

		Return:
		On success, the name as a string

		Error:
		Raises RuntimeError on error
		'''
		# AMDeviceGetName and AMDeviceCopyDeviceIdentifier return the same value
		# AMDeviceRef + 20
		cf = AMDeviceGetName(self.dev)
		if cf is None:
			raise RuntimeError('Unable to get device id')
		return CFTypeTo(cf)

	def get_location(self):
		'''Retrieves the location of the device; the address on the interface
		(see get_interface_type)

		Return:
		On success, a location value e.g. the USB location ID

		Error:
		Raises RuntimeError on error		
		'''
		# AMDeviceCopyDeviceLocation and AMDeviceUSBLocationID both return 
		# same value
		# AMDeviceRef + 12
		retval = AMDeviceCopyDeviceLocation(self.dev)
		if retval is None:
			raise RuntimeError('Unable to get device location')
		return retval

	def get_value(self, domain=None, name=None):
		'''Retrieves a value from the device

		Arguments:
		domain -- the domain to retrieve, or None to retrieve default domain
		          (default None)
		name -- the name of the value to retrieve, or None to retrieve all 
		        (default None)

		Return:
		On success the requested value
		
		Error:
		Raises RuntimeError on error

		Domains:
		AMDevice.value_domains
		'''
		retval = None
		cfdomain = None
		cfname = None
		if domain is not None:
			cfdomain = CFTypeFrom(domain)
		if name is not None:
			cfname = CFTypeFrom(name)
		value = AMDeviceCopyValue(self.dev, cfdomain, cfname)
		if cfdomain is not None: 
			CFRelease(cfdomain)
		if cfname is not None:
			CFRelease(cfname)
		if value is None:
			raise RuntimeError('Unable to retrieve value', domain, name)
		retval = CFTypeTo(value)
		CFRelease(value)
		return retval

	def deactivate(self):
		'''Deactivates the device - removing it from the network.  WARNING: 
		you probably don't want to do this.

		Error:
		Raises RuntimeError on error
		'''
		if AMDeviceDeactivate != MDERR_OK:
			raise RuntimeError('Unable to deactivate the device')

	def disconnect(self):
		'''Disconnects from the device, ending the session'''
		if self.dev is not None:
			AMDeviceStopSession(self.dev)
			AMDeviceDisconnect(self.dev)
			AMDeviceRelease(self.dev)
			self.dev = None

	def enter_recovery_mode(self):
		'''Puts the device into recovery mode

		Error:
		Raises RuntimeError on error'''
		if AMDeviceEnterRecovery(self.dev) != MDERR_OK:
			raise RuntimeError('Unable to put device in recovery mode')

	def get_interface_speed(self):
		'''Retrieves the interface speed'''
		return AMDeviceGetInterfaceSpeed(self.dev)

	def get_interface_type(self):
		'''Retrieves the interface type

		Return:
		None or error, else a AMDevice.INTERFACE_* value on success
		'''
		# AMDeviceRef + 24
		retval = AMDeviceGetInterfaceType(self.dev)
		if retval == -1:
			retval = None
		return retval

	def get_wireless_buddyflags(self):
		'''Retrieve the wireless buddy flags; Probably used to do wifi sync

		Error:
		Raises a RuntimeError on error
		'''
		retval = None
		obj = c_long()
		if AMDeviceGetWirelessBuddyFlags(self.dev, byref(obj)) != MDERR_OK:
			raise RuntimeError('Unable to get wireless buddy flags')

		if obj is not None:
			retval = obj.value
		return retval

	def remove_value(self, domain, name):
		'''Removes a value from the device

		Arguments:
		domain -- the domain to work in, or None to use the default domain
		          (default None)
		name -- the name of the value to delete

		Error:
		Raises RuntimeError on error
		'''
		cfdomain = None
		cfname = None
		if domain is not None:
			cfdomain = CFTypeFrom(domain)
		if name is not None:
			cfname = CFTypeFrom(name)
		retval = AMDeviceRemoveValue(self.dev, cfdomain, cfname)
		if cfdomain is not None: 
			CFRelease(cfdomain)
		if cfname is not None:
			CFRelease(cfname)
		if retval != MDERR_OK:
			raise RuntimeError('Unable to remove value %s/%s' % (domain, name))

	def set_value(self, domain, name, value):
		'''Sets a value on the device

		Arguments:
		domain -- the domain to set in, or None to use the default domain
		          (default None)
		name -- the name of the value to set
		value -- the value to set

		Error:
		Raises RuntimeError on error
		'''
		cfdomain = None
		cfname = None
		if domain is not None:
			cfdomain = CFTypeFrom(domain)
		if name is not None:
			cfname = CFTypeFrom(name)
		if value is not None:
			cfvalue = CFTypeFrom(value)
		retval = AMDeviceSetValue(self.dev, cfdomain, cfname, cfvalue)
		if cfdomain is not None: 
			CFRelease(cfdomain)
		if cfname is not None:
			CFRelease(cfname)
		if cfvalue is not None:
			CFRelease(cfvalue)
		if retval != MDERR_OK:
			raise RuntimeError('Unable to set value %s/%s' % (domain, name, value))

	def set_wireless_buddyflags(self, enable_wifi=True, setid=True):
		'''Sets the wireless buddy flags, and optionally enables wifi

		Arguments:
		enable_wifi -- turns on/off wifi  (default True)
		setid -- if true, sets buddy id (default True)

		Error:
		Raises RuntimeError on error
		'''
		flags = 0
		if enable_wifi:
			flags |= AMDevice.BUDDY_WIFI
		if setid:
			flags |= AMDevice.BUDDY_SETID
		if AMDeviceSetWirelessBuddyFlags(self.dev, flags) != MDERR_OK:
			raise RuntimeError('Unable to set buddy id flags', enable_wifi, setid)

	# XXX change api so start_service takes a python string and convert
	def start_service(self, service_name, options=None):
		'''Starts the service and returns the socket

		Argument:
		service_name -- the reverse domain name for the service
		options -- a dict of options, or None (default None)

		Return:
		The OS socket associated with the connection to the service

		Error:
		Raises RuntimeError on error
		''' 
		sock = c_int32()
		cfsvc_name = CFStringCreateWithCString(
			None, 
			bytes( service_name, 'utf-8' ), 
			kCFStringEncodingUTF8
		)
		err = False
		if AMDeviceStartServiceWithOptions(
				self.dev, 
				cfsvc_name, 
				options,
				byref(sock)
			) != MDERR_OK:
			err = True
		CFRelease(cfsvc_name)
		if err:
			raise RuntimeError('Unable to start service %s' % service_name)
		return sock.value

	def get_usb_deviceid(self):
		'''Retrieves the USB device id

		Return:
		The usb device id

		Error:
		Raises RuntimeError if theres no usb device id
		'''
		# AMDeviceRef + 8
		retval = AMDeviceUSBDeviceID(self.dev)
		if retval == 0:
			raise RuntimeError('No usb device id')
		return retval

	def get_usb_productid(self):
		'''Retrieves the USB product id

		Return:
		The usb product id

		Error:
		Raises RuntimeError if theres no usb product id
		'''
		# AMDeviceRef + 16
		retval = AMDeviceUSBProductID(self.dev)
		if retval == 0:
			raise RuntimeError('No usb device id')
		return retval

	def pair(self):
		'''Pairs the device to the host

		Error:
		Raises RuntimeError on error
		'''
		if AMDeviceIsPaired(self.dev) != 1:
			if AMDevicePair(self.dev) != MDERR_OK:
				raise RuntimeError('If your phone is locked with a passcode, unlock then reconnect it')

		if AMDeviceValidatePairing(self.dev) != MDERR_OK: 
			raise RuntimeError('Unable to validate pairing')


	def unpair(self):
		'''Unpairs device from host WARNING: you probably dont want to call 
		this

		Error:
		Raises RuntimeError on error
		'''
		if AMDeviceUnpair(self.dev) != MDERR_OK:
			raise RuntimeError('Unable to unpair device')

	def connect_to_port(self, port):
		'''Connects to a listening TCP port on the device.

		Error:
		Raises RuntimeError on error
		'''
		sock = c_int()
		# logic taken from _connect_to_port
		if self.get_interface_type() == AMDevice.INTERFACE_USB:
			if USBMuxConnectByPort(
					AMDeviceGetConnectionID(self.dev),
					socket.htons(port),
					byref(sock)
				) != MDERR_OK:
				raise RuntimeError('Unable to connect to socket via usb')
		else:
			# XXX test!
			raise NotImplementedError('WiFi sync connect')
			#if AMDeviceConnectByAddressAndPort(
			#		self.dev, 
			#		port, 
			#		byref(sock)
			#	) != MDERR_OK:
			#	raise RuntimeError(u'Unable to connect to socket')
		return socket.fromfd(sock.value, socket.AF_INET, socket.SOCK_STREAM)

	def find_device_support_path(self):
		'''Returns the best device support path for this device

		Returns:
		the path

		Error:
		Raises RuntimeError if a suitable path can be found
		'''
		# XXX: Windows version
		support_paths = glob.glob(
			'/Applications/Xcode*.app/Contents/Developer/Platforms/iPhoneOS.platform/DeviceSupport/*'
		)
		# process all the support paths to extract all the components
		support = []
		for path in support_paths:
			name = os.path.split(path)[1]
			parts = name.split(' ')
			version = parts[0]
			build = None
			if len(parts) != 1:
				build = parts[1].replace('(', '').replace(')', '')
			version_parts = version.split('.')
			major_version = version_parts[0]
			minor_version = version_parts[1]
			support.append({
				'version': version,
				'major_version': major_version,
				'minor_version': minor_version,
				'build': build,
				'path': path
			})
	
		# get the device info
		version = self.get_value(name='ProductVersion')
		version_parts = version.split('.')
		major_version = version_parts[0]
		minor_version = version_parts[1]

		build = self.get_value(name='BuildVersion')

		# lets find the best support path.
		support_path = None
		for s in support:
			# version match is more important than build
			if s['major_version'] == major_version:
				if support_path is None:
					support_path = s
				else:
					# is this better than the last match?
					if s['minor_version'] == minor_version:
						if s['build'] == build:
							# perfect match
							support_path = s
						else:
							if support_path['build'] != build:
								# we're still better than existing match
								support_path = s

		if support_path is None:
			raise RuntimeError('Unable to find device support path')
		return support_path['path']

	def find_developer_disk_image_path(self, device_support_path=None):
		'''Returns the best debug disk image for the device

		Returns:
		the path of the .dmg

		Error:
		Raises RuntimeError if a suitable disk image can't be found
		'''
		if device_support_path is None:
			device_support_path = self.find_device_support_path()

		path = os.path.join(
			device_support_path, 
			'DeveloperDiskImage.dmg'
		)
		if not os.path.exists(path):
			# bum - that shouldn't happen
			raise RuntimeError('Unable to find developer disk image')
		return path


def handle_devices(factory):
	'''Waits indefinatly handling devices arrival/removal events.
	
	Upon arrival the factory function will be called; providing the device as 
	a param.  This method should return an object on success, None on error.
	When the device is removed your object will have 'disconnect' called upon it

	Typical Example:
	def factory(dev):
		dev.connect()
		pprint.pprint(dev.get_value())
		dev.disconnect()

	Arguments:
	factory -- the callback function, called on device arrival

	Error:
	Raises a RuntimeError on error
	'''
	# XXX: what do I need to release
	devices = {}

	def cbFunc(info, cookie):
		info = info.contents
		if info.message == ADNCI_MSG_CONNECTED:
			devices[info.device] = AMDevice(info.device)
			factory(devices[info.device])

		elif info.message == ADNCI_MSG_DISCONNECTED:
			devices[info.device].disconnect()
			del devices[info.device]			

	notify = AMDeviceNotificationRef()
	notifyFunc = AMDeviceNotificationCallback(cbFunc)
	err = AMDeviceNotificationSubscribe(notifyFunc, 0, 0, 0, byref(notify))
	if err != MDERR_OK:
		raise RuntimeError('Unable to subscribe for notifications')

	# loop so we can exit easily
	while CFRunLoopRunInMode(kCFRunLoopDefaultMode, 0.1, False) == kCFRunLoopRunTimedOut:
		pass

	AMDeviceNotificationUnsubscribe(notify)


def list_devices(waittime=0.1):
	'''Returns a dictionary of AMDevice objects, indexed by device id, 
	currently connected; waiting at least waittime for them to be discovered.

	Arguments:
	waittime -- time to wait for devices to be discovered (default 0.1 seconds)
	'''
	# XXX: what do I need to release
	devices = {}

	def cbFunc(info, cookie):
		info = info.contents
		if info.message == ADNCI_MSG_CONNECTED:
			dev = AMDevice(info.device)
			devices[dev.get_deviceid()] = dev

	notify = AMDeviceNotificationRef()
	notifyFunc = AMDeviceNotificationCallback(cbFunc)
	err = AMDeviceNotificationSubscribe(notifyFunc, 0, 0, 0, byref(notify))
	if err != MDERR_OK:
		raise RuntimeError('Unable to subscribe for notifications')

	CFRunLoopRunInMode(kCFRunLoopDefaultMode, waittime, False)
	AMDeviceNotificationUnsubscribe(notify)
	return devices


def argparse_parse(scope):
	'''Provides basic argument parsing functionality (listing and selection of 
	devices).  Will call any methods in scope whose keys start with 
	"register_argparse_" and call them with the argument parser

	Arguments:
	scope -- a dictionary of name -> functions
	'''
	import os
	import sys
	import argparse

	class CmdArguments(object):
		def __init__(self):
			self._devs = list_devices()

			self._parser = argparse.ArgumentParser()

			self._parser.add_argument(
				'-x',
				dest='advanced',
				action='store_true',
				help='''enables advanced mode; where helpful tasks are not done 
				automatically; e.g. pairing if your not already paired'''
			)

			group = self._parser.add_mutually_exclusive_group()
			group.add_argument(
				'-d',
				metavar='devid',
				dest='device_idx',
				choices=list(range(len(list(self._devs.keys())))),
				type=int,
				action='store',
				help='operate on the specified device'
			)
			
			group.add_argument(
				'-i',
				metavar='identifier',
				dest='device_id',
				choices=list(self._devs.keys()),
				type=str,
				action='store',
				help='operate on the specified device'
			)

			# add subparsers for commands
			self._subparsers = self._parser.add_subparsers(
				help='sub-command help; use <cmd> -h for help on sub commands'
			)
			
			# add listing command
			listparser = self._subparsers.add_parser(
				'list', 
				help='list all attached devices'
			)
			listparser.set_defaults(listing=True)

		def add_parser(self, *args, **kwargs):
			return self._subparsers.add_parser(*args, **kwargs)

		def parse_args(self):
			args = self._parser.parse_args(namespace=self)
			i = 0
			if 'listing' in dir(self):
				sys.stdout.write(self._print_devices().encode("utf-8"))

			else:
				if len(self._devs) > 0:
					devs = sorted(self._devs.keys())
					if self.device_id is not None:
						identifier = self.device_id.decode('utf-8')
						for i in range(len(devs)):
							if devs[i] == identifier:
								self.device_idx = i

					if self.device_idx is None:
						self.device_idx = 0 # default to first device
					k = devs[self.device_idx]
					v = self._devs[k]

					# connect before trying to get device name
					v.connect(args.advanced)
					name = ''
					try:
						name = v.get_value(name='DeviceName')
					except:
						pass
					print(('%u: %s - "%s"' % (
						self.device_idx, 
						v.get_deviceid(), 
						name.decode('utf-8')
					)))
					args.func(args, v)
					v.disconnect()

		def _print_devices(self):
			retval = 'device list:\n'
			i = 0
			for k in sorted(self._devs.keys()):
				v = self._devs[k]
				try:
					v.connect()
					name = v.get_value(name='DeviceName')
					retval += '  %u: %s - "%s"\n' % (
						i, 
						v.get_deviceid(), 
						name.decode('utf-8')
					)
				except:
					retval += '  %u: %s\n' % (i, k)
				finally:
					v.disconnect()
				i = i + 1
			return retval			


	cmdargs = CmdArguments()

	# register any command line arguments from the modules
	for member in list(scope.keys()):
		if member.startswith('register_argparse_'):
			scope[member](cmdargs)

	cmdargs.parse_args()


def register_argparse_dev(cmdargs):
	import argparse
	import pprint

	def get_number_in_units(size,precision=2):
		suffixes = ['b', 'kb', 'mb', 'gb']
		suffixIndex = 0
		while size > 1024:
			suffixIndex += 1 #increment the index of the suffix
			size = size / 1024.0 #apply the division
		return '%.*f%s' % (precision,size,suffixes[suffixIndex])

	def cmd_info(args, dev):
		iface_types = {
			AMDevice.INTERFACE_USB: 'USB',
			AMDevice.INTERFACE_WIFI: 'WIFI'
		}
		device_type = dev.get_interface_type()
		print(('  identifier: %s' % dev.get_deviceid()))
		print(('  interface type: %s' % iface_types[device_type]))
		print(('  interface speed: %sps' % 
			get_number_in_units(int(dev.get_interface_speed()))
		))
		print(('  location: 0x%x' % dev.get_location()))
		if device_type is AMDevice.INTERFACE_USB:
			print(('  usb device id: 0x%x' % dev.get_usb_deviceid()))
			print(('  usb product id: 0x%x' % dev.get_usb_productid()))
		
	def cmd_get(args, dev):
		if args.domain is not None or args.key is not None:
			key = None
			if args.key is not None:
				key = args.key.decode('utf-8')

			domain = None
			if args.domain is not None:
				domain = args.domain.decode('utf-8')
			try:
				pprint.pprint(dev.get_value(domain, key))
			except:
				pass
		else:
			# enumerate all the value_domains
			output = {}
			output[None] = dev.get_value()
			for domain in AMDevice.value_domains:
				output[domain] = dev.get_value(domain)
			pprint.pprint(output)

	def cmd_set(args, dev):
		domain = None
		if args.domain is not None:
			domain = args.domain.decode('utf-8')
		# XXX add support for non-string types; bool next
		dev.set_value(domain, args.key.decode('utf-8'), args.value.decode('utf-8'))

	def cmd_del(args, dev):
		domain = None
		if args.domain is not None:
			domain = args.domain.decode('utf-8')
		dev.remove_value(domain, args.key.decode('utf-8'))

	def cmd_pair(args, dev):
		dev.pair()

	def cmd_unpair(args, dev):
		dev.unpair()

	def cmd_buddy(args, dev):
		if args.wifi is not None or args.setid is not None:
			dev.set_wireless_buddyflags(args.wifi, args.setid)
		else:
			flags = dev.get_wireless_buddyflags()
			s = ''
			if flags & AMDevice.BUDDY_WIFI:
				s += 'BUDDY_WIFI'
			if flags & AMDevice.BUDDY_SETID:
				if len(s) != 0:
					s += ' | '
				s += 'BUDDY_SETID'
			s += ' (0x%x)' % flags
			print(('  wireless buddy flags: %s' % s))

	def cmd_relay(args, dev):
		class Relay(object):
			def __init__(self, dev, src, dst):
				self.dev = dev
				self.src = src
				self.dst = dst
				self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.server.bind(('localhost', src))
				self.server.listen(5)

			def accept(self):
				s, addr = self.server.accept()
				print(('connection to device on port: %u' % self.dst))
				retval = None
				try:
					retval = (s, self.dev.connect_to_port(self.dst))
				except:
					print(('dev relay: error: unable to connect to port %u on device' % self.dst))
				return retval

			def close(self):
				self.server.close()

		def close_connection(endpoints, ins, outs, errs, s):
			# remove src and dst
			other = endpoints[s][0]
			rem = [
				(ins, s), (ins, other), 
				(outs, s), (outs, other), 
				(errs, s), (errs, other)
			]
			for rset, robj in rem:
				try:
					rset.remove(robj)
				except:
					pass
			del endpoints[s]
			del endpoints[other]
			try:
				s.shutdown(socket.SHUT_RDWR)
			except:
				pass
			try:
				other.shutdown(socket.SHUT_RDWR)
			except:
				pass
			s.close()
			other.close()

		pairs = getattr(args, 'port:pair')
		relays = {}
		endpoints = {}
		import sys
		# check arguments
		try:
			for pair in pairs:
				src, dst = pair.split(':')
				src = int(src)
				dst = int(dst)
				# create and register server
				relay = Relay(dev, src, dst)
				relays[relay.server] = relay
		except socket.error:
			print(('dev relay: error: unable to bind to local port - %u' % src))
		except:
			print(('dev relay: error: invalid port pair - %s' % pair))
			print(sys.exc_info())

		# do relaying
		if len(list(relays.keys())) == len(pairs):
			for relay in list(relays.values()):
				print(('relaying traffic from local port %u to device port %u' % (relay.src, relay.dst)))
			ins = list(relays.keys())
			outs = []
			errs = []
			while len(ins) > 0 or len(outs) > 0:
				ready = select.select(ins, outs, errs)
				for s in ready[0]: # inputs
					if s in relays:
						# accept a new connection
						e = relays[s].accept()
						if e is not None:
							a, b = e
							endpoints[a] = (b, '')
							endpoints[b] = (a, '')
							# add both a and b to recv
							ins.append(a)
							ins.append(b)
							errs.append(a)
							errs.append(b)

					elif s in endpoints:
						# recv data and store data against opposite socket
						data = s.recv(4096)
						if len(data) > 0:
							dst = endpoints[s][0]
							endpoints[dst] = (s, data)
							ins.remove(s)
							outs.append(dst)
						else:
							close_connection(endpoints, ins, outs, errs, s)

				for s in ready[1]: # output
					if s in endpoints:
						# write data
						src, data = endpoints[s]
						bs = s.send(data)
						endpoints[s] = (src, data[bs:])
						if len(data) == bs:
							# sent everything - put src back in the recv list
							outs.remove(s)
							ins.append(src)

				for s in ready[2]: # errors
					if s in endpoints:
						close_connection(endpoints, ins, outs, errs, s)

		# cleanup
		for endp in list(endpoints.keys()):
			try:
				endp.shutdown(socket.SHUT_RDWR)
			except:
				pass
			endp.close()

		for relay in relays:
			relay.close()


	# standard dev commands
	devparser = cmdargs.add_parser(
		'dev', 
		help='commands related to the device'
	)

	# device info
	devcmds = devparser.add_subparsers()
	infocmd = devcmds.add_parser(
		'info', 
		help='display basic info about the device'
	)
	infocmd.set_defaults(func=cmd_info)

	# get value
	getcmd = devcmds.add_parser(
		'get', 
		help='display key/value info about the device'
	)
	getcmd.add_argument(
		'key', 
		nargs='?',
		help='the key of the value to get'
	)
	getcmd.add_argument(
		'-d', 
		metavar='domain', 
		dest='domain', 
		help='the domain of the key to get'
	)
	getcmd.set_defaults(func=cmd_get)

	# set value
	setcmd = devcmds.add_parser(
		'set', 
		help='set key/value info about the device'
	)
	setcmd.add_argument(
		'key',
		help='the key to set'
	)
	# XXX how do we support complex (dict) settings?
	setcmd.add_argument(
		'value', 
		help='the value of the key to apply (only able to set simple values at present)'
	)
	setcmd.add_argument(
		'-d', 
		metavar='domain', 
		dest='domain',
		help='the domain the key to set lives in'
	)
	setcmd.set_defaults(func=cmd_set)

	# delete value
	delcmd = devcmds.add_parser(
		'del', 
		help='delete key/value info from the device - DANGEROUS'
	)
	delcmd.add_argument(
		'key', 
		help='the key of the value to delete'
	)
	delcmd.add_argument(
		'-d', 
		metavar='domain', 
		dest='domain', 
		help='the domain of the key to delete'
	)
	delcmd.set_defaults(func=cmd_del)

	# pair
	paircmd = devcmds.add_parser(
		'pair',
		help='pair the device to this host'
	)
	paircmd.set_defaults(func=cmd_pair)

	# unpair
	unpaircmd = devcmds.add_parser(
		'unpair',
		help='unpair the device from this host'
	)
	unpaircmd.set_defaults(func=cmd_unpair)

	# set buddy id
	buddycmd = devcmds.add_parser(
		'buddy',
		help='get/set wireless buddy parameters'
	)
	buddycmd.add_argument(
		'-w', 
		help='enable wifi (0 or 1)', 
		dest='wifi', 
		type=int,
		choices=(0, 1)
	)
	buddycmd.add_argument(
		'-s', 
		help='sets buddy id (0 or 1)', 
		dest='setid',
		type=int,		
		choices=(0, 1)
	)
	buddycmd.set_defaults(func=cmd_buddy)

	# relay ports from localhost to device (tcprelay style)
	relaycmd = devcmds.add_parser(
		'relay',
		help='relay tcp ports from locahost to device'
	)
	relaycmd.add_argument(
		'port:pair',
		nargs='+',
		help='a pair of ports to relay <local>:<device>'
	)
	relaycmd.set_defaults(func=cmd_relay)

	# XXX activate, deactivate - do we really want to be able to do these?

