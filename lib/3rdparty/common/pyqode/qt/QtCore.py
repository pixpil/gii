"""
Provides QtCore classes and functions.
"""
import os
from qtpy import QT_API
from qtpy import PYQT5_API
from qtpy import PYQT4_API
from qtpy import PYSIDE_API


if os.environ[QT_API] in PYQT5_API:
    from PyQt5.QtCore import *
    # compatibility with pyside
    from PyQt5.QtCore import Signal as Signal
    from PyQt5.QtCore import Slot as Slot
    from PyQt5.QtCore import pyqtProperty as Property
    # use a common __version__
    from PyQt5.QtCore import QT_VERSION_STR as __version__
elif os.environ[QT_API] in PYQT4_API:
    from qtpy.QtCore import *
    # compatibility with pyside
    from qtpy.QtCore import Signal as Signal
    from qtpy.QtCore import Slot as Slot
    from qtpy.QtCore import pyqtProperty as Property
    from qtpy.QtWidgets import QSortFilterProxyModel
    # use a common __version__
    from qtpy.QtCore import QT_VERSION_STR as __version__
elif os.environ[QT_API] in PYSIDE_API:
    from PySide.QtCore import *
    from PySide.QtWidgets import QSortFilterProxyModel
    # use a common __version__
    import PySide.QtCore
    __version__ = PySide.QtCore.__version__
