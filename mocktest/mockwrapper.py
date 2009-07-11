"""
MockWrapper objects are to be used in test code. They allow
behaviour and expectations to be set on a SilentMock.

A wrapper can be created for an existing SilentMock with
mock(silent_mock).

A MockWrapper / SilentMock pair can be created with mock()
(the silent mock object is accessible via wrapper.raw)
"""
__unittest = True

from lib.realsetter import RealSetter
from silentmock import SilentMock, raw_mock
from mockmatcher import MockMatcher
from mockerror import MockError

def mock(*args):
	"""
	return a mock wrapper for the given silent mock, delegating to `proxied`
	when a given call is not set to be intercepted by the mock. You can use
	the mock wrapper to set expectations or get invocation details for a silent mock
	
	usage:
	mock("name of mock"), or
	mock(raw_mock_to_wrap), or
	mock(proxied_object), or
	mock(raw, proxied)
	"""
	raw, name, proxied = None, None, None
	if len(args) == 1:
		arg = args[0]
		if isinstance(arg, str):
			name = arg
		elif isinstance(arg, SilentMock):
			raw = arg
		else:
			proxied = arg
	elif len(args) == 2:
		raw, proxied = args
	elif len(args) == 0:
		# this is ok too
		pass
	else:
		raise TypeError("mock takes zero, one, or two arguments - got %s" % (len(args),))
		
	if raw is None:
		raw = raw_mock()
	return MockWrapper(raw, proxied, name)

class MockWrapper(RealSetter):
	"""
	a mock object wrapper for use in test cases
	 - allows expectations and mock actions to be set
	
	all setattr and getattr calls go via the attached silent mock's _mock_get and _mock_set
	"""
	_all_expectations = None
	def __init__(self, wrapped_mock = None, proxied = None, name = None):
		if self.__class__._all_expectations is None:
			raise RuntimeError(("%s._setup has not been called. " +
				"Make sure you are inheriting from mocktest.TestCase, " +
				"not unittest.TestCase") % (self.__class__.__name__,))
		if wrapped_mock is None:
			wrapped_mock = raw_mock()
		if not isinstance(wrapped_mock, SilentMock):
			raise TypeError("expected SilentMock, got %s" % (wrapped_mock.__class__.__name__,))
		self._real_set(_mock = wrapped_mock)
		self._proxied = proxied
		if name:
			self.name = name
	
	# delegate getting and setting to SilentMock
	def _set(self, **kwargs):
		self._mock._mock_set(**kwargs)
	
	def _get(self, attr):
		return self._mock._mock_get(attr)
	
	def _get_mock(self):
		return self._mock
	raw = property(_get_mock)
			
	# mockExpecation integration
	@classmethod
	def _setup(cls):
		if not cls._all_expectations is None:
			raise RuntimeError("%s._setup has been called twice in a row"
				% (cls.__name__,))
		cls._all_expectations = []
	
	@classmethod
	def _teardown(cls):
		if cls._all_expectations is None:
			raise RuntimeError("%s._teardown has been called twice in a row"
				% (cls.__name__,))
		try:
			for expectation in cls._all_expectations:
				assert expectation, expectation
		finally:
			cls._all_expectations = None

	def __called_matcher(self):
		return MockMatcher(self)
	called = property(__called_matcher)
	
	def __wrapped_child(self, attr):
		"return a mock wrapper for an attribute of self"
		return type(self)(self.__child(attr))
	
	def __child(self, attr):
		return self._mock._mock_get_child(attr, force=True)
	
	def __expect_call_on(self, obj):
		matcher = MockMatcher(obj)
		self.__class__._all_expectations.append(matcher)
		return matcher

	def __expect_none(self):
		return self.is_expected.exactly(0).times
	def __expect_call_matcher(self):
		return self.__expect_call_on(self)
	is_expected = property(__expect_call_matcher)
	is_not_expected = property(__expect_none)

	def expects(self, methodname):
		return self.__wrapped_child(methodname).is_expected
	def does_not_expect(self, methodname):
		return self.__wrapped_child(methodname).is_not_expected

	def __str__(self):
		return 'mock wrapper for \"%s\"' %(self._get('name'))

	def __setattr__(self, attr, val):
		self._mock._mock_set(**{attr:val})

	def __getattr__(self, attr):
		return self._mock._mock_get(attr)
		
	def __delattr__(self, attr):
		self._mock._mock_del(attr)
	
	def reset(self):
		self._mock._mock_reset()
	
	def child(self, val):
		return self.__wrapped_child(val)
	method = child
	
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
	
	# selectively proxy calls; when should_intercept returns false then the
	# original (proxied) object is actually called, and no call on the mock is recorded
	def with_args(self, *args, **kwargs):
		self._ensure_can_set_intercept()
		self.should_intercept = lambda *a, **k: a == args and k == kwargs
		return self
	with_ = with_args

	def when_args(self, predicate):
		self._ensure_can_set_intercept()
		self.should_intercept = predicate
		return self
	when_ = when_args
	
	def _ensure_can_set_intercept(self):
		if self.should_intercept is not True:
			raise MockError("an interception condition (`with_args` or `where_args`) has already been set on mock %r" % (self._mock))

	def raising(self, ex):
		def mock_raise(*args, **kwargs):
			raise ex
		return self.with_action(mock_raise)

	def with_spec(self, spec):
		children = [member for member in dir(spec) if not 
			(member.startswith('__') and member.endswith('__'))]
		return self.with_children(*children)
	
	def with_methods(self, *methods, **kwmethods):
		self._with_children(*methods)
		for key in kwmethods:
			kwmethods[key] = raw_mock(return_value = kwmethods[key])
		return self.with_children(**kwmethods)
	
	def with_children(self, *children, **kwchildren):
		self._with_children(*children, **kwchildren)
		return self.frozen()
	
	def _with_children(self, *children, **kwchildren):
		"""internally add children, but don't freeze the mock"""
		for child in children:
			self.__child(child)
		for child, val in kwchildren.items():
			self.__child(child) # force the child to be created
			setattr(self._mock, child, val)
		return self
	
	def frozen(self):
		self._modifiable_children = False
		return self

	def unfrozen(self):
		self._modifiable_children = True
		return self
