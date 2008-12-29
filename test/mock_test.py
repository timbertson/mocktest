import os
import sys
import re

import helper
from mocktest import TestCase
from mocktest import raw_mock, mock_wrapper
import mocktest

mock_class = mocktest.silentmock.SilentMock

class MockObjectAndWrapperTest(TestCase):
	def is_a_mock(self, val):
		self.assertTrue(isinstance(val, mock_class))
		
	def test_constructor(self):
		mock = raw_mock()
		wrapper = mock_wrapper(mock)
		self.assertFalse(wrapper.called, "called not initialised correctly")
		self.assertTrue(wrapper.called.exactly(0), "call_count not initialised correctly")
	
		self.assertEquals(wrapper.call_list, [])
		self.assertEquals(wrapper._children, {})
		self.assertEquals(wrapper.action, None)
		self.assertEquals(wrapper.name, 'unnamed mock')
		wrapper.name = 'lil bobby mock'
	
	def test_default_return_value(self):
		wrapper = mock_wrapper()
		mock = wrapper.mock
		self.assertTrue(wrapper.return_value is mocktest.silentmock.DEFAULT)
		retval = mock()
		self.is_a_mock(retval)
		self.assertEqual(mock_wrapper(retval).name, 'return value for (unnamed mock)')
		self.is_a_mock(wrapper.return_value)

	def test_default_accessor_value(self):
		wrapper = mock_wrapper()
		mock = wrapper.mock
		retval = mock.child_a
		self.is_a_mock(retval)
		self.assertEqual(mock_wrapper(retval).name, 'child_a')
		
	def test_return_value(self):
		wrapper = mock_wrapper().returning(None)
		self.assertEquals(None, wrapper.return_value)
		self.assertEquals(None, wrapper.mock())
	
	def assert_mock_is_frozen(self, wrapper):
		self.assertFalse(wrapper._modifiable_children)
		self.assertRaises(AttributeError, lambda: wrapper.mock.nonexistant_child)
		def set_thingie():
			wrapper.mock.set_nonexistant_child = 'x'
		self.assertRaises(AttributeError, lambda: set_thingie())
		
	def test_with_methods_should_set_return_values_and_freeze_mock(self):
		wrapper = mock_wrapper().with_methods('blob', foo='bar', x=123)
		mock = wrapper.mock
		
		self.is_a_mock(mock.blob())
		self.assertEqual(mock.foo(), 'bar')
		self.assertEqual(mock.x(), 123)
		
		self.assertEqual(sorted(wrapper._children.keys()), ['blob', 'foo','x'])
		self.assert_mock_is_frozen(wrapper)
	
	def test_with_children_should_set_return_values_and_freeze_mock(self):
		wrapper = mock_wrapper().with_children('blob', foo='bar', x=123)
		mock = wrapper.mock
		
		self.is_a_mock(mock.blob)
		self.assertEqual(mock.foo, 'bar')
		self.assertEqual(mock.x, 123)
		
		self.assertEqual(sorted(wrapper._children.keys()), ['blob', 'foo','x'])
		self.assert_mock_is_frozen(wrapper)
	
	def test_name_as_first_arg_in_constructor(self):
		wrapper = mock_wrapper(raw_mock("li'l mocky"))
		self.assertEqual(wrapper.name, "li'l mocky")
	
	class SpecClass:
		b = "bee"
		__something__ = None
		def a(self):
			return "foo"
		
		
	def test_spec_class_in_constructor(self):
		wrapper = mock_wrapper().with_spec(self.SpecClass)
		self.assertEqual(wrapper._children.keys(), ['a','b'])
		self.is_a_mock(wrapper.mock.a())
		self.assert_mock_is_frozen(wrapper)
		
		self.assertRaises(AttributeError, lambda: wrapper.mock.__something__)
	
	def test_spec_instance_in_constructor(self):
		wrapper = mock_wrapper().with_spec(self.SpecClass())
		self.assertEqual(wrapper._children.keys(), ['a','b'])
		self.is_a_mock(wrapper.mock.a())
		self.assert_mock_is_frozen(wrapper)
		self.assertRaises(AttributeError, lambda: wrapper.mock.__something__)
	
	def test_children_can_be_added_later(self):
		wrapper = mock_wrapper()
		wrapper.mock.foo = 1
		wrapper.mock.bar = 2
		self.assertEqual(wrapper._children, {'foo':1, 'bar':2})
	
	def test_frozen(self):
		wrapper = mock_wrapper().frozen().unfrozen()
		wrapper.mock.child_a = 'baz'
		self.assertEqual(wrapper.mock.child_a, 'baz')
		
		wrapper = mock_wrapper().frozen()
		self.assert_mock_is_frozen(wrapper)
	
	def test_raising(self):
		# class
		wrapper = mock_wrapper().raising(SystemError)
		self.assertRaises(SystemError, wrapper.mock)
	
		# instance
		wrapper = mock_wrapper().raising(SystemError("this simply will not do"))
		self.assertRaises(SystemError, wrapper.mock)
	
	def test_children_and_methods_can_coexist(self):
		wrapper = mock_wrapper().with_children(a='a').unfrozen().with_methods(b='b')
		self.assertEqual(wrapper.mock.a, 'a')
		self.assertEqual(wrapper.mock.b(), 'b')
	
	def test_side_effect_is_called(self):
		wrapper = mock_wrapper()
		def effect():
			raise SystemError('kablooie')
		wrapper.action = effect
		
		self.assertRaises(SystemError, wrapper.mock)
		self.assertEquals(True, wrapper.called)
		
		results = []
		def effect(n):
			results.append('call %s' % (n,))
		wrapper.action = effect
		
		wrapper.mock(1)
		self.assertEquals(results, ['call 1'])
		wrapper.mock(2)
		self.assertEquals(results, ['call 1','call 2'])
	
		sentinel = object()
		wrapper = mock_wrapper().with_action(sentinel)
		self.assertEquals(wrapper.action, sentinel)
	
	def test_side_effect_return_used_when_return_value_not_specified(self):
		def return_foo():
			return "foo"
		wrapper = mock_wrapper().with_action(return_foo)
		self.assertEqual(wrapper.mock(), 'foo')
	
	def test_side_effect_can_change_mock_return_value(self):
		wrapper = mock_wrapper()
		def modify_it():
			wrapper.return_value = 'foo'
		wrapper.action = modify_it
		self.assertEqual(wrapper.mock(), 'foo')
	
	def test_side_effect_can_remove_mock_return_value_and_replace_it(self):
		wrapper = mock_wrapper()
		wrapper.return_value = "not me"
		def modify_it():
			del wrapper.return_value
			return "me instead"
		wrapper.action = modify_it
		self.assertEqual(wrapper.mock(), "me instead")
	
	def test_side_effect_return_val_used_even_when_it_is_none(self):
		def return_foo():
			print "i've been called!"
		wrapper = mock_wrapper().with_action(return_foo)
		self.assertEqual(wrapper.mock(), None)
	
	def test_side_effect_return_not_used_when_return_value_specified(self):
		def return_foo():
			return "foo"
		wrapper = mock_wrapper().returning('bar').with_action(return_foo)
		self.assertEqual(wrapper.mock(), 'bar')
	
	def test_should_allow_setting_of_magic_methods(self):
		clean_wrapper = mock_wrapper().named('clean')
		modified_wrapper = mock_wrapper().named('modified').with_special(
			__repr__ = mock_wrapper().returning('my repr!').mock,
			__len__ = lambda x: 5)
			
		self.assertNotEqual(clean_wrapper.mock.__class__, modified_wrapper.mock.__class__)
		
		val = repr(modified_wrapper.mock)
		self.assertTrue(modified_wrapper.child('__repr__').called.once())
		self.assertEqual(val, 'my repr!')
	
		# can't override builtin mock magic methods
		self.assertRaises(
			AttributeError, lambda: modified_wrapper.with_special(__str__ = lambda x: 'foop'),
			message="cannot override SilentMock special method '__str__'")
	
		# can't assign non-magic ones
		self.assertRaises(ValueError, lambda: modified_wrapper.with_special(_len = lambda x: 5))
		
		self.assertEqual(len(modified_wrapper.mock), 5)
		self.assertRaises(AttributeError, lambda: clean_wrapper.mock.__len__)
		self.assertRaises(TypeError, lambda: len(clean_wrapper.mock))
		self.assertEqual(str(clean_wrapper.mock), 'clean')
	
	def test_should_show_where_calls_were_made(self):
		wrapper = mock_wrapper()
		mock = wrapper.mock
		
		mock(1,2,345)
		print str(wrapper.called)
		self.assertTrue(re.search('// mock_test\.py:[0-9]+ +:: mock\(1,2,345\)', str(wrapper.called)))

	def test_should_compare_call_records_to_tuples_and_other_call_records(self):
		args = (1,2,3)
		kwargs = {'x':123, 'y':456}
		CallRecord = mocktest.silentmock.CallRecord
		self.assertEqual(
			mocktest.silentmock.CallRecord(args, kwargs),
			mocktest.silentmock.CallRecord(args, kwargs))

		self.assertEqual(
			mocktest.silentmock.CallRecord(args, kwargs),
			(args, kwargs))

		self.assertEqual(
			(args, kwargs),
			mocktest.silentmock.CallRecord(args, kwargs))
		
	def test_call_recording(self):
		wrapper = mock_wrapper()
		mock = wrapper.mock
		
		result = mock()
		self.assertEquals(mock(), result, "different result from consecutive calls")
		self.assertEquals(wrapper.call_list,
			[
				None, # called with nothing
				None, # (twice)
			])
	
		wrapper.reset()
		self.assertEquals(wrapper.call_list, [])
		
		mock('first_call')
		mock('second_call', 'arg2', call_=2)
		self.assertEquals(wrapper.call_list,
			[
				('first_call',),
				(('second_call','arg2'), {'call_':2}),
			])
