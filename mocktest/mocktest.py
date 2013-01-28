from __future__ import absolute_import
from __future__ import print_function
"""
Test Infrastructure
-------------------
"""
__all__ = (
	'TestCase',
	'pending',
	'ignore',
	'Skeleton',
)

import unittest
import re
import sys
from . import core
from .mocking import _special_method
import types
from functools import wraps
import collections

__unittest = True

# set the SkipTest exception class
try:
	from unittest import SkipTest
except ImportError:
	SkipTest = None
	

def subclass_only(parent, method_names, safe_superclasses=()):
	def filter_parent_class(cls):
		if cls in safe_superclasses:
			return cls
		return subclass_only(cls, method_names, safe_superclasses)

	filtered_parents = tuple(map(filter_parent_class, parent.__bases__))
	cls = type("%s::Skeleton" % (parent.__name__,), filtered_parents, {})

	safe_method = lambda name: name in method_names or name.startswith('_')

	def copy_attr(name):
		attr = getattr(parent, name)
		if _special_method(name): return
		if isinstance(attr, types.MethodType):
			#python2 only:
			if not safe_method(name): return
			# make a copy of the method that's tied to the destination class instead of the source
			attr = types.MethodType(attr.im_func, None, cls)
		elif callable(attr):
			if not safe_method(name): return
		setattr(cls, name, attr)

	for attr in dir(parent): copy_attr(attr)
	return cls

def Skeleton(cls):
	"""
	Generate a subclass inheriting only private methods and setUp/tearDown, for the purpose
	of inheriting test setup but not any actual test implementations
	"""
	from . import mocktest
	return subclass_only(cls, ('setUp', 'tearDown'), safe_superclasses=(unittest.TestCase, object, mocktest.TestCase))

def _compose(hook, func, onerror=None):
	def run_hook():
		try:
			if hook is not None: hook()
			if func is not None: func()
		except Exception:
			try:
				if onerror is not None: onerror()
			except Exception: pass
			raise

	run_hook.__name__ = func.__name__
	return run_hook

class ParamDecorator(object):
	## use to decorate a decorator, allowing it to optionally take arguments
	def __init__(self, decorator_function):
		self.func = decorator_function

	def __call__(self, *args, **kwargs):
		if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
			# we're being called without paramaters
			# (just the decorated function)
			return self.func(args[0])
		return self.decorate_with(args, kwargs)

	def decorate_with(self, args, kwargs):
		def decorator(callable_):
			return self.func(callable_, *args, **kwargs)
		return decorator

@ParamDecorator
def pending(function, reason = None):
	"""
	A decorator for pending tests.
	Note that pending tests are always run, and will cause a failure if they succeed (a pending test is assumed to be in a failing state.
	To not run a test at all. use :py:func:mocktest.ignore:
	"""
	reason_str = "" if reason is None else " (%s)" % reason
	@wraps(function)
	def actually_call_it(*args, **kwargs):
		fn_name = function.__name__
		success = False
		try:
			function(*args, **kwargs)
			success = True
		except Exception:
			if reason_str:
				print("[[[ PENDING ]]]%s ... " % (reason_str,), file=sys.stderr)
			if SkipTest is not None:
				raise SkipTest(reason_str)
		if success:
			raise AssertionError("%s%s PASSED unexpectedly " % (fn_name, reason_str))
	return actually_call_it

@ParamDecorator
def ignore(function, reason = None):
	"""a decorator for tests that should not be run"""
	reason_str = "" if reason is None else " (%s)" % reason
	@wraps(function)
	def actually_call_it(*args, **kwargs):
		print("[[[ IGNORED ]]]%s ... " % (reason_str,), file=sys.stderr)
	return actually_call_it

class TestCase(unittest.TestCase):
	"""
	A subclass of unittest.TestCase with the following additions:

	- Automatically calls MockTransaction.__enter__ and __exit__ in \
		order to reset mock state and verify expectations upon test \
		completion.
	- enhanced versions of assertTrue / False, assertRaises
	- assertMatches
	"""
	pending = globals()['pending']
	ignore = globals()['ignore']
	def __init__(self, methodName = 'runTest'):
		super(TestCase, self).__init__(methodName)
		subclass_setup = getattr(self, 'setUp', None)
		subclass_teardown = getattr(self, 'tearDown', None)
		
		self.setUp = _compose(self.__setup, subclass_setup, onerror=self.__teardown)
		self.tearDown = _compose(self.__teardown, subclass_teardown)

	def __setup(self):
		core._setup()
	
	def __teardown(self):
		core._teardown()

	def assert_(self, expr, desc = None):
		if desc is None:
			desc = "expected (%r) to be True" % (expr,)
		super(TestCase, self).assert_(expr, desc)
	
	assertTrue = assert_
	failUnless = assert_
	
	def assertFalse(self, expr, desc = None):
		if desc is None:
			desc = "Expected (%r) to be False" % (expr,)
			super(TestCase, self).assertFalse(expr, desc)
	
	def assertEqual(self, a, b, desc = None):
		if a == b:
			return
		if desc is not None:
			return super(TestCase, self).assertEqual(a, b, desc)
		if (isinstance(a, list) and isinstance(b, list)) or (isinstance(a, tuple) and isinstance(b, tuple)):
			self.__assertEqual_array(a, b)
		elif isinstance(a, dict) and isinstance(b, dict):
			self.__assertEqual_dict(a, b)
		super(TestCase, self).assertEqual(a, b, desc)
	assertEquals = assertEqual
	
	def __assertEqual_dict(self, a, b):
		akeys, bkeys = sorted(a.keys()), sorted(b.keys())
		if not akeys == bkeys:
			raise AssertionError("%r != %r\ndict keys differ: %r != %r" % (a, b, akeys, bkeys))
		a_and_not_b = self.__dict_differences_btwn(a, b)
		b_and_not_a = self.__dict_differences_btwn(b, a)
		raise AssertionError("%r != %r\ndifference between dicts: %r vs %r" % (a, b, a_and_not_b, b_and_not_a))
	
	def __assertEqual_array(self, a, b):
		la, lb = len(a), len(b)
		longest = max(la, lb)
		def _raise(index, adesc, bdesc):
			raise AssertionError("%r != %r\nlists differ at index %s:\n\t%s != %s" % (a, b, index, adesc, bdesc))
		
		if la != lb:
			# length mismatch
			nomore = '(no more values)'
			if la < lb:
				index = la
				a_desc = nomore
				b_desc = b[index]
			else:
				index=lb
				a_desc = a[index]
				b_desc = nomore
			_raise(index, a_desc, b_desc)
			
		for i in range(0, longest):
			same = False
			if a[i] != b[i]:
				_raise(i, repr(a[i]), repr(b[i]))
			
		akeys, bkeys = sorted(a.keys()), sorted(b.keys())
		if not akeys == bkeys:
			raise AssertionError("%r != %r\ndict keys differ: %r != %r" % (a, b, akeys, bkeys))
		a_and_not_b = self.__dict_differences_btwn(a, b)
		b_and_not_a = self.__dict_differences_btwn(b, a)
	
	def __dict_differences_btwn(self, a, b):
		in_a_not_b = {}
		for k,v in a.items():
			same = False
			try:
				same = b[k] == v
			except KeyError:
				pass
			if not same:
				in_a_not_b[k] = v
		return in_a_not_b
	
	def assertRaises(self, exception, func, message = None, args = None, kwargs = None, matching=None):
		"""
		Enhanced assertRaises, able to:
		 - check arguments (args)
		 - check keyword arguments (kwargs)
		 - match a regular expression on the resulting expression message (matching)
		 - compare message strings (message)
		"""
		callsig = "%s()" % (func.__name__,)

		try:
			func()
		except exception as exc:
			if args is not None:
				self.failIf(exc.args != args,
					"%s raised %s with unexpected args: "\
					"expected=%r, actual=%r"\
					% (callsig, exc.__class__, args, exc.args))
			if kwargs is not None:
				self.failIf(exc.kwargs != kwargs,
					"%s raised %s with unexpected keyword args: "\
					"expected=%r, actual=%r"\
					% (callsig, exc.__class__, kwargs, exc.kwargs))
			if matching is not None:
				pattern = re.compile(matching)
				self.failUnless(pattern.search(str(exc)),
					"%s raised %s, but the exception "\
					"does not match '%s': %r"\
					% (callsig, exc.__class__, matching, str(exc)))
			if message is not None:
				self.failUnless(str(exc) == message,
					"%s raised %s, but the exception "\
					"does not equal \"%s\": %r"\
					% (callsig, exc.__class__, message, str(exc)))
		except:
			exc_info = sys.exc_info()
			self.fail("%s raised an unexpected exception type: "\
				"expected=%s, actual=%s (%s)"\
				% (callsig, exception, exc_info[0], exc_info[1]))
		else:
			self.fail("%s did not raise an exception" % (callsig,))
	failUnlessRaises = assertRaises

	def assertMatches(self, matcher, val, message=None):
		"""
		Fail the test if an object does not satisfy the given matcher.
		"""
		if not matcher.matches(val):
			fail_msg = "expected:\n%r\nto be %s" % (val, matcher.desc())
			if message is not None:
				fail_msg += "\n(%s)" % (message,)
			self.fail(fail_msg)
	
	def run(self, result=None):
		"""
		This is (mostly) the default implementation of unittest.run
		the only modification is that a `self.FailureException` raised
		in the teardown method counts for a failure
		"""
		if result is None: result = self.defaultTestResult()
		addError = result.addError
		if not getattr(addError, '_mocktest_patched', False):
			def patchedAddError(*a, **k):
				# be very cautious, as addError could change, and we've no good reason to break it.
				if len(a) == 2 and len(a[1]) == 3:
					type = a[1][0]
					if issubclass(type, self.failureException):
						# call it a failure instead of an error
						return result.addFailure(*a, **k)
				else:
					import warnings
					warnings.warn("unexpected argument set: (*%r, **%r)" % (a, k))
				return addError(*a, **k)
			patchedAddError._mocktest_patched = True
			result.addError = patchedAddError
		return super(TestCase, self).run(result)

