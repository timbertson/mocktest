import os
import sys

import helper
from mocktest import TestCase, pending
from mocktest import mock_on, raw_mock, mock_wrapper
import mocktest
mock_class = mocktest.silentmock.SilentMock

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

class MockAnchorTest(TestCase):
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
		self.assertTrue(isinstance(real_dict['c'], mock_class))
		self.assertTrue(isinstance(real_object.c, mock_class))
	
	def test_should_not_clobber_anchors_for_the_same_parent(self):
		anchor_a = mock_on(real_object)
		anchor_a.foo
		self.assertEqual(anchor_a._children.keys(), ['foo'])

		anchor_b = mock_on(real_object)
		self.assertEqual(anchor_b._children.keys(), ['foo'])
		
		self.assertTrue(anchor_a, anchor_b)
		self.assertTrue(isinstance(anchor_a, mocktest.mockanchor.MockAnchor))
	
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
	
	def test_should_disallow_replacing_mocks(self):
		obj = RealClass()
		obj.foo = mock_wrapper().mock
		def set_foo():
			mock = mock_on(obj).foo
		self.assertRaises(TypeError, set_foo)
	
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

	def test_should_warn_on_nonexistant_attributes(self):
		stderr = mock_on(sys).stderr

		mock_on(real_object).c

		self.assertEqual(stderr.child('write').called.get_calls(),[
			('Warning: object %s has no attribute "c"' % (real_object,),),
			('\n',)
		])
		
	def test_should_warn_on_nonexistant_keys_unless_quiet(self):
		stderr = mock_on(sys).stderr
		dict_copy = real_dict.copy()
		mock_on(real_dict)['c']
		
		self.assertEqual(stderr.child('write').called.get_calls(), [
			('Warning: object %s has no key "c"' % (dict_copy,),),
			('\n',)
		])
	
	# @pending
	def test_should_allow_setting_of_special_instance_methods(self):
		# note: stubbing __init__ only makes sense for class objects
		class C(object):
			def __init__(self):
				self.x = 1
				
		init_mock = mock_on(C).__init__
		print repr(init_mock)
		instance = C()
		
		self.assertTrue(init_mock.called.once())
		self.assertFalse(hasattr(instance, 'x'))

	# @pending
	def test_should_allow_setting_of_special_class_methods(self):
		# note: all __**__ methods get set on the class object (except __init__)
		class C(object):
			def __init__(self):
				self.x = 1
			
			def __str__(self):
				return 'str to be overridden'
				
		instance = C()
		str_mock = mock_on(instance).__str__.retuning('fakestr')
		
		self.assertEqual(str(instance), 'fakestr')
		self.assertTrue(str_mock.called.once())
		
	def test_should_not_warn_if_quiet_specified(self):
		stderr = mock_on(sys).stderr
		mock_on(real_object, quiet=True).c
		self.assertFalse(stderr.child('write').called)

	def test_should_set_proxy_for_an_existing_attribute(self):
		class Foo(object):
			def callme(self, arg):
				self.actually_called = True
		f = Foo()
		f.actually_called = False
		
		wrapper = mock_on(f).callme.with_('a')
		
		wrapper.mock('a')
		self.assertTrue(wrapper.called.once())
		self.assertFalse(f.actually_called)
	
		wrapper.mock('b')
		self.assertTrue(wrapper.called.once())
		self.assertTrue(f.actually_called)
