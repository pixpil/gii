##----------------------------------------------------------------##
from qtpy           import QtCore, QtWidgets, QtGui, uic
from qtpy.QtCore    import Qt, Signal

##----------------------------------------------------------------##
class CategoryContainer( QtWidgets.QWidget ):
	foldChanged  = Signal( bool )
	def __init__(self, parent, id, label = None ):
		super(CategoryContainer, self).__init__( parent )
		self.titleBar = QtWidgets.QPushButton( self )
		self.content = QtWidgets.QWidget( self )
		self.id = id
		self.label = label
		layout = QtWidgets.QVBoxLayout( self )
		layout.addWidget( self.titleBar )
		layout.addWidget( self.content )
		layout.setSpacing( 5 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		self.titleBar.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding, 
			QtWidgets.QSizePolicy.Fixed
		)
		self.titleBar.setObjectName( 'CategoryTitleBar' )
		self.titleBar.setMinimumSize( 100, 30 )

		self.content.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding, 
			QtWidgets.QSizePolicy.Minimum
		)
		self.content.setMinimumSize( 100, 20 )

		self.titleBar.clicked.connect( self.onToggleContent )
		self.expanded = None
		self.label = label or ''
		self.setExpanded( True )
		contentLayout = QtWidgets.QVBoxLayout( self.content )
		contentLayout.setContentsMargins( 0 , 0 , 0 , 0 )
		contentLayout.setSpacing( 1 )

	def onToggleContent( self ):
		self.setExpanded( not self.expanded )

	def setExpanded( self, expanded = True ):
		if expanded == self.expanded : return
		self.expanded = expanded
		self.foldChanged.emit( self.expanded )
		if expanded:
			self.titleBar.setText( '[ - ] %s' % self.label )
			self.content.show()
		else:
			self.titleBar.setText( '[ + ] %s' % self.label )
			self.content.hide()

##----------------------------------------------------------------##
class CategoryList( QtWidgets.QScrollArea ):
	def __init__( self, *args ):
		super( CategoryList, self ).__init__( *args )
		self.categories = {}
		self.body = QtWidgets.QWidget( self )
		layout = QtWidgets.QVBoxLayout( self.body )
		self.body.setSizePolicy(
			QtWidgets.QSizePolicy.Expanding, 
			QtWidgets.QSizePolicy.Minimum
		)
		layout.setSpacing( 0 )
		layout.setContentsMargins( 0 , 0 , 0 , 0 )
		layout.addStretch()
		self.setWidget( self.body )
		self.setWidgetResizable(True)
		self.setAlignment( Qt.AlignTop )


	def addCategory( self, id, label = None ):
		body = self.body
		container = CategoryContainer( body, id, label )
		layout = body.layout()
		# layout.addWidget( container )
		self.categories[ id ] = container
		count = layout.count()
		assert count>0
		layout.insertWidget( count - 1, container )
		return container.content

	def getCategory( self, id ):
		container = self.getCategoryContainer( id )
		if container:
			return container.content

	def getCategoryContainer( self, id ) :
		return self.categories.get( id, None )

	def removeCategory( self, id ):
		pass

