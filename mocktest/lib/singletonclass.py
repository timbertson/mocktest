__all__ = [
	'ensure_singleton_class',
	'revert_singleton_class',
	'SingletonClass',
]

ORIGINAL_CLASSES = {}
CLASS = object()
BASES = object()

def _root(instance):
	if isinstance(instance, type):
		return type
	return object

def ensure_singleton_class(self):
	global ORIGINAL_CLASSES
	root = _root(self)
	if self not in ORIGINAL_CLASSES:
		# make a new class that inherits from my current class, with the same name
		new_class = type(type(self).__name__, (type(self),), {})
		to_save = type(self)
		try:
			root.__setattr__(self, '__class__', new_class) # bypass any __setattr__ interception
		except TypeError:
			raise TypeError("Can't alter class of '%s'" % (type(self).__name__))
		ORIGINAL_CLASSES[self] = to_save # do this last; as a TypeError might have been thrown already

def revert_singleton_class(self):
	global ORIGINAL_CLASSES
	try:
		_root(self).__setattr__(self, '__class__', ORIGINAL_CLASSES[self])
		del ORIGINAL_CLASSES[self]
	except (KeyError, TypeError):
		pass


#handy mixin class
class SingletonClass(object):
	def _ensure_singleton_class(self):
		ensure_singleton_class(self)
	
	def _revert_singleton_class(self):
		revert_singleton_class(self)
	
