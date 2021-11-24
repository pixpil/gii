import sip
try:
	sip.setapi("QString", 2)
	sip.setapi('QVariant', 2)
except Exception as e:
	pass

from .QtSupport import QtSupport, QtGlobalModule
from .QtEditorModule import QtEditorModule
from .TopEditorModule import TopEditorModule, SubEditorModule

from . import QtWindowSchemeManager

from . import QtResGuard
