from mocktest import TestCase

import helper

from mocktest import stub
from mocktest.silentmock import SilentMock

class StubTest(TestCase):
	def test_should_be_a_silent_mock(self):
		self.assertTrue(isinstance(stub(), SilentMock))

	def test_should_be_frozen(self):
		self.assertRaises(AttributeError, lambda: stub().some_attr)
	
	def test_should_have_a_name(self):
		self.assertTrue('the_name' in str(stub('the_name')))

