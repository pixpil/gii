from . import DeviceManager
from . import DeviceBrowser

import sys

if sys.platform == 'darwin':
	from . import IOSDevice