__all__ = [
	'ensure_singleton_class',
]

ORIGINAL_CLASSES = {}
CLASS = object()
BASES = object()

from ..mockerror import MockError
from ..transaction import MockTransaction

def _root(instance):
	if isinstance(instance, type):
		return type
	return object

class Singleton(object): pass

def ensure_singleton_class(self):
	if isinstance(self, Singleton):
		return
	root = _root(self)
	original_class = type(self)
	new_class = type(original_class.__name__, (original_class, Singleton), {})
	try:
		root.__setattr__(self, '__class__', new_class) # bypass any __setattr__ interception
	except TypeError:
		raise MockError("Can't alter class of '%s'" % (type(self).__name__))
	MockTransaction.add_teardown(lambda: revert_singleton_class(self, original_class))

def revert_singleton_class(self, original_class):
	_root(self).__setattr__(self, '__class__', original_class)

#handy mixin class
class SingletonClass(object):
	def _ensure_singleton_class(self):
		ensure_singleton_class(self)
	
	def _revert_singleton_class(self):
		revert_singleton_class(self)
	
