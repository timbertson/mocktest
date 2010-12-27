from matchers import Matcher, SplatMatcher
__unittest = True

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
			raise AssertionError("Errors occurred during mocktest cleanup:\n%s" % ("\n".join(errors),))
		return False

def when(obj):
	return GetWrapper(lambda name: mock_when(obj, name))

def expect(obj):
	return GetWrapper(lambda name: mock_expect(obj, name))

def stub(obj):
	return GetWrapper(lambda name: mock_stub(obj, name))

def mock(name, create_on_access=True):
	return RecursiveStub(name, create_on_access)

def modify(obj):
	replacements = []
	def replace_(name, val):
		replace_attr(obj, name, val, generate_reset=len(replacements)==0)
		replacements.append(name)
	return RecursiveAssignmentWrapper(replace_)

def replace_attr(obj, name, val, generate_reset=True):
	assert MockTransaction.started
	if generate_reset:
		add_teardown_for_attr(obj, name)
	setattr(obj, name, val)
	return val

def add_teardown_for_attr(obj, attr):
	try:
		old_attr = getattr(obj, attr)
		reset = lambda: setattr(obj, attr, old_attr)
	except AttributeError:
		reset = lambda: delattr(obj, attr)
	MockTransaction.add_teardown(reset)


def mock_when(obj, name):
	return stub_method(obj, name)._new_act(name)

def mock_stub(obj, name):
	return stub_method(obj, name)._new_act(name).at_least(0).times()

def mock_expect(obj, name):
	return stub_method(obj, name)._new_act(name).at_least(1).times()

def _special_method(name):
	return name.startswith('__') and name.endswith('__')

from lib.realsetter import RealSetter
class RecursiveAssignmentWrapper(RealSetter):
	def __init__(self, callback):
		self._real_set(_callback=callback)
	
	def children(self, **children):
		[setattr(self, k, v) for k, v in children.items()]
		return self

	def methods(self, **methods):
		def do_return(return_value):
			return lambda *a, **k: return_value

		for k,v in methods.items():
			setattr(self, k, do_return(v))
		return self

	def copying(self, other):
		for attr in dir(other):
			if _special_method(attr): continue
			setattr(self, attr, lambda *a, **kw: None)
		return self

	def __setattr__(self, name, val):
		self._real_set(**{name:val})
		return self._callback(name, val)

	def __getattr__(self, name):
		if name in self.__dict__:
			return self._real_get(name)
		val = RecursiveAssignmentWrapper(self._callback)
		setattr(self, name, val)
		return val

class GetWrapper(object):
	def __init__(self, callback):
		self._callback = callback
		self._used = False

	def __getattr__(self, name):
		if self._used: raise RuntimeError("already used!")
		self._used = True
		return self._callback(name)
	
class Object(object):
	def __init__(self, name="unnamed object"):
		self.__name = name
	def __repr__(self): return "<#%s: %s>" % (type(self).__name__, self.__name)
	def __str__(self): return self.__name

class RecursiveStub(Object):
	def __init__(self, name="unnamed object", create_on_access=True):
		self.received_calls = []
		super(RecursiveStub, self).__init__(name)
		self._create_on_access = create_on_access

	def __getattr__(self, name):
		if not self._create_on_access:
			return super(RecursiveStub, self).__getattr__(name)
		obj = RecursiveStub(name=name)
		setattr(self, name, obj)
		return obj
	
	def __call__(self, *a, **kw):
		self.received_calls.append(Call(a,kw))
		return None

class Call(object):
	@classmethod
	def like(cls, *a, **kw):
		return cls(a, kw)

	def __init__(self, args, kwargs):
		self.args = args
		self.kwargs = kwargs
		self.tuple = (self.args, self.kwargs)
	
	def __eq__(self, other):
		if isinstance(other, type(self)):
			return self.tuple == other.tuple
		else:
			return self.tuple == other
	
	def __ne__(self, other):
		return not self.__eq__(other)
	
	def __str__(self):
		if self.kwargs:
			kwargs = ", " + ", ".join(["%s=%r" % (k,v) for k,v in self.kwargs.items()])
		else:
			kwargs = ''
		return "(%s%s)" % (", ".join(map(repr, self.args)), kwargs)
	
	def play(self, function):
		return function(*self.args, **self.kwargs)

def stub_method(obj, name):
	assert MockTransaction.started
	add_teardown_for_attr(obj, name)
	try:
		old_attr = getattr(obj, name)
		if isinstance(old_attr, StubbedMethod):
			return old_attr
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
	
	def __repr__(self):
		return "stubbed method %r" %(self.name,)
	
	def _new_act(self, name):
		act = MockAct(name)
		self.acts.append(act)
		return act
	
	def __call__(self, *a, **kw):
		call = Call(a, kw)
		self.calls.append(call)
		for act in reversed(self.acts):
			if act._matches(call):
				return act._act_upon(call)
		else:
			act_condition_descriptions = ["   - " + act.condition_description for act in self.acts]
			raise TypeError("stubbed method %r received unexpected arguments: %s\nAllowable argument conditions are:\n%s" % (self.name, call,"\n".join(act_condition_descriptions)))

	def _verify(self):
		for act in self.acts:
			if not act._satisfied_by(self.calls):
				raise AssertionError(act.summary(False, self.calls))

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

	def __init__(self, name):
		self.time = self.times = NoopDelegator(self)
		self._name = name
	
	def __call__(self, *args, **kwargs):
		"""
		restrict the checked set of function calls to those with
		arguments equal to (args, kwargs)
		"""
		self.__assert_not_set(self._cond_args, "argument condition")
		self._cond_args = self._args_equal_func(args, kwargs)
		self._cond_description = "arguments equal to: %s" % (Call(args, kwargs),)
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

	@property
	def condition_description(self):
		if self._cond_description is None:
			return "any arguments"
		return self._cond_description
	
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
	
	def never(self):
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

	def _match_or_equal(self, expected, actual):
		if isinstance(expected, Matcher):
			return expected.matches(actual)
		return actual == expected

	def _args_equal_func(self, args, kwargs):
		"""
		returns a function that returns whether its arguments match the
		args (tuple), and its keyword arguments match the kwargs (dict)
		"""
		def check_args(a, args):
			try:
				splat_pos = map(lambda x: isinstance(x, SplatMatcher), args).index(True)
			except ValueError:
				splat_pos = None

			if splat_pos is not None:
				expected_leading_args = args[:splat_pos]
				leading_args = a[:splat_pos]
				leading_match = check_args(leading_args, expected_leading_args)
				if not leading_match:
					return False

				#TODO: support trailing args in py3
				assert splat_pos == len(args)-1

				splattable_args = a[splat_pos:]
				splat_item = args[splat_pos]
				return splat_item.matches(splattable_args, {})

			if not len(a) == len(args):
				return False

			for expected, actual in zip(args, a):
				if not self._match_or_equal(expected, actual):
					return False
			return True
			
		def check_kwargs(k, kwargs):
			if kwargs.keys() == ['__kwargs']:
				return kwargs['__kwargs'].matches(k)

			if not len(k) == len(kwargs):
				return False

			if set(kwargs.keys()) != set(k.keys()):
				return False
				
			for key in kwargs.keys():
				if not self._match_or_equal(kwargs[key], k[key]):
					return False
			return True

		def check(*a, **k):
			return check_args(a, args) and check_kwargs(k, kwargs)
		return check
	
	def _equals_or_matches(self, expected, actual):
		if isinstance(expected, Matcher):
			return expected.matches(actual)
		return expected == actual

	def summary(self, matched=None, call_list=None):
		return "Mock \"%s\" %s expectations:\n expected %s\n %s" % (
			self._name,
			"has not yet checked" if matched is None else ("matched" if matched else "did not match"),
			self.describe(),
			'' if call_list is None else "received " + self.describe_reality(call_list))

	def __repr__(self):
		return self.summary()
		
	# fluffy user-visible expectation descriptions
	def describe(self):
		times = 'at least one' if self._multiplicity_description is None else self._multiplicity_description
		desc = "%s calls" % (times,)
		if self._cond_description is not None:
			desc += " with %s" % (self._cond_description)
		return desc
	
	def describe_reality(self, call_list):
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
