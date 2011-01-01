from mockerror import MockError

__unittest = True

class MockTransaction(object):
	"""
	A context manager to encapsulate a single mocktest transaction.

	**Note**: this is a global context manager - you
	cannot have more than one.
	"""
	teardown_actions = None
	started = False
	@classmethod
	def add_teardown(cls, func):
		cls.teardown_actions.append(func)
	
	@classmethod
	def __enter__(cls):
		"""begin a new transaction"""
		if cls.started: raise MockError("MockTransaction started while already in progress!")
		cls.teardown_actions = []
		cls.started = True

	@classmethod
	def __exit__(cls, *optional_err_info):
		"""end the current transaction, resetting all mocks and verifying all expectations"""
		if not cls.started: raise MockError("MockTransaction is not in progress!")
		errors = []
		for action in reversed(cls.teardown_actions):
			try:
				action()
			except StandardError, e:
				errors.append(e)
		cls.teardown_actions = None
		cls.started = False
		if errors:
			raise errors[0]
		return False

