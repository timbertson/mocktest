class RealSetter(object):
	def _real_set(self, **kwargs):
		for k,v in kwargs.items():
			object.__setattr__(self, k, v)
	
	def _real_get(self, attr):
		return object.__getattribute__(self, attr)
