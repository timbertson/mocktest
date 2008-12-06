__all__ = (
	'TestCase',
	'pending',
)

import unittest
import re
import sys
from mock import Mock

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
			try:
				func(*args, **kwargs)
				print >> sys.stderr, "%s%s PASSED unexpectedly " % (fn_name, reason_str),
				print "%s%s PASSED unexpectedly " % (fn_name, reason_str),
			except:
				print >> sys.stderr, "[[[ PENDING ]]]%s ... " % (reason_str,),
				print "[[[ PENDING ]]]%s ... " % (reason_str,),
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
		Mock._setup()
	
	def __teardown(self):
		Mock._teardown()

	# a helper to make mock assertions more traceable
	# (the same does not make sense for assertFalse)
	def assert_(self, expr, desc = None):
		if desc is None:
			desc = expr
		super(TestCase, self).assert_(expr, desc)
	
	assertTrue = assert_
	failUnless = assert_
	
	def assertRaises(self, exception, func, message = None, with_args = None, matching=None):
		"""
		Enhanced assertRaises, able to:
		 - check arguments (with_args)
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
			if with_args is not None:
				self.failIf(exc.args != with_args,
					"%s raised %s with unexpected args: "\
					"expected=%r, actual=%r"\
					% (callsig, exc.__class__, with_args, exc.args))
			if matching is not None:
				pattern = re.compile(matching)
				self.failUnless(pattern.search(str(exc)),
					"%s raised %s, but the exception "\
					"does not match '%s': %r"\
					% (callsig, exc.__class__, matching, str(exc)))
			if message is not None:
				self.failUnless(str(exc) == matching,
					"%s raised %s, but the exception "\
					"does not equal '%s': %r"\
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
