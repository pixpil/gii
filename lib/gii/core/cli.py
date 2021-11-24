import abc
import argparse
import sys
import logging

##----------------------------------------------------------------##
class CLICommand(object, metaclass=abc.ABCMeta):	
	commands = []

	@abc.abstractmethod
	def getName( self ):
		return 'clicommand'
		
	@abc.abstractmethod
	def getHelp( self ):
		return 'cli help string'

	def __init__( self ):
		CLICommand.commands.append( self )

	def setupParser( self, parser ):
		pass

	def start( self, **kwargs ):
		pass

##----------------------------------------------------------------##
def buildCLIParser():
	parserTop = argparse.ArgumentParser(
		description = 'GII game development environment'
	)

	parserCommands = parserTop.add_subparsers(
		help = 'commands'
	)

	for cmd in CLICommand.commands:
		parser = parserCommands.add_parser( cmd.getName(), help = cmd.getHelp() )
		parser.set_defaults( cmd = cmd )
		cmd.setupParser( parser )

	return parserTop

##----------------------------------------------------------------##
def parseCLI( argv = None ):	
	args = argv or sys.argv
	opt = buildCLIParser().parse_args( args[1:] )
	cmd = opt.cmd
	if cmd:
		optdict = vars( opt )
		logging.info( 'cli cmd: <%s>' % cmd.getName() )
		cmd.start( **optdict )

