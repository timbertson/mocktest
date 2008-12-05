import unittest
from mock import Mock
import mocktest

class TestAutoSpecVerification(unittest.TestCase):
	
	def run_suite(self, class_):
		suite = unittest.makeSuite(class_)
		result = unittest.TestResult()
		suite.run(result)
		return result
	
	def run_method(self, test_func):
		class SingleTest(mocktest.TestCase):
			def test_method(self):
				test_func(self)
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
			assert False
		
		@mocktest.pending("reason")
		def test_failure_with_reason(self):
			assert False
			callback('b')
		
		@mocktest.pending
		def test_successful_pending_test(self):
			assert True
			callback('c')
		
		assert self.run_method(test_failure).wasSuccessful
		assert self.run_method(test_failure_with_reason).wasSuccessful
		assert self.run_method(test_successful_pending_test).wasSuccessful
		
		self.assertEqual(callback.called.exactly(2).times.get_calls(), [('a',), ('c',)])
		assert callback.called.once().with_args('a')
	
	def test_invalid_usage(self):
		# before any setup
		self.assertRaises(Mock().is_expected, RuntimeError, "Mock._setup has not been called. Make sure you are inheriting from mock.TestCase, not unittest.TestCase")
		
		# after a test case
		Mock._setup()
		Mock._teardown()
		self.assertRaises(Mock().is_expected, RuntimeError, "Mock._setup has not been called. Make sure you are inheriting from mock.TestCase, not unittest.TestCase")
	
	def test_assert_raises(self):
		def make_error(*args, **kwargs):
			raise RuntimeError, "args are %r, kwargs are %r" % (args, kwargs)
			
		def test_raise_match(s):
			s.assertRaises(RuntimeError, lambda: make_error(1,2, foo='bar'), message="args are [1,2], kwargs are {'foo':'bar'}")
			s.assertRaises(Exception, make_error, matches="^a")
			s.assertRaises(Exception, make_error, matches="\\}$")
			s.assertRaises(RuntimeError, lambda: make_error(1,2, foo='bar'), args=((1,2),{'foo':'bar'}), foo="bar")

		self.assertTrue( self.run_method(test_raise_match).wasSuccessful)
		
		def test_raise_mismatch_type(s):
			s.assertRaises(TypeError, make_error)
		self.assertFalse( self.run_method(test_raise_mismatch_type).wasSuccessful)

		def test_raise_mismatch_message(s):
			s.assertRaises(RuntimeError, make_error, message='nope')
		self.assertFalse( self.run_method(test_raise_mismatch_message).wasSuccessful)
	
		def test_raise_mismatch_regex(s):
			s.assertRaises(RuntimeError, make_error, matches='^a')
		self.assertFalse( self.run_method(test_raise_mismatch_regex).wasSuccessful)
	
	#TODO: expectation / reality formatting
	#TODO: ensure things are alyways checked (and cleared) on setup / teardown
	#TODO: test assertTrue for more verbose error messages

class FooTest(mocktest.TestCase):
	def setUp(self):
		print "test case pre"
	
	def tearDown(self):
		print "test case post"
	
	def test_should_do_expectations(self):
		print self._testMethodName
		f = Mock()
		f.foo.is_expected.once()
		f.foo('a')
		f.foo()
		self.assertRaises(AssertionError, Mock._teardown, matching='Mock "foo" expected exactly 1 calls\nIt received 2 calls.*')
		
		# pretend we're in a new test
		Mock._setup()

if __name__ == '__main__':
	unittest.main()