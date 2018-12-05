from __future__ import absolute_import
"""
Basic Matchers
^^^^^^^^^^^^^^

.. data:: Any

	A matcher instance that matches any object.
	If called with a type, e.g.:
		>>> Any(int)

	It returns a matcher for any instance of that type.

.. data:: any_

	Alias for :data:`Any`


.. function:: Not(matcher)

	Call with a matcher to return a matcher inverting the logic of tha passed-in matcher.
	e.g.:
		>>> Not(Any(str))

	Would match anything that isn't a string instance.

.. data:: _not

	Alias for :data:`Not`
"""

__all__ = ['Matcher', 'Any', 'any_', 'Not', 'not_', 'SplatMatcher', 'KwargsMatcher', 'matcher']

class Matcher(object):
	"""
	Base matcher class
	"""
	_desc = 'unnamed matcher'

	def desc(self):
		"""return a description of this matcher"""
		return self._desc

	def __str__(self):
		return "Matcher for \"%s\"" % (self.desc(),)

	def __repr__(self):
		return self.desc()

	def __iter__(self):
		matcher_list = (ElementWiseSplatMatcher(self),)
		return iter(matcher_list)

	def matches(self, obj):
		"""return True if this matcher is satisfied by the given object, else False"""
		raise AssertionError("matcher has not overidden `matches`!")

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
	"""
	Create a matcher

	:param matches: given one argument (the subject), this function should return either True or False
	:type matches: callable
	:param desc: Human readable desription of this matcher's logic, e.g "a positive number"
	"""
	return type('Matcher', (Matcher,), {'matches':matches, 'desc': lambda self: desc})()


class SplatMatcherMaker(Matcher):
	def __init__(self, matcher):
		self._matcher = matcher
	
	def __iter__(self):
		return iter((SplatMatcher(self._matcher),))

	def matches(self, *a):
		raise RuntimeError("SplatMatcher instance used without prefixing with '*'")
	desc = matches

class SplatMatcher(Matcher):
	def __init__(self, matcher):
		self._matcher = matcher
	
	def matches(self, args, kwargs):
		return self._matcher.matches(args)

	def desc(self):
		return "args like [%r]" % (self._matcher.desc(),)

class ElementWiseSplatMatcher(SplatMatcher):
	def matches(self, args, kwargs):
		return all(map(self._matcher.matches, args))

	def desc(self):
		return "each argument is [%r]" % (self._matcher.desc(),)

class KwargsMatcher(Matcher):
	def __init__(self, matcher):
		super(KwargsMatcher, self).__init__()
		self._matcher = matcher
		self._dict = {'__kwargs': matcher}

	def matches(self, *a):
		raise RuntimeError("KwargsMatcher instance used without prefixing with '**'")

	desc = matches

	# implements kwargs-splat (**Any)
	def keys(self):
		return {'__kwargs': self}.keys()
	def __getitem__(self, key):
		return self._dict[key]

	# fallback to dict
	def __getattr__(self, key):
		return getattr(self._dict, key)


class AnyObject(KwargsMatcher):
	"""Matches any object.
	If called and given a type, returns a :py:class:mocktest.matchers.type_matcher.TypeMatcher: instance for that type
	"""
	def __init__(self):
		super(AnyObject, self).__init__(self)

	# implements splat (*Any)
	def __iter__(self):
		return iter([SplatMatcher(self)])

	def __call__(self, cls=None):
		if cls is None:
			return self
		from .type_matcher import TypeMatcher
		return TypeMatcher(cls)

	def matches(self, other):
		return True

	def desc(self):
		return "any object"

Not = NegatedMatcher
not_ = NegatedMatcher

Any = AnyObject()
any_ = Any

