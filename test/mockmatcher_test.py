import unittest
import helper
from mocktest import *

class TestPySpec(TestCase):
	def test_should_track_calls(self):
		wrapper_ = mock()
		wrapper_.raw('arg1')
		
		self.assertTrue(wrapper_.called)
		self.assertEquals(wrapper_.called, True)
		self.assertTrue(wrapper_.called.with_args('arg1'))

		self.assertFalse(mock().called)
		self.assertFalse(wrapper_.called.with_args('arg1', 'arg2'))
	
	def test_should_track_number_of_calls(self):
		wrapper_ = mock()
		mock_ = wrapper_.raw
		mock_('a')
		mock_('b')
		mock_('b')
		
		# exactly
		self.assertTrue(wrapper_.called.exactly(3).times)
		self.assertTrue(mock(wrapper_.raw.bar).called.exactly(0).times)

		# at_least
		self.assertTrue(wrapper_.called.at_least(1).times)
		self.assertFalse(wrapper_.called.at_least(4).times)

		# at_most
		self.assertFalse(wrapper_.called.at_most(2).times)
		self.assertTrue(wrapper_.called.at_most(4).times)

		# between
		self.assertTrue(wrapper_.called.between(1,4).times)
		self.assertTrue(wrapper_.called.between(4,1).times)

		# failed betweens
		self.assertFalse(wrapper_.called.between(4,5).times)
		self.assertFalse(wrapper_.called.between(5,4).times)
		self.assertFalse(wrapper_.called.between(5,5).times)
	
	def test_should_default_to_one_or_more_calls(self):
		wrapper_ = mock()
		wrapper_.raw.a()
		wrapper_.raw.a(1)
		
		self.assertTrue(wrapper_.child('a').called)
		self.assertFalse(wrapper_.child('b').called)
	
	def test_should_have_no_times_once_twice_and_thrice_aliases(self):
		wrapper_ = mock()
		mock_ = wrapper_.raw
		mock_.a()
		
		mock_.b()
		mock_.b()
		
		mock_.c()
		mock_.c()
		mock_.c()
		
		self.assertTrue(wrapper_.child('a').called.once())
		self.assertFalse(wrapper_.child('a').called.twice())
		self.assertFalse(wrapper_.child('a').called.thrice())
	
		self.assertFalse(wrapper_.child('b').called.once())
		self.assertTrue(wrapper_.child('b').called.twice())
		self.assertFalse(wrapper_.child('b').called.thrice())
		
		self.assertFalse(wrapper_.child('c').called.once())
		self.assertFalse(wrapper_.child('c').called.twice())
		self.assertTrue(wrapper_.child('c').called.thrice())

		self.assertTrue(wrapper_.child('d').called.no_times())
		
	def test_should_track_number_of_calls_with_arguments(self):
		wrapper_ = mock()
		mock_ = wrapper_.raw
		mock_.foo('a')
		mock_.foo('b')
		mock_.foo('b')
		mock_.foo('unused_call')
		
		self.assertTrue(wrapper_.child('foo').called.with_args('a').exactly(1))
		self.assertTrue(wrapper_.child('foo').called.with_args('b').exactly(2))
		
		# reverse check order:
		
		self.assertTrue(wrapper_.child('foo').called.exactly(1).with_args('a'))
		self.assertTrue(wrapper_.child('foo').called.exactly(2).with_args('b'))
	
	def test_should_return_arguments(self):
		wrapper_ = mock()
		mock_ = wrapper_.raw
		mock_.foo(1)
		mock_.foo('bar', x='y')
		mock_.bar()
		mock_.xyz(foo='bar')

		self.assertEqual(wrapper_.child('foo').called.get_calls(),
			[
				(1,),
				(('bar',),{'x':'y'})
			])
		self.assertRaises(AssertionError, wrapper_.child('foo').called.once().get_calls)
		self.assertEqual(wrapper_.child('foo').called.twice().get_calls(),
			[
				(1,),
				(('bar',),{'x':'y'})
			])
		self.assertEqual(wrapper_.child('xyz').called.once().get_calls()[0], (None, {'foo':'bar'}))
		
		self.assertRaises(ValueError, wrapper_.child('foo').called.twice().get_args)
		self.assertRaises(ValueError, wrapper_.child('bar').called.get_args)
		self.assertEqual(wrapper_.child('bar').called.once().get_args(), (None))
		
		
	def test_should_allow_argument_checking_callbacks(self):
		wrapper_ = mock()
		mock_ = wrapper_.raw
		mock_.foo(1)
		mock_.foo(2)
		mock_.foo(3)
		mock_.foo(4)
		
		self.assertTrue(wrapper_.child('foo').called.twice().where_args(lambda *args: all([x < 3 for x in args])))
		self.assertTrue(wrapper_.child('foo').called.exactly(4).times)
	
	def test_should_allow_matchers_for_argument_specs(self):
		wrapper_ = mock()
		mock_ = wrapper_.raw
		
		mock_.raw(foo='hjdsfhsdfds')
		
		class WithAttribute_foo(object):
			def foo(self):
				pass
		
		mock_.raw(WithAttribute_foo(), 1)
		
		self.assertTrue(mock_.called.once().with_(any_string))
		self.assertTrue(mock_.called.once().with_(object_with('foo')))
	
	def test_should_format_matchers_with_their_description(self):
		wrapper_ = mock()
		expectation = wrapper_.expects('a').with_(anything)
		self.assertTrue(expectation.describe().endswith('with arguments equal to: <#Matcher: any object>'), expectation.describe())
		# now satisfy the expectation:
		wrapper_.raw.a(123)
	
	def test_should_return_arguments_for_a_subset_of_calls_given_conditions(self):
		wrapper_ = mock()
		mock_ = wrapper_.raw
		mock_(1)
		mock_(1)
		mock_(2)
		
		self.assertEqual(wrapper_.called.with_(1).get_calls(), [(1,), (1,)])
	
	def test_should_allow_chaining_of_mock_wrapper_returning_method(self):
		wrapper_ = mock()
		expectation = wrapper_.called.once()
		same_expectation = expectation.returning(5)
		
		self.assertTrue(expectation is same_expectation)
		self.assertEqual(wrapper_.return_value, 5)
		
	def test_should_allow_chaining_of_mock_wrapper_raising_method(self):
		wrapper_ = mock()
		expectation = wrapper_.called.once()
		class FooError(RuntimeError): pass
		same_expectation = expectation.raising(FooError)
		
		self.assertTrue(expectation is same_expectation)
		self.assertRaises(FooError, wrapper_.raw)
		
	def test_should_allow_chaining_of_mock_wrapper_action_method(self):
		wrapper_ = mock()
		expectation = wrapper_.called.once()
		def doSomething():
			print "something happened!"
		same_expectation = expectation.with_action(doSomething)
		
		self.assertTrue(expectation is same_expectation)
		self.assertEqual(wrapper_.action, doSomething)
		
	
if __name__ == '__main__':
	unittest.main()
