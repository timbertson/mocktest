from mocktest import *
from unittest import TestCase
import unittest
from functools import wraps

def run_func(self, func):
	from mocktest import TestCase as MockTestCase
	class AnonymousTestCase(MockTestCase):
		def runTest(self):
			func(self)
	suite = unittest.TestSuite(tests=(AnonymousTestCase(),))
	result = unittest.TestResult()
	suite.run(result)
	assert result.testsRun == 1
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
	
	@passing
	def test_calling_with_incorrect_number_of_args_should_raise_TypeError(self):
		when(obj).meth().then_return(True)
		assert obj.meth() == True
		self.assertRaises(TypeError, lambda: obj.meth2(1))

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
		replace(obj).foo = 'replaced'
		replace(obj).grand.child = True
		assert obj.foo == 'replaced'
		assert obj.grand.child
		core._teardown()
		core._setup()
		assert obj.foo == 'original', obj.foo
		self.assertRaises(AttributeError, lambda: obj.grand)


class TestMockingSpecialMethods(TestCase):
	@passing
	@pending
	def test_mocking_call(self):
		self.assertRaises(TypeError, lambda: obj())
		when(obj)(2).then_return('two')
		when(obj).__call__(3).then_return('three')
		assert obj(2) == 'two'
		assert obj(3) == 'three'
	
	@passing
	@pending
	def test_mocking_length(self):
		when(obj).__len__().then_return(2)
		assert len(obj) == 2
	
	@passing
	def test_mocking_special_methods_on_class_directly(self):
		when(Object).__len__.then_return(5)
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
		stub(obj).meth()
		stub(obj).meth(1).and_return(1)
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
		self.assertRaises(TypeError, obj.foo('str'))
		self.assertRaises(TypeError, obj.foo(int))
		self.assertRaises(TypeError, obj.foo(1,2))

	@passing
	def test_multiple_any_instance(self):
		when(obj).foo(*Any(int)).then_return(True)
		assert obj.foo(1)
		assert obj.foo(2)
		assert obj.foo()
		assert obj.foo(1,2,3,4)
		self.assertRaises(TypeError, obj.foo('str'))
		self.assertRaises(TypeError, obj.foo(int))

	@passing
	def test_multiple_any_instance_after_normal_args(self):
		when(obj).foo(Any(str), *Any(int)).then_return(True)
		assert obj.foo('str')
		assert obj.foo('string', 2)
		assert obj.foo(1,2,3,4)
		self.assertRaises(TypeError, obj.foo())
		self.assertRaises(TypeError, obj.foo(int))

class TestMockCreation(TestCase):
	@passing
	def test_creation_methods_kwargs(self):
		obj = mock('foo').with_methods(x=1, y=2)
		assert obj.x() == 1
		assert obj.x(1,2,3) == 1
		assert obj.y() == 2

	@passing
	def test_creation_children_kwargs(self):
		obj = mock('foo').with_children(x=1, y=2)
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
		obj = mock('foo').copying(base).with_children(x=1)
		assert obj.three_args(1,2,3) == None
		assert obj._private() == None
		assert obj() == None
		assert obj.x == 1
		self.assertRaises(TypeError, lambda: obj.three_args())
		self.assertRaises(TypeError, lambda: obj.no_such_method())
	
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
		obj = stub('foo')
		obj.a()
		obj.b(1,2,3)
		obj.c(1,2,3,x=1)
		assert obj.stubbed_calls == [
			('a', (), {}),
			('b', (1,2,3), {}),
			('c', (1,2,3), {'x':1}),
		]

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


