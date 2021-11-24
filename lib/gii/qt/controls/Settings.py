from qtpy import QtCore

globalSettings=QtCore.QSettings('Hatrix','GII')

def setGlobalSettingFile(filepath):
	global globalSettings
	globalSettings=QtCore.QSettings(filepath, QtCore.QSettings.IniFormat)

def getGlobalSettings():
	return globalSettings

def setSettingValue(name, value):
	globalSettings.setValue(name, value)

def getSettingValue(name):
	return globalSettings.getValue(name)


setGlobalSettingFile('gii.ini')