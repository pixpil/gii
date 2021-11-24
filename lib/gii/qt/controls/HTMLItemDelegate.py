from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import Qt
from qtpy.QtWidgets import \
	QStyle, QStyleOptionViewItemV4, QApplication, QTextDocument, QAbstractTextDocumentLayout, QPalette, \
	QColor

class HTMLItemDelegate(QtWidgets.QStyledItemDelegate):
	def paint(self, painter, option, index):
		options = QStyleOptionViewItemV4(option)
		self.initStyleOption(options,index)

		style = QApplication.style() if options.widget is None else options.widget.style()

		doc = QTextDocument()
		doc.setHtml(options.text)

		options.text = ""
		style.drawControl( QStyle.CE_ItemViewItem, options, painter)

		ctx = QAbstractTextDocumentLayout.PaintContext()
		textRect = style.subElementRect( QStyle.SE_ItemViewItemText, options )

		# Highlighting text if item is selected
		if options.state & QStyle.State_Selected :
			# ctx.palette.setColor(
			# 	QPalette.Text, options.palette.color(QPalette.Active, QPalette.HighlightedText)
			# )
			# painter.setBrush( options.palette.color( QPalette.Active, QPalette.Highlight ) )
			# painter.setBrush( QColor( '#c1f48b' ) )
			painter.setBrush( QColor( 0,180,0,30 ) )
			painter.setPen( Qt.NoPen )
			painter.drawRect( textRect )
			

		elif options.state & QStyle.State_MouseOver :
			# painter.setBrush( QColor( '#faffb8' ) )
			# painter.setPen( Qt.NoPen )
			# painter.drawRect( textRect )
			painter.setBrush( QColor( 0,255,0,10 ) )
			painter.setPen( Qt.NoPen )
			painter.drawRect( textRect )

		else:
			painter.setPen( QColor( 0,0,0,10 ) )
			painter.drawLine( textRect.bottomLeft(), textRect.bottomRight() )

		painter.save()
		painter.translate(textRect.topLeft())
		painter.setClipRect(textRect.translated(-textRect.topLeft()))
		doc.documentLayout().draw(painter, ctx)

		painter.restore()

	def sizeHint(self, option, index):
		options = QStyleOptionViewItemV4(option)
		self.initStyleOption(options,index)

		doc = QTextDocument()
		doc.setHtml(options.text)
		doc.setTextWidth(options.rect.width())
		return QtCore.QSize(doc.idealWidth(), doc.size().height())
