from mocktest import *
from mocktest.transaction import MockTransaction
from mocktest.mockerror import MockError
from unittest import TestCase
import unittest
from functools import wraps

def _dir(obj):
	return filter(lambda x: not x.startswith('_'), dir(obj))

#TODO: expose these for mocktest_test?
def run_func(self, func):
	from mocktest import TestCase as MockTestCase
	class AnonymousTestCase(MockTestCase):
		def runTest(self):
			func(self)
	suite = unittest.TestSuite(tests=(AnonymousTestCase(),))
	result = unittest.TestResult()
	suite.run(result)
	assert result.testsRun == 1
	assert _dir(obj) == [], _dir(obj)
	return result

def passing(func):
	@wraps(func)
	def _run_test(self):
		result = run_func(self, func)
		assert result.wasSuccessful(), (result.failures + result.errors)[0][1]
	_run_test.__name__ == func.__name__
	return _run_test

def failing(func):
	@wraps(func)
	def _run_test(self):
		result = run_func(self, func)
		assert not result.wasSuccessful(), "test unexpectedly succeeded!"
	_run_test.__name__ == func.__name__
	return _run_test

class Object(object): pass
obj = Object()

class TestMockingCalls(TestCase):
	@passing
	def test_return_values(self):
		when(obj).meth.then_return('foo')
		assert obj.meth() == 'foo', repr(obj.meth())
		when(obj).meth(1,2,3).then_return('123')
		assert obj.meth(1,2,3) == '123'
		assert obj.meth(3, 2, 1) == 'foo'
		self.assertRaises(AttributeError, lambda: obj.meth2)
	
	def test_should_revert_all_replaced_attrs(self):
		self.assertEquals(_dir(object), [])
		with MockTransaction:
			when(obj).meth1.then_return(1)
			assert obj.meth1() == 1
			expect(obj).meth2.and_return(2)
			assert obj.meth2() == 2
			modify(obj).attr = 3
			assert obj.attr == 3
		self.assertEquals(_dir(object), [])

	@passing
	def test_give_a_useful_message_when_overriding_an_inbuilt_method_is_impossible(self):
		self.assertRaises(MockError, lambda: when('some string').__call__.then_return('fake'), message='Can\'t alter class of \'str\'')
	
	@passing
	def test_calling_with_incorrect_number_of_args_should_raise_TypeError(self):
		when(obj).meth().then_return(True)
		assert obj.meth() == True
		self.assertRaises(TypeError, lambda: obj.meth(1))

	@passing
	def test_leaving_out_parens_matches_any_args(self):
		when(obj).any_args.then_return(True)
		assert obj.any_args() == True
		assert obj.any_args(1) == True
		assert obj.any_args(1, x=2) == True
	
	@passing
	def test_mocking_class_methods(self):
		when(Object).foo().then_return(True)
		assert obj.foo() == True, repr(obj.foo())

	@passing
	def test_delegating_action(self):
		when(obj).repr.then_return('repr')
		when(obj).foo(1).then_call(lambda i: "%s proxied! %s" % (obj.repr(), i))
		assert obj.foo(1) == "repr proxied! 1"
	
	@passing
	def test_replacing_properties(self):
		obj = Object()
		obj.foo = 'original'
		modify(obj).foo = 'replaced'
		modify(obj).grand.child = True
		assert obj.foo == 'replaced'
		assert obj.grand.child
		core._teardown()
		core._setup()
		assert obj.foo == 'original', obj.foo
		self.assertRaises(AttributeError, lambda: obj.grand)


class TestMockingSpecialMethods(TestCase):
	@passing
	def test_mocking_call(self):
		self.assertRaises(TypeError, lambda: obj())
		when(obj).__call__(2).then_return('two')
		when(obj).__call__(3).then_return('three')
		assert obj(2) == 'two'
		assert obj(3) == 'three'
	
	def test_mocking_special_methods_should_revert_class_heirarchies(self):
		with MockTransaction:
			when(obj).__call__(2).then_return('two')
			assert obj(2) == 'two'
			print type(obj)
			assert type(obj) is not Object
			assert isinstance(obj, Object)
		assert type(obj) is Object
	
	@passing
	def test_mocking_length(self):
		when(obj).__len__().then_return(2)
		assert len(obj) == 2
	
	@passing
	def test_mocking_special_methods_on_class_directly(self):
		when(Object).__len__().then_return(5)
		assert len(obj) == 5
	
class TestExpectations(TestCase):
	@passing
	def test_receiving_call_once(self):
		expect(obj).meth.once()
		obj.meth()

	@failing
	def test_receiving_call_too_many_times(self):
		expect(obj).meth.once()
		obj.meth()
		obj.meth()

	@failing
	def test_receiving_call_not_enough_times(self):
		expect(obj).meth.exactly(4).times()
		obj.meth()
		obj.meth()
		obj.meth()
	
	@passing
	def test_receiving_any_number_of_times(self):
		when(obj).meth()
		when(obj).meth(1).then_return(1)
		assert obj.meth() == None
		assert obj.meth() == None
		assert obj.meth(1) == 1
	
	@passing
	def test_at_least(self):
		expect(obj).meth().at_least(2).times()
		obj.meth()
		obj.meth()
		obj.meth()

	@failing
	def test_at_most(self):
		expect(obj).meth().at_most(2).times()
		obj.meth()
		obj.meth()
		obj.meth()
	
class TestMatchers(TestCase):
	@passing
	def test_any_single_arg(self):
		when(obj).foo(Any).then_return(True)
		assert obj.foo(1) == True
		assert obj.foo('foo') == True
		self.assertRaises(TypeError, lambda: obj.foo())
		self.assertRaises(TypeError, lambda: obj.foo(1, 2))

	@passing
	def test_any_multiple_args(self):
		when(obj).foo(*Any).then_return(True)
		assert obj.foo(1) == True
		assert obj.foo('foo') == True
		assert obj.foo() == True
		assert obj.foo(1, 2) == True
		self.assertRaises(TypeError, lambda: obj.foo(1, 2, x=3))

	@passing
	def test_any_named_args(self):
		when(obj).foo(**Any).then_return(True)
		assert obj.foo(x=1) == True
		assert obj.foo(y='foo') == True
		assert obj.foo() == True
		assert obj.foo(x=1, y=2) == True
		self.assertRaises(TypeError, lambda: obj.foo(1, 2, x=3))
	
	@passing
	def test_matching_only_some_kwargs(self):
		when(obj).foo(**kwargs_containing(x=1)).then_return(True)
		assert obj.foo(x=1)
		assert obj.foo(x=1, y=2)
		self.assertRaises(TypeError, lambda: obj.foo(x=3))
	
	@passing
	def test_using_splats_is_enforced_for_kwargs(self):
		self.assertRaises(RuntimeError,
			lambda: when(obj).foo(kwargs_containing(x=1)),
			message="KwargsMatcher instance used without prefixing with '**'")

	@passing
	def test_using_splats_is_enforced_for_args(self):
		self.assertRaises(RuntimeError,
			lambda: when(obj).foo(args_containing(1)),
			message="SplatMatcher instance used without prefixing with '*'")

	@passing
	def test_matching_only_some_args(self):
		when(obj).foo(*args_containing(1,2)).then_return(True)
		assert obj.foo(1,4,3,2)
		assert obj.foo(1,2)
		self.assertRaises(TypeError, lambda: obj.foo(1))

	@passing
	def test_any_args_at_all(self):
		when(obj).foo(*Any, **Any).then_return(True)
		assert obj.foo(x=1) == True
		assert obj.foo(y='foo') == True
		assert obj.foo() == True
		assert obj.foo(x=1, y=2) == True
		assert obj.foo(1, 2, x=3) == True
	
	@passing
	def test_any_instance(self):
		when(obj).foo(Any(int)).then_return(True)
		assert obj.foo(1)
		assert obj.foo(2)
		self.assertRaises(TypeError, lambda: obj.foo('str'))
		self.assertRaises(TypeError, lambda: obj.foo(int))
		self.assertRaises(TypeError, lambda: obj.foo(1,2))

	@passing
	def test_multiple_any_instance(self):
		when(obj).foo(*Any(int)).then_return(True)
		assert obj.foo(1)
		assert obj.foo(2)
		assert obj.foo()
		assert obj.foo(1,2,3,4)
		self.assertRaises(TypeError, lambda: obj.foo('str'))
		self.assertRaises(TypeError, lambda: obj.foo(int))

	@passing
	def test_multiple_any_instance_after_normal_args(self):
		when(obj).foo(Any(str), *Any(int)).then_return(True)
		assert obj.foo('str')
		assert obj.foo('string', 2)
		self.assertRaises(TypeError, lambda: obj.foo(1,2,3,4))
		self.assertRaises(TypeError, lambda: obj.foo())
		self.assertRaises(TypeError, lambda: obj.foo(int))

	##TODO: this should work in py3k?
	#@passing
	#def test_splat_in_amongst_normal_matchers(self):
	#	when(obj).foo(1, 2, *Any(int), 3, 4, 5).then_return(True)
	#	assert obj.foo(1,2,3,4,5)
	#	assert obj.foo(1,2,0,0,0,3,4,5)
	#	self.assertRaises(TypeError, lambda: obj.foo(1,2,3,4,4,5))
	#	self.assertRaises(TypeError, lambda: obj.foo())
	#	self.assertRaises(TypeError, lambda: obj.foo(int))

class TestMockCreation(TestCase):
	@passing
	def test_creation_methods_kwargs(self):
		obj = mock('foo')
		modify(obj).methods(x=1, y=2)
		assert obj.x() == 1
		assert obj.x(1,2,3) == 1
		assert obj.y() == 2, obj.y()

	@passing
	def test_creation_children_kwargs(self):
		obj = mock('foo')
		modify(obj).children(x=1, y=2)
		assert obj.x == 1
		assert obj.y == 2
	
	@passing
	def test_creation_copying_existing_object(self):
		class Base(object):
			def three_args(self, a, b, c):
				raise RuntimeError("shouldn't actually be called!")
			def _private(self):
				raise RuntimeError("shouldn't actually be called!")
			def __call__(self):
				raise RuntimeError("shouldn't actually be called!")

		base = Base()
		obj = mock('foo', create_unknown_children=False)
		modify(obj).copying(base).children(x=1)
		assert obj.three_args(1,2,3) == None
		assert obj._private() == None
		assert obj() == None
		assert obj.x == 1
		self.assertRaises(AttributeError, lambda: obj.no_such_method())
	
	@passing
	def test_responses_should_use_most_recently_added_first(self):
		when(obj).foo(Any).then_return('anything')
		assert obj.foo(1) == 'anything'
		when(obj).foo(1).then_return('one')
		assert obj.foo(1) == 'one'
		assert obj.foo(2) == 'anything'

class CallInspection(TestCase):
	@passing
	def test_inspect_calls(self):
		obj = mock('foo')
		obj.a()
		obj.a(1)
		obj.b(1,2,3)
		obj.c(1,2,3,x=1)
		self.assertEquals(obj.a.received_calls, [Call.like(), Call.like(1)])
		self.assertEquals(obj.b.received_calls, [Call.like(1,2,3)])
		self.assertEquals(obj.c.received_calls, [((1,2,3), {'x':1})])

class TestSkeletons(TestCase):
	def test_inheriting_setup_teardown(self):
		class FirstTestCase(TestCase):
			def setUp(self):
				self.x = 1

			def tearDown(self):
				pass

			def test_that_will_fail(self):
				assert 1 == 2

		class SecondTestCase(Skeleton(FirstTestCase)):
			def test_that_ensures_setup_was_run(self):
				assert self.x == 1
				assert hasattr(self, 'tearDown')
		
		suite = unittest.makeSuite(SecondTestCase)
		result = unittest.TestResult()
		suite.run(result)
		assert result.testsRun == 1, repr(result)
		assert result.wasSuccessful(), result.errors[0][1]


