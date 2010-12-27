class MockTransaction(object):
	teardown_actions = None
	started = False
	@classmethod
	def add_teardown(cls, func):
		cls.teardown_actions.append(func)
	
	@classmethod
	def __enter__(cls):
		assert not cls.started, "MockTransaction started while already in progress!"
		cls.teardown_actions = []
		cls.started = True

	@classmethod
	def __exit__(cls, *optional_err_info):
		errors = []
		for action in reversed(cls.teardown_actions):
			try:
				action()
			except StandardError, e:
				errors.append(e)
		cls.teardown_actions = None
		cls.started = False
		if errors:
			raise MockError("Errors occurred during mocktest cleanup:\n%s" % ("\n".join(errors),))
		return False

