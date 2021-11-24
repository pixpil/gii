import xxhash
from PIL import Image

def affirmImgHash( img ):
	if hasattr( img, '__unique_hash__' ): return img.__unique_hash__
	testimg = img
	hvalue = xxhash.xxh64( testimg.tobytes() ).hexdigest()
	img.__unique_hash__ = hvalue
	return hvalue
##----------------------------------------------------------------##
class UniqueImageSet(object):
	"""docstring for UniqueImageSet"""
	def __init__(self):
		self.hashToImages = {}
	
	def affirm( self, src ):
		hvalue = affirmImgHash( src )
		unique = self.hashToImages.get( hvalue, None )
		if not unique:
			unique = src
			self.hashToImages[ hvalue ] = unique
		return unique

#TODO: iteration?
class UniqueImageMap(object):
	def __init__(self):
		self.hashToValues = {}

	def affirm( self, imgKey, newValue ):
		hvalue = affirmImgHash( imgKey )
		target = self.hashToValues.get( hvalue, None )
		if not target:
			target = src
			self.hashToImages[ hvalue ] = target
		return target