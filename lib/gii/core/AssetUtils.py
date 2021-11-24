import os
import os.path

import subprocess
import platform
import ctypes



##TOOL Functions
def openFileInOS(path):
	sysName=platform.system()
	if sysName=='Darwin':
		subprocess.call(["open", path])
	elif sysName == 'Windows':
		os.startfile( os.path.normpath(path) )
		#TODO:linux?

def showFileInBrowser(path):
	sysName=platform.system()
	if sysName=='Darwin':
		subprocess.call(["open", "--reveal", path])
	elif sysName == 'Windows':
		ctypes.windll.shell32.ShellExecuteW(None, 'open', 'explorer.exe', '/n,/select, ' + os.path.normpath(path), None, 1)
		#TODO:linux?