import os
import sys
import re

import helper
from mocktest import TestCase
from mocktest import raw_mock, mock
from mocktest import MockError
import mocktest

mock_class = mocktest.silentmock.SilentMock

class MockObjectAndWrapperTest(TestCase):
	def is_a_mock(self, val):
		self.assertTrue(isinstance(val, mock_class))
		
	def test_constructor(self):
		mock_ = raw_mock()
		wrapper = mock(mock_)
		self.assertFalse(wrapper.called, "called not initialised correctly")
		self.assertTrue(wrapper.called.exactly(0), "call_count not initialised correctly")
	
		self.assertEquals(wrapper.call_list, [])
		self.assertEquals(wrapper._children, {})
		self.assertEquals(wrapper.action, None)
		self.assertEquals(wrapper.name, 'unnamed mock')
		wrapper.name = 'lil bobby mock'
	
	def test_default_return_value(self):
		wrapper = mock()
		mock_ = wrapper.raw
		self.assertTrue(wrapper.return_value is mocktest.silentmock.DEFAULT)
		retval = mock_()
		self.is_a_mock(retval)
		self.assertEqual(mock(retval).name, 'return value for (unnamed mock)')
		self.is_a_mock(wrapper.return_value)

	def test_default_accessor_value(self):
		wrapper = mock()
		mock_ = wrapper.raw
		retval = mock_.child_a
		self.is_a_mock(retval)
		self.assertEqual(mock(retval).name, 'child_a')
		
	def test_return_value(self):
		wrapper = mock().returning(None)
		self.assertEquals(None, wrapper.return_value)
		self.assertEquals(None, wrapper.raw())
	
	def assert_mock_is_frozen(self, wrapper):
		self.assertFalse(wrapper._modifiable_children)
		self.assertRaises(AttributeError, lambda: wrapper.raw.nonexistant_child)
		def set_thingie():
			wrapper.raw.set_nonexistant_child = 'x'
		self.assertRaises(AttributeError, lambda: set_thingie())
		
	def test_with_methods_should_set_return_values_and_freeze_mock(self):
		wrapper = mock().with_methods('blob', '_blob', foo='bar', x=123, _blobx='underscore!')
		mock_ = wrapper.raw
		
		self.is_a_mock(mock_.blob())
		self.is_a_mock(mock_._blob())
		self.assertEqual(mock_.foo(), 'bar')
		self.assertEqual(mock_.x(), 123)
		self.assertEqual(mock_._blobx(), 'underscore!')
		
		self.assertEqual(sorted(wrapper._children.keys()), ['_blob', '_blobx', 'blob', 'foo','x'])
		self.assert_mock_is_frozen(wrapper)
	
	def test_with_children_should_set_return_values_and_freeze_mock(self):
		wrapper = mock().with_children('blob', foo='bar', x=123)
		mock_ = wrapper.raw
		
		self.is_a_mock(mock_.blob)
		self.assertEqual(mock_.foo, 'bar')
		self.assertEqual(mock_.x, 123)
		
		self.assertEqual(sorted(wrapper._children.keys()), ['blob', 'foo','x'])
		self.assert_mock_is_frozen(wrapper)
	
	def test_name_as_first_arg_in_constructor(self):
		wrapper = mock(raw_mock("li'l mocky"))
		self.assertEqual(wrapper.name, "li'l mocky")
	
	class SpecClass:
		b = "bee"
		__something__ = None
		def a(self):
			return "foo"
		
	def test_spec_class_in_constructor(self):
		wrapper = mock().with_spec(self.SpecClass)
		self.assertEqual(wrapper._children.keys(), ['a','b'])
		self.is_a_mock(wrapper.raw.a())
		self.assert_mock_is_frozen(wrapper)
		
		self.assertRaises(AttributeError, lambda: wrapper.raw.__something__)
	
	def test_spec_instance_in_constructor(self):
		wrapper = mock().with_spec(self.SpecClass())
		self.assertEqual(wrapper._children.keys(), ['a','b'])
		self.is_a_mock(wrapper.raw.a())
		self.assert_mock_is_frozen(wrapper)
		self.assertRaises(AttributeError, lambda: wrapper.raw.__something__)
	
	def test_children_can_be_added_later(self):
		wrapper = mock()
		wrapper.raw.foo = 1
		wrapper.raw.bar = 2
		self.assertEqual(wrapper._children, {'foo':1, 'bar':2})
	
	def test_frozen(self):
		wrapper = mock().frozen().unfrozen()
		wrapper.raw.child_a = 'baz'
		self.assertEqual(wrapper.raw.child_a, 'baz')
		
		wrapper = mock().frozen()
		self.assert_mock_is_frozen(wrapper)
	
	def test_raising(self):
		# class
		wrapper = mock().raising(SystemError)
		self.assertRaises(SystemError, wrapper.raw)
	
		# instance (with random extra args)
		wrapper = mock().raising(SystemError("this simply will not do"))
		self.assertRaises(SystemError, lambda: wrapper.raw('a','b',foo='blah'))
	
	def test_children_and_methods_can_coexist(self):
		wrapper = mock().with_children(a='a').unfrozen().with_methods(b='b')
		self.assertEqual(wrapper.raw.a, 'a')
		self.assertEqual(wrapper.raw.b(), 'b')
	
	def test_side_effect_is_called(self):
		wrapper = mock()
		def effect():
			raise SystemError('kablooie')
		wrapper.action = effect
		
		self.assertRaises(SystemError, wrapper.raw)
		self.assertEquals(True, wrapper.called)
		
		wrapper = mock()
		results = []
		def effect(n):
			results.append('call %s' % (n,))
		wrapper.action = effect
		
		wrapper.raw(1)
		self.assertEquals(results, ['call 1'])
		wrapper.raw(2)
		self.assertEquals(results, ['call 1','call 2'])
	
		sentinel = object()
		wrapper = mock().with_action(sentinel)
		self.assertEquals(wrapper.action, sentinel)
	
	def test_side_effect_return_used(self):
		def return_foo():
			return "foo"
		wrapper = mock().with_action(return_foo)
		self.assertEqual(wrapper.raw(), 'foo')
	
	def test_side_effect_return_val_used_even_when_it_is_none(self):
		def return_foo():
			print "i've been called!"
		wrapper = mock().with_action(return_foo)
		self.assertEqual(wrapper.raw(), None)
	
	def test_should_allow_setting_of_magic_methods(self):
		clean_wrapper = mock().named('clean')
		modified_wrapper = mock().named('modified')
		
		modified_wrapper.method('__repr__').returning('my repr!')
		modified_wrapper.method('__str__').returning('my str!')
		modified_wrapper.method('__len__').returning(5)
		
		self.assertNotEqual(type(clean_wrapper.raw), type(modified_wrapper.raw))
		self.assertEqual(type(clean_wrapper.raw).__name__, type(modified_wrapper.raw).__name__)
		
		val = repr(modified_wrapper.raw)
		self.assertEqual(val, 'my repr!')
		self.assertTrue(modified_wrapper.child('__repr__').called.once())
	
		str_val = str(modified_wrapper.raw)
		self.assertEqual(str_val, 'my str!')
		self.assertTrue(modified_wrapper.child('__str__').called.once())
	
	def test_should_allow_setting_of_magic_methods_in_bulk(self):
		wrapper = mock().with_methods(__str__ = 's!', __len__ = 5)
		self.assertEqual(str(wrapper.raw), 's!')
		self.assertEqual(len(wrapper.raw), 5)
	
	def test_should_show_where_calls_were_made(self):
		wrapper = mock()
		mock_ = wrapper.raw
		
		mock_(1,2,345)
		print str(wrapper.called)
		self.assertTrue(re.search('// mock_test\.py:[0-9]+ +:: mock_\(1,2,345\)', str(wrapper.called)))

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
		wrapper = mock()
		mock_ = wrapper.raw
		
		result = mock_()
		self.assertEquals(mock_(), result, "different result from consecutive calls")
		self.assertEquals(wrapper.call_list,
			[
				None, # called with nothing
				None, # (twice)
			])
	
		wrapper.reset()
		self.assertEquals(wrapper.call_list, [])
		
		mock_('first_call')
		mock_('second_call', 'arg2', call_=2)
		self.assertEquals(wrapper.call_list,
			[
				('first_call',),
				(('second_call','arg2'), {'call_':2}),
			])

class ProxyingTest(TestCase):
	def setUp(self):
		
		self.actually_called = False
		def called(whoami, *args, **kwargs):
			print "ACTUALLY CALLED"
			whoami.actually_called = True
			return 'real_return'
		
		self.wrapper = mock(called).returning('mock_return')
	
	def test_should_not_let_you_set__should_intercept__twice(self):
		self.wrapper.with_args(self, 'x',y=1)
		self.assertRaises(MockError, lambda: self.wrapper.with_args(self))
		self.assertRaises(MockError, lambda: self.wrapper.when_args(self))
		
	def test_should_act_as_mock_only_when_args_match(self):
		self.wrapper.with_args(self, 'x',y=1)

		self.assertEqual(self.wrapper.raw(self, 'x',y=1), 'mock_return')
		self.assertTrue(self.wrapper.called.once())
		self.assertFalse(self.actually_called)

		# now this one should be ignored by the mock
		self.assertEqual(self.wrapper.raw(self, 'y', y=1), 'real_return')
		self.assertTrue(self.wrapper.called.once())
		self.assertTrue(self.actually_called)
		
	def test_should_act_as_mock_only_when_should_intercept_returns_true(self):
		def are_single(arg):
			# accept exactly one argument
			return True
		
		self.wrapper.when_args(are_single)
		
		self.assertEqual(self.wrapper.raw(self), 'mock_return')
		self.assertTrue(self.wrapper.called.once())
		self.assertFalse(self.actually_called)

		# now this one should be ignored by the mock
		self.assertEqual(self.wrapper.raw(self, 'y'), 'real_return')
		self.assertTrue(self.wrapper.called.once())
		self.assertTrue(self.actually_called)
	

# -- options that clobber each other:
class ClobberTest(TestCase):
	def setUp(self):
		self.mock = mock().named("bob")
	
	def test_should_not_let_you_overwrite_return_value_with_action(self):
		self.mock.returning('foo')
		self.assertRaises(MockError, lambda: self.mock.with_action(lambda x: x))

	def test_should_not_let_you_overwrite_return_value_with_raises(self):
		self.mock.returning('foo')
		self.assertRaises(MockError, lambda: self.mock.raising(StandardError()), message =  "Cannot set action on mock 'bob': a return value has already been set")

	def test_should_not_let_you_overwrite_raise_with_action(self):
		self.mock.raising(StandardError())
		self.assertRaises(MockError, lambda: self.mock.returning(1), message =  "Cannot set return value on mock 'bob': an action has already been set")

	def test_should_not_let_you_overwrite_raise_with_return_value(self):
		self.mock.raising(StandardError())
		self.assertRaises(MockError, lambda: self.mock.returning(1), message =  "Cannot set return value on mock 'bob': an action has already been set")

	def test_should_not_let_you_overwrite_action_with_return_value(self):
		self.mock.with_action(lambda: 1)
		self.assertRaises(MockError, lambda: self.mock.returning(1), message =  "Cannot set return value on mock 'bob': an action has already been set")

	def test_should_not_let_you_overwrite_action_with_raise(self):
		self.mock.with_action(lambda: 1)
		self.assertRaises(MockError, lambda: self.mock.raising(1), message =  "Cannot set action on mock 'bob': an action has already been set")
	
	def test_should_let_you_clear_actions(self):
		self.mock.with_action(lambda a: a)
		del self.mock.action
		self.mock.with_action(lambda a: a + 2)
		del self.mock.action
		
		self.mock.returning(1)
		del self.mock.return_value
		self.mock.returning(2)
		del self.mock.return_value
		
		self.mock.raising(StandardError())
		del self.mock.action
		self.mock.raising(RuntimeError())
		del self.mock.action
