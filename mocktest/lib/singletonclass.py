def _root(instance):
	if isinstance(instance, type):
		return type
	return object

def ensure_singleton_class(self):
	root = _root(self)
	try:
		root.__getattr__(self, '_singleton_class_original_bases')
	except AttributeError:
		self._singleton_class_original_bases = type(self).__bases__
		# make a new class that inherits from my current class, with the same name
		new_class = type(type(self).__name__, (type(self),), {})
		root.__setattr__(self, '__class__', new_class)

def revert_singleton_class(self):
	try:
		_root(self).__getattr__(self, '_singleton_class_original_bases')
	except:
		return
	type(self).__bases__ = self._singleton_class_original_bases


#handy mixin class
class SingletonClass(object):
	def _ensure_singleton_class(self):
		ensure_singleton_class(self)
	
	def _revert_singleton_class(self):
		revert_singleton_class(self)
	
