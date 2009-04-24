import unittest
import helper
from mocktest import *

class TestPySpec(TestCase):
	def test_should_track_calls(self):
		wrapper = mock_wrapper()
		wrapper.mock('arg1')
		
		self.assertTrue(wrapper.called)
		self.assertEquals(wrapper.called, True)
		self.assertTrue(wrapper.called.with_args('arg1'))

		self.assertFalse(mock_wrapper().called)
		self.assertFalse(wrapper.called.with_args('arg1', 'arg2'))
	
	def test_should_track_number_of_calls(self):
		wrapper = mock_wrapper()
		mock = wrapper.mock
		mock('a')
		mock('b')
		mock('b')
		
		# exactly
		self.assertTrue(wrapper.called.exactly(3).times)
		self.assertTrue(mock_wrapper(wrapper.mock.bar).called.exactly(0).times)

		# at_least
		self.assertTrue(wrapper.called.at_least(1).times)
		self.assertFalse(wrapper.called.at_least(4).times)

		# at_most
		self.assertFalse(wrapper.called.at_most(2).times)
		self.assertTrue(wrapper.called.at_most(4).times)

		# between
		self.assertTrue(wrapper.called.between(1,4).times)
		self.assertTrue(wrapper.called.between(4,1).times)

		# failed betweens
		self.assertFalse(wrapper.called.between(4,5).times)
		self.assertFalse(wrapper.called.between(5,4).times)
		self.assertFalse(wrapper.called.between(5,5).times)
	
	def test_should_default_to_one_or_more_calls(self):
		wrapper = mock_wrapper()
		wrapper.mock.a()
		wrapper.mock.a(1)
		
		self.assertTrue(wrapper.child('a').called)
		self.assertFalse(wrapper.child('b').called)
	
	def test_should_have_no_times_once_twice_and_thrice_aliases(self):
		wrapper = mock_wrapper()
		mock = wrapper.mock
		mock.a()
		
		mock.b()
		mock.b()
		
		mock.c()
		mock.c()
		mock.c()
		
		self.assertTrue(wrapper.child('a').called.once())
		self.assertFalse(wrapper.child('a').called.twice())
		self.assertFalse(wrapper.child('a').called.thrice())
	
		self.assertFalse(wrapper.child('b').called.once())
		self.assertTrue(wrapper.child('b').called.twice())
		self.assertFalse(wrapper.child('b').called.thrice())
		
		self.assertFalse(wrapper.child('c').called.once())
		self.assertFalse(wrapper.child('c').called.twice())
		self.assertTrue(wrapper.child('c').called.thrice())

		self.assertTrue(wrapper.child('d').called.no_times())
		
	def test_should_track_number_of_calls_with_arguments(self):
		wrapper = mock_wrapper()
		mock = wrapper.mock
		mock.foo('a')
		mock.foo('b')
		mock.foo('b')
		mock.foo('unused_call')
		
		print wrapper.child
		
		self.assertTrue(wrapper.child('foo').called.with_args('a').exactly(1))
		self.assertTrue(wrapper.child('foo').called.with_args('b').exactly(2))
		
		# reverse check order:
		
		self.assertTrue(wrapper.child('foo').called.exactly(1).with_args('a'))
		self.assertTrue(wrapper.child('foo').called.exactly(2).with_args('b'))
	
	def test_should_return_arguments(self):
		wrapper = mock_wrapper()
		mock = wrapper.mock
		mock.foo(1)
		mock.foo('bar', x='y')
		mock.bar()
		mock.xyz(foo='bar')

		self.assertEqual(wrapper.child('foo').called.get_calls(),
			[
				(1,),
				(('bar',),{'x':'y'})
			])
		self.assertRaises(AssertionError, wrapper.child('foo').called.once().get_calls)
		self.assertEqual(wrapper.child('foo').called.twice().get_calls(),
			[
				(1,),
				(('bar',),{'x':'y'})
			])
		self.assertEqual(wrapper.child('xyz').called.once().get_calls()[0], (None, {'foo':'bar'}))
		
		self.assertRaises(ValueError, wrapper.child('foo').called.twice().get_args)
		self.assertRaises(ValueError, wrapper.child('bar').called.get_args)
		self.assertEqual(wrapper.child('bar').called.once().get_args(), (None))
		
		
	def test_should_allow_argument_checking_callbacks(self):
		wrapper = mock_wrapper()
		mock = wrapper.mock
		mock.foo(1)
		mock.foo(2)
		mock.foo(3)
		mock.foo(4)
		
		self.assertTrue(wrapper.child('foo').called.twice().where_args(lambda *args: all([x < 3 for x in args])))
		self.assertTrue(wrapper.child('foo').called.exactly(4).times)
	
	def test_should_return_arguments_for_a_subset_of_calls_given_conditions(self):
		wrapper = mock_wrapper()
		mock = wrapper.mock
		mock(1)
		mock(1)
		mock(2)
		
		self.assertEqual(wrapper.called.with_(1).get_calls(), [(1,), (1,)])
	
	def test_should_allow_chaining_of_mock_wrapper_returning_method(self):
		wrapper = mock_wrapper()
		expectation = wrapper.called.once()
		same_expectation = expectation.returning(5)
		
		self.assertTrue(expectation is same_expectation)
		self.assertEqual(wrapper.return_value, 5)
		
	def test_should_allow_chaining_of_mock_wrapper_raising_method(self):
		wrapper = mock_wrapper()
		expectation = wrapper.called.once()
		class FooError(RuntimeError): pass
		same_expectation = expectation.raising(FooError)
		
		self.assertTrue(expectation is same_expectation)
		self.assertRaises(FooError, wrapper.mock)
		
	def test_should_allow_chaining_of_mock_wrapper_raising_method(self):
		wrapper = mock_wrapper()
		expectation = wrapper.called.once()
		def doSomething():
			print "something happened!"
		same_expectation = expectation.with_action(doSomething)
		
		self.assertTrue(expectation is same_expectation)
		self.assertEqual(wrapper.action, doSomething)
		
	
if __name__ == '__main__':
	unittest.main()
