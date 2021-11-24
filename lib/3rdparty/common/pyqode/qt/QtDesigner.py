"""
Provides QtDesigner classes and functions.
"""
import os
from qtpy import QT_API
from qtpy import PYQT5_API
from qtpy import PYQT4_API


if os.environ[QT_API] in PYQT5_API:
    from PyQt5.QtDesigner import *
elif os.environ[QT_API] in PYQT4_API:
    from qtpy.QtDesigner import *
