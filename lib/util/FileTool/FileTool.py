# -*- coding: utf-8 -*-
import pathtools.path

import os
import os.path
import logging
import shutil

import hashlib
import xxhash

##----------------------------------------------------------------##
def _copyFile( src, dst, **option ):
	ignore_file = option.get( 'ignore_file', None )
	if os.path.isdir( src ): #dir
		if not os.path.exists( dst ): os.mkdir( dst )
		if os.path.isdir( dst ):
			for f in os.listdir( src ):
				if ignore_file and ignore_file( f ): continue
				_copyFile( src + '/' + f, dst + '/' + f, **option )
	else: #file
		if not os.path.exists( dst )\
			or ( os.path.getmtime( src ) > os.path.getmtime( dst ) ):
				try:
					shutil.copy( src, dst )
				except Exception as e:
					logging.warn( e )
					logging.warn( 'failed copy file:{0}->{1}'.format( src, dst ) )
					return False
	return True

##----------------------------------------------------------------##
def syncFile( src, dst, **option ):
	return _copyFile( src, dst, **option )

##----------------------------------------------------------------##
def hash_value(filename, filesize, maxsize, xhash):
		with open(filename, 'rb') as openfile: # 打开文件，一定要是以二进制打开
				while True: 
						data = openfile.read(maxsize) # 读取文件块
						if not data: # 直到读完文件
								break
						xhash.update(data)
		return xhash.hexdigest()

##----------------------------------------------------------------##
def hash_directory( dirpath, blockSize, xhash ):
	files = sorted( list( pathtools.path.list_files( dirpath ) ) )
	for filepath in files:
		relativeName = os.path.relpath( filepath, dirpath )
		xhash.update( bytes( relativeName, 'utf-8'))
		with open(filepath, 'rb') as openfile: # 打开文件，一定要是以二进制打开
			while True: 
				data = openfile.read( blockSize ) # 读取文件块
				if not data: break;
				xhash.update( data )
	return xhash.hexdigest()

def hash_directory_quick( dirpath, blockSize, xhash ):
	#TODO: collect file hashes with multithread, then hash the collected hash dataset
	files = sorted( list( pathtools.path.list_files( dirpath ) ) )
	for filepath in files:
		relativeName = os.path.relpath( filepath, dirpath )
		xhash.update( bytes( relativeName, 'utf-8'))
		with open(filepath, 'rb') as openfile: # 打开文件，一定要是以二进制打开
			while True: 
				data = openfile.read( blockSize ) # 读取文件块
				if not data: break;
				xhash.update( data )
	return xhash.hexdigest()


##----------------------------------------------------------------##
def calcFileMD5( path, blockSize = None ):
	if not blockSize:
		blockSize = 1024*1024
	size = os.path.getsize( path )
	return hash_value( path, size, blockSize, hashlib.md5() )

##----------------------------------------------------------------##
def calcFileSHA1( path, blockSize = None ):
	if not blockSize:
		blockSize = 1024*1024
	size = os.path.getsize( path )
	return hash_value( path, size, blockSize, hashlib.sha1() )

##----------------------------------------------------------------##
def calcFileXXH64( path, blockSize = None ):
	if not blockSize:
		blockSize = 1024*1024
	size = os.path.getsize( path )
	return hash_value( path, size, blockSize, xxhash.xxh64() )

##----------------------------------------------------------------##
def calcFileXXH32( path, blockSize = None ):
	if not blockSize:
		blockSize = 1024*1024
	size = os.path.getsize( path )
	return hash_value( path, size, blockSize, xxhash.xxh32() )


	
##----------------------------------------------------------------##
def calcDirectoryMD5( path, blockSize = None ):
	if not os.path.isdir( path ): return None
	if not blockSize:
		blockSize = 1024*1024*4
	size = os.path.getsize( path )
	return hash_directory( path, blockSize, hashlib.md5() )

##----------------------------------------------------------------##
def calcDirectorySHA1( path, blockSize = None ):
	if not os.path.isdir( path ): return None
	if not blockSize:
		blockSize = 1024*1024*4
	size = os.path.getsize( path )
	return hash_directory( path, blockSize, hashlib.sha1() )

##----------------------------------------------------------------##
def calcDirectoryXXH64( path, blockSize = None ):
	if not os.path.isdir( path ): return None
	if not blockSize:
		blockSize = 1024*1024*4
	size = os.path.getsize( path )
	return hash_directory( path, blockSize, xxhash.xxh64() )

##----------------------------------------------------------------##
def calcDirectoryXXH32( path, blockSize = None ):
	if not os.path.isdir( path ): return None
	if not blockSize:
		blockSize = 1024*1024*4
	size = os.path.getsize( path )
	return hash_directory( path, blockSize, xxhash.xxh32() )


##----------------------------------------------------------------##
if __name__ == '__main__':
	print( 'sha1:', calcFileSHA1( 'FileTool.py' ) )
	print( 'md5:', calcFileMD5( 'FileTool.py' ) )
	print( 'xxhash64:', calcFileXXH64( 'FileTool.py' ) )
	print( 'xxhash32:', calcFileXXH32( 'FileTool.py' ) )
	print( 'xxhash32 dir:', calcDirectoryXXH64( '..' ) )
