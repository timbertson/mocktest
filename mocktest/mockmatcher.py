from matchers import Matcher
__unittest = True

class MockTransaction(object):
	teardown_actions = None
	@classmethod
	def add_teardown(cls, func):
		cls.teardown_actions.append(func)
	
	@classmethod
	def __enter__(cls):
		assert cls.teardown_actions is None
		cls.teardown_actions = []

	@classmethod
	def __exit__(cls):
		try:
			for action in reversed(cls.teardown_actions):
				action()
		finally:
			cls.teardown_actions = None
		return False

def when(obj):
	return GetWrapper(lambda name: mock_when(obj, name))

def expect(obj):
	return GetWrapper(lambda name: mock_expect(obj, name))

def replace(obj):
	return AssignmentWrapper(lambda name, val: replace_attr(obj, name, val))

def replace_attr(obj, name, val):
	try:
		old_attr = getattr(obj, name)
		def reset():
			setattr(obj, name, old_attr)
		MockTransaction.add_teardown(reset)
	except AttributeError:
		pass
	setattr(obj, name, val)


def mock_when(obj, name):
	stub_method(obj, name)._new_act()

def mock_expect(obj, name):
	stub_method(obj, name)._new_act().at_least(1).times()

class AssignmentWrapper(object):
	def __init__(self, callback):
		self.__callback = callback
		self.__used = False

	def __setattr__(self, name, val):
		if self.__used: raise RuntimeError("already used!")
		self.__used = True
		return self.__callback(name, val)

class GetWrapper(object):
	def __init__(self, callback):
		self.__callback = callback
		self.__used = False

	def __getattr__(self, name):
		if self.__used: raise RuntimeError("already used!")
		self.__used = True
		return self.__callback(name)

class Object(object):
	def __init__(self, name="unnamed object"):
		self.__name = name
	def __repr__(self): return "<#%s: %s>" % (type(self).__name__, self.__name)
	def __str__(self): return self.__name

class RecursiveStub(Object):
	def __getattr__(self, name):
		obj = RecursiveStub(name=name)
		setattr(self, name, obj)
		return obj

class Call(object):
	@classmethod
	def like(cls, *a, **kw):
		return cls(a, kw)

	def __init__(self, args, kwargs):
		self.args = args
		self.kwargs = kwargs
	
	def play(self, function):
		return function(*self.args, **self.kwargs)

def stub_method(obj, name):
	try:
		old_attr = getattr(obj, name)
		if isinstance(old_attr, StubbedMethod):
			return old_attr
		def reset():
			setattr(obj, name, old_attr)
		MockTransaction.add_teardown(reset)
	except AttributeError:
		pass
	new_attr = StubbedMethod(name)
	setattr(obj, name, new_attr)
	return new_attr


class StubbedMethod(object):
	def __init__(self, name):
		self.acts = []
		self.name = name
		self.calls = []
		MockTransaction.add_teardown(self._verify)
	
	def _new_act(self):
		act = MockAct()
		self.acts.append(act)
		return act
	
	def __call__(self, *a, **kw):
		call = Call(a, kw)
		self.calls.append(call)
		for act in self.acts:
			if act._matches(call):
				act.act_upon(call)
				break
		else:
			raise TypeError("no matching actions found for arguments: %r" % (call,))

	def _verify(self):
		for act in self.acts:
			if not act._satisfied_by(self.calls):
				raise AssertionError(act.summary(False))

class NoopDelegator(object):
	def __init__(self, delegate):
		self._delegate = delegate

	def __call__(self):
		return self._delegate

	def __getattr__(self, attr):
		return getattr(self._delegate, attr)

class MockAct(object):
	_multiplicity = None
	_multiplicity_description = None
	
	_cond_args = None
	_cond_description = None

	_action = None

	def __init__(self, target):
		target._mock_acts
		self.time = self.times = NoopDelegator(self)
	
	def __call__(self, *args, **kwargs):
		"""
		restrict the checked set of function calls to those with
		arguments equal to (args, kwargs)
		"""
		self.__assert_not_set(self._cond_args, "argument condition")
		self._cond_args = self._args_equal_func(args, kwargs)
		self._cond_description = "with arguments equal to: %s" % (Call(args, kwargs),)
		return self

	def _matches(self, call):
		if self._cond_args is None:
			return True
		try:
			return call.play(self._cond_args)
		except TypeError:
			return False
		return True
	
	def _satisfied_by(self, calls):
		if self._multiplicity is None:
			return True
		matched_calls = filter(self._matches, calls)
		return self._multiplicity(len(matched_calls))

	def _act_upon(self, call):
		if self._action is None:
			return None
		return call.play(self._action)
	
	def where(self, func):
		"""
		restrict the checked set of function calls to those where
		func(*args, **kwargs) is True
		"""
		self.__assert_not_set(self._cond_args, "argument condition")
		self._cond_args = func
		self._cond_description = "where arguments satisfy the supplied function: %r" % (func,)
		return self

	def exactly(self, n):
		"""set the allowed number of calls made to this function"""
		self._multiplicity = lambda x: x == n
		self._multiplicity_description = "exactly %s" % (n,)
		return self
	
	def at_least(self, n):
		"""set the allowed number of calls made to this function"""
		self._multiplicity = lambda x: x >= n
		self._multiplicity_description = "at least %s" % (n,)
		return self
	
	def at_most(self, n):
		"""set the allowed number of calls made to this function"""
		self._multiplicity = lambda x: x <= n
		self._multiplicity_description = "at most %s" % (n,)
		return self
	
	def between(self, start_range, end_range):
		"""set the allowed number of calls made to this function"""
		self._multiplicity = lambda x: x >= start_range and x <= end_range
		self._multiplicity_description = "between %s and %s" % (start_range, end_range)
		return self

	# syntactic sugar to make more readabale expressions
	def __noop(self): return self
	times = property(__noop)
	time = property(__noop)
	
	def no_times(self):
		"""alias for exactly(0).times"""
		return self.exactly(0)
		
	def once(self):
		"""alias for exactly(1).times"""
		return self.exactly(1)
		
	def twice(self):
		"""alias for exactly(2).times"""
		return self.exactly(2)
	
	def thrice(self):
		"""alias for exactly(3).times"""
		return self.exactly(3)
	
	# overloading
	def __eq__(self, other):
		"""
		overloaded operator for comparing to True or False
		"""
		return self._matches() == other
	
	def __nonzero__(self):
		return self._matches()
		
	def __assert_not_set(self, var, msg="this value"):
		if var is not None:
			raise ValueError, "%s has already been set" % (msg,)
	
	def _args_equal_func(self, args, kwargs):
		"""
		returns a function that returns whether its arguments match the
		args (tuple), and its keyword arguments match the kwargs (dict)
		"""
		def check(*a, **k):
			if not len(a) == len(args) and len(k) == len(kwargs):
				return False
			
			for expected, actual in zip(args, a):
				if not self._match_or_equal(expected, actual):
					return False
			
			if set(kwargs.keys()) != set(k.keys()):
				return False
				
			for key in kwargs.keys():
				if not self._match_or_equal(kwargs[key], k[key]):
					return False
			return True
		return check
	
	def _equals_or_matches(self, expected, actual):
		if isinstance(expected, Matcher):
			return expected.matches(actual)
		return expected == actual

	def summary(self, matched=None):
		return "Mock \"%s\" %s expectations:\n expected %s\n received %s" % (
			self._mock,
			"has not yet checked" if matched is None else ("matched" if matched else "did not match"),
			self.describe(),
			self.describe_reality())

	def __repr__(self):
		return self.summary()
		
	# fluffy user-visible expectation descriptions
	def describe(self):
		times = 'at least one' if self._multiplicity_description is None else self._multiplicity_description
		desc = "%s calls" % (times,)
		if self._cond_description is not None:
			desc += " %s" % (self._cond_description)
		return desc
	
	def describe_reality(self):
		call_list = self.call_list
		call_count = len(call_list)
		desc = "%s calls" % (call_count,)
		if call_count > 0:
			desc += " with arguments:"
			i = 1
			for arg_set in call_list:
				desc += "\n  %s:   %s" % (i, arg_set)
				i += 1
		return desc

	def and_return(self, val):
		self._action = lambda *a, **k: val
		return self
	then_return = and_return
	returning = and_return
	
	def and_call(self, func):
		self._action = func
		return self
	then_call = and_call
	calling = and_call

	def and_raise(self, exc):
		def _do_raise(*a, **kw):
			raise exc
		self._action = _do_raise
		return self
