import unittest
from mock import Mock
import mocktest
import sys
from mocktest import pending

def assert_desc(expr):
	assert expr, expr

class TestAutoSpecVerification(unittest.TestCase):

	def setUp(self):
		sys.stderr = Mock()
		sys.stderr.write = self.output = Mock()
	
	def run_suite(self, class_):
		suite = unittest.makeSuite(class_)
		result = unittest.TestResult()
		suite.run(result)
		return result
	
	def run_method(self, test_func):
		class SingleTest(mocktest.TestCase):
			test_method = test_func
		return self.run_suite(SingleTest)
		
	def test_should_hijack_setup_and_teardown(self):
		lines = []
		def capture(line):
			lines.append(line)
		Mock._setup = Mock(action = lambda: capture("_setup"))
		Mock._teardown = Mock(action = lambda: capture("_teardown"))
		
		class Foo(mocktest.TestCase):
			def setUp(self):
				capture("setup")
			def tearDown(self):
				capture("teardown")
			def test_main_is_called(self):
				capture("main")

		result = self.run_suite(Foo)
		self.assertTrue(result.wasSuccessful)
		self.assertEqual(lines, ['_setup', 'setup', 'main', '_teardown', 'teardown'])
	
	def test_pending(self):
		callback = Mock()
			
		@mocktest.pending
		def test_failure(self):
			callback('a')
			raise RuntimeError, "something went wrong!"
		
		self.assert_(self.run_method(test_failure).wasSuccessful)
		# assert_desc(self.output.called.with_('failure one'))
		
		@mocktest.pending("reason")
		def test_failure_with_reason(self):
			assert False
			callback('b')
		
		self.assert_(self.run_method(test_failure_with_reason).wasSuccessful)
		# assert_desc(self.output.called.with_('failure two'))
		
		@mocktest.pending
		def test_successful_pending_test(self):
			assert True
			callback('c')
		
		self.assert_(self.run_method(test_successful_pending_test).wasSuccessful)
		# assert_desc(self.output.called.with_('failure three'))
		
		self.assertEqual(callback.called.exactly(2).times.get_calls(), [('a',), ('c',)])
	
	def test_invalid_usage_before_setup(self):
		# before any setup
		e = None
		try:
			Mock().is_expected
		except Exception, e_:
			e = e_
		self.assertFalse(e is None, "no exception was raised")
		self.assertEqual(e.__class__, RuntimeError)
		self.assertEqual(e.message, "Mock._setup has not been called. Make sure you are inheriting from mock.TestCase, not unittest.TestCase")
	
	def test_invalid_usage_after_teardown(self):
		# after a test case
		Mock._setup()
		Mock._teardown()
		
		e = None
		try:
			Mock().is_expected
		except Exception, e_:
			e = e_

		self.assertFalse(e is None, "no exception was raised")
		self.assertEqual(e.__class__, RuntimeError)
		self.assertEqual(e.message, "Mock._setup has not been called. Make sure you are inheriting from mock.TestCase, not unittest.TestCase")

	def make_error(self, *args, **kwargs):
		print "runtime error is being raised..."
		raise RuntimeError, "args are %r, kwargs are %r" % (args, kwargs)

	def test_assert_raises_matches(self):
		def test_raise_match(s):
			s.assertRaises(RuntimeError, lambda: self.make_error(1,2, foo='bar'), message="args are [1,2], kwargs are {'foo':'bar'}")
			s.assertRaises(Exception, self.make_error, matches="^a")
			s.assertRaises(Exception, self.make_error, matches="\\}$")
			s.assertRaises(RuntimeError, lambda: self.make_error(1,2, foo='bar'), args=((1,2),{'foo':'bar'}), foo="bar")
		self.assertTrue( self.run_method(test_raise_match).wasSuccessful)
	
	def test_assert_raises_verifies_type(self):
		def test_raise_mismatch_type(s):
			s.assertRaises(TypeError, self.make_error)
		result = self.run_method(test_raise_mismatch_type)
		self.assertFalse(result.failures == 1)

	def test_assert_raises_verifies_message(self):
		def test_raise_mismatch_message(s):
			s.assertRaises(RuntimeError, self.make_error, message='nope')
		self.assertFalse( self.run_method(test_raise_mismatch_message).failures == 1)
	
	def test_assert_raises_verifies_regex(self):
		def test_raise_mismatch_regex(s):
			s.assertRaises(RuntimeError, self.make_error, matches='^a')
		self.assertFalse( self.run_method(test_raise_mismatch_regex).failures == 1)
	
	def test_expectation_formatting(self):
		self.assertEqual(
			repr(Mock().called.with_('foo', bar=1).twice()),
			'\n'.join([
				'Mock "unknown-mock" did not match expectations:',
				' expected exactly 2 calls with arguments equal to: \'foo\', bar=1',
				' received 0 calls'])
		)

	def test_reality_formatting(self):
		m = Mock(name='ze_mock')
		m(1,2,3)
		m(foo='bar')
		m()
		m(1, foo=2)
		self.assertEqual(
			repr(m.called.once()),
			'\n'.join([
				'Mock "ze_mock" did not match expectations:',
				' expected exactly 1 calls',
				' received 4 calls with arguments:',
				'  1:   1, 2, 3',
				'  2:   foo=\'bar\'',
				'  3:   No arguments',
				'  4:   1, foo=2'])
		)

	
class MockTestTest(mocktest.TestCase):
	def test_should_do_expectations(self):
		f = Mock()
		f.foo.is_expected.once()
		f.foo('a')
		f.foo()
		import re
		self.assertRaises(AssertionError, Mock._teardown, matching=re.compile('Mock "foo" .*expected exactly 1 calls.* received 2 calls.*', re.DOTALL))
		
		# pretend we're in a new test (wipe the expected calls register)
		Mock._all_expectations = []

if __name__ == '__main__':
	unittest.main()