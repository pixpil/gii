from gii.core import *
from AKU import _LuaTable, _LuaThread, _LuaObject, _LuaFunction

def wrapLuaFunc(func):
	#todo: type operator crashes.  will replace lunatic with lupa
	if func and hasattr(func,'__call__'):
		return func

	if func or func==None or func==False:
		return None

	def caller(*args):
		try:
			func(*args)
		except Exception as e:
			print(e) #TODO
	return caller

##----------------------------------------------------------------##
class LuaEditorModuleContainer(EditorModule):
	def __init__(self, setting):
		super(LuaEditorModuleContainer, self).__init__()

		self.name       = setting['name']
		self.dependency = setting['dependency'] or ['moai']
		
		self._onLoad        = wrapLuaFunc(setting['onLoad'])
		self._onUnload      = wrapLuaFunc(setting['onUnload'])
		self._onSerialize   = wrapLuaFunc(setting['onSerialize'])
		self._onDeserialize = wrapLuaFunc(setting['onDeserialize'])

		self._onGUI         = wrapLuaFunc(setting['onGUI'])
		self._onMenu        = wrapLuaFunc(setting['onMenu'])

		self.useIMGUI       = setting['IMGUI'] and self._onGUI
		self.usingIMGUI=False

	def getName(self):
		return self.name

	def getDependency(self):
		return self.dependency

	def enableIMGUI(self):
		main=self.getManager().affirmModule('main')
		self.container=main.requestDockWindow(self.name,
				title=self.name,
				dock='right',
				minSize=(200,200)
			)
		self.imguiWidget=self.container.addWidget(
				IMGUIContextWidget(self.container)
			)
		self.imguiWidget.setDelegate(self)
		self.usingIMGUI=True

		
	def onLoad(self):
		if self.useIMGUI:
			self.enableIMGUI()
		if self._onLoad: self._onLoad()

	def onUnload(self):
		if self._onUnload: self._onUnload()
		if self.usingIMGUI:
			self.usingIMGUI=False
			self.imguiWidget.destroy()
			self.container.destroy()
		self._onLoad        = None
		self._onUnload      = None
		self._onSerialize   = None
		self._onDeserialize = None

		self._onGUI=None
		self._onMenu=None
		#release all lua reference

	def onSerialize(self):
		if self._onSerialize: self._onSerialize()

	def onDeserialize(self):
		if self._onDeserialize: self._onDeserialize()

	def onMenu(self, menuitem):
		if self._onMenu: self._onMenu(menuitem)

	def onGui(self, context):
		if self._onGUI and self.usingIMGUI: self._onGUI(context)

