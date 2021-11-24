import shutil
import re
import os
import os.path
import sys

def updateFile( src, dst, ignore = None, **option ):
	if not os.path.exists( dst ):
		if os.path.isdir( src ):
			shutil.copytree( src, dst )
		else:
			shutil.copy( src, dst )
		return
	##
	if os.path.isdir( dst ):
		for f in os.listdir( src ):			
			updateFile( src + '/' + f, dst + '/' + f, ignore, **option )
	else:
		if os.path.getmtime( src ) > os.path.getmtime( dst ):
			shutil.copy( src, dst )


# class SyncPackage(object):
# 	pass

# class SyncPackageFileSystem(object):
# 	def getMTime( self, path ):
# 		pass

# 	def getType( self, path ):
# 		pass

# 	def copy( self, path ):
# 		pass

# 	def mkdir( self, path ):
# 		