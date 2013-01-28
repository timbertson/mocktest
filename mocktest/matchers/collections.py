from __future__ import absolute_import

"""
Collection Matchers
-------------------

.. function:: any_of(*elements)

	Matches an argument if it is any of the listed elements

.. function:: object_containing(*elements)

	Matches an object that includes all given elements.

.. data:: any_args

	like `any`, but used for a series of arguments - e.g.
		foo(*any_args)

.. data:: any_kwargs

	like `any`, but used for a dict of keyword arguments - e.g.
		foo(**any_kwargs)
		
.. function:: args_containing(*args)

	Just like :func:`object_containing`, but used for matching args. E.g:
		>>> expect(obj).meth(*args_containing(2, 3))

.. function:: dict_containing(**kwargs)

	Matches a mapping with at least the given keys and values.

.. function:: kwargs_containing(**kwargs)

	Just like :func:`dict_containing`, but used for matching kwargs. E.g:
		>>> expect(obj).meth(1, 2, 3, **kwargs_containing(do_frob=True))


"""
from .base import Matcher, KwargsMatcher, SplatMatcherMaker, Any
__all__ = [
	'object_containing',
	'dict_containing',
	'kwargs_containing',
	'args_containing',
	'any_kwargs',
	'any_args',
	'any_of',
	]

class IncludeMatcher(Matcher):
	def __init__(self, *items):
		self.items = items
	
	def matches(self, other):
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
		return "an item from the collection: %r" % (self.collection,)

object_containing = IncludeMatcher
dict_containing = DictIncludeMatcher

kwargs_containing = lambda **k: KwargsMatcher(dict_containing(**k))
args_containing = lambda *a: SplatMatcherMaker(object_containing(*a))
any_args = SplatMatcherMaker(Any)
any_kwargs = KwargsMatcher(Any)

any_of = ItemMatcher
