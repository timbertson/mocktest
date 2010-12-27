from mocktest import TestCase

from mocktest.matchers import *

class Collection(object):
	def __init__(self, col):
		self.col = col

	def __contains__(self, item):
		return item in self.col

class CollectionsTest(TestCase):
	def test_should_match_items_in_a_collection(self):
		self.assertTrue(object_containing('f').matches(Collection(['a','b','f'])))
		self.assertFalse(object_containing('f').matches(Collection([])))

	def test_should_match_multiple_items_in_a_collection(self):
		self.assertTrue(object_containing('f', 'g').matches(Collection(['a','g', 'b','f'])))
		self.assertFalse(object_containing('f', 'g').matches(Collection(['a','b','f'])))

	def test_should_match_a_collection_containing_the_desired_item(self):
		self.assertTrue(any_of(Collection([1,2,3])).matches(3))
		self.assertFalse(any_of(Collection([1,2,3])).matches(4))

	def test_should_match_a_dictionary_containing_the_given_items_at_minimum(self):
		self.assertTrue(dict_containing(x=1).matches({'x':1}))
		self.assertTrue(dict_containing(x=1).matches({'x':1, 'y':2}))
		self.assertFalse(dict_containing(x=1).matches({'x':2, 'y':2}))

	def test_should_match_a_dictionary_with_value_matchers(self):
		self.assertTrue(dict_containing(x=Any(int)).matches({'x':1}))
		self.assertTrue(dict_containing(x=Any(int)).matches({'x':3}))
		self.assertFalse(dict_containing(x=Any(int)).matches({'x':'three'}))
