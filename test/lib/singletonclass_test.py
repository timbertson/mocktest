from unittest import TestCase
from mocktest.lib.singletonclass import ensure_singleton_class
import mocktest

class SomeClass(str):
	def __init__(self, val):
		self.val = val
	
	def __str__(self): return str(self.val)
	def __repr__(self): return repr(self.val)

class SingletonClassTest(TestCase):
	def test_singleton_classes_should_be_created_and_destroyed(self):
		f = SomeClass('str')
		g = SomeClass('another str')
		with mocktest.MockTransaction:
			self.assertTrue(type(f) is SomeClass)
			self.assertTrue(type(g) is SomeClass)
			
			ensure_singleton_class(f)
			ensure_singleton_class(g)
			self.assertTrue(isinstance(f, SomeClass))
			self.assertTrue(isinstance(g, SomeClass))

			self.assertFalse(isinstance(f, type(g)))
			self.assertFalse(isinstance(g, type(f)))
			
			self.assertFalse(type(f) is SomeClass)
			self.assertFalse(type(f) is type(g))
			self.assertEqual(type(f).__name__, 'SomeClass')
		
		self.assertTrue(type(f) is SomeClass)
		self.assertTrue(type(f) is type(g))
	
	def test_should_ignore_revertions_on_non_singleton_classes(self):
		f = SomeClass('str')
		with mocktest.MockTransaction:
			self.assertTrue(type(f) is SomeClass)
		self.assertTrue(type(f) is SomeClass)

	def test_should_ignore_request_to_make_singleton_again(self):
		f = SomeClass('str')
		with mocktest.MockTransaction:
			ensure_singleton_class(f)
			singleton_cls = type(f)
			ensure_singleton_class(f)
			self.assertTrue(type(f) is singleton_cls)



