import unittest
import re
import sys
import os

import helper
import mocktest
from mocktest import mock, raw_mock, pending, ignore, expect, core

def assert_desc(expr):
	assert expr, expr

class SomeError(RuntimeError):
	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs

	def __str__(self):
		return "args are %r, kwargs are %r" % (self.args, self.kwargs)
	

class TestAutoSpecVerification(unittest.TestCase):

	def setUp(self):
		core._setup()
		self.stderr = mock().named('stderr')
		sys.stderr = self.stderr.raw
		self.output = mock(sys.stderr.write)
		print "all expectations is %r" % (core.MockWrapper._all_expectations,)
	
	def tearDown(self):
		print "all expectations is %r" % (core.MockWrapper._all_expectations,)
		core._teardown()
	
	def run_suite(self, class_):
		core._teardown()
		suite = unittest.makeSuite(class_)
		result = unittest.TestResult()
		suite.run(result)
		ret = result
		core._setup()
		return result
	
	def run_method(self, test_func):
		class SingleTest(mocktest.TestCase):
			test_method = test_func
		
		result = self.run_suite(SingleTest)
		
		if not result.wasSuccessful():
			print "ERRORS: %s" % (result.errors,)
			print "FAILURES: %s" % (result.failures,)
		return result
		
	def test_should_hijack_setup_and_teardown(self):
		lines = []
		def capture(line):
			lines.append(line)
		backup_setup = core._setup
		backup_teardown = core._teardown
		
		core._setup = mock().with_action(lambda: capture("_setup")).raw
		core._teardown = mock().with_action(lambda: capture("_teardown")).raw
		
		class Foo(mocktest.TestCase):
			def setUp(self):
				capture("setup")
			def tearDown(self):
				capture("teardown")
			def test_main_is_called(self):
				capture("main")

		suite = unittest.makeSuite(Foo)
		result = unittest.TestResult()
		suite.run(result)

		self.assertTrue(result.wasSuccessful())
		self.assertEqual(lines, ['_setup', 'setup', 'main', '_teardown', 'teardown'])
		
		core._setup = backup_setup
		core._teardown = backup_teardown
	
	def test_ignore(self):
		callback = raw_mock()
		mock(callback).is_expected.exactly(0).times
			
		@ignore
		def test_failure(self):
			callback('a')
		
		self.assert_(self.run_method(test_failure).wasSuccessful())
		assert_desc(self.output.called.with_('[[[ IGNORED ]]] ... '))
	
	def test_should_ignore_with_description(self):
		callback = raw_mock()
		mock(callback).is_expected.exactly(0).times
			
		@ignore('not done yet')
		def test_failure(self):
			callback('a')
		
		self.assert_(self.run_method(test_failure).wasSuccessful())
		assert_desc(self.output.called.with_('[[[ IGNORED ]]] (not done yet) ... '))
	
	def test_pending(self):
		callback = raw_mock()
			
		@pending
		def test_failure(self):
			callback('a')
			raise RuntimeError, "something went wrong!"
		
		self.assert_(self.run_method(test_failure).wasSuccessful())
		assert_desc(self.output.called.with_('[[[ PENDING ]]] ... '))
		
		@pending("reason")
		def test_failure_with_reason(self):
			assert False
			callback('b')
		
		self.assert_(self.run_method(test_failure_with_reason).wasSuccessful())
		assert_desc(self.output.called.with_('[[[ PENDING ]]] (reason) ... '))
		
		@pending
		def test_successful_pending_test(self):
			assert True
			callback('c')
		
		self.assertEqual(self.run_method(test_successful_pending_test).wasSuccessful(), False)
		assert_desc(self.output.called.with_('test_successful_pending_test PASSED unexpectedly '))
		
		self.assertEqual(mock(callback).called.exactly(2).times.get_calls(), [('a',), ('c',)])
	
	def test_pending_should_raise_skipTest(self):
		@pending
		def test_failed_pending(self):
			assert False
		
		try:
			from unittest import SkipTest
			self.assertRaises(SkipTest, test_failed_pending)
		except ImportError:
			print "cant find SkipTest, so this test case won't work"
	
	def test_invalid_usage_after_teardown(self):
		core._teardown()
		
		e = None
		try:
			mock()
		except Exception, e_:
			e = e_

		self.assertFalse(e is None, "no exception was raised")
		self.assertEqual(e.__class__, RuntimeError)
		self.assertEqual(e.message, "MockWrapper._setup has not been called. Make sure you are inheriting from mocktest.TestCase, not unittest.TestCase")
		core._setup()
		
	def test_expectation_errors_should_be_failures(self):
		class myTest(mocktest.TestCase):
			def test_a(self):
				foo = mocktest.mock()
				foo.expects('blah').once()
		results = self.run_suite(myTest)
		self.assertEqual(1, results.testsRun)
		self.assertEqual(1, len(results.failures))
		self.assertEqual(0, len(results.errors))

	def make_error(self, *args, **kwargs):
		print "runtime error is being raised..."
		raise SomeError(*args, **kwargs)
	
	def test_assert_equal_should_be_friendly_for_arrays(self):
		def arrayNE(s):
			s.assertEqual([1,2,3], [1,4,3])
			
		result = self.run_method(arrayNE)
		self.assertFalse(result.wasSuccessful())
		failmsgs = result.failures[0][1].split('\n')
		
		print "failmsgs = %s" % (failmsgs,)
		
		self.assertTrue('AssertionError: [1, 2, 3] != [1, 4, 3]' in failmsgs)
		self.assertTrue('lists differ at index 1:' in failmsgs)
		self.assertTrue('\t2 != 4' in failmsgs)

	def test_assert_equal_should_be_friendly_for_tuples(self):
		def arrayNE(s):
			s.assertEqual((1,2,3), (1,4,3))
			
		result = self.run_method(arrayNE)
		self.assertFalse(result.wasSuccessful())
		failmsgs = result.failures[0][1].split('\n')
		
		print "failmsgs = %s" % (failmsgs,)
		
		self.assertTrue('AssertionError: (1, 2, 3) != (1, 4, 3)' in failmsgs)
		self.assertTrue('lists differ at index 1:' in failmsgs)
		self.assertTrue('\t2 != 4' in failmsgs)

	def test_assert_equal_should_be_friendly_for_array_lengths(self):
		def arrayNE(s):
			s.assertEqual([1,2,3], [1])
			
		result = self.run_method(arrayNE)
		self.assertFalse(result.wasSuccessful())
		failmsgs = result.failures[0][1].split('\n')
		
		print "failmsgs = %s" % (failmsgs,)
		
		self.assertTrue('AssertionError: [1, 2, 3] != [1]' in failmsgs)
		self.assertTrue('lists differ at index 1:' in failmsgs)
		self.assertTrue('\t2 != (no more values)' in failmsgs)
			
	def test_assert_equal_should_work(self):
		def arrayEQ(s):
			s.assertEqual([1,2,3], [1,2,3])
			
		self.assertTrue(self.run_method(arrayEQ).wasSuccessful())
			
	def test_assert_equal_should_be_friendly_for_dict_key_diffs(self):
		def dictNE(s):
			s.assertEqual({'a': 'b'}, {'4': 'x', '5': 'd'})

		result = self.run_method(dictNE)
		self.assertFalse(result.wasSuccessful())
		failmsgs = result.failures[0][1].split('\n')
		
		print "failmsgs = %s" % (failmsgs,)
		
		self.assertTrue("AssertionError: %r != %r" % ({'a': 'b'}, {'4': 'x', '5': 'd'}) in failmsgs)
		self.assertTrue("dict keys differ: ['a'] != ['4', '5']" in failmsgs)

	def test_assert_equal_should_be_friendly_for_dict_value_diffs(self):
		def dictNE(s):
			s.assertEqual({'a': 'b', '4': 'x'}, {'4': 'x', 'a': 'd'})

		result = self.run_method(dictNE)
		self.assertFalse(result.wasSuccessful())
		failmsgs = result.failures[0][1].split('\n')
		
		print "failmsgs = %s" % (failmsgs,)
		
		self.assertTrue("AssertionError: %r != %r" % ({'a': 'b', '4': 'x'}, {'4': 'x', 'a': 'd'}) in failmsgs)
		self.assertTrue("difference between dicts: {'a': 'b'} vs {'a': 'd'}" in failmsgs)

	def test_assert_equal_should_use_super_if_desc_is_defined(self):
		def dictNE(s):
			s.assertEqual({'a': 'b', '4': 'x'}, {'4': 'x', 'a': 'd'}, 'foo went bad!')

		result = self.run_method(dictNE)
		self.assertFalse(result.wasSuccessful())
		failmsgs = result.failures[0][1].split('\n')
		
		print "failmsgs = %s" % (failmsgs,)
		self.assertTrue("AssertionError: foo went bad!" in failmsgs)
		
	def test_assert_equal_should_work(self):
		def dictEQ(s):
			s.assertEqual({'a':'1'}, {'a':'1'})
		self.assertTrue(self.run_method(dictEQ).wasSuccessful())



	def test_assert_raises_matches(self):
		def test_raise_match(s):
			s.assertRaises(RuntimeError, lambda: self.make_error(1,2), message="args are (1, 2), kwargs are {}")
			s.assertRaises(Exception, self.make_error, matching="^a")
			s.assertRaises(Exception, self.make_error, matching="\\{\\}$")
			s.assertRaises(RuntimeError, lambda: self.make_error('foo'), args=('foo',))
			s.assertRaises(RuntimeError, lambda: self.make_error(), args=())
			s.assertRaises(RuntimeError, lambda: self.make_error(x=1), kwargs=dict(x=1))
		
		result = self.run_method(test_raise_match)
		self.assertTrue(result.wasSuccessful())
	
	def test_assert_raises_verifies_type(self):
		def test_raise_mismatch_type(s):
			s.assertRaises(TypeError, self.make_error)
		result = self.run_method(test_raise_mismatch_type)
		self.assertFalse(result.wasSuccessful())
		
	def test_assert_raises_verifies_args(self):
		def test_raise_mismatch_args(s):
			s.assertRaises(RuntimeError, lambda: self.make_error(1,2,3), args=())
		result = self.run_method(test_raise_mismatch_args)
		self.assertFalse(result.wasSuccessful())
	
	def test_assert_raises_verifies_kwargs(self):
		def test_raise_mismatch_kwargs(s):
			s.assertRaises(RuntimeError, lambda: self.make_error(x=1), kwargs=dict(x=2))
		result = self.run_method(test_raise_mismatch_kwargs)
		self.assertFalse(result.wasSuccessful())
	
	def test_assert_raises_verifies_message(self):
		def test_raise_mismatch_message(s):
			s.assertRaises(RuntimeError, self.make_error, message='nope')
		result = self.run_method(test_raise_mismatch_message)
		self.assertFalse(result.wasSuccessful())
	
	def test_assert_raises_verifies_regex(self):
		def test_raise_mismatch_regex(s):
			s.assertRaises(RuntimeError, self.make_error, matches='^a')
		result = self.run_method(test_raise_mismatch_regex)
		self.assertFalse(result.wasSuccessful())

	def test_expectation_formatting(self):
		self.assertEqual(
			repr(mock().called.with_('foo', bar=1).twice()),
			'\n'.join([
				'Mock "unnamed mock" did not match expectations:',
				' expected exactly 2 calls with arguments equal to: \'foo\', bar=1',
				' received 0 calls'])
		)
	
	def test_expect_should_work_on_a_mock_or_wrapper(self):
		wrapper = mock()
		mock_ = wrapper.raw
		
		expect(mock_.a).once()
		wrapper.expects('b').once()
		wrapper.child('c').is_expected.once()

		self.assertTrue(len(core.MockWrapper._all_expectations) == 3)
		
		mock_.a()
		mock_.b()
		mock_.c()
	
	def test_is_not_expected(self):
		wrapper = mock()
		mock_ = wrapper.raw
		
		expect(mock_.a).once()
		wrapper.child('b').is_not_expected
		mock_.a()
		
		core._teardown()
		core._setup()
		

	def test_reality_formatting(self):
		m = mock().named('ze_mock').raw
		m(1,2,3)
		m(foo='bar')
		m()
		m(1, foo=2)
		
		line_agnostic_repr = [
			re.sub('\.py:[0-9 ]{3} ', '.py:LINE ', line)
			for line in repr(mock(m).called.once()).split('\n')]
		
		expected_lines = [
			'Mock "ze_mock" did not match expectations:',
			' expected exactly 1 calls',
			' received 4 calls with arguments:',
			'  1:   1, 2, 3                  // mocktest_test.py:LINE :: m(1,2,3)',
			"  2:   foo='bar'                // mocktest_test.py:LINE :: m(foo='bar')",
			'  3:   No arguments             // mocktest_test.py:LINE :: m()',
			'  4:   1, foo=2                 // mocktest_test.py:LINE :: m(1, foo=2)']
		
		for got, expected in zip(line_agnostic_repr, expected_lines):
			self.assertEqual(got, expected)
	
	def test_removing_of_mocktest_lines_from_exception_traces(self):
		# unittest has built-in functionality to ignore lines that correspond
		# to internal unittest code. Mocktest hooks into this, by defining
		# a __unittest variable in the global scope of all mocktest files that
		# raise AssertionErrors. This causes unittest to think that mocktest is
		# an internal part of unittest.
		mocktest_file_names = os.listdir(os.path.join(os.path.dirname(__file__), '..','mocktest'))
		mocktest_file_names = filter(lambda x: x.endswith('.py'), mocktest_file_names)
		self.assertTrue(len(mocktest_file_names) > 2) # make sure we have some file names
		def ensure_no_mocktest_files_appear_in_failure(failure_func):
			result = self.run_method(failure_func)
			self.assertEqual(len(result.failures), 1, "test case %s was expected to fail but didn't: %r" % (failure_func.__name__, result))
			lines = result.failures[0][1].splitlines()
			for filename in mocktest_file_names:
				lines_containing_mocktest_internal_files = [line for line in lines if (filename + '"') in line]
				self.assertEqual([], lines_containing_mocktest_internal_files)
			
		ensure_no_mocktest_files_appear_in_failure(lambda slf: slf.assertEqual(False, True))
		ensure_no_mocktest_files_appear_in_failure(lambda slf: slf.assertTrue(False))
		ensure_no_mocktest_files_appear_in_failure(lambda slf: slf.assertFalse(True))
		ensure_no_mocktest_files_appear_in_failure(lambda slf: slf.assertRaises(TypeError, self.make_error))
		
		def failing_mock_expectation(slf):
			mocktest.mock().is_expected
			# emulate a refresh
			try:
				core._teardown()
			finally:
				core._setup()
		ensure_no_mocktest_files_appear_in_failure(failing_mock_expectation)

		

class MockTestTest(mocktest.TestCase):
	def test_should_do_expectations(self):
		f = mock()
		f.expects('foo').once()
		f.raw.foo('a')
		f.raw.foo()
		self.assertRaises(AssertionError, core._teardown, matching=re.compile('Mock "foo" .*expected exactly 1 calls.* received 2 calls.*', re.DOTALL))
		
		# pretend we're in a new test (wipe the expected calls register)
		core.MockWrapper._all_expectations = []

class Mystr(object):
	def __init__(self, s):
		self.s = s
	
	def split(self, string):
		return self.s.split(string)
	
	def __str__(self):
		return "STRING:%s" % self.s
foo = Mystr("blah")
class TestFailuresDontAffectSuccessiveTests(unittest.TestCase):
	def test_failures_dont_affect_successive_tests(self):
		class InnerTest(mocktest.TestCase):
			def test_one(self):
				mocktest.mock_on(foo).split.is_expected.with_('a')
				foo.split('x')
	
			def test_two(self):
				print foo
				print foo.split('a')
				self.assertEqual(foo.split('a'), ['bl','h'])

		suite = unittest.makeSuite(InnerTest)
		result = unittest.TestResult()
		suite.run(result)
		self.assertEqual(len(result.errors), 0)
		self.assertEqual(len(result.failures), 1)
		self.assertEqual(result.testsRun, 2)


if __name__ == '__main__':
	unittest.main()