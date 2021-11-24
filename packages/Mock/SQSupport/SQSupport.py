import subprocess
import os.path
import shutil
import time
import json

from gii.core         import *

from gii.SceneEditor  import SceneEditorModule

from mock import MOCKEditCanvas
from gii.moai.MOAIRuntime import getAKU
from gii.qt.dialogs                    import alertMessage, requestConfirm, requestString

from mock import getMockClassName, _MOCK, _MOCK_EDIT
##----------------------------------------------------------------##

def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path

def _fixDuplicatedName( names, name, id = None ):
	if id:
		testName = name + '_%d' % id
	else:
		id = 0
		testName = name
	#find duplicated name
	if testName in names:
		return _fixDuplicatedName( names, name, id + 1)
	else:
		return testName

##----------------------------------------------------------------##
class SQSupport( SceneEditorModule ):
	name = 'sq_support'
	dependencies = [ 'mock' ]
	def onLoad( self ):
		pass

