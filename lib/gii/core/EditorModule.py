from abc import ABCMeta, abstractmethod
import logging
import inspect
import sys
import os.path
import time

from functools import cmp_to_key
from time import time as getTime

from .res     import *

from . import signals
from .project import Project
from .Command import EditorCommandRegistry

from .EditorTimer import EditorTimer

##----------------------------------------------------------------##
class EditorModuleMeta( ABCMeta ):
	def __init__( cls, name, bases, attrs ):
		super( EditorModuleMeta, cls ).__init__( name, bases, attrs )
		name                   = attrs.get( 'name', None )
		override               = attrs.get( 'override', False )
		dependency             = attrs.get( 'dependency', [] )
		allow_compiled_project = attrs.get( 'allow_compiled_project', False )
		if name:
			m = cls()
			if isinstance( dependency, str ):
				dependency = [ dependency ]
			m._dependency = dependency
			m._name       = name
			m._allow_compiled_project = allow_compiled_project
			m._override   = override
			m.getDependency = lambda: dependency
			EditorModuleManager.get().registerModule(	m )


##----------------------------------------------------------------##
## EDITORMODULE
##----------------------------------------------------------------##
class EditorModule( ResHolder, metaclass=EditorModuleMeta ):
	def __repr__(self):
		return '<module: %s>'%self.getName()

	def getDependency(self):
		return self._dependency or []

	def getBaseDependency( self ):
		return [ 'gii' ]

	def getActualDependency( self ):
		return self.getDependency() + self.getBaseDependency()

	def getName(self):		
		return self._name or '???'

	def getAttr( self, key, default = None ):
		if hasattr( self, key ):
			return getattr( self, key )
		else:
			return default

	def checkAllowedInProject( self, project ):
		ptype = project.getProjectType()
		if ptype == 'compiled':
			if not self.getAttr( '_allow_compiled_project', False ): return False
		return True
	
	def getModulePath( self, path = None ):
		modName = self.__class__.__module__		
		m = sys.modules.get( modName, None )
		if m:			
			dirname = os.path.dirname( m.__file__ )
			if path:
				return dirname + '/' + path
			else:
				return dirname

	def register( self ):
		EditorModuleManager.get().registerModule( self )

	def getApp( self ):
		return self._app

	def findDataFile( self, fileName ):
		return self.getApp().findDataFile( filename )

	def doCommand( self, fullname, *args, **kwargs ):
		return self._app.doCommand( fullname, *args, **kwargs )

	def getProject( self ):
		return Project.get()

	def isCompiledProject( self ):
		return Project.get().isCompiledProject()

	def getAssetLibrary( self ):
		return self.getProject().getAssetLibrary()
	
	def getManager(self):
		return self._manager

	def getModule(self, name):
		return self._manager.getModule(name)

	def affirmModule(self, name):
		return self._manager.affirmModule(name)

	def affirmConfigTable(self):
		data = {}

	def setConfig( self, name, value ):
		assert(isinstance(name, str))
		self.getProject().setModuleConfig( self.getName(), name, value )

	def getConfig( self, name, defaultValue=None ):
		assert( isinstance(name, str) )
		value = self.getProject().getModuleConfig( self.getName(), name, None )
		if value != None: return value
		#legacy
		fullname = self.getName()+'/'+name
		return self.getProject().getConfig( fullname, defaultValue )

	def setAppConfig( self, name, value ):
		assert(isinstance(name, str))
		fullname = self.getName()+'/'+name
		self.getApp().setConfig( fullname, value )

	def getAppConfig( self, name, defaultValue=None ):
		assert( isinstance(name, str) )
		fullname = self.getName()+'/'+name
		return self.getApp().getConfig( fullname, defaultValue )

	def getAppUserSetting( self, name, default = None ):
		return self.getApp().getUserSetting( name, default )

	def getProjectUserSetting( self, name, default = None ):
		return self.getProject().getUserSetting( name, default )

	def setWorkspaceConfig( self, name, value ):
		assert(isinstance(name, str))
		fullname = self.getName()+'/'+name
		self.getProject().setWorkspaceConfig( fullname, value )

	def getWorkspaceConfig( self, name, defaultValue = None ):
		assert( isinstance(name, str) )
		fullname = self.getName()+'/'+name
		return self.getProject().getWorkspaceConfig( fullname, defaultValue )
	
	def isDependencyReady(self):
		dep=self.getActualDependency()
		if not dep: return True

		manager=self.getManager()
		for name in dep:
			m = manager.affirmModule(name)
			if not getattr(m,'alive'): return False
		return True
	
	def isDependentUnloaded(self): #FIXME: use a clear name		
		dependent = self.dependent #added by manager
		for m in dependent:
			if m.alive: return False
		return True

	def load(self):
		self.timers = []
		logging.info('loading module:%s' % self.getName())
		self.onLoad()
		self.alive  = True
		
	def unload(self):
		for timer in self.timers:
			timer.stop()
		logging.info('unloading module:%s' % self.getName())
		if self.active:
			self.stop()
		self.alive  = False
		self.releaseAll()
		self.onUnload()

	def start( self ):
		if self.active: return
		logging.info( 'starting module:' + self.getName() )
		self.active = True
		for dep in self.getActualDependency():
			m = self.getModule( dep )
			if m: m.start()

		self.onStart()

	def stop( self ):
		if not self.active: return
		self.active = False
		for depModule in self.dependent:
			depModule.stop()
		self.onStop()

	def confirmStop( self ):
		return True

	def needUpdate( self ):
		return False
		
	def update( self ):
		self.onUpdate()
		
	#Tool
	def addTimer( self, **kwargs ):
		timer = self.getApp().addTimer( **kwargs )
		self.timers.append( timer )
		return timer

	#Callbacks
	def onLoad(self):
		pass

	def onRegister(self, name):
		pass

	def onSerialize(self):
		pass

	def onDeserialize(self):
		pass

	def onUnload(self):
		pass

	def onUpdate(self):
		pass
	
	def onStart( self ):
		pass

	def onAppReady( self ):
		pass
		
	def onStop( self ):
		pass


##----------------------------------------------------------------##
def _sortModuleIndex( m1, m2 ):
	diffIndex = m2.moduleIndex - m1.moduleIndex
	if diffIndex > 0 : return -1
	if diffIndex < 0 : return 1
	diffRegIndex = m2.regIndex - m1.regIndex
	if diffRegIndex > 0 : return -1
	if diffRegIndex < 0 : return 1
	return 0


##----------------------------------------------------------------##
## MODULE MANAGER
##----------------------------------------------------------------##
class EditorModuleManager(object):
	"""docstring for EditorModuleManager"""
	_singleton=None
	@staticmethod
	def get():
		return EditorModuleManager._singleton

	def __init__(self):
		assert not EditorModuleManager._singleton
		EditorModuleManager._singleton = self
		self.modules     = {}
		self.moduleQueue = []
		self.updatingModuleQueue = []
		self.sortedModuleQueue = []
		self.moduleChanged = False

	def getAllModules(self):
		return self.modules

	def loadModule( self, m, loadDep=True ):
		if m.alive: return True
		m.loading = True
		for n in m.getActualDependency():
			m1 = self.affirmModule(n)
			if m1 == m: continue
			if not m1.alive:
				if not loadDep:
					m.loading = False
					return False
				if m1.loading: 
					raise Exception('cyclic dependency:%s -> %s'%( m.getName(), m1.getName()) )
				self.loadModule( m1 )
			m1.dependent.append( m )

		t0 = time.process_time()
		m.load()
		# print 'loading module', m.getName(), ( time.process_time() - t0 ) * 1000
		m.loading=False
		signals.emit('module.load',m)
		return True

	def unloadModule( self, m ):
		self.moduleChanged = True
		if m.isDependentUnloaded():
			signals.emit('module.unload',m)
			m.unload()
			return True
		else:
			return False

	def loadAllModules(self):
		#filter disallowed module
		project = Project.get()
		for name, m in self.modules.items():
			m.allowed = m.checkAllowedInProject( project )

		#load
		queue = self.affirmSortedModuleQueue()
		for m in queue:
			self.loadModule( m )

	def updateAllModules( self ):
		for m in self.getUpdatingModuleQueue():
			if m.alive:
				# t = getTime()
				m.update()
				# dt = getTime() - t
				# if dt > 0.0005:
				# 	print 'update module', m, dt

	def startAllModules( self ):
		logging.info( 'start all modules' )
		for m in self.affirmSortedModuleQueue():
			if m.alive: m.start()
	
	def confirmStopModules( self ):
		logging.info( 'confirm all modules stoppable' )
		for m in self.affirmSortedModuleQueue():
			if not m.alive: continue
			if m.confirmStop() == False:
				logging.info( 'cannot stop module:' + m.getName() )
				return False
		return True

	def stopAllModules( self ):
		logging.info( 'stop all modules' )
		for m in self.affirmSortedModuleQueue():
			if m.alive: m.stop()

	def tellAllModulesAppReady( self ):
		logging.info( 'post start all modules' )
		for m in self.affirmSortedModuleQueue():
			if m.alive: 
				logging.info( 'app ready for module:' + m.getName() )
				m.onAppReady()
				m.ready = True

	def unloadAllModules(self):
		self.moduleChanged = True
		for m in reversed( self.affirmSortedModuleQueue() ):
			self.unloadModule( m )

	def registerModule( self, module, **option ):
		if not isinstance(module, EditorModule):
			raise Exception('Module expected, given:%s' % type(module))

		self.moduleChanged = True

		name = module.getName()
		override = False
		if hasattr( module, '_override' ):
			override = module._override
		if self.getModule(name):  #overriding?
			if not override:
				raise Exception('Module name duplicated:%s' % name)
			else: #override
				module0 = self.getModule( name )
				self.moduleQueue.remove( module0 )
				signals.emit( 'module.override', name, module, module0 )
		else:
			if override:
				raise Exception('No module to override:%s' % name)

		self.modules[name] = module
		self.moduleQueue.append(module)

		module._app      = self._app
		module._manager  = self

		module.regIndex    = len( self.moduleQueue ) - 1
		module.moduleIndex = None
		module.allowed     = True
		module.alive       = False
		module.ready       = False
		module.active      = False
		module.loading     = False
		module.dependent   = []

		module.onRegister( name )
		signals.emit( 'module.register', module )


	def unregisterModule(self, m):
		if m.alive:
			if m.isDependentUnloaded():
				self.moduleChanged = True
				m.unload()
				del self.modules[m.getName()]
				self.moduleQueue.remove(m)
				signals.emit( 'module.unregister', m )
			else:
				return False

	def getUpdatingModuleQueue( self ):
		return self.updatingModuleQueue

	def affirmSortedModuleQueue( self ):
		if self.moduleChanged:
			#clear moduleIndex
			for m in self.moduleQueue:
				if not m.allowed: continue
				m.moduleIndex = None
			modulesToSort = self.moduleQueue[ : ]

			while True:
				modulesNotSorted = []
				progressing = False
				for m in modulesToSort:
					newIndex = 0
					for depId in m.getActualDependency():
						depM = self.getModule( depId )
						if not depM:
							raise Exception( 'for %s, depencency module not found: %s' % ( m.getName(), depId ) )
						if depM == m: continue
						if depM.moduleIndex is None:
							newIndex = None
							break #dependency not calculated
						else:
							newIndex = max( newIndex, depM.moduleIndex + 1 )

					if newIndex is None:
						modulesNotSorted.append( m )
					else:
						m.moduleIndex = newIndex	
						progressing = True

				modulesToSort = modulesNotSorted
				if not modulesToSort:
					break

				if not progressing:
					print('These modules may have cyclic dependency')
					for m in modulesToSort:
						print((m.getName(), m.getActualDependency()))
					raise Exception('Modules may have cyclic Dependency')

			self.sortedModuleQueue = sorted( self.moduleQueue, key = cmp_to_key(_sortModuleIndex) )
			for m in self.sortedModuleQueue:
				if m.needUpdate():
					# if not m.__class__.update == EditorModule.update:
						# print 'update overrided', m.getName()
					# if not m.__class__.onUpdate == EditorModule.onUpdate:
						# print 'onUpdate overrided', m.getName()
					self.updatingModuleQueue.append( m )
			self.moduleChanged = False
			# for m in self.sortedModuleQueue:
			# 	print m.getName(), m.moduleIndex, m.regIndex	
		return self.sortedModuleQueue
	
	def getModule(self, name):
		return self.modules.get(name,None)

	def affirmModule( self, name ):
		m = self.getModule(name)
		if not m: raise Exception('Module not found: %s' %name)
		return m

EditorModuleManager()

##----------------------------------------------------------------##	
def registerEditorModule(m):
	EditorModuleManager.get().registerModule(m)

def unregisterEditorModule(m):
	EditorModuleManager.get().unregisterModule(m)

def getEditorModule(name):
	return EditorModuleManager.get().getModule(name)

def affirmEditorModule(name):
	return EditorModuleManager.get().affirmModule(name)