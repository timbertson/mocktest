import helper
import os
import unittest

from mocktest import *
from mocktest import TestCase


class TestMock2(TestCase):
	def test_should_track_calls(self):
		mockos = mock_on(os)
		mockos.command = "foo"
		mockos.path.return_value = "foo2"
		
		self.assertTrue(os.command("ls ~") == 'foo')
		self.assertTrue(os.path() == 'foo2')
		
		mock_on(os).system.is_expected.with_args('ls ~')
		os.system('ls ~')
		
		mock_on(os).expects('system').with_args('ls /')
		os.system('ls ~')
		
		
# what's new?
# resets over tests
# mock_on(parent) vs mock() vs mock_of(silent_mock)
# mock_on(os).system should raise the second time
# dsl-like chaining
# removal of spec