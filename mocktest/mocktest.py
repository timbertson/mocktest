__all__ = (
	'TestCase',
	'pending',
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


def pending(function_or_reason):
	def wrap_func(func, reason = None):
		reason_str = "" if reason is None else " (%s)" % reason
		def actually_call_it(*args, **kwargs):
			fn_name = func.__name__
			success = False
			try:
				func(*args, **kwargs)
				success = True
				print >> sys.stderr, "%s%s PASSED unexpectedly " % (fn_name, reason_str),
				print "%s%s PASSED unexpectedly " % (fn_name, reason_str),
			except StandardError:
				print >> sys.stderr, "[[[ PENDING ]]]%s ... " % (reason_str,)
				print "[[[ PENDING ]]]%s ... " % (reason_str,)
			if success:
				print "RAISING!"
				raise AssertionError, "%s%s PASSED unexpectedly " % (fn_name, reason_str)
		actually_call_it.__name__ = func.__name__
		return actually_call_it
	
	if callable(function_or_reason):
		# we're decorating a function
		return wrap_func(function_or_reason)
	else:
		# we've been given a description - return a decorator
		def decorator(func):
			return wrap_func(func, function_or_reason)
		return decorator

def ignore(func):
	return lambda self: None

class TestCase(unittest.TestCase):
	def __init__(self, methodName = 'runTest'):
		# unittest.TestCase.__init__(self, methodName)
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
		mock.setup()
	
	def __teardown(self):
		mock.teardown()

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
	
	def assertRaises(self, exception, func, message = None, args = None, matching=None):
		"""
		Enhanced assertRaises, able to:
		 - check arguments (args)
		 - match a regular expression on the resulting expression message (matching)
		 - compare message strings (message)
		"""
		callsig = "%s()" % (callable.__name__,)

		try:
			print "calling %s " % callsig
			func()
			print "NO ERRORS!"
		except exception, exc:
			print repr(exc)
			if args is not None:
				self.failIf(exc.args != args,
					"%s raised %s with unexpected args: "\
					"expected=%r, actual=%r"\
					% (callsig, exc.__class__, args, exc.args))
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
			print exc_info
			self.fail("%s raised an unexpected exception type: "\
				"expected=%s, actual=%s"\
				% (callsig, exception, exc_info[0]))
		else:
			self.fail("%s did not raise %s" % (callsig, exception))
	failUnlessRaises = assertRaises

