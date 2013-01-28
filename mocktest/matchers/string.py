from __future__ import absolute_import
"""
String Matchers
---------------

.. function:: string_matching(pattern)

	Takes either a string or a compiled regex pattern.

.. function:: string_containing(substring)

	Matches any string containing the given substring
"""

__all__ = [
	'string_matching',
	'string_containing',
]
import re
from .base import Matcher

class StringRegexMatcher(Matcher):
	def __init__(self, regex):
		self.desc_str = regex
		if isinstance(regex, str):
			regex = re.compile(regex)
		self.regex = regex
	
	def matches(self, other):
		return bool(self.regex.match(other))
	
	def desc(self):
		return "a string matching: %s" % (self.desc_str,)

class SubstringMatcher(Matcher):
	def __init__(self, regex):
		self.expected = regex
	
	def matches(self, other):
		return isinstance(other, str) and self.expected in other
	
	def desc(self):
		return "a string containing: %s" % (self.expected,)

string_matching = StringRegexMatcher
string_containing = SubstringMatcher

