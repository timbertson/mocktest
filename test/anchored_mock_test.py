import os
import sys

import helper
from mocktest import TestCase
from mocktest import mock_on, raw_mock, mock_wrapper
import mocktest

real_dict = {'a':'a', 'b':'b'}
class RealClass(object):
	a = 'a'
	def b(self):
		return 'b'

class NoDeletesDict(dict):
	def __delitem__(self, attr):
		raise StandardError

class NoDeletesObject(object):
	def __delattr__(self, attr):
		raise StandardError
		
real_object = RealClass()

class AnchoredMockTest(TestCase):
	def downup(self):
		mocktest._teardown()
		mocktest._setup()
		
	def test_should_attach_new_mocks_to_parent(self):
		mock_on(real_object).a
		mock_on(real_object).c = 'c'
		mock_on(real_dict)['a'] = 1
		mock_on(real_dict)['c']
		
		real_object.a()
		self.assertEqual(real_object.c(), 'c')
		self.assertEqual(real_dict['a'](), 1)
		self.assertEqual(real_dict['c'].__class__, raw_mock().__class__)
	
	def test_should_reinstate_original_objects_on_teardown(self):
		mock_on(real_object).a = 'mocky a'
		mock_on(real_dict)['a'] = 'mocky a'
		self.assertEqual(real_object.a(), 'mocky a')
		self.assertEqual(real_dict['a'](), 'mocky a')
		self.downup()
		self.assertEqual(real_object.a, 'a')
		self.assertEqual(real_dict['a'], 'a')
		
	def test_should_delete_original_objects_if_they_didnt_exist_before_the_mock(self):
		mock_on(real_object).c = 'mocky c'
		mock_on(real_dict)['c'] = 'mocky c'
		self.assertEqual(real_object.c(), 'mocky c')
		self.assertEqual(real_dict['c'](), 'mocky c')
		self.downup()
		self.assertRaises(AttributeError, lambda: real_object.c)
		self.assertRaises(KeyError, lambda: real_dict['c'])
	
	def test_should_set_original_objects_to_none_if_they_cant_be_deleted(self):
		obj = NoDeletesObject()
		dict_ = NoDeletesDict()
		mock_on(obj).c = 'mocky c'
		mock_on(dict_)['c'] = 'mocky c'

		self.assertEqual(obj.c(), 'mocky c')
		self.assertEqual(dict_['c'](), 'mocky c')
		
		self.downup()
		
		self.assertEqual(obj.c, None)
		self.assertEqual(dict_['c'], None)
		
	def test_should_allow_expectations(self):
		mock_anchor = mock_on(real_object)
		self.assertEqual(mock_anchor.expects('foo'), mock_anchor.foo.is_expected)

		# not part of the test -- just to satisfy the above expectation
		mock_foo = mock_anchor.foo.mock
		mock_foo()

	def test_should_warn_on_nonexistant_attributes_unless_quiet(self):
		stderr = mock_on(sys).stderr
		stderr.expects('write').once().with_('Warning: object %s has no attribute "c"' % (real_object,))
		mock_on(real_object).c
		
	def test_should_warn_on_nonexistant_keys_unless_quiet(self):
		stderr = mock_on(sys).stderr
		stderr.expects('write').once().with_('Warning: object %s has no key "c"' % (real_dict,))
		mock_on(real_dict)['c']
		
