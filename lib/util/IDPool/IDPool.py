class IDPool(object):
	def __init__(self):
		self.maxid=0
		self.pool=[]

	def request(self):
		if self.pool:
			id=self.pool[0]
			del self.pool[0]
			return id
		else:
			self.maxid+=1
			return self.maxid

	def drop(id):
		self.pool.append(id)
