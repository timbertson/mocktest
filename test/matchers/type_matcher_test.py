from mocktest import TestCase

from mocktest.matchers import *

class TypeMatcherTest(TestCase):
	def test_should_match_strings(self):
		self.assertTrue(any_string.matches('fdfds'))
		self.assertFalse(any_string.matches(1234))
	
	def test_should_match_ints(self):
		self.assertTrue(any_int.matches(1234))
		self.assertFalse(any_int.matches('fdsfsd'))
	
	def test_should_match_floats(self):
		self.assertTrue(any_float.matches(123.0))
		self.assertFalse(any_float.matches(123))
	
	def test_should_match_instances_of_arbitrary_classes(self):
		class Super(object):
			pass
		class Sub(Super):
			pass
		self.assertTrue(any_(Super).matches(Sub()))
		self.assertFalse(any_(Super).matches(object()))
	
	def test_should_match_any_dict(self):
		self.assertTrue(any_dict.matches({}))
		self.assertFalse(any_dict.matches('fdsfsd'))
	
	def test_should_match_any_list(self):
		self.assertTrue(any_list.matches([1,2,3]))
		self.assertFalse(any_list.matches((1,2,3)))
	
	def test_should_match_instances_with_attributes(self):
		class ClassWith_foo(object):
			def foo(self):
				pass
		self.assertTrue(object_with('foo').matches(ClassWith_foo()))
		self.assertFalse(object_with('not_foo').matches(ClassWith_foo()))
	
	
	
