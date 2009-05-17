from .. import helper
from unittest import TestCase

from mocktest.matchers import *

class BaseTest(TestCase):
	def test_should_have_str_and_repr(self):
		class MatcherSubclass(Matcher):
			def desc(self):
				return 'foo'
		
		self.assertEqual(str(MatcherSubclass()), 'Matcher for "foo"')
		self.assertEqual(repr(MatcherSubclass()), '<#Matcher: foo>')
	
	def test_anything_matcher_should_match_anything(self):
		self.assertTrue(anything.matches(object()))
		self.assertEqual(anything.desc(), 'any object')
	
	def test_not__matcher_should_invert_matches_and_descriptions(self):
		self.assertFalse(not_(anything).matches(object()))
		self.assertEqual(not_(anything).desc(), 'not any object')
		

