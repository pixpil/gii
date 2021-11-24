import os
import sys
import logging
import time

from watchdog.observers import Observer
from watchdog.events    import FileSystemEventHandler,PatternMatchingEventHandler
from gii.core           import EditorModule, app, signals
from qtpy							import QtCore


##----------------------------------------------------------------##
class ModuleFileWatcher( EditorModule ):

	name = 'file_watcher'
	dependency = []

	def __init__( self ):
		self.started = False

	def onLoad(self):
		self.watches  = []

		self.internalWatches = {}
		self.observer = Observer()
		self.observer.start()
		
		signals.connect( 'file.moved',    self.onFileMoved )
		signals.connect( 'file.added',    self.onFileCreated )
		signals.connect( 'file.removed',  self.onFileDeleted )
		signals.connect( 'file.modified', self.onFileModified )

	def onStart( self ):
		self.started = True
		#start all watches
		for watch in self.watches:
			watch.start()

	def onStop( self ):
		for watch in self.watches:
			watch.stop()
		# print 'stop file watcher'
		self.observer.stop()
		self.observer.join( 0.5 )
		# print 'stopped file watcher'

	def registerFileWatch( self, watch ):
		self.watches.append( watch )
		if self.started:
			watch.start()

	def removeFileWatch( self, watch ):
		if watch in self.watches:
			watch.stop()
			self.watches.pop( watch )

	def requestInternalWatch( self, handler, path, recursive ):
		if self.internalWatches.get(path):
			logging.warning( 'already watching: %s' % path )
			return False
			# return self.internalWatches[path]
		watch = self.observer.schedule( handler, path, recursive )
		logging.info ( 'start watching: %s' % path )
		
		self.internalWatches[ path ] = watch
		return watch

	def stopInternalWatch(self, path):
		path  = os.path.realpath(path)
		watch = self.internalWatches.get(path, None)
		if not watch: return
		self.observer.unschedule(watch)
		self.internalWatches[path] = None

	def stopAllWatches(self):
		# logging.info('stop all file watchers')
		self.observer.unschedule_all()
		self.internalWatches = {}

	def onFileMoved(self, watch, path, newpath):
		return watch.onFileMoved( path, newpath )

	def onFileCreated(self, watch, path):
		return watch.onFileCreated( path )

	def onFileModified(self, watch, path):
		return watch.onFileModified( path )

	def onFileDeleted(self, watch, path):
		return watch.onFileDeleted( path )


##----------------------------------------------------------------##
class FileWatchEventHandler(PatternMatchingEventHandler):
	def __init__( self, owner, *args ):
		super( FileWatchEventHandler, self ).__init__( *args )
		self.owner = owner

	def on_moved(self, event):
		super(FileWatchEventHandler, self).on_moved(event)
		signals.emit('file.moved', self.owner, event.src_path, event.dest_path)		
		# what = 'directory' if event.is_directory else 'file'
		# logging.info("Moved %s: from %s to %s", what, event.src_path,
		# 						 event.dest_path)

	def on_created(self, event):
		super(FileWatchEventHandler, self).on_created(event)
		signals.emit('file.added', self.owner, event.src_path)
		# what = 'directory' if event.is_directory else 'file'
		# logging.info("Created %s: %s", what, event.src_path)

	def on_deleted(self, event):
		super(FileWatchEventHandler, self).on_deleted(event)
		signals.emit('file.removed', self.owner, event.src_path)
		# what = 'directory' if event.is_directory else 'file'
		# logging.info("Deleted %s: %s", what, event.src_path)

	def on_modified(self, event):
		super(FileWatchEventHandler, self).on_modified(event)
		signals.emit('file.modified', self.owner, event.src_path)
		# what = 'directory' if event.is_directory else 'file'
		# logging.info("Modified %s: %s", what, event.src_path)


##----------------------------------------------------------------##
class FileWatch(object):
	def __init__( self ):
		self.started = False
		self.watchDogWatch   = None
		self.watchDogHandler = FileWatchEventHandler( 
			self,
			self.getPatterns() or None,
			self.getIgnorePatterns() or False,
			self.getIgnoreDirectories() or False,
			self.getCaseSensitive() or True
		)
	
	def register( self ):
		app.getModule( 'file_watcher' ).registerFileWatch( self )

	def start( self ):
		if self.started: return
		
		path = self.getPath()
		if not path: return False

		path = os.path.realpath( path )
		recursive = self.getRecursive()

		self.watchDogWatch = app.getModule( 'file_watcher' ).requestInternalWatch( 
			self.watchDogHandler,
			path,
			recursive
		)
		self.started = True
		self.onStart()

		return True

	def stop( self ):
		path = self.getPath()
		if not self.started: return
		self.onStop()
		if self.watchDogWatch:
			app.getModule( 'file_watcher' ).stopInternalWatch( path )
			self.watchDogWatch = None
		self.started = False


	#Configs
	def getPath( self ):
		return None
	
	def getPatterns( self ):
		return None

	def getIgnorePatterns( self ):
		return [ '*/.git', '*/.DS_Store', '*/.~*', '*/.svn' ]

	def getIgnoreDirectories( self ):
		return None

	def getCaseSensitive( self ):
		return None

	def getRecursive( self ):
		return True

	#Callbacks
	def onStart( self ):
		pass

	def onStop( self ):
		pass

	def onFileMoved(self, path, newpath):
		pass

	def onFileCreated(self, path):
		pass

	def onFileModified(self, path):
		pass

	def onFileDeleted(self, path):
		pass

	