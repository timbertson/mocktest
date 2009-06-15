from base import Matcher
__all__ = [
	'object_containing',
	'any_of'
	]

class IncludeMatcher(Matcher):
	def __init__(self, item):
		self.item = item
	
	def matches(self, other):
		print other
		return self.item in other
	
	def desc(self):
		return "A collection containing %s" % (self.item,)

class ItemMatcher(Matcher):
	def __init__(self, collection):
		self.collection = collection
	
	def matches(self, other):
		return other in self.collection
	
	def desc(self):
		return "An item from the collection: %s" % (self.item,)

object_containing = IncludeMatcher
any_of = ItemMatcher
