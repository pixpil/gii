from gii.core import app
from .MOAIRuntime import _G, _GII

import os.path
import subprocess
import shutil

##----------------------------------------------------------------##
def _getLuajitBinPath():
	platformName = app.getPlatformName()
	if platformName == 'osx':
		return app.getNativeSupportPath( 'luajit/luajit' )
	elif platformName == 'windows':
		return app.getNativeSupportPath( 'luajit/luajit.exe' )
	else:
		return 'luajit'


##----------------------------------------------------------------##
def _getLuacBinPath():
	platformName = app.getPlatformName()
	if platformName == 'osx':
		return app.getNativeSupportPath( 'lua/luac' )
	elif platformName == 'windows':
		return app.getNativeSupportPath( 'lua/luac.exe' )
	else:
		return 'luac'

##----------------------------------------------------------------##
def _isFileNewer( f1, f2 ):
	if os.path.exists( f1 ) and os.path.exists( f2 ):
		t1 = os.path.getmtime( f1 )
		t2 = os.path.getmtime( f2 )
		return t1 > t2
	else:
		return None


##----------------------------------------------------------------##
def compileLua( srcPath, dstPath, version = 'source', checktime = False ):
	if version == 'lua':
		return compilePlainLua( srcPath, dstPath, checktime = checktime, strip = False )
	elif version == 'lua_strip':
		return compilePlainLua( srcPath, dstPath, checktime = checktime, strip = True )
	elif version == 'luajit':
		return compileLuaJIT( srcPath, dstPath, checktime = checktime, strip = False )
	elif version == 'luajit_strip':
		return compileLuaJIT( srcPath, dstPath, checktime = checktime, strip = True )
	elif version == 'source':
		if srcPath != dstPath:
			shutil.copy( srcPath, dstPath )
	else:
		raise Exception( 'no lua version specified' )

##----------------------------------------------------------------##
def compilePlainLua( srcPath, dstPath, checktime = False, strip = False ):
	if checktime:
		if _isFileNewer( dstPath, srcPath ): return #copmiled file is newer? skip
		
	# 'luajit -b -g $in $out'
	arglist =  [ _getLuacBinPath() ]

	if strip:
		arglist += [ '-s' ]
		
	arglist += [ '-o', dstPath ]
	arglist += [ srcPath ]

	try:
		code = subprocess.call( arglist, cwd = os.path.dirname( _getLuacBinPath()  ) )
	except Exception as e:
		raise Exception( 'error on lua compliation: %s ' % e )

##----------------------------------------------------------------##
def compileLuaJIT( srcPath, dstPath, checktime = False, strip = False ):
	if checktime:
		if _isFileNewer( dstPath, srcPath ): return #copmiled file is newer? skip

	# 'luajit -b -g $in $out'
	arglist =  [ _getLuajitBinPath() ]
	arglist += [ '-b' ]

	if not strip:
		arglist += [ '-g' ]
		
	arglist += [ srcPath, dstPath ]
	try:
		code = subprocess.call( arglist, cwd = os.path.dirname( _getLuajitBinPath()  ) )
	except Exception as e:
		raise Exception( 'error on luajit compliation: %s ' % e )
