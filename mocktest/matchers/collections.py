from base import Matcher, KwargsMatcher, SplatMatcherMaker
__all__ = [
	'object_containing',
	'dict_containing',
	'kwargs_containing',
	'args_containing',
	'any_of',
	]

class IncludeMatcher(Matcher):
	def __init__(self, *items):
		self.items = items
	
	def matches(self, other):
		print '--'
		print other
		print repr(self.items)
		return all([item in other for item in self.items])
	
	def desc(self):
		return "object containing %r" % (self.items,)

class DictIncludeMatcher(Matcher):
	def __init__(self, **kw):
		self._kw = kw
	
	def matches(self, other):
		try:
			for k, v in self._kw.items():
				val = other[k]
				if isinstance(v, Matcher):
					matches = v.matches(val)
				else:
					matches = v == val
				if not matches:
					return False
		except KeyError:
			return False
		return True
	
	def desc(self):
		return "dict includes %r" % (self._kw,)

class ItemMatcher(Matcher):
	def __init__(self, collection):
		self.collection = collection
	
	def matches(self, other):
		return other in self.collection
	
	def desc(self):
		return "An item from the collection: %r" % (self.collection,)

object_containing = IncludeMatcher
dict_containing = DictIncludeMatcher

kwargs_containing = lambda **k: KwargsMatcher(dict_containing(**k))
args_containing = lambda *a: SplatMatcherMaker(object_containing(*a))

any_of = ItemMatcher
