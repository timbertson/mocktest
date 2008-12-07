# Copyright (C) 2007-2008 Michael Foord
# E-mail: fuzzyman AT voidspace DOT org DOT uk
# http://www.voidspace.org.uk/python/mock.html

from mocktest import pending ##TODO: FIX

import os
import sys
this_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..','..'))
if not this_dir in sys.path:
	sys.path.insert(0, this_dir)

from testcase import TestCase

from mocktest import Mock, sentinel


class MockTest(TestCase):

	def testConstructor(self):
		mock = Mock()
		
		self.assertFalse(mock.called, "called not initialised correctly")
		self.assertEquals(mock.call_count, 0, "call_count not initialised correctly")
		self.assertTrue(isinstance(mock.return_value, Mock), "return_value not initialised correctly")
		
		self.assertEquals(mock.call_args, None, "call_args not initialised correctly")
		self.assertEquals(mock.call_args_list, [], "call_args_list not initialised correctly")
		self.assertEquals(mock.method_calls, [], 
						  "method_calls not initialised correctly")
		
		self.assertNone(mock._parent, "parent not initialised correctly")
		self.assertEquals(mock._children, {}, "children not initialised incorrectly")
		
		
	def testReturnValueInConstructor(self):
		mock = Mock(return_value=None)
		self.assertNone(mock.return_value, "return value in constructor not honoured")
	
	def testSpecHashAsFirstArgInConstructor(self):
		mock = Mock({'foo':'bar', 'x':123})
		self.assertEqual(sorted(mock._children.keys()), ['foo','x'])
		self.assertEqual(mock.foo(), 'bar')
		self.assertEqual(mock.x(), 123)
		self.assertRaises(AttributeError, lambda: mock.blah)
	
	def testSpecArrayAsFirstArgInConstructor(self):
		mock = Mock(['foo', 'x'])
		self.assertEqual(sorted(mock._children.keys()), ['foo','x'])
		self.assert_(isinstance(mock.foo(), Mock))
		self.assert_(isinstance(mock.x(), Mock))
		self.assertRaises(AttributeError, lambda: mock.blah)
	
	def testNameAsFirstArgInConstructor(self):
		mock = Mock("li'l mocky")
		self.assertEqual(mock._name, "li'l mocky")
	
	def testSpecObjectInConstructor(self):
		# should set _spec if the first arg in a constructor is not an array, hash or string
		class MyCls:
			def a(self):
				return "foo"
		mock = Mock(MyCls())
		self.assertEqual(mock._children.keys(), ['a'])
		self.assert_(isinstance(mock.a(), Mock))
		self.assertRaises(Exception, lambda: mock.b)
	
	def testPolymorphFailsWhenConflictingOptionsProvidedInConstructor(self):
		# a hash or array would normally be used as _methods, but it's ambiguous when any of
		# - methods
		# - spec
		# - children
		# are provided as well
		self.assertRaises(TypeError, lambda: Mock({'foo':'bar'}, methods=['a','b']))
		self.assertRaises(TypeError, lambda: Mock({'foo':'bar'}, methods={'a':'b'}))
		self.assertRaises(TypeError, lambda: Mock({'foo':'bar'}, spec=object()))
		self.assertRaises(TypeError, lambda: Mock({'foo':'bar'}, children={}))
		

		self.assertRaises(TypeError, lambda: Mock(['foo','bar'], methods=['a','b']))
		self.assertRaises(TypeError, lambda: Mock(['foo','bar'], methods={'a':'b'}))
		self.assertRaises(TypeError, lambda: Mock(['foo','bar'], spec=object()))
		self.assertRaises(TypeError, lambda: Mock(['foo','bar'], children={}))
	
	def testChildrenMustBeADictOrList(self):
		mock = Mock(children=['foo','bar'])
		self.assertEqual(mock._children.keys(), ['foo','bar'])
		self.assert_(isinstance(mock.foo, Mock))

		self.assertRaises(TypeError, lambda: Mock(children=object()))
		mock = Mock(children={'foo':'bar'})
		self.assertEqual(mock._children, {'foo':'bar'})
		self.assertEqual(mock.foo, 'bar')
	
	def testChildrenAreTheOnlyChildrenAllowed(self):
		# we can't access other children when it's given in the constructor
		mock = Mock(children={'foo':'bar'})
		self.assertRaises(AttributeError, lambda: mock.new_child)
	
	def testChildrenCanBeAddedLater(self):
		mock = Mock()
		mock.foo = 1
		mock.bar = 2
		self.assertEqual(mock._children, {'foo':1, 'bar':2})
	
	def testChildrenCantBeAddedLaterIfTheyAreGivenInInit(self):
		mock = Mock(children={'foo':1, 'bar':2})
		def set_child():
			mock.child_a = 1
			print "set child_a"
		self.assertRaises(AttributeError, set_child)
	
	def testSideEffect(self):
		mock = Mock()
		def effect():
			raise SystemError('kablooie')
		mock._side_effect = effect
		
		self.assertRaises(SystemError, mock)
		self.assertTrue(mock.called, "call not recorded")
		
		results = []
		def effect(n):
			results.append('call %s' % (n,))
		mock._side_effect = effect
		
		mock(1)
		self.assertEquals(results, ['call 1'])
		mock(2)
		self.assertEquals(results, ['call 1','call 2'])

		mock = Mock(action=sentinel.SideEffect)
		self.assertEquals(mock._side_effect, sentinel.SideEffect,
						  "side effect in constructor not used")

	def testSideEffectReturnUsedWhenReturnValueNotSpecified(self):
		def return_foo():
			return "foo"
		mock = Mock(action=return_foo)
		self.assertEqual(mock(), 'foo',
		                "side effect return value not used")

	def testSideEffectReturnNotUsedWhenReturnValueSpecified(self):
		def return_foo():
			return "foo"
		mock = Mock(action=return_foo, return_value='bar')
		self.assertEqual(mock(), 'bar',
		                 "return value not used")
	
	def testReset(self):
		parent = Mock()
		methods = ["something"]
		mock = Mock(name="child", parent=parent, methods=methods)
		# mock(sentinel.Something, something=sentinel.SomethingElse)
		something = mock.something
		
		mock.something()
		mock._side_effect = sentinel.SideEffect
		return_value = mock.return_value
		return_value()
		
		mock.reset()
		
		self.assertEquals(mock._name, "child", "name incorrectly reset")
		self.assertEquals(mock._parent, parent, "parent incorrectly reset")
		
		self.assertFalse(mock.called, "called not reset")
		self.assertEquals(mock.call_count, 0, "call_count not reset")
		self.assertEquals(mock.call_args, None, "call_args not reset")
		self.assertEquals(mock.call_args_list, [], "call_args_list not reset")
		self.assertEquals(mock.method_calls, [], 
						  "method_calls not initialised correctly")
		
		self.assertEquals(mock._side_effect, sentinel.SideEffect,
						  "side_effect incorrectly reset")
		self.assertEquals(mock.return_value, return_value,
						  "return_value incorrectly reset")
		self.assertFalse(return_value.called, "return value mock not reset")
		self.assertEquals(mock._children, {'something': something}, 
						  "children reset incorrectly")
		self.assertEquals(mock.something, something,
						  "children incorrectly cleared")
		self.assertFalse(mock.something.called, "child not reset")
		
	
	def testResetOnlyPropagatesToMockChildren(self):
		a = Mock()
		mock = Mock(children={'a':a, 'b':'string'})
		mock.a('foo')
		self.assertTrue(mock.a.called)
		mock.reset()
		self.assertFalse(mock.a.called)
		# string doesn't have a reset method, so it can't have been called
	
	def testCall(self):
		mock = Mock()
		self.assertTrue(isinstance(mock.return_value, Mock), "Default return_value should be a Mock")
		
		result = mock()
		self.assertEquals(mock(), result, "different result from consecutive calls")
		mock.reset()
		
		ret_val = mock(sentinel.Arg)
		self.assertTrue(mock.called, "called not set")
		self.assertEquals(mock.call_count, 1, "call_count incoreect")
		self.assertEquals(mock.call_args, ((sentinel.Arg,), {}), "call_args not set")
		self.assertEquals(mock.call_args_list, [((sentinel.Arg,), {})], "call_args_list not initialised correctly")

		mock.return_value = sentinel.ReturnValue
		ret_val = mock(sentinel.Arg, key=sentinel.KeyArg)
		self.assertEquals(ret_val, sentinel.ReturnValue, "incorrect return value")
						  
		self.assertEquals(mock.call_count, 2, "call_count incorrect")
		self.assertEquals(mock.call_args, ((sentinel.Arg,), {'key': sentinel.KeyArg}), "call_args not set")
		self.assertEquals(mock.call_args_list, [((sentinel.Arg,), {}), ((sentinel.Arg,), {'key': sentinel.KeyArg})], "call_args_list not set")
		

	def testAttributeAccessReturnsMocks(self):
		mock = Mock()
		something = mock.something
		self.assertTrue(isinstance(something, Mock), "attribute isn't a mock")
		self.assertEquals(mock.something, something, "different attributes returned for same name")
		
		# Usage example
		mock = Mock()
		mock.something.return_value = 3
		
		self.assertEquals(mock.something(), 3, "method returned wrong value")
		self.assertTrue(mock.something.called, "method didn't record being called")
		

	def testAttributesHaveNameAndParentSet(self):
		mock = Mock()
		something = mock.something
		
		self.assertEquals(something._name, "something", "attribute name not set correctly")
		self.assertEquals(something._parent, mock, "attribute parent not set correctly")
	
	def testChildrenHaveParentSet(self):
		self.assert_(Mock(children=['foo']).foo._parent is not None)
	
	def testMethodsHaveParentSet(self):
		mock = Mock(methods=['foo'])
		self.assert_(mock.foo._parent is mock)

		mock = Mock(methods={'foo':'bar'})
		self.assert_(mock.foo._parent is mock)

	def testMethodCallsRecorded(self):
		mock = Mock()
		mock.something(3, fish=None)
		mock.something_else.something(6, cake=sentinel.Cake)
		
		self.assertEquals(mock.something_else.method_calls,
						  [("something", (6,), {'cake': sentinel.Cake})])
		self.assertEquals(mock.method_calls,
						  [("something", (3,), {'fish': None}),
						   ("something_else.something", (6,), {'cake': sentinel.Cake})],
						  "method calls not recorded correctly")
		
		
	def testOnlyAllowedMethodsExist(self):
		methods = ["something"]
		mock = Mock(methods=methods)
		
		# this should be allowed
		mock.something
		self.assertRaisesWithMessage(AttributeError, 
									 "object has no attribute 'something_else'",
									 lambda: mock.something_else)

	
	def testFromSpec(self):
		class Something(object):
			x = 3
			__something__ = None
			def y(self):
				pass
		
		def testAttributes(mock):
			# should work
			mock.x
			mock.y
			self.assertRaisesWithMessage(AttributeError, 
										 "object has no attribute 'z'",
										 lambda: mock.z)
			self.assertRaisesWithMessage(AttributeError, 
										 "object has no attribute '__something__'",
										 lambda: mock.__something__)
			
		testAttributes(Mock(spec=Something))
		testAttributes(Mock(spec=Something()))
		
