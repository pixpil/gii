import os
import stat

from gii.core import *

from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import QEventLoop, QEvent, QObject

from gii.qt.IconCache       import getIcon
from gii.qt.controls.Window import MainWindow
from gii.qt.controls.Menu   import MenuManager
from gii.qt.QtEditorModule  import QtEditorModule

from gii.SearchView       import requestSearchView, registerSearchEnumerator

from . import Device

##----------------------------------------------------------------##
# def getIOSDeviceName( dev ):
# 	name = u''
# 	try:
# 		name = dev.get_value(name=u'DeviceName')
# 	except:
# 		pass
# 	print( u'%s - "%s"' % ( dev.get_deviceid(), name.decode(u'utf-8') ) )
##----------------------------------------------------------------##

signals.register( 'device.connected' )
signals.register( 'device.disconnected' )
signals.register( 'device.activated' )
signals.register( 'device.deactivated' )

##----------------------------------------------------------------##		
class DeviceManager( EditorModule ):
	def __init__( self ):
		pass
		
	def getName( self ):
		return 'device_manager'

	def getDependency( self ):
		return []
		
	def onLoad( self ):
		self.deviceTypes  = {}
		self.containers   = {}
		self.devices      = {}

		self.activeDevice = None
		registerSearchEnumerator( deviceSearchEnumerator )
		#load device history
		signals.connect( 'project.done_deploy', self.onDoneDeploy )

	def onDeviceEvent( self, ev, device ):
		if ev == 'connected':
			signals.emit( 'device.connected', device )
			self.devices[ device ] = True
			device.setActive( False )
			if not self.activeDevice:
				self.setActiveDevice( device )

		elif ev == 'disconnected':
			signals.emit( 'device.disconnected', device )
			self.devices[ device ] = False
			if device == self.activeDevice:
				self.activeDevice = None

	def setActiveDevice( self, device ):
		if self.activeDevice:
			self.activeDevice.setActive( False )
			signals.emit( 'device.deactivated', self.activeDevice )

		self.activeDevice = device
		if device:
			self.activeDevice.setActive( True )
			signals.emit( 'device.activated', device )

	def onDoneDeploy( self, context ):
		if not self.devices: return
		activeDevice = self.activeDevice or self.devices[0]
		print('deploy on device:')
		r = repr( activeDevice )
		print(r)
		activeDevice.deploy( context )
		print('deploy done!')
	

DeviceManager().register()
##----------------------------------------------------------------##
def deviceSearchEnumerator( typeId, context, option ):
		if not context in [ 'device' ]: return
		result = []
		dm = app.getModule( 'device_manager' )
		for device in dm.enumerateDevice():
			entry = ( device, device.getName(), device.getType(), None )
			result.append( entry )
		return result

##----------------------------------------------------------------##
