# -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod

import colorama
from colorama import Fore, Back, Style

import logging
import string
import json
import os
import os.path
import sys
import imp

from . import signals
from . import globalSignals
from . import JSONHelper

from .project import Project

from .MainModulePath import getMainModulePath

##----------------------------------------------------------------##
def _getModulePath( path ):
	import os.path
	return os.path.dirname( __file__ ) + '/' + path


##----------------------------------------------------------------##
class ToolBase(object):
	@abstractmethod
	def getName( self ):
		return 'APP'

	@abstractmethod
	def getVersion( self ):
		return '0.1'

	def setupCLI( self, parser ):
		pass

	def start( self, argv ):
		pass
	
##----------------------------------------------------------------##
#STUB

_DEFAULT_TOOL_PATH = 'tools'
_INFO_FILE_NAME    = '__gii__.json'
_TOOLS = []

_libTools = []
_prjTools = []

def loadToolSetting( path ):
	infoFilePath = path + '/' + _INFO_FILE_NAME
	if not os.path.exists( infoFilePath ): return False
	logging.debug( 'try loading tool: %s ' % path )
	try:
		data = json.load( open( infoFilePath, mode = 'r', encoding = 'utf-8' ) )
		if not data.get( 'active', True ): return False
		data[ 'module_path' ] = path
	except Exception as e:
		return False
	return data	

def scanToolsInPath( path ):
	toolList = []
	path = os.path.abspath( path )
	for currentDir, dirs, files in os.walk( str(path) ):
		for dirname in dirs:
			fullpath = currentDir + '/' + dirname
			data = loadToolSetting( fullpath )
			if data: toolList.append( data )
	return toolList

def scanTools( path ):
	global _libTools, _prjTools
	mainPath  = getMainModulePath()
	_libTools = scanToolsInPath( mainPath + '/' + _DEFAULT_TOOL_PATH )
	if path:
		_prjTools = scanToolsInPath( path + '/' + _DEFAULT_TOOL_PATH )
	return ( _libTools, _prjTools )

def startTool( toolInfo ):
	path = toolInfo[ 'module_path' ]
	toolModuleName = 'gii_tool_' + toolInfo['name']
	logging.info( 'start tool: %s <%s>' % ( toolInfo['name'], path ) )
	sys.path.insert( 0, path )
	m = imp.load_source( toolModuleName, path + '/__init__.py' )
	if hasattr( m, 'main' ):
		m.main( sys.argv[ 1: ] )

##----------------------------------------------------------------##
def printGII():
	output = Fore.YELLOW + Style.BRIGHT +"""
 &b--&y     ,_______    &b------------------------------------------------------ 
   &y    /        \\  &r     _______  ___   ___                               
   &y   /        |  > &r   |       ||   | |   |                              
   &y   |          ;  &r   |    ___||   | |   |                                
   &y  /           |  &r   |   | __ |   | |   |                                
   &y / <_         |  &r   |   ||  ||   | |   |                                
   &y/             |  &r   |   |_| ||   | |   |                               
   &y\\,,,,,,,,,,,,/  &r    |_______||___| |___|   &wGII development environment 
 &b--&y      |   |      &b------------------------------------------------------
 """

	output = output.replace( '&y', Fore.YELLOW + Style.BRIGHT )
	output = output.replace( '&r', Fore.BLUE + Style.NORMAL )
	output = output.replace( '&w', Fore.BLUE + Style.NORMAL )
	output = output.replace( '&b', Fore.BLUE + Style.NORMAL )
	print(output)
	print((Style.RESET_ALL + ''))


def printHeader():
	printGII()

def printProjectInfo( path, info ):
	if not info: return
	print(('  current project: ' + ( Fore.CYAN + path + Fore.RESET )))
	print('')
	print(('    - NAME   : \t%s' % ( Fore.CYAN + info.get('name', 'N/A') + Fore.RESET )))
	print(('    - AUTHOR : \t%s' % ( Fore.CYAN + info.get('author', 'N/A') + Fore.RESET )))
	print(('    - VERSION: \t%s' % ( Fore.CYAN + str( info.get('version', 'N/A') ) + Fore.RESET )))
	print('')

def printToolInfo( info ):
	output = '    %s \t %s' % ( Fore.RED + info.get('name', '???') + Fore.RESET, info.get('help','') )
	output = output.expandtabs( 16 )
	print(output)

def printAvailTools():	
	print((Fore.GREEN+'  available tool(s):'))
	print((Style.DIM+''))
	print((Fore.WHITE + '    + BUILTIN TOOLS'))
	print((Style.RESET_ALL + ''))
	for info in _libTools:
		printToolInfo( info )	
	if _prjTools:
		print((Style.DIM + ''))
		print('    + PROJECT TOOLS')
		print((Style.RESET_ALL + ''))
		for info in _prjTools:
			printToolInfo( info )	
	print('')

def printUsage():
	print('Usage:  gii <tool-name> ...')
	print('')
	printAvailTools()

def printMissingCommand( cmd ):
	printAvailTools( )
	print(('  [ERROR] TOOL NOT FOUND: ' + cmd))
	print('')
	
##----------------------------------------------------------------##
def startupTool():	
	colorama.init()

	projectPath, projectInfo = Project.findProject()
	scanTools( projectPath )
	argv = sys.argv
	if len( argv ) < 2:
		printHeader()
		printUsage()
		printProjectInfo(  projectPath, projectInfo )
		return False
	cmd = argv[1]
	for toolInfo in _prjTools + _libTools:
		if toolInfo.get('name') == cmd:
			return startTool( toolInfo )
	#show help
	printHeader()
	printProjectInfo(  projectPath, projectInfo )
	printMissingCommand( cmd )

