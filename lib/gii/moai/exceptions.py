class MOAIException(Exception):
	def __init__(self, code):
		self.args=(code,)
		self.code=code
