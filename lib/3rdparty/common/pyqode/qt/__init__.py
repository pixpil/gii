"""
**qtpy** is a shim over the various qt bindings. It is used to write
qt bindings indenpendent library or application.

The shim will automatically select the first available API (PyQt5, qtpy and
finally PySide).

You can force the use of one specific bindings (e.g. if your application is
using one specific bindings and you need to use library that use qtpy) by
setting up the ``QT_API`` environment variable.

PyQt5
+++++

For pyqt5, you don't have to set anything as it will be used automatically::

    >>> from qtpy import QtWidgets, QtGui, QtCore
    >>> print(QtWidgets.QWidget)


qtpy
+++++

Set the ``QT_API`` environment variable to 'qtpy' (case insensitive) before
importing any python package::

    >>> import os
    >>> os.environ['QT_API'] = 'qtpy'
    >>> from qtpy import QtWidgets, QtGui, QtCore
    >>> print(QtWidgets.QWidget)


.. warning:: This requires to set the SIP api to version 2 (for strings and
    covariants). If you're using python2 you have to make sure the correct sip
    api is set before importing any qtpy module (qtpy can take care of
    that for you but it must be imported before any qtpy module).


PySide
++++++

Set the QT_API environment variable to 'PySide' (case insensitive) before
importing pyqode::

    >>> import os
    >>> os.environ['QT_API'] = 'PySide'
    >>> from qtpy import QtWidgets, QtGui, QtCore
    >>> print(QtWidgets.QWidget)

"""
import os
import sys
import logging

__version__ = '2.9.dev'


#: Qt API environment variable name
QT_API = 'QT_API'
#: names of the expected PyQt5 api
PYQT5_API = ['pyqt5']
#: names of the expected qtpy api
PYQT4_API = [
    'pyqt',  # name used in IPython.qt
    'qtpy'  # qtpy original name
]
#: names of the expected PySide api
PYSIDE_API = ['pyside']


class PythonQtError(Exception):

    """
    Error raise if no bindings could be selected
    """
    pass


def setup_apiv2():
    """
    Setup apiv2 when using qtpy and Python2.
    """
    # setup PyQt api to version 2
    if sys.version_info[0] == 2:
        logging.getLogger(__name__).debug(
            'setting up SIP API to version 2')
        import sip
        try:
            sip.setapi("QString", 2)
            sip.setapi("QVariant", 2)
        except ValueError:
            logging.getLogger(__name__).critical(
                "failed to set up sip api to version 2 for qtpy")
            raise ImportError('qtpy')


def autodetect():
    """
    Auto-detects and use the first available QT_API by importing them in the
    following order:

    1) PyQt5
    2) qtpy
    3) PySide
    """
    logging.getLogger(__name__).debug('auto-detecting QT_API')
    try:
        logging.getLogger(__name__).debug('trying PyQt5')
        import PyQt5
        os.environ[QT_API] = PYQT5_API[0]
        logging.getLogger(__name__).debug('imported PyQt5')
    except ImportError:
        try:
            logging.getLogger(__name__).debug('trying qtpy')
            setup_apiv2()
            import qtpy
            os.environ[QT_API] = PYQT4_API[0]
            logging.getLogger(__name__).debug('imported qtpy')
        except ImportError:
            try:
                logging.getLogger(__name__).debug('trying PySide')
                import PySide
                os.environ[QT_API] = PYSIDE_API[0]
                logging.getLogger(__name__).debug('imported PySide')
            except ImportError:
                raise PythonQtError('No Qt bindings could be found')


if QT_API in os.environ:
    # check if the selected QT_API is available
    try:
        if os.environ[QT_API].lower() in PYQT5_API:
            logging.getLogger(__name__).debug('importing PyQt5')
            import PyQt5
            os.environ[QT_API] = PYQT5_API[0]
            logging.getLogger(__name__).debug('imported PyQt5')
        elif os.environ[QT_API].lower() in PYQT4_API:
            logging.getLogger(__name__).debug('importing qtpy')
            setup_apiv2()
            import qtpy
            os.environ[QT_API] = PYQT4_API[0]
            logging.getLogger(__name__).debug('imported qtpy')
        elif os.environ[QT_API].lower() in PYSIDE_API:
            logging.getLogger(__name__).debug('importing PySide')
            import PySide
            os.environ[QT_API] = PYSIDE_API[0]
            logging.getLogger(__name__).debug('imported PySide')
    except ImportError:
        logging.getLogger(__name__).warning(
            'failed to import the selected QT_API: %s',
            os.environ[QT_API])
        # use the auto-detected API if possible
        autodetect()
else:
    # user did not select a qt api, let's perform auto-detection
    autodetect()


logging.getLogger(__name__).info('using %s' % os.environ[QT_API])
