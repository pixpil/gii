# -*- coding: utf-8 -*-

from qtpy import QtWidgets, QtGui, QtCore, QtOpenGL, uic
from qtpy.QtCore import Qt, QObject, QEvent, Signal
from qtpy.QtCore import QPoint, QRect, QSize
from qtpy.QtCore import QPointF, QRectF, QSizeF
from qtpy.QtGui import QColor, QTransform

from .GraphicsViewHelper import *

import sys
import math


##----------------------------------------------------------------##
class GraphNodeItemBase( object ):
	def isGroup( self ):
		return False

	def initGraphNode( self ):
		pass

	def acceptConnection( self, conn ):
		return False

	def createConnection( self, **options ):
		return None


if __name__ == '__main__':
	from . import TestGraphView
	