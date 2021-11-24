import logging
##----------------------------------------------------------------##
#CONFIG
LOG_LEVEL = logging.WARNING
# LOG_LEVEL = logging.INFO
# LOG_LEVEL = logging.DEBUG

##----------------------------------------------------------------##
##APPLY CONFIG
logging.addLevelName( logging.INFO, 'STATUS' )

logging.basicConfig(
	format = '[%(levelname)s : %(created)f]\t%(message)s',
	level  = LOG_LEVEL
	)
