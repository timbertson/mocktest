from .. import helper
from mocktest import TestCase

from mocktest.matchers import *
import re

class Collection(object):
	def __init__(self, col):
		self.col = col

	def __contains__(self, item):
		return item in self.col

class CollectionsTest(TestCase):
	def test_should_match_items_in_a_collection(self):
		self.assertTrue(object_containing('f').matches(Collection(['a','b','f'])))
		self.assertFalse(object_containing('f').matches(Collection([])))

	def test_should_match_a_collection_containing_the_desired_item(self):
		self.assertTrue(any_of(Collection([1,2,3])).matches(3))
		self.assertFalse(any_of(Collection([1,2,3])).matches(4))


