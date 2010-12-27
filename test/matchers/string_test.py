from mocktest import TestCase

from mocktest.matchers import *
import re

class TypeMatcherTest(TestCase):
	def test_should_match_regexes(self):
		self.assertTrue(string_matching('^f').matches('fdfds'))
		self.assertTrue(string_matching(re.compile('f', re.I)).matches('F'))
		self.assertFalse(string_matching('^f').matches('x'))

