from mocktest import pending ##TODO: FIX

import os
import sys
this_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..'))
if not this_dir in sys.path:
	sys.path.insert(0, this_dir)

from mocktest import TestCase

from mocktest import mock_on, raw_mock, mock_wrapper


class MockTest(TestCase):

	def testConstructor(self):
		mock_ = raw_mock()
		wrapper = mock_wrapper(mock_)
		self.assertFalse(wrapper.called, "called not initialised correctly")
		self.assertTrue(wrapper.called.exactly(0), "call_count not initialised correctly")

		self.assertEquals(wrapper.call_list, [])
		self.assertEquals(wrapper._children, {})
		
		self.assertNotEquals(wrapper.return_value.__class__, object.__class__)
		retval = mock_()
		self.assertEqual(retval.__class__, raw_mock().__class__)
		self.assertEqual(mock_wrapper(retval).name, 'return value for (unnamed mock)')
		self.assertEquals(wrapper.return_value.__class__, raw_mock().__class__)
		
	# def testReturnValueInConstructor(self):
	# 	mock = mock(return_value=None)
	# 	self.assertNone(mock.return_value, "return value in constructor not honoured")
	# 
	# def testSpecHashAsFirstArgInConstructor(self):
	# 	mock = mock({'foo':'bar', 'x':123})
	# 	self.assertEqual(sorted(mock._children.keys()), ['foo','x'])
	# 	self.assertEqual(mock.foo(), 'bar')
	# 	self.assertEqual(mock.x(), 123)
	# 	self.assertRaises(AttributeError, lambda: mock.blah)
	# 
	# def testSpecArrayAsFirstArgInConstructor(self):
	# 	mock = mock(['foo', 'x'])
	# 	self.assertEqual(sorted(mock._children.keys()), ['foo','x'])
	# 	self.assert_(isinstance(mock.foo(), Mock))
	# 	self.assert_(isinstance(mock.x(), Mock))
	# 	self.assertRaises(AttributeError, lambda: mock.blah)
	# 
	# def testNameAsFirstArgInConstructor(self):
	# 	mock = mock("li'l mocky")
	# 	self.assertEqual(mock._name, "li'l mocky")
	# 
	# def testSpecObjectInConstructor(self):
	# 	# should set _spec if the first arg in a constructor is not an array, dict or string
	# 	class MyCls:
	# 		def a(self):
	# 			return "foo"
	# 	mock = mock(MyCls())
	# 	self.assertEqual(mock._children.keys(), ['a'])
	# 	self.assert_(isinstance(mock.a(), Mock))
	# 	self.assertRaises(Exception, lambda: mock.b)
	# 
	# def testPolymorphFailsWhenConflictingOptionsProvidedInConstructor(self):
	# 	# methods vs methods
	# 	self.assertRaises(ValueError, lambda: mock({'foo':'bar'}, methods=['a','b']))
	# 	
	# 	# spec vs methods / children
	# 	self.assertRaises(ValueError, lambda: mock(object(), methods={'a':'b'}))
	# 	self.assertRaises(ValueError, lambda: mock(object(), children={'a':'b'}))
	# 	
	# 	# methods vs spec
	# 	self.assertRaises(ValueError, lambda: mock({'foo':'bar'}, spec=object()))
	# 	
	# 	#name vs name
	# 	self.assertRaises(ValueError, lambda: mock("name", name="bar"))
	# 
	# def testChildrenMustBeADictOrList(self):
	# 	mock = mock(children=['foo','bar'])
	# 	self.assertEqual(mock._children.keys(), ['foo','bar'])
	# 	self.assert_(isinstance(mock.foo, Mock))
	# 
	# 	self.assertRaises(TypeError, lambda: mock(children=object()))
	# 	mock = mock(children={'foo':'bar'})
	# 	self.assertEqual(mock._children, {'foo':'bar'})
	# 	self.assertEqual(mock.foo, 'bar')
	# 
	# def testChildrenAreTheOnlyChildrenAllowed(self):
	# 	# we can't access other children when it's given in the constructor
	# 	mock = mock(children={'foo':'bar'})
	# 	self.assertRaises(AttributeError, lambda: mock.new_child)
	# 
	# def testChildrenCanBeAddedLater(self):
	# 	mock = mock()
	# 	mock.foo = 1
	# 	mock.bar = 2
	# 	self.assertEqual(mock._children, {'foo':1, 'bar':2})
	# 
	# def testChildrenCantBeAddedLaterIfTheyAreGivenInInit(self):
	# 	mock = mock(children={'foo':1, 'bar':2})
	# 	def set_child():
	# 		mock.child_a = 1
	# 		print "set child_a"
	# 	self.assertRaises(AttributeError, set_child)
	# 
	# def testFrozenCanBeOverriddenInConstructor(self):
	# 	mock = mock(children={'foo':1, 'bar':2},frozen=False)
	# 	mock.child_a = 'baz'
	# 	self.assertEqual(mock.child_a, 'baz')
	# 
	# 	mock = mock(frozen=True)
	# 	def set_child():
	# 		mock.child_a = 1
	# 		print "set child_a"
	# 	self.assertRaises(AttributeError, set_child)
	# 
	# def testChildrenAndMethodsCanCoexist(self):
	# 	# both as dicts
	# 	mock = mock(children={'a':'a'}, methods={'b':'b'})
	# 	self.assertEqual(mock.a, 'a')
	# 	self.assertEqual(mock.b(), 'b')
	# 
	# 	mock = mock({'b':'b'}, children={'a':'a'})
	# 	self.assertEqual(mock.a, 'a')
	# 	self.assertEqual(mock.b(), 'b')
	# 	
	# 	# both as arrays
	# 	mock = mock(['b'], children=['a'])
	# 	self.assertEqual(sorted(mock._children.keys()), ['a','b'])
	# 	
	# 	# children as dict, methods as array
	# 	mock = mock(['b'], children={'a':'a'})
	# 	self.assertEqual(mock.a, 'a')
	# 	mock.b() # should not raise
	# 	
	# 	# children as array, method as dict
	# 	mock = mock({'b':'b'}, children=['a'])
	# 	mock.a, # should not raise
	# 	self.assertEqual(mock.b(), 'b')
	# 
	# def testChildrenAndMethodsNeedToBeUnique(self):
	# 	self.assertRaises(ValueError, lambda: mock(children=['a'],      methods=['a']))
	# 	self.assertRaises(ValueError, lambda: mock(children={'a':None}, methods={'a':None}))
	# 	self.assertRaises(ValueError, lambda: mock(children=['a'],      methods={'a':None}))
	# 	self.assertRaises(ValueError, lambda: mock(children={'a':None}, methods=['a']))
	# 
	# def testSideEffect(self):
	# 	mock = mock()
	# 	def effect():
	# 		raise SystemError('kablooie')
	# 	mock._side_effect = effect
	# 	
	# 	self.assertRaises(SystemError, mock)
	# 	self.assertTrue(mock.called, "call not recorded")
	# 	
	# 	results = []
	# 	def effect(n):
	# 		results.append('call %s' % (n,))
	# 	mock._side_effect = effect
	# 	
	# 	mock(1)
	# 	self.assertEquals(results, ['call 1'])
	# 	mock(2)
	# 	self.assertEquals(results, ['call 1','call 2'])
	# 
	# 	mock = mock(action=sentinel.SideEffect)
	# 	self.assertEquals(mock._side_effect, sentinel.SideEffect,
	# 					  "side effect in constructor not used")
	# 
	# def testSideEffectReturnUsedWhenReturnValueNotSpecified(self):
	# 	def return_foo():
	# 		return "foo"
	# 	mock = mock(action=return_foo)
	# 	self.assertEqual(mock(), 'foo')
	# 
	# def testSideEffectCanChangeMockReturnValue(self):
	# 	mock = mock()
	# 	def modify_it():
	# 		mock.return_value = 'foo'
	# 	mock._side_effect = modify_it
	# 	self.assertEqual(mock(), 'foo')
	# 
	# def testSideEffectReturnValUsedEvenWhenItIsNone(self):
	# 	self.assertEqual(mock(action=lambda: None)(), None)
	# 
	# def testDefaultReturnShouldBeAmock(self):
	# 	self.assertTrue(isinstance(mock()(), Mock))
	# 
	# def testSideEffectReturnNotUsedWhenReturnValueSpecified(self):
	# 	def return_foo():
	# 		return "foo"
	# 	mock = mock(action=return_foo, return_value='bar')
	# 	self.assertEqual(mock(), 'bar',
	# 	                 "return value not used")
	# 
	# def testReset(self):
	# 	parent = mock()
	# 	methods = ["something"]
	# 	mock = mock(name="child", parent=parent, methods=methods)
	# 	# mock(sentinel.Something, something=sentinel.SomethingElse)
	# 	something = mock.something
	# 	
	# 	mock.something()
	# 	mock._side_effect = sentinel.SideEffect
	# 	return_value = mock.return_value
	# 	return_value()
	# 	
	# 	mock.reset()
	# 	
	# 	self.assertEquals(mock._name, "child", "name incorrectly reset")
	# 	self.assertEquals(mock._parent, parent, "parent incorrectly reset")
	# 	
	# 	self.assertFalse(mock.called, "called not reset")
	# 	self.assertEquals(mock.call_count, 0, "call_count not reset")
	# 	self.assertEquals(mock.call_args, None, "call_args not reset")
	# 	self.assertEquals(mock.call_args_list, [], "call_args_list not reset")
	# 	self.assertEquals(mock.method_calls, [], 
	# 					  "method_calls not initialised correctly")
	# 	
	# 	self.assertEquals(mock._side_effect, sentinel.SideEffect,
	# 					  "side_effect incorrectly reset")
	# 	self.assertEquals(mock.return_value, return_value,
	# 					  "return_value incorrectly reset")
	# 	self.assertFalse(return_value.called, "return value mock not reset")
	# 	self.assertEquals(mock._children.keys(), ['something'], 
	# 					  "children reset incorrectly")
	# 	self.assertNotEquals(mock.something, something,
	# 					  "children was not cleared")
	# 	self.assertFalse(mock.something.called, "child not reset")
	# 
	# def testResetRemovesAddedChildren(self):
	# 	mock = mock()
	# 	mock.a = 1
	# 	mock.reset()
	# 	self.assertTrue(mock._children == {})
	# 
	# def testResetOnlyPropagatesToMockChildren(self):
	# 	a = mock()
	# 	mock = mock(children={'a':a, 'b':'string'})
	# 	mock.a('foo')
	# 	self.assertTrue(mock.a.called)
	# 	mock.reset()
	# 	self.assertFalse(mock.a.called)
	# 	# string doesn't have a reset method, so it can't have been called
	# 
	# def testCall(self):
	# 	mock = mock()
	# 	self.assertTrue(isinstance(mock.return_value, Mock), "Default return_value should be a Mock")
	# 	
	# 	result = mock()
	# 	self.assertEquals(mock(), result, "different result from consecutive calls")
	# 	mock.reset()
	# 	
	# 	ret_val = mock(sentinel.Arg)
	# 	self.assertTrue(mock.called, "called not set")
	# 	self.assertEquals(mock.call_count, 1, "call_count incoreect")
	# 	self.assertEquals(mock.call_args, ((sentinel.Arg,), {}), "call_args not set")
	# 	self.assertEquals(mock.call_args_list, [((sentinel.Arg,), {})], "call_args_list not initialised correctly")
	# 
	# 	mock.return_value = sentinel.ReturnValue
	# 	ret_val = mock(sentinel.Arg, key=sentinel.KeyArg)
	# 	self.assertEquals(ret_val, sentinel.ReturnValue, "incorrect return value")
	# 					  
	# 	self.assertEquals(mock.call_count, 2, "call_count incorrect")
	# 	self.assertEquals(mock.call_args, ((sentinel.Arg,), {'key': sentinel.KeyArg}), "call_args not set")
	# 	self.assertEquals(mock.call_args_list, [((sentinel.Arg,), {}), ((sentinel.Arg,), {'key': sentinel.KeyArg})], "call_args_list not set")
	# 	
	# 
	# def testAttributeAccessReturnsMocks(self):
	# 	mock = mock()
	# 	something = mock.something
	# 	self.assertTrue(isinstance(something, Mock), "attribute isn't a mock")
	# 	self.assertEquals(mock.something, something, "different attributes returned for same name")
	# 	
	# 	# Usage example
	# 	mock = mock()
	# 	mock.something.return_value = 3
	# 	
	# 	self.assertEquals(mock.something(), 3, "method returned wrong value")
	# 	self.assertTrue(mock.something.called, "method didn't record being called")
	# 	
	# 
	# def testAttributesHaveNameAndParentSet(self):
	# 	mock = mock()
	# 	something = mock.something
	# 	
	# 	self.assertEquals(something._name, "something", "attribute name not set correctly")
	# 	self.assertEquals(something._parent, mock, "attribute parent not set correctly")
	# 
	# def testChildrenHaveParentSet(self):
	# 	self.assert_(mock(children=['foo']).foo._parent is not None)
	# 
	# def testMethodsHaveParentSet(self):
	# 	mock = mock(methods=['foo'])
	# 	self.assert_(mock.foo._parent is mock)
	# 
	# 	mock = mock(methods={'foo':'bar'})
	# 	self.assert_(mock.foo._parent is mock)
	# 
	# def testMethodCallsRecorded(self):
	# 	mock = mock()
	# 	mock.something(3, fish=None)
	# 	mock.something_else.something(6, cake=sentinel.Cake)
	# 	
	# 	self.assertEquals(mock.something_else.method_calls,
	# 					  [("something", (6,), {'cake': sentinel.Cake})])
	# 	self.assertEquals(mock.method_calls,
	# 					  [("something", (3,), {'fish': None}),
	# 					   ("something_else.something", (6,), {'cake': sentinel.Cake})],
	# 					  "method calls not recorded correctly")
	# 	
	# 	
	# def testOnlyAllowedMethodsExist(self):
	# 	methods = ["something"]
	# 	mock = mock(methods=methods)
	# 	
	# 	# this should be allowed
	# 	mock.something
	# 	self.assertRaisesWithMessage(AttributeError, 
	# 								 "object has no attribute 'something_else'",
	# 								 lambda: mock.something_else)
	# 
	# 
	# def testFromSpec(self):
	# 	class Something(object):
	# 		x = 3
	# 		__something__ = None
	# 		def y(self):
	# 			pass
	# 	
	# 	def testAttributes(mock):
	# 		# should work
	# 		mock.x
	# 		mock.y
	# 		self.assertRaisesWithMessage(AttributeError, 
	# 									 "object has no attribute 'z'",
	# 									 lambda: mock.z)
	# 		self.assertRaisesWithMessage(AttributeError, 
	# 									 "object has no attribute '__something__'",
	# 									 lambda: mock.__something__)
	# 		
	# 	testAttributes(mock(spec=Something))
	# 	testAttributes(mock(spec=Something()))
