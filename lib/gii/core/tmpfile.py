import shutil
import tempfile

class TempDir(object):
	"""docstring for TempDir"""
	def __init__(self, **kwarg):
		self._dir=tempfile.mkdtemp(**kwarg)
	
	def __del__(self):
		shutil.rmtree(self._dir)

	def __call__(self, name):
		return self._dir+'/'+name

	def __str__(self):
		return self._dir

