from unittest import TestCase

from mocktest.matchers import *

class BaseTest(TestCase):
	def test_should_have_str_and_repr(self):
		class MatcherSubclass(Matcher):
			def desc(self):
				return 'foo'
		
		self.assertEqual(str(MatcherSubclass()), 'Matcher for "foo"')
		self.assertEqual(repr(MatcherSubclass()), 'foo')
	
	def test_anything_matcher_should_match_anything(self):
		self.assertTrue(Any.matches(object()))
		self.assertEqual(Any.desc(), 'any object')
	
	def test_not__matcher_should_invert_matches_and_descriptions(self):
		self.assertFalse(Not(Any).matches(object()))
		self.assertEqual(Not(Any).desc(), 'not any object')
	
	def test_splat_matcher_should_have_a_meaningful_description(self):
		self.assertEquals(repr(*any_args), "args like [\'any object\']")
