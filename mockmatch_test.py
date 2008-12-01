import unittest
from mock import Mock
from mock import SpecTest

class TestPySpec(unittest.TestCase):
	def test_should_track_calls(self):
		obj = Mock()
		obj.foo('arg1')
		
		self.assertTrue(obj.foo.called)
		self.assertEquals(obj.foo.called, True)
		self.assertTrue(obj.foo.called.with_args('arg1'))

		self.assertFalse(obj.bar.called)
		self.assertFalse(obj.foo.called.with_args('arg1', 'arg2'))
	
	def test_should_track_number_of_calls(self):
		obj = Mock()
		obj.foo('a')
		obj.foo('b')
		obj.foo('b')
		
		# exactly
		self.assertTrue(obj.foo.called.exactly(3).times)
		self.assertTrue(obj.bar.called.exactly(0).times)

		# at_least
		self.assertTrue(obj.foo.called.at_least(1).times)
		self.assertFalse(obj.foo.called.at_least(4).times)

		# at_most
		self.assertFalse(obj.foo.called.at_most(2).times)
		self.assertTrue(obj.foo.called.at_most(4).times)

		# between
		self.assertTrue(obj.foo.called.between(1,4).times)
		self.assertTrue(obj.foo.called.between(4,1).times)

		# failed betweens
		self.assertFalse(obj.foo.called.between(4,5).times)
		self.assertFalse(obj.foo.called.between(5,4).times)
		self.assertFalse(obj.foo.called.between(5,5).times)
	
	def test_should_default_to_one_or_more_calls(self):
		obj = Mock()
		obj.a()
		obj.a(1)
		
		self.assertTrue(obj.a.called)
		self.assertFalse(obj.b.called)
	
	def test_should_have_once_and_twice_aliases(self):
		obj = Mock()
		obj.a()
		obj.b()
		obj.b()
		
		self.assertTrue(obj.a.called.once())
		self.assertFalse(obj.a.called.twice())
		
		self.assertTrue(obj.b.called.twice())
		self.assertFalse(obj.b.called.once())
		
	def test_should_track_number_of_calls_with_arguments(self):
		obj = Mock()
		obj.foo('a')
		obj.foo('b')
		obj.foo('b')
		obj.foo('unused_call')
		
		self.assertTrue(obj.foo.called.with_args('a').exactly(1))
		self.assertTrue(obj.foo.called.with_args('b').exactly(2))
		
		# reverse check order:
		
		self.assertTrue(obj.foo.called.exactly(1).with_args('a'))
		self.assertTrue(obj.foo.called.exactly(2).with_args('b'))
	
	def test_should_return_arguments(self):
		obj = Mock()
		obj.foo(1)
		obj.foo('bar', x='y')
		obj.bar()
		obj.xyz(foo='bar')
		
		self.assertEqual(obj.foo.called.get_calls(), (   ((1,),None), (('bar',),{'x':'y'})    ))
		self.assertEqual(obj.foo.called.once().get_calls(), None)
		self.assertEqual(obj.foo.called.twice().get_calls(), (    ((1,),None), (('bar',),{'x':'y'})   ))
		self.assertEqual(obj.xyz.called.once().get_calls()[0], (None, {'foo':'bar'}))
		
		self.assertRaises(ValueError, lambda: obj.foo.called.twice().get_args())
		self.assertRaises(ValueError, lambda: obj.bar.called.get_args())
		self.assertEqual(obj.bar.called.once().get_args(), (None, None))
		
		
	def test_should_allow_argument_checking_callbacks(self):
		obj = Mock()
		obj.foo(1)
		obj.foo(2)
		obj.foo(3)
		obj.foo(4)
		
		self.assertTrue(obj.foo.called.twice().where_args(lambda *args: all([x < 3 for x in args])))
		self.assertTrue(obj.foo.called.exactly(4).times)
	
class TestAutoSpecVerification(unittest.TestCase):
	def test_should_hijack_setup_and_teardown(self):
		lines = []
		def capture(line):
			lines.append(line)
		Mock._setup = Mock(side_effect = lambda: capture("_setup"))
		Mock._teardown = Mock(side_effect = lambda: capture("_teardown"))
		
		class Foo(SpecTest):
			##TODO: fix this rubbish! maybe in the core libray itself! o_O
			_testMethodName = 'test_main_is_called'
			_testMethodDoc = None

			def setUp(self):
				capture("setup")
			def tearDown(self):
				capture("teardown")
			def test_main_is_called(self):
				capture("main")

		suite = unittest.makeSuite(Foo)
		result = unittest.TestResult()
		suite.run(result)
		self.assertTrue(result.wasSuccessful)
		self.assertEqual(lines, ['_setup', 'setup', 'main', '_teardown', 'teardown'])
		assert Mock._setup.called.once()
		assert Mock._teardown.called.once()
	
	#TODO: expectation / reality formatting
	#TODO: ensure things are alyways checked (and cleared)
	#TODO: test assertTrue for more verbose error messages

class FooTest(SpecTest):
	_testMethodName = 'test_should_do_expectations'
	_testMethodDoc = None
	
	def setUp(self):
		print "test case pre"
	
	def tearDown(self):
		print "test case post"
	
	def test_should_do_expectations(self):
		f = Mock()
		f.foo.is_expected.once()
		f.foo('a')
		f.foo()
		self.assertTrue(f.foo.called.once())


if __name__ == '__main__':
	unittest.main()