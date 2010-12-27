__all__ = (
	'MockTransaction',
	'_setup',
	'_teardown',
)

__unittest = True

from mockmatcher import MockTransaction
_setup = MockTransaction.__enter__
_teardown = MockTransaction.__exit__
