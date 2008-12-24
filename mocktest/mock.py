__all__ = (
	'raw_mock',
	'mock_wrapper',
	'mock_on',
	'__version__'
)

__version__ = '0.2'

import sys
from mockmatcher import MockMatcher
from silentmock import SilentMock, raw_mock
from mockwrapper import MockWrapper, mock_wrapper
from mockanchor import MockAnchor, mock_on

def _setup():
	MockWrapper._setup()

def _teardown():
	MockWrapper._teardown()
	MockAnchor._reset_all()

def expect(mock_wrapper):
	if not isinstance(mock_wrapper, MockWrapper):
		raise TypeError("Expected %s, got %s" % (MockWrapper, mock_wrapper.__class__))
	return mock_wrapper.is_expected


