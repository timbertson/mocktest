from __future__ import absolute_import
"""
Type matchers
-------------
.. data:: any_string
.. data:: any_int
.. data:: any_float
.. data:: any_dict
.. data:: any_list

.. function:: object_with(attribute_name)

	Match an object that has an attribute named `attribute_name`.

"""
__all__ = [
	'any_string',
	'any_int',
	'any_float',
	'any_dict',
	'any_list',
	'object_with'
]

from .base import Matcher

class TypeMatcher(Matcher):
	def __init__(self, cls):
		self.cls = cls
	
	def matches(self, other):
		return isinstance(other, self.cls)
	
	def desc(self):
		return "any instance of %s" % (self.cls.__name__,)

class ObjectWithAttribute(Matcher):
	def __init__(self, attr_name):
		self.attr_name = attr_name
	
	def matches(self, other):
		return hasattr(other, self.attr_name)
	
	def desc(self):
		return "any object with attribute \"%s\"" % (self.attr_name,)

any_string = TypeMatcher(str)
any_int = TypeMatcher(int)
any_float = TypeMatcher(float)
any_dict = TypeMatcher(dict)
any_list = TypeMatcher(list)

object_with = ObjectWithAttribute


