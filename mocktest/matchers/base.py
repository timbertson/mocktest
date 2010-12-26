__all__ = ['Matcher', 'Any', 'Not']

class Matcher(object):
	_desc = 'unnamed matcher'

	def desc(self):
		return self._desc

	def __str__(self):
		return "Matcher for \"%s\"" % (self.desc(),)

	def __repr__(self):
		return "<#Matcher: %s>" % (self.desc(),)

class NegatedMatcher(Matcher):
	def __init__(self, orig):
		if not isinstance(orig, Matcher):
			raise TypeError("expected a Matcher, got %s" % (type(orig).__name__,))
		self.orig = orig
		
	def matches(self, other):
		return not self.orig.matches(other)

	def desc(self):
		return 'not %s' % (self.orig.desc(),)

def matcher(matches, desc = 'anonymous matcher'):
	return type('Matcher', (Matcher,), {'matches':matches, 'desc': lambda self: desc})()

class Any(Matcher):
	def __init__(self, cls=None):
		self._cls = cls

	def matches(self, other):
		if self._cls is not None:
			return isinstance(other, self._cls)
		return True

	def desc(self):
		if self._cls is None:
			return "any object"
		return "any instance of %r" % (self._cls,)

Not = NegatedMatcher

