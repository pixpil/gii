import os
import time
import stat
import logging

from .Device import DeviceItem
from gii.core import app, EditorModule
import json

from MobileDevice.MobileDevice import *
import MobileDevice
import subprocess
import threading

_FILE_INDEX = '_FILE_INDEX'
_TEST_APP_ID = 'com.pixpil.test'
##----------------------------------------------------------------##
def copyToDevice( afc, srcFile, tgtFile, **option ):	
	force = option.get( 'force', False )
	index = option['index']

	srcMTime = os.path.getmtime( srcFile )
	if force:
		tgtMTime = 0
	else:
		tgtMTime = index.get( tgtFile, None )

	if not tgtMTime:
		try:
			tgtInfo = afc.lstat( tgtFile )
			tgtMTime = int( tgtInfo.st_mtime )
		except Exception as e:
			tgtMTime = 0

	index[ tgtFile ] = srcMTime
	if tgtMTime < srcMTime:
		logging.info( 'copy new version: %s ' % srcFile )
		try:
			afc.unlink( tgtFile )
		except Exception as e:
			pass
		tgtFP = afc.open( tgtFile, 'w' )
		srcFP = open( srcFile, 'r' )
		tgtFP.write( srcFP.read() )
		srcFP.close()
		tgtFP.close()
	
##----------------------------------------------------------------##
def fileTypeOnDevice( afc, path ):
	try:
		info = afc.lstat( path )
	except Exception as e:
		return None
	return info.st_ifmt

##----------------------------------------------------------------##
def cleanDirFromDevice( afc, path ):
	if fileTypeOnDevice( afc, path ) != stat.S_IFDIR: return False
	for fileName in afc.listdir( path ):
		fullPath = path + '/' + fileName
		info = afc.lstat( fullPath )
		if info.st_ifmt == stat.S_IFDIR:
			removeTreeFromDevice( afc, fullPath )
		else:
			logging.info( 'remove file :%s ' % fullPath )
			afc.unlink( fullPath )
	return True

##----------------------------------------------------------------##
def removeTreeFromDevice( afc, path ):
	if not cleanDirFromDevice( afc, path ): return False
	afc.unlink( path )
	return True

##----------------------------------------------------------------##
def affirmDirOnDevice( afc, path ):
	ft = fileTypeOnDevice( afc, path )
	if ft == stat.S_IFDIR: return True
	if ft: return False #File Type
	try:
		afc.mkdir( path )
	except Exception as e:
		print(('cannot save device file index', repr( e )))
		return False
	return True	

##----------------------------------------------------------------##
def loadDeviceFileIndex( afc, tgtDir ):
	print('loading index')
	path = tgtDir + '/' + _FILE_INDEX
	try:
		fp = afc.open( path, 'r' )
		if fp:
			data = fp.read()
			fp.close()
		return json.loads( data )
	except Exception as e:
		# print 'cannot open device file index', repr( e )
		return None

def saveDeviceFileIndex( afc, index, tgtDir ):
	# print 'saving index'
	path = tgtDir + '/' + _FILE_INDEX
	try:
		afc.unlink( path )
	except Exception as e:
		pass

	try:
		fp = afc.open( path, 'w' )
		data = json.dumps( index ).encode( 'utf-8' )
		fp.write( data )
		fp.close()
	except Exception as e:
		# print 'cannot save device file index', repr( e )
		return None

##----------------------------------------------------------------##
def copyTreeToDevice( afc, srcDir, tgtDir, **option ):
	if not os.path.isdir( srcDir ): raise Exception('dir expected')
	#retreive file index		
	option['index'] = loadDeviceFileIndex( afc, tgtDir ) or {}

	for currentDir, dirs, files in os.walk( srcDir ):
		relDir = os.path.relpath( currentDir, srcDir )
		if relDir == '.':
			currentTgtDir = tgtDir
		else:
			currentTgtDir = tgtDir + '/' + relDir			
		if not affirmDirOnDevice( afc, currentTgtDir ): raise Exception('invalid target directory')
		for f in files:
			if f == _FILE_INDEX: continue
			#TODO:ignore pattern
			srcFile = currentDir + '/' + f
			tgtFile = currentTgtDir + '/' + f
			copyToDevice( afc, srcFile, tgtFile, **option)
			print(('copying', srcFile))
		#todo:remove file not found in source
	saveDeviceFileIndex( afc, option['index'], tgtDir )

##----------------------------------------------------------------##
def getAppAFC( dev, appName ):
	return  MobileDevice.AFCApplicationDirectory( dev, appName )

##----------------------------------------------------------------##
class IOSDeviceDebugSession(object):
	def __init__( self, deviceItem ):
		tool = app.getPath( 'support/deploy/ios-deploy' )
		arglist = [ tool ]
		localPath = app.getProject().getHostPath( 'ios/build/Release-iphoneos/YAKA.app' )
		arglist += ['--id', deviceItem.getId() ]
		arglist += ['--bundle', localPath ]
		arglist += ['--debug']
		try:
			code = subprocess.call( arglist )
			if code!=0: return code
		except Exception as e:
			logging.error( 'error in debugging device: %s ' % e)
			return -1		


##----------------------------------------------------------------##
class IOSDeviceItem( DeviceItem ):
	def __init__( self, devId, connected = True ):
		self._deviceId = devId
		self._device   = dev = MobileDevice.AMDevice( devId )
		dev.connect()
		name = ''
		try:
			name = dev.get_value( name = 'DeviceName' )
		except Exception as e :
			logging.exception( e )
		self.name = str( name, 'utf-8' )
		print( self.name )
		self.id   = dev.get_deviceid()
		self.connected = connected

	def getName( self ):
		return self.name

	def getType( self ):
		return 'ios'

	def getId( self ):
		return self.id
	
	def isConnected( self ):
		return self.connected

	def deploy( self, deployContext, **option ):
		appName        = _TEST_APP_ID
		localDataPath  = deployContext.getPath()
		remoteDataPath = 'Documents/game'
		try:
			return self._deployDataFiles( appName, localDataPath, remoteDataPath, **option )
		except Exception as e:
			logging.exception( e )
			return False

	def disconnect( self ):
		if self.connected:
			self._device.disconnect()
			self._deviceId = None
			self._device   = None
			self.connected = False

	def clearData( self ):
		appName        = _TEST_APP_ID
		dev   = self._device
		remoteDataPath = 'Documents/game'
		if not self.isConnected():
			logging.warn( 'device not connected' )
			return False

		afc = getAppAFC( dev, appName )
		cleanDirFromDevice( afc, remoteDataPath )
		afc.disconnect()
		# dev.disconnect()

	def startDebug( self ):
		self.debugSession = IOSDeviceDebugSession( self )

	def _deployDataFiles( self, appName, localDataPath, remoteDataPath, **option ):
		# devices = MobileDevice.list_devices()
		if not self.isConnected():
			logging.warn( 'device not connected' )
			return False
		dev   = self._device
		afc = getAppAFC( dev, appName )				
		copyTreeToDevice( afc, localDataPath, remoteDataPath, **option )
		afc.disconnect()
		return True


##----------------------------------------------------------------##
class IOSDeviceMonitorThread( threading.Thread ):
	def __init__( self, callback, *args ):
		super( IOSDeviceMonitorThread, self ).__init__( *args )
		self.devices = {}
		self.callback = callback
		self.active   = False
		self.deamon   = True

	def run( self ):		
		self.active   = True
		devices = self.devices
		def cbFunc(info, cookie):
			info = info.contents
			if info.message == ADNCI_MSG_CONNECTED:
				dev = IOSDeviceItem( info.device, True )
				devices[info.device] = dev
				self.callback( 'connected', dev )

			elif info.message == ADNCI_MSG_DISCONNECTED:
				dev = devices[info.device]
				self.callback( 'disconnected', dev )
				del devices[info.device]

		notify = AMDeviceNotificationRef()
		notifyFunc = AMDeviceNotificationCallback(cbFunc)
		err = AMDeviceNotificationSubscribe(notifyFunc, 0, 0, 0, byref(notify))
		if err != MDERR_OK:
			raise RuntimeError('Unable to subscribe for notifications')

		# loop so we can exit easily
		while self.active:
			CFRunLoopRunInMode(kCFRunLoopDefaultMode, 0.01, False)
			time.sleep( 0.1 )

		AMDeviceNotificationUnsubscribe(notify)

	def getDevices( self ):
		return self.devices

	def stop( self ):
		self.active = False

##----------------------------------------------------------------##
class IOSDeviceMonitor( EditorModule ):
	name       = 'ios_device_monitor'
	dependency = ['device_manager']

	def __init__( self ):
		self._monitorThread = None

	def onStart( self ):
		self._monitorThread = IOSDeviceMonitorThread( self.onDeviceEvent  )
		self._monitorThread.start()

	def onStop( self ):
		self._monitorThread.stop()
		self._monitorThread = None

	def onDeviceEvent( self, ev, device ):
		self.getModule( 'device_manager' ).onDeviceEvent( ev, device )
