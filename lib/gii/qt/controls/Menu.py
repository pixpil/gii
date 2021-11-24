import logging
import weakref

from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtWidgets import QMenu, QMenuBar, QAction

from gii.core import signals, app

class MenuNode(object):
	_currentMenuContext = None

	"""docstring for MenuNode"""
	def __init__(self, option, parent, menubar = None):
		if isinstance(option ,str):
			blobs = option.split('|')
			_option={
				'label':blobs[0]
			}
			l = len(blobs)
			if l>1:	_option['shortcut'] = blobs[1]
			if l>2:	_option['help'] = blobs[2]
			option = _option

		self.qtmenubar = menubar
		self.qtaction  = None
		self.qtmenu    = None

		# self.qtaction = None
		self.owner  = None
		self.parent = parent
		self.groupName = None

		signal = option.get( 'signal', None )
		self.setSignal(signal)

		self.mgr = parent and parent.mgr
		self.owner = parent and parent.owner
		
		self.children = []
		self.actionGroups = {}
		
		self.label = option.get('label', 'UNNAMED')
		self.name  = option.get('name',self.label.replace('&','').replace(' ','_'))
		self.name  = self.name.lower()

		self.shortcut = option.get( 'shortcut',     False )
		self.help     = option.get( 'help',         ''    )
		self.priority = option.get( 'priority',     0     )
		self.itemType = option.get( 'type',         False )
		self.onClick  = option.get( 'on_click',     None  )
		self.cmd      = option.get( 'command',      None  )
		self.cmdArgs  = option.get( 'command_args', None  )
		self.link     = None

		self.groupName = option.get( 'group', None )

		self.menuType = self.qtmenubar and 'menubar' or 'item'

		children = option.get( 'children', None )
		link     = option.get( 'link', None )

		if children or self.itemType == 'menu':
			if self.menuType != 'menubar':
				self.menuType = 'menu'
				self.itemType = False

		elif link:
			self.link = link
			if self.menuType != 'menubar':
				self.menuType = 'link'

		elif parent and parent.menuType == 'menubar':
			self.menuType = 'menu'

		if self.menuType == 'menu' :
			self.qtmenu = QMenu(self.label)

		if not parent or parent.menuType == 'root': return 

		parent.addChildControl(self)
		if self.itemType == 'check':
			checked = option.get('checked',False)
			self.setValue(checked or False)
		if children:
			for data in children:
				self.addChild(data)
		# self.mgr.addNodeIndex(self)

	def getFullName(self):
		if parent:
			return parent.getFullName()+'/'+self.name
		return self.name
		
	def addChild( self, option, owner = None ):
		if option=='----':
			if self.qtmenu:
				self.qtmenu.addSeparator()
		elif isinstance(option, list):
			output=[]
			for data in option:
				n = self.addChild(data)
				if n :
					output.append(n)
					if owner: n.owner = owner
			return output
		else:
			node = MenuNode(option, self)
			if owner: node.owner = owner
			self.children.append(node)
			return node

	def affirmQtActionGroup( self, name ):
		group = self.actionGroups.get( name, None )
		if not group:
			group = QtWidgets.QActionGroup( self.qtmenu )
			self.actionGroups[ name ] = group
		return group

	def addChildControl(self, child):
		childType = child.menuType
		selfType  = self.menuType

		if selfType=='menu':
			if childType=='menu':
				child.qtaction = self.qtmenu.addMenu(child.qtmenu)

			elif child.link:
				qtmenu = child.link.qtmenu
				child.qtaction = self.qtmenu.addMenu(qtmenu)

			else:
				
				action = QtWidgets.QAction(child.label, None, 
					shortcut = child.shortcut,
					statusTip = child.help,
					checkable = child.itemType=='check',
					triggered = child.handleEvent
				)

				self.qtmenu.addAction(action)
				child.qtaction = action

				if child.groupName:
					self.affirmQtActionGroup( child.groupName ).addAction( action )

		elif selfType=='menubar':
			if childType=='menu':
				self.qtmenubar.addMenu(child.qtmenu)
				child.qtaction = child.qtmenu.menuAction()
			else:
				logging.warning('attempt to add menuitem/link to a menubar')
				return
		else:
			logging.warning('menuitem has no child')	

	def setEnabled(self, enabled):
		#todo: set state of linked item
		selfType = self.menuType
		if selfType == 'menubar':
			self.qtmenubar.setEnable(enabled)
			return

		if self.qtmenu:
			self.qtmenu.setEnabled(enabled)
		else:
			self.qtaction.setEnabled(enabled)

	def remove(self):
		self.clear()
		self.parent.children.remove(self)
		selfType = self.menuType
		
		if not self.parent: return

		if selfType=='menubar':
			return

		parentType = self.parent.menuType

		if parentType == 'menu':
			self.parent.qtmenu.removeAction( self.qtaction )
		elif parentType == 'menubar':
			self.parent.qtmenubar.removeAction( self.qtaction )
		logging.info('remove menunode:' + self.name )

	def clear( self ):
		if self.menuType in [ 'menu', 'menubar' ]:
			for node in self.children[:]:
				node.remove()
		
	def findChild(self,name):
		name = name.lower()
		for c in self.children:
			if c.name==name: return c
		return None

	def getValue(self):
		if self.itemType in ('check','radio'):
			return self.qtaction.isChecked()
		return True

	def setValue(self, v):
		if self.itemType in ('check','radio'):
			self.qtaction.setChecked(v and True or False)
	
	def setSignal(self, signal):
		if isinstance(signal, str):
			signal = signals.get(signal)
		self.signal = signal

	def popUp( self, **option ):
		if self.qtmenu:
			context = option.get( 'context', None )
			MenuNode._currentMenuContext = context
			self.qtmenu.exec_(QtGui.QCursor.pos())

	def getContext( self ):
		return MenuNode._currentMenuContext
		
	def setOnClick(self, onClick):
		self.onClick = onClick

	def handleEvent(self):
		itemtype = self.itemType
		value    = self.getValue()
		logging.debug( 'menu event:' + self.name )
		if self.owner:
			if hasattr( self.owner, 'onMenu' ):
				self.owner.onMenu( self )

		if self.signal:
			self.signal(value)
		if self.onClick != None:			
			self.onClick(value)
		if self.cmd:
			args = self.cmdArgs or {}
			app.doCommand( self.cmd, **args )
		MenuNode._currentMenuContext = None

class MenuManager(object):
	"""docstring for MenuManager"""
	_singleton = None

	@staticmethod
	def get():
		return MenuManager._singleton

	def __init__(self):
		assert(not MenuManager._singleton)
		MenuManager._singleton = self
		super(MenuManager, self).__init__()
		
		self.rootNode = MenuNode({}, None)
		self.rootNode.mgr = self		
		self.rootNode.menuType ='root'

		self.menuNodes = {}

	# def removeNodeIndex(self, node):
	# 	id = node.qtaction
	# 	if id:
	# 		del self.menuNodes[id]

	# def addNodeIndex(self, node):
	# 	id = node.qtaction
	# 	if id:
	# 		self.menuNodes[id]=node

	# def getNodeByIndex(self, id):
	# 	return self.menuNodes.get(id, None)
	
	def find(self,path):
		blobs = path.split('/')
		result = self.rootNode
		for b in blobs:
			result = result.findChild(b)
			if not result: return None

		if result!=self.rootNode:
			return result
		else:
			return None

	def addMenuBar(self, name, menubar, owner = None):
		node = MenuNode({
				'name':name
			}, self.rootNode, menubar)
		self.rootNode.children.append(node)
		if owner: node.owner = owner
		return node

	def addMenu(self, path, option = None, owner = None): #menu for link or popup
		blobs     = path.split('/')
		upperPath = "/".join(blobs[:-1])
		name      = blobs[-1]
		parent    = self.find(upperPath) 
		
		if not parent: parent = self.rootNode
		if not option: option={}
		if name == '----':
			option = '----'
		else:
			if isinstance(option, dict):
				if not option.get('label',None):
					option['label'] = name
				if not option.get('name'):
					option['name']  = name
			option[ 'type' ]='menu'
			
		return parent.addChild( option, owner )

	def addMenuItem(self, path, option = None, owner = None):
		blobs     = path.split('/')
		upperPath = "/".join(blobs[:-1])
		name      = blobs[-1]
		parent    = self.find(upperPath) 
		
		if not parent: raise Exception('menu parent not found:%s'%upperPath)
		
		if isinstance(option, dict):
			if not option.get('label',None):
				option['label'] = name
			if not option.get('name'):
				option['name']  = name

		return parent.addChild( option or name, owner)

	def enableMenuItem(self, path, enabled = True):
		node = self.find(path)
		if node: node.setEnabled(enabled)
	
	def disableMenuItem(self, path, disabled = True):
		self.enableMenuItem(path, not disabled)


MenuManager()