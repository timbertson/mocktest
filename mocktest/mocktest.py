"""
mocktest includes:

 - TestCase: a subclass of unittest.TestCase with the following additions:
	- mock._setup and _teardown are automatically called between tests,
	  ensuring that expectations on mock objects are always checked
	- enhanced versions of assertTrue / False, assertRaises

 - pending annotation: the test case is run but is allowed to fail
 - ignore annotation: the test case is not run
"""

__all__ = (
	'TestCase',
	'pending',
	'ignore',
)

import unittest
import re
import sys
import mock

def _compose(hook, func):
	if hook is None:
		return func
	if hook is None:
		return func
	def run_hook():
		hook()
		func()
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
	reason_str = "" if reason is None else " (%s)" % reason
	def actually_call_it(*args, **kwargs):
		fn_name = function.__name__
		success = False
		try:
			function(*args, **kwargs)
			success = True
			print >> sys.stderr, "%s%s PASSED unexpectedly " % (fn_name, reason_str),
			print "%s%s PASSED unexpectedly " % (fn_name, reason_str),
		except StandardError:
			print >> sys.stderr, "[[[ PENDING ]]]%s ... " % (reason_str,)
			print "[[[ PENDING ]]]%s ... " % (reason_str,)
		if success:
			raise AssertionError, "%s%s PASSED unexpectedly " % (fn_name, reason_str)
	actually_call_it.__name__ = function.__name__
	return actually_call_it

@ParamDecorator
def ignore(function, reason = None):
	reason_str = "" if reason is None else " (%s)" % reason
	def actually_call_it(*args, **kwargs):
		print >> sys.stderr, "[[[ IGNORED ]]]%s ... " % (reason_str,)
		print "[[[ IGNORED ]]]%s ... " % (reason_str,)
	actually_call_it.__name__ = function.__name__
	return actually_call_it

class TestCase(unittest.TestCase):
	pending = globals()['pending']
	pending = globals()['ignore']
	def __init__(self, methodName = 'runTest'):
		super(TestCase, self).__init__(methodName)
		try:
			subclass_setup = self.setUp
		except AttributeError:
			subclass_setup = None
		try:
			subclass_teardown = self.tearDown
		except AttributeError:
			subclass_teardown = None
		
		self.setUp = _compose(self.__setup, subclass_setup)
		self.tearDown = _compose(self.__teardown, subclass_teardown)

	def __setup(self):
		mock._setup()
	
	def __teardown(self):
		mock._teardown()

	def __assert_not_callable(self, expr):
		if callable(expr):
			raise TypeError, "Assertion called on a callable object - this usually means you forgot to call it"

	def assert_(self, expr, desc = None):
		self.__assert_not_callable(expr)
		if desc is None:
			desc = expr
		super(TestCase, self).assert_(expr, desc)
	
	assertTrue = assert_
	failUnless = assert_
	
	def assertFalse(self, expr, desc = None):
		self.__assert_not_callable(expr)
		if desc is None:
			desc = "Expected (%r) to be False" % (expr,)
			super(TestCase, self).assertFalse(expr, desc)
	
	def assertEqual(self, a, b, desc = None):
		"""
		Enhanced assertEquals, prints out more information when
		comparing two dicts or two arrays
		"""
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
		callsig = "%s()" % (callable.__name__,)

		try:
			func()
		except exception, exc:
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
				"expected=%s, actual=%s"\
				% (callsig, exception, exc_info[0]))
		else:
			self.fail("%s did not raise %s" % (callsig, exception))
	failUnlessRaises = assertRaises
	
	def run(self, result=None):
		"""
		this is (mostly) the default implementation of unittest.run
		the only modification is that a `self.FailureException` raised
		in the teardown method counts for a failure
		"""
		if result is None: result = self.defaultTestResult()
		result.startTest(self)
		testMethod = getattr(self, self._testMethodName)
		try:
			try:
				self.setUp()
			except KeyboardInterrupt:
				raise
			except:
				result.addError(self, self._exc_info())
				return

			ok = False
			try:
				testMethod()
				ok = True
			except self.failureException:
				result.addFailure(self, self._exc_info())
			except KeyboardInterrupt:
				raise
			except:
				result.addError(self, self._exc_info())

			try:
				self.tearDown()
			except self.failureException:
				# ignore this failure if the test already failed
				if ok:
					result.addFailure(self, self._exc_info())
					ok = False
			except KeyboardInterrupt:
				raise
			except:
				result.addError(self, self._exc_info())
				ok = False
			if ok: result.addSuccess(self)
		finally:
			result.stopTest(self)

