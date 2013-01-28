

import unittest
import re
import sys
import os

import mocktest
from mocktest import core, modify, when, MockTransaction, mock, expect, ignore, pending

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
		self.output = []
		def write(s):
			print("appending: %s" % s)
			self.output.append(s)
		modify(sys).stderr.write = write
	
	def tearDown(self):
		core._teardown()
	
	#TODO: duplicated?
	def run_suite(self, class_):
		core._teardown()
		suite = unittest.makeSuite(class_)
		result = unittest.TestResult()
		suite.run(result)
		core._setup()
		return result
	
	#TODO: duplicated?
	def run_method(self, test_func):
		class SingleTest(mocktest.TestCase):
			test_method = test_func
		
		result = self.run_suite(SingleTest)
		
		if not result.wasSuccessful():
			print("ERRORS: %s" % (result.errors,))
			print("FAILURES: %s" % (result.failures,))
		return result
		
	def test_should_hijack_setup_and_teardown(self):
		lines = []
		def capture(line):
			lines.append(line)
		backup_setup = core._setup
		backup_teardown = core._teardown
		
		try:
			when(core)._setup.then_call(lambda: capture("_setup"))
			when(core)._teardown.then_call(lambda: capture("_teardown"))
			
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
		
		finally:
			core._setup = backup_setup
			core._teardown = backup_teardown
	
	def test_ignore(self):
		callback = mock()
		expect(callback).__call__.never()
			
		@ignore
		def test_failure(self):
			callback('a')
		
		self.assert_(self.run_method(test_failure).wasSuccessful())
	
	def test_should_ignore_with_description(self):
		callback = mock()
		expect(callback).__call__.never()
			
		@ignore('not done yet')
		def test_failure(self):
			callback('a')
		
		self.assert_(self.run_method(test_failure).wasSuccessful())
	
	def test_pending(self):
		callbacks = []
		callback = callbacks.append
			
		@pending
		def test_failure(self):
			callback('a')
			raise RuntimeError("something went wrong!")
		self.assert_(self.run_method(test_failure).wasSuccessful())
		
		@pending("reason")
		def test_failure_with_reason(self):
			assert False
			callback('b')
		
		self.assert_(self.run_method(test_failure_with_reason).wasSuccessful())
		
		@pending
		def test_successful_pending_test(self):
			assert True
			callback('c')
		
		self.assertEqual(self.run_method(test_successful_pending_test).wasSuccessful(), False)
		self.assertEqual(callbacks, ['a', 'c'])
	
	def test_pending_should_raise_skipTest(self):
		@pending
		def test_failed_pending(self):
			assert False
		
		try:
			from unittest import SkipTest
			self.assertRaises(SkipTest, test_failed_pending)
		except ImportError:
			print("cant find SkipTest, so this test case won't work")
	
	def test_invalid_usage_after_teardown(self):
		core._teardown()
		try:
			e = None
			try:
				m = mock()
				expect(m).foo().never()
			except Exception as e_:
				print(repr(e_))
				e = e_

			self.assertFalse(e is None, "no exception was raised")
			self.assertEqual(str(e), "Mock transaction has not been started. Make sure you are inheriting from mocktest.TestCase")
			self.assertEqual(e.__class__, AssertionError)
		finally:
			core._setup()
		
	def test_expectation_errors_should_be_failures(self):
		class myTest(mocktest.TestCase):
			def test_a(self):
				foo = mock()
				expect(foo).blah.once()
		results = self.run_suite(myTest)
		self.assertEqual(1, results.testsRun)
		assert len(results.errors) == 0, results.errors
		self.assertEqual(1, len(results.failures))
		self.assertEqual(0, len(results.errors))

	def make_error(self, *args, **kwargs):
		print("runtime error is being raised...")
		raise SomeError(*args, **kwargs)
	
	def test_assert_equal_should_be_friendly_for_arrays(self):
		def arrayNE(s):
			s.assertEqual([1,2,3], [1,4,3])
			
		result = self.run_method(arrayNE)
		self.assertFalse(result.wasSuccessful())
		failmsgs = result.failures[0][1].split('\n')
		
		print("failmsgs = %s" % (failmsgs,))
		
		self.assertTrue('AssertionError: [1, 2, 3] != [1, 4, 3]' in failmsgs)
		self.assertTrue('lists differ at index 1:' in failmsgs)
		self.assertTrue('\t2 != 4' in failmsgs)

	def test_assert_equal_should_be_friendly_for_tuples(self):
		def arrayNE(s):
			s.assertEqual((1,2,3), (1,4,3))
			
		result = self.run_method(arrayNE)
		self.assertFalse(result.wasSuccessful())
		failmsgs = result.failures[0][1].split('\n')
		
		print("failmsgs = %s" % (failmsgs,))
		
		self.assertTrue('AssertionError: (1, 2, 3) != (1, 4, 3)' in failmsgs)
		self.assertTrue('lists differ at index 1:' in failmsgs)
		self.assertTrue('\t2 != 4' in failmsgs)

	def test_assert_equal_should_be_friendly_for_array_lengths(self):
		def arrayNE(s):
			s.assertEqual([1,2,3], [1])
			
		result = self.run_method(arrayNE)
		self.assertFalse(result.wasSuccessful())
		failmsgs = result.failures[0][1].split('\n')
		
		print("failmsgs = %s" % (failmsgs,))
		
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
		
		print("failmsgs = %s" % (failmsgs,))
		
		self.assertTrue("AssertionError: %r != %r" % ({'a': 'b'}, {'4': 'x', '5': 'd'}) in failmsgs)
		self.assertTrue("dict keys differ: ['a'] != ['4', '5']" in failmsgs)

	def test_assert_equal_should_be_friendly_for_dict_value_diffs(self):
		def dictNE(s):
			s.assertEqual({'a': 'b', '4': 'x'}, {'4': 'x', 'a': 'd'})

		result = self.run_method(dictNE)
		self.assertFalse(result.wasSuccessful())
		failmsgs = result.failures[0][1].split('\n')
		
		print("failmsgs = %s" % (failmsgs,))
		
		self.assertTrue("AssertionError: %r != %r" % ({'a': 'b', '4': 'x'}, {'4': 'x', 'a': 'd'}) in failmsgs)
		self.assertTrue("difference between dicts: {'a': 'b'} vs {'a': 'd'}" in failmsgs)

	def test_assert_equal_should_use_super_if_desc_is_defined(self):
		def dictNE(s):
			s.assertEqual({'a': 'b', '4': 'x'}, {'4': 'x', 'a': 'd'}, 'foo went bad!')

		result = self.run_method(dictNE)
		self.assertFalse(result.wasSuccessful())
		failmsgs = result.failures[0][1].split('\n')
		
		print("failmsgs = %s" % ("\n".join(failmsgs),))
		self.assertTrue(
				"AssertionError: foo went bad!" in failmsgs or # py2
				" : foo went bad!" in failmsgs # py3
				)
		
	def test_assert_equal_should_work_for_dicts(self):
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
	
	def test_assert_matches_success(self):
		from mocktest.matchers import string_matching
		def test_string_match(s):
			s.assertMatches(string_matching('^f'), 'foo')
		result = self.run_method(test_string_match)
		self.assertTrue(result.wasSuccessful())

	def test_assert_matches_error_message(self):
		from mocktest.matchers import string_matching
		def test_string_match(s):
			s.assertMatches(string_matching('^f'), 'boo')
		result = self.run_method(test_string_match)
		self.assertFalse(result.wasSuccessful())
		failure_text = result.failures[0][1]
		self.assertTrue(
			"""AssertionError: expected:\n'boo'\nto be a string matching: ^f""" in failure_text,
			repr(result))

	def test_assert_matches_error_message_with_custom_message(self):
		from mocktest.matchers import string_matching
		def test_string_match(s):
			s.assertMatches(string_matching('^f'), 'boo', 'message')
		result = self.run_method(test_string_match)
		self.assertFalse(result.wasSuccessful())
		failure_text = result.failures[0][1]
		self.assertTrue(
			"""AssertionError: expected:\n'boo'\nto be a string matching: ^f\n(message)""" in failure_text,
			repr(result))
	
	def test_reality_formatting(self):
		core._teardown()
		try:
			with MockTransaction:
				m = mock('meth')
				expect(m).meth.once()
				m.meth(1,2,3)
				m.meth(foo='bar')
				m.meth()
				m.meth(1, foo=2)
		except AssertionError as e:
			line_agnostic_repr = [
				re.sub('\.py:[0-9 ]{3} ', '.py:LINE ', line)
				for line in str(e).split('\n')]
			
			expected_lines = [
				'Mock "meth" did not match expectations:',
				' expected exactly 1 calls',
				' received 4 calls with arguments:',
				'  1:   (1, 2, 3)                // mocktest_test.py:LINE :: m.meth(1,2,3)',
				"  2:   (foo='bar')              // mocktest_test.py:LINE :: m.meth(foo='bar')",
				'  3:   ()                       // mocktest_test.py:LINE :: m.meth()',
				'  4:   (1, foo=2)               // mocktest_test.py:LINE :: m.meth(1, foo=2)']
			
			for got, expected in zip(line_agnostic_repr, expected_lines):
				self.assertEqual(got, expected)
		finally:
			core._setup()
	
	def test_removing_of_mocktest_lines_from_exception_traces(self):
		# unittest has built-in functionality to ignore lines that correspond
		# to internal unittest code. Mocktest hooks into this, by defining
		# a __unittest variable in the global scope of all mocktest files that
		# raise AssertionErrors. This causes unittest to think that mocktest is
		# an internal part of unittest.
		mocktest_file_names = os.listdir(os.path.join(os.path.dirname(__file__), '..','mocktest'))
		mocktest_file_names = [x for x in mocktest_file_names if x.endswith('.py')]
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
		# ensure_no_mocktest_files_appear_in_failure(lambda slf: slf.assertRaises(TypeError, self.make_error)) # breaks on py3 due to exception contexts, not a big deal...
		def mock_failure(slf):
			expect(mock()).foo().at_least.once()
		ensure_no_mocktest_files_appear_in_failure(mock_failure)
		
		def failing_mock_expectation(slf):
			expect(mock()).foo
			# emulate a refresh
			try:
				core._teardown()
			finally:
				core._setup()
		ensure_no_mocktest_files_appear_in_failure(failing_mock_expectation)

class MockTestTest(unittest.TestCase):
	def test_should_do_expectations(self):
		try:
			with MockTransaction:
				f = mock()
				expect(f).foo.once()
				f.foo('a')
				f.foo()
			raise RuntimeError("should not reach here!")
		except AssertionError as e:
			assert re.compile('Mock "foo" .*expected exactly 1 calls.* received 2 calls.*', re.DOTALL).match(str(e)), str(e)
		
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
				expect(foo).split('a')
	
			def test_two(self):
				print(foo)
				print(foo.split('a'))
				self.assertEqual(foo.split('a'), ['bl','h'])

		suite = unittest.makeSuite(InnerTest)
		result = unittest.TestResult()
		suite.run(result)
		assert len(result.errors) == 0, result.errors[0][1]
		self.assertEqual(len(result.errors), 0)
		self.assertEqual(len(result.failures), 1)
		self.assertEqual(result.testsRun, 2)


if __name__ == '__main__':
	unittest.main()
