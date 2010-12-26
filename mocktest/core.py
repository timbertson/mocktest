#__all__ = (
#	'raw_mock',
#	'mock',
#	'mock_on',
#	'expect',
#)

__unittest = True

from mockmatcher import *
_setup = MockTransaction.__enter__
_teardown = MockTransaction.__exit__
