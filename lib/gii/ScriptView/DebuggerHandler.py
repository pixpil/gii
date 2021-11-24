import json
from gii.core import signals

class DebuggerHandler(object):
	def __init__(self, module):
		assert(module)
		self.module=module
		signals.connect('debug.enter', self.onDebugEnter)
		signals.connect('debug.exit', self.onDebugExit)
		signals.connect('debug.info', self.onDebugInfo)
		self.busy=False

	#EVENT
	def onDebugEnter(self):		
		self.busy=True
		self.module.setFocus()
		self.module.toggleDebug(True)
		# self.module.frame.MakeModal(True)

	def onDebugExit(self):
		self.busy=False
		if not self.module.alive: return
		self.module.toggleDebug(False)
		# self.module.frame.MakeModal(False)
		# self.module.book.clearHilight('normal')


	def onDebugInfo(self, msg=False, dataJSON=None):
		data={}
		if dataJSON:
			data=json.loads(dataJSON.encode('utf-8'))
		if msg=='callstack':
			self.module.panelDebug.loadStackData(data)
		if msg=='vars':
			scope=data['scope']
			self.module.panelDebug.loadVarData(data['data'],data['parent'])
		
	#COMMAND
	def emitCMD(self, cmd, data=None):		
		signals.emit('debug.command', cmd.encode('utf-8'), data)

	def doStepIn(self):
		self.emitCMD('step')

	def doStepOver(self):
		self.emitCMD('over')

	def doStepOut(self):
		self.emitCMD('out')

	def doStop(self):
		self.emitCMD('terminate')
		signals.emitNow('debug.stop')

	def doContinue(self):
		self.emitCMD('exit')
		signals.emitNow('debug.continue')
		
	def getScopeInfo(self, stackId):
		self.emitCMD('set %d' % stackId)
		self.emitCMD('vars')

	def dumpVar(self, index):		
		self.emitCMD('dump %s' % index)

	def getWatch(self):
		pass
		
	def addBreakPoint(self, file, line):
		pass

	def removeBreakPoint(self, file, line):
		pass

	def clearBreakPointInFile(self, file):
		pass