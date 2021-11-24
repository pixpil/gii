import logging

# loggingLevel = logging.WARNING
# loggingLevel = logging.INFO
# loggingLevel = logging.DEBUG


##----------------------------------------------------------------##
from . import signals
from . import globalSignals
from .signals import slot

from .mime import *
##----------------------------------------------------------------##
from .guid           import *
from .helpers        import *
from .model          import *
from .res            import ResGuard
from .cli            import CLICommand, parseCLI
from .tool           import ToolBase, startupTool
from .project        import Project
from .deploy         import DeployConfig, DeployContext, registerDeployConfigClass
from .asset          import AssetLibrary, AssetException, AssetNode, AssetManager, AssetCreator
from .cache          import CacheManager
# from target         import Target, DeployManager

from .MainModulePath import getMainModulePath

##----------------------------------------------------------------##
from .Command        import EditorCommand, EditorCommandStack, EditorCommandRegistry
from .RemoteCommand  import RemoteCommand, RemoteCommandRegistry
from .RemoteControlSession import RemoteSessionItem
from .EditorTimer    import EditorTimer
from .EditorModule   import EditorModule
from .EditorApp      import app
from .URLHandler     import encodeGiiURL, processGiiURL
from .LuaHelper      import *

##----------------------------------------------------------------##
from . import CoreModule

##----------------------------------------------------------------##
from . import CommonAsset
from . import CommonRemoteCommand

def getProjectPath( path = None ):
	return Project.get().getBasePath( path )

def getAppPath( path = None ):
	return app.getPath( path )
