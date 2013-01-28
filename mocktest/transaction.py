from .mockerror import MockError

__unittest = True

__all__ = ['MockTransaction']

class _MockTransaction(object):
	"""
	A context manager to encapsulate a single mocktest transaction.

	**Note**: this is a global context manager - you
	cannot have more than one.
	"""
	def __init__(self):
		self.teardown_actions = None
		self.started = False

	def add_teardown(self, func):
		self.teardown_actions.append(func)
	
	def __enter__(self):
		"""begin a new transaction"""
		if self.started: raise MockError("MockTransaction started while already in progress!")
		self.teardown_actions = []
		self.started = True

	def __exit__(self, *optional_err_info):
		"""end the current transaction, resetting all mocks and verifying all expectations"""
		if not self.started: raise MockError("MockTransaction is not in progress!")
		errors = []
		for action in reversed(self.teardown_actions):
			try:
				action()
			except Exception as e:
				errors.append(e)
		self.teardown_actions = None
		self.started = False
		if errors:
			raise errors[0]
		return False

# The global MockTransaction instance:
MockTransaction = _MockTransaction()
