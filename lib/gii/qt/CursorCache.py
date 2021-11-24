import os.path

from qtpy import QtCore, QtWidgets, QtGui
from qtpy.QtCore import Qt

import logging
from gii.core import app

_cursorCache = {}
_nullCursor = Qt.ArrowCursor


_builtinCursors = {
	'arrow'           : Qt.ArrowCursor,
	'up-arrow'        : Qt.UpArrowCursor,
	'cross'           : Qt.CrossCursor,
	'wait'            : Qt.WaitCursor,
	'i-beam'          : Qt.IBeamCursor,
	'size-vertical'   : Qt.SizeVerCursor,
	'size-horizontal' : Qt.SizeHorCursor,
	'size-bd'         : Qt.SizeBDiagCursor,
	'size-fd'         : Qt.SizeFDiagCursor,
	'size-all'        : Qt.SizeAllCursor,
	'blank'           : Qt.BlankCursor,
	'split-v'         : Qt.SplitVCursor,
	'split-h'         : Qt.SplitHCursor,
	'pointing-hand'   : Qt.PointingHandCursor,
	'forbidden'       : Qt.ForbiddenCursor,
	'open-hand'       : Qt.OpenHandCursor,
	'closed-hand'     : Qt.ClosedHandCursor,
	'whats-this'      : Qt.WhatsThisCursor,
	'busy'            : Qt.BusyCursor,
}

def getCursor( name, fallback=None, **option ):
	if ( not name ) or name == 'arrow' : return _nullCursor
	
	cursor = _builtinCursors.get( name ,None )
	if cursor: return cursor

	cursor = _cursorCache.get( name, None )
	if cursor: return cursor

	cursorFile = None
	path = app.findDataFile( 'cursors/%s.png' % name )
	if not path:
		if fallback:
			return getCursor( fallback )
		logging.error('cursor not found: %s' % name)
		return QtGui.QCursor()

	pix = QtGui.QPixmap(path)
	# hx = -1
	# hy = -1
	# w, h = pix.width(), pix.height()

	hx = option.get( 'x', -1 )
	hy = option.get( 'y', -1 )
	cursor = QtGui.QCursor( pix, hx, hy )

	_cursorCache[ name ]=cursor
	return cursor

