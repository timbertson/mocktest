__all__ = ['Matcher', 'Any', 'Not', 'SplatMatcher']

class Matcher(object):
	_desc = 'unnamed matcher'

	def desc(self):
		return self._desc

	def __str__(self):
		return "Matcher for \"%s\"" % (self.desc(),)

	def __repr__(self):
		return self.desc()

	def __iter__(self):
		matcher_list = (ElementWiseSplatMatcher(self),)
		return iter(matcher_list)

	def __getitem__(self, name):
		return None

	def items(self):
		return ('x',1)

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


class AnyInstanceOf(Matcher):
	def __init__(self, cls):
		self._cls = cls

	def desc(self):
		return "any instance of %r" % (self._cls,)

	def matches(self, other):
		print repr(other)
		return isinstance(other, self._cls)

class SplatMatcherMaker(Matcher):
	def __init__(self, matcher):
		self._matcher = matcher

	def matches(self, *a):
		raise RuntimeError("SplatMatcher instance used without prefixing with '*'")
	desc = matches

	def __iter__(self):
		return iter([SplatMatcher(self._matcher)])

class SplatMatcher(object):
	def __init__(self, matcher):
		self._matcher = matcher
	
	def matches(self, args, kwargs):
		print "splatter matching %r against %r" % (args,self._matcher)
		return self._matcher.matches(args)

	def desc(self):
		return "args where [%r]" % (self._matcher.desc(),)

class ElementWiseSplatMatcher(SplatMatcher):
	def matches(self, args, kwargs):
		print "splatter matching %r against %r" % (args,self._matcher)
		print repr(args)
		print repr(map(self._matcher.matches, args))
		return all(map(self._matcher.matches, args))

	def desc(self):
		return "each argument is [%r]" % (self._matcher.desc(),)

class AnyObject(Matcher, dict):
	def __init__(self):
		dict.__init__(self, __kwargs=self)

	def __call__(self, cls):
		return AnyInstanceOf(cls)

	def matches(self, other):
		return True

	def desc(self):
		return "any object"

class KwargsMatcher(Matcher, dict):
	def __init__(self, matcher):
		self._matcher = matcher
		dict.__init__(self, __kwargs=matcher)

	def matches(self, *a):
		raise RuntimeError("KwargsMatcher instance used without prefixing with '**'")
	desc = matches

kwargs_with = KwargsMatcher
args_with = SplatMatcherMaker

Not = NegatedMatcher

Any = AnyObject()
