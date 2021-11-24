from gii.core.model import *
from .PropertyEditor import *
from .CommonFieldEditors import *
from gii.qt.helpers    import addWidgetWithLayout, restrainWidgetToScreen
from qtpy import QtWidgets, QtGui, QtCore
from qtpy.QtCore import Qt,QObject,QEvent


##------------------------------------------------------------##

def _getTypeRepr( t ):
	if isinstance( t, type ):
		return t.__name__
	elif isinstance(t,AssetRefType):
		return '%s'%(t.getName())
	else:
		return t[ '__name' ]

##------------------------------------------------------------##

class SizeEditor(object):
	def __init__(self,parentWidget):
		self.parentWidget = parentWidget
		self.sizeField = Field(None,'__size',int)
		self.editor = NumberFieldEditor(self.parentWidget,self.sizeField)

		label = 'size'
		if not self.editor:
			logging.info( 'no field editor for: size')
			return
		labelWidget = self.editor.initLabel(label,self.parentWidget)
		editorWidget = self.editor.initEditor(self.parentWidget)
		self.editor.setWheelEventConfig( True )
		editorWidget.setKeyboardTracking(False)
		editorWidget.setObjectName('SizeEditor')
		labelWidget.setObjectName('sizeLabel')
		if labelWidget in (None, False):
			self.parentWidget.layout().insertRow(0, editorWidget )
		else:
			self.parentWidget.layout().insertRow(0, labelWidget, editorWidget )
		self.parentWidget.editors['size'] = self.editor
		self.editor.set( len( self.parentWidget.owner.value ) )



##------------------------------------------------------------##
class SimpleArrayEditor(QtWidgets.QFrame):
	def __init__( self, container, owner ):
		super( SimpleArrayEditor, self ).__init__( container )
		# self.setWindowFlags( Qt.Tool )
		self.elementChanging = False
		self.owner = owner
		self.arraySize = 0

		layout = QtWidgets.QFormLayout( self )
		layout.setHorizontalSpacing( 2 )
		layout.setVerticalSpacing( 2 )
		layout.setContentsMargins( 2 , 2 , 2 , 2 )
		layout.setLabelAlignment( Qt.AlignLeft )
		layout.setFieldGrowthPolicy( QtWidgets.QFormLayout.ExpandingFieldsGrow )
		layout.setContentsMargins( 15, 0,0,0 )

		self.setSizePolicy( 
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Minimum
		)

		self.editors    = {}
		self.sizeEditor = SizeEditor( self )
		self.factories = getPropertyEditorFactories()

	def addAllEditor( self ):
		for i,v in enumerate( self.owner.value ):
			self.addOneEditor( self.owner.field, i )

	def addOneEditor(self,field,index):
		elementField = ArrayItemVirtualField(self.owner.field,index)
		editor = buildFieldEditor(self.owner,elementField)
		label = '[%d]'%( index + 1 ) #1-based
		if not editor:
			logging.info( 'no field editor for:' + label )
		labelWidget = editor.initLabel(label, self)
		editorWidget = editor.initEditor(self)
		editor.set(self.owner.value[index])
		editorWidget.setObjectName( 'ElementEditor' )
		labelWidget.setObjectName( 'ElementLabel' )
		if labelWidget in (None, False):
			self.layout().insertRow (index + 1, editorWidget )
		else:
			self.layout().insertRow (index + 1, labelWidget, editorWidget )
		self.editors[index] = editor
		pass

	def clear(self,fromIndex,endIndex):
		for index in range(fromIndex,endIndex):
			self.editors[index].clear()

		layout = self.layout()
		fromLayoutIndex = 2*fromIndex + 2
		while layout.count() > fromLayoutIndex:
			child = layout.takeAt( fromLayoutIndex )
			if child :
				w = child.widget()
				if w:
					w.setParent( None )
					w.deleteLater()
			else:
				break

	def rebuild( self ):
		self.clear( 0, self.arraySize )
		self.addAllEditor()
		self.sizeEditor.editor.set( len( self.sizeEditor.parentWidget.owner.value ) )

	def onPropertyChanged(self,field,value):
		self.onSizeChanged( field, value )
	
	def onSizeChanged(self,field,size):
		self.setUpdatesEnabled( False )

		newArray = self.owner.value
		arraySize = len(newArray)
		self.arraySize = arraySize
		if size < 0:
			size = 0
			self.editors['size'].set(0)
			return self.setUpdatesEnabled( True )

		if size > 1000:
			size = 1000
			self.editors['size'].set(1000)
			return self.setUpdatesEnabled( True )

		if size == arraySize:
			return self.setUpdatesEnabled( True )

		elif size > arraySize:
			for i in range(arraySize, size):
				if isinstance(self.owner.targetType, type):
					newArray.append(self.owner.targetType())
				else:
					newArray.append(False)
				self.addOneEditor(field,i)

		elif size < arraySize:
			for i in range(size, arraySize):
				newArray.pop()
			self.clear(size , arraySize)
			
		self.owner.setValue(newArray)
		self.setUpdatesEnabled( True )

	def onElementChanged(self,field,value):
		tempValue = self.owner.value
		tempValue[field.index] = value
		self.elementChanging = True
		self.owner.setValue(tempValue)
		self.elementChanging = False

##------------------------------------------------------------##
##------------------------------------------------------------##
class SimpleArrayFieldButton(QtWidgets.QToolButton):
	def sizeHint(self):
		return 	QtCore.QSize(20,20)



##------------------------------------------------------------##
class SimpleArrayFieldEditor(FieldEditor):
	def setTarget(self,parent,field):
		super( SimpleArrayFieldEditor, self).setTarget(parent,field)
		t = field.getType()
		self.field = field
		self.targetType = t.itemType
		self.targetContext = None
		self.value = None
		self.selectionFunc = field.getOption( 'selection', None )
		self.editor = None

	def get(self):
		pass

	def set(self, value):
		self.value = value or []
		self.size = len(self.value)
		text = '%s[%d]'%( _getTypeRepr( self.targetType ), self.size )
		self.button.setText(text)
		if self.editor:
			if not self.editor.elementChanging:
				self.editor.rebuild()

	def setValue(self, value):
		self.set(value)
		self.notifyChanged(value)

	def initEditor(self,container):
		self.button = SimpleArrayFieldButton(container)
		self.button.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding,
			QtWidgets.QSizePolicy.Expanding
			)
		self.button.setCheckable( True )
		self.value = []
		self.size =len( self.value )
		self.button.setText('%s[%d]'%( _getTypeRepr( self.targetType ), self.size ))
		if self.getOption('readonly',False):
			self.button.setEnabled(False)
		self.button.clicked.connect( self.openArrayEdit )
		return self.button

	def postInit( self, container ):
		self.editor = SimpleArrayEditor( container, self )
		container.layout().addRow( self.editor )
		self.editor.hide()

	def onPropertyChanged(self,field,value):
		if not self.editor:
			return
		if field.id != '__size':
			self.editor.onElementChanged(field,value)
		else:
			self.editor.onSizeChanged(field,value)

	def openArrayEdit(self):
		if self.button.isChecked():
			self.editor.show()
		else:
			self.editor.hide()

##------------------------------------------------------------##
class SimpleArrayFieldEditorFactory(FieldEditorFactory):
	def getPriority(self):
		return 100

	def build(self, parentEditor,field,context = None):
		dataType = field._type
		while dataType:
			if dataType == ArrayType:
				return SimpleArrayFieldEditor(parentEditor,field)
			dataType = getSuperType(dataType)
		return None

registerFieldEditorFactory( SimpleArrayFieldEditorFactory() )