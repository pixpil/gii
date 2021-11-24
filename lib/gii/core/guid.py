import uuid

def generateGUID():
	# return str( uuid.uuid1() )
	return uuid.uuid1().hex
