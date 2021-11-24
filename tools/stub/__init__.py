import os.path
import logging

from gii.core import Project, app

from . import stub 
##----------------------------------------------------------------##
def main( argv ):
	task = stub.start()
	if task['task'] == 'open':
		app.openProject( task['path'] )
		import gii.SceneEditor
		import gii.AssetEditor
		# import gii.ScriptView
		import gii.DeviceManager
		app.run()

