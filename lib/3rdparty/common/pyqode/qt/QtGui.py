"""
Provides QtWidgets classes and functions.

.. warning:: All qtpy/PySide gui classes are exposed but when you use
    PyQt5, those classes are not available. Therefore, you should treat/use
    this package as if it was ``PyQt5.QtWidgets`` module.
"""
import os
from qtpy import QT_API
from qtpy import PYQT5_API
from qtpy import PYQT4_API
from qtpy import PYSIDE_API


if os.environ[QT_API] in PYQT5_API:
    from PyQt5.QtWidgets import *
elif os.environ[QT_API] in PYQT4_API:
    from qtpy.QtWidgets import *
elif os.environ[QT_API] in PYSIDE_API:
    from PySide.QtWidgets import *
