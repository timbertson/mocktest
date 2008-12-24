from lib.realsetter import RealSetter
from silentmock import SilentMock
from mockmatcher import MockMatcher

def mock_wrapper(silent_mock = None):
	"""
	return a mock wrapper for the given silent mock
	you can use the mock wrapper to set expectations or get invocation details
	for a slent mock
	"""
	if silent_mock is None:
		silent_mock = SilentMock()
	if isinstance(silent_mock, SilentMock):
		return MockWrapper(silent_mock)
	raise TypeError("expected a SilentMock instance, got %s" % (mock_.__class__,))


class MockWrapper(RealSetter):
	"""
	a mock object wrapper for use in test cases
	 - allows expectations and mock actions to be set
	
	all setattr and getattr go via the attahced silent mock's _mock_get and _mock_set
	"""
	_all_expectations = None
	def __init__(self, wrapped_mock = None):
		if self.__class__._all_expectations is None:
			raise RuntimeError(("%s._setup has not been called. " +
				"Make sure you are inheriting from mock.TestCase, " +
				"not unittest.TestCase") % (self.__class__.__name__,))
		if wrapped_mock is None:
			wrapped_mock = SilentMock()
		if not isinstance(wrapped_mock, SilentMock):
			raise TypeError("expected SilentMock, got %s" % (wrapped_mock.__class__,))
		self._real_set(_mock = wrapped_mock)
	
	# delegate getting and setting to SilentMock
	def _set(self, **kwargs):
		self._mock._mock_set(**kwargs)
	
	def _get(self, attr):
		return self._mock._mock_get(attr)
	
	def _get_mock(self):
		return self._mock
	mock = property(_get_mock)
			
	# mockExpecation integration
	@classmethod
	def _setup(cls):
		if not cls._all_expectations is None:
			raise RuntimeError("%s._setup been called twice in a row"
				% (cls.__name__,))
		cls._all_expectations = []
	
	@classmethod
	def _teardown(cls):
		if cls._all_expectations is None:
			raise RuntimeError("%s._teardown been called twice in a row"
				% (cls.__name__,))
		for expectation in cls._all_expectations:
			assert expectation, expectation
		cls._all_expectations = None

	def __called_matcher(self):
		return MockMatcher(self._mock)
	called = property(__called_matcher)
	
	def __expect_call_on(self, obj):
		matcher = MockMatcher(obj)
		self.__class__._all_expectations.append(matcher)
		return matcher
	
	def __expect_call_matcher(self):
		return self.__expect_call_on(self._mock)
	is_expected = property(__expect_call_matcher)

	def expects(self, methodname):
		return self.__expect_call_on(getattr(self._mock, methodname))

	def __str__(self):
		return 'mock wrapper for \"%s\"' %(self._get('name'))

	def __setattr__(self, attr, val):
		self._mock._mock_set(**{attr:val})

	def __getattr__(self, attr):
		return self._mock._mock_get(attr)
		
	def __delattr__(self, attr):
		self._mock._mock_del(attr)
	
	def reset(self):
		self.mock._mock_reset()
	
	def child(self, val):
		return mock_wrapper(getattr(self.mock, val))
		
	# convenience methods for dsl-like chaining
	def returning(self, val):
		self.return_value = val
		return self

	def named(self, val):
		self.name = val
		return self
	
	def with_action(self, val):
		self.action = val
		return self

	def raising(self, ex):
		def mock_raise():
			raise ex
		return self.with_action(mock_raise)

	def with_spec(self, spec):
		children = [member for member in dir(spec) if not 
			(member.startswith('__') and member.endswith('__'))]
		return self.with_children(*children)
	
	def with_methods(self, *methods, **kwmethods):
		self._with_children(*methods)
		for key in kwmethods:
			kwmethods[key] = SilentMock(return_value = kwmethods[key])
		return self.with_children(**kwmethods)
	
	def with_children(self, *children, **kwchildren):
		self._with_children(*children, **kwchildren)
		return self.frozen()
	
	def _with_children(self, *children, **kwchildren):
		"""internally add children, but don't freeze the mock"""
		for child in children:
			getattr(self.mock, child)
		for child, val in kwchildren.items():
			setattr(self.mock, child, val)
		return self
	
	def frozen(self):
		self._modifiable_children = False
		return self

	def unfrozen(self):
		self._modifiable_children = True
		return self