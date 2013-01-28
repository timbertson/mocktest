from __future__ import absolute_import
from .matchers import Matcher, SplatMatcher
from .mockerror import MockError
from .callrecord import Call
from .transaction import MockTransaction
import itertools
import collections
import operator

from .lib.singletonclass import ensure_singleton_class
__unittest = True

__all__ = [
	'when',
	'expect',
	'mock',
	'modify',
	'Object',
]

class ReturnValuesExhausted(Exception): pass

Settable = collections.namedtuple('Settable', ('get','set','delete', 'error'))
Item = Settable(
	get=operator.getitem,
	set=operator.setitem,
	delete=operator.delitem,
	error=KeyError,
)

Attr = Settable(
	get=getattr,
	set=setattr,
	delete=delattr,
	error=AttributeError,
)

def when(obj):
	"""
	Replace a method on an object. Just like `expect`, except
	that no verification against the number of calls received
	will be performed.

	:rtype: :class:`~mocktest.mocking.MockAct`
	"""
	return GetWrapper(lambda name: mock_when(obj, name))

def expect(obj):
	"""
	Add an expectation to a method of `obj`.
	By default, the method is expected at least once.
	E.g:
		>>> expect(some_object).method

	:rtype: :class:`~mocktest.mocking.MockAct`
	"""
	return GetWrapper(lambda name: mock_expect(obj, name))

def mock(name='unnamed mock', create_children=True):
	"""
	Make a mock object.

	:param name: the name of this mock object
	:param create_children: when attributes are accessed on this
		mock, they will be created by default. Set this to False to
		raise an AttributeError instead
	:rtype: :class:`~mocktest.mocking.RecursiveStub`
	"""
	return RecursiveStub(name, create_children)

def modify(obj):
	"""
	Replace children of an existing object for the duration of
	this test. E.g:
		>>> modify(obj).child = replacement_child
		>>> modify(obj).grand.child = replacement_grand_child
		>>> modify(obj)['item'] = replacement_item
	
	All replaced attributes / items will be reverted when the test completes.

	:rtype: :class:`~mocktest.mocking.RecursiveAssignmentWrapper`
	"""
	return RecursiveAssignmentWrapper(obj)

def add_teardown_for(obj, attr, settable = Attr):
	"""add a hook to remove `attr` when transaction ends.
	Settable can be Attr or Item"""
	try:
		old_attr = settable.get(obj, attr)
	except settable.error:
		reset = lambda: settable.delete(obj, attr)
	else:
		reset = lambda: settable.set(obj, attr, old_attr)
	MockTransaction.add_teardown(reset)

def delegating_settable_with_rollback(obj, settable):
	"""a settable that, when `set` is called, will add
	a teardown hook to revert this key to the original value
	(which includes deleting it if it didn't initially exist).

	Teardown methods are only added the first time each new
	attribute is encountered.
	"""
	keys = set()
	def _set(_ignored_obj, name, val):
		assert MockTransaction.started
		if name not in keys:
			add_teardown_for(obj, name, settable)
			keys.add(name)
		settable.set(obj, name, val)
	_get = lambda _, *a: settable.get(obj, *a)
	_delete = lambda _, *a: settable.delete(obj, *a)
	return settable._replace(get=_get, set=_set, delete=_delete)

def fallback_settable(fallback_obj, settable):
	"""a settable that will set items locally, and fallback to the original object when
	`get` is called for an unset key"""
	d = {}
	def _get(_ignored_obj, name):
		if name in d:
			return d[name]
		else:
			return settable.get(obj, name)
	
	def _set(_ignored_obj, name, val):
		d[name] = val
	def _delete(_ignored_obj, name, val):
		del d[name]

	return settable._replace(get=_get, set=_set, delete=_delete)

def mock_when(obj, name):
	return stub_method(obj, name)._new_act(name).at_least(0).times()

def mock_expect(obj, name):
	return stub_method(obj, name)._new_act(name).at_least(1).times()

def _special_method(name):
	return name.startswith('__') and name.endswith('__')


def assign_kwargs_children(self, **children):
	[setattr(self, k, v) for k, v in children.items()]
	return self

def assign_kwargs_methods(self, **methods):
	def do_return(return_value):
		return lambda *a, **k: return_value

	for k,v in methods.items():
		setattr(self, k, do_return(v))
	return self

from .lib.realsetter import RealSetter
class RecursiveAssignmentWrapper(RealSetter):
	"""
	The return value from :func:`modify`.

	Assigning a value to an attribute of this object
	assigns the same value to the original object, but
	only for the duration of the current test.

	The same goes for items (i.e dictionary-style access).

	Getting an attribute or item from this object replaces
	that item on the original object with a wrapped version
	that always supports assignment of attributes / items.
	This is useful e.g to replace readonly attributes
	on nested objects:

	# does NOT work, as `write` is not assignable
	>>> modify(sys.stderr).write = my_write_func

	# but we can work around it, by replacing the whole `stderr`
	# object with one that has all the values of the real `stderr`
	# but allowing us to override of any attribute:
	>>> modify(sys).stderr.write = my_write_func
	"""
	def __init__(self, delegate, modify_delegate=True):
		self._real_set(_modify_delegate=modify_delegate)
		if modify_delegate:
			item = delegating_settable_with_rollback(delegate, Item)
			attr = delegating_settable_with_rollback(delegate, Attr)
		else:
			item = fallback_settable(delegate, Item)
			attr = fallback_settable(delegate, Attr)

		self._real_set(_item_setter=item)
		self._real_set(_attr_setter=attr)
	
	def children(self, **children):
		"""
		Set children via kwargs, e.g.:

			>>> modify(obj).children(x=1, y='child y')
			>>> obj.x
			1
			>>> obj.y
			'child y'
		"""
		return assign_kwargs_children(self, **children)

	def methods(self, **methods):
		"""
		Set child methods via kwargs, e.g.:

			>>> modify(obj).methods(x=1, y=mock('child y'))
		"""
		return assign_kwargs_methods(self, **methods)

	def copying(self, other, value=lambda *a, **kw: None):
		"""
		Copy all non-special attributes of `other`, setting
		the value of each child to `value`. The default `value` paramater
		is a function returning `None` for all arguments.
		"""
		for attr in dir(other):
			if _special_method(attr): continue
			setattr(self, attr, value)
		return self

	def __setitem__(self, key, val):
		self._item_setter.set(self, key, val)

	def __setattr__(self, key, val):
		self._attr_setter.set(self, key, val)
		self._real_set(**{key:val})

	def _do_get(self, name, settable):
		if self._modify_delegate:
			return self._mutating_get(name, settable)
		else:
			return settable.get(self, name)

	def _mutating_get(self, name, settable):
		"""get an item or attr from the original object, wrapping it in a RecursiveAssignmentWrapper()"""
		try:
			delegate = settable.get(self, name)
		except settable.error:
			delegate = DictObject(name)
		if not isinstance(delegate, RecursiveAssignmentWrapper):
			delegate = RecursiveAssignmentWrapper(delegate, modify_delegate = False)
			settable.set(self, name, delegate)
		return delegate

	def __getattr__(self, name):
		return self._do_get(name, self._attr_setter)

	def __getitem__(self, name):
		return self._do_get(name, self._item_setter)

class GetWrapper(object):
	"""
	An intermediate object that calls its callback when an attribute
	is accessed (via __getattr__).
	Can only be used once, or it throws an error
	"""
	def __init__(self, callback):
		self._callback = callback
		self._used = False

	def __getattr__(self, name):
		if self._used: raise RuntimeError("already used!")
		self._used = True
		return self._callback(name)

	def __getitem__(self, name): # workaround for special methods like __new__
		return self.__getattr__(name)
	
	@property
	def __call__(self):
		return self.__getattr__('__call__')
	
class Object(object):
	"""a named object"""
	def __init__(self, name="unnamed object"):
		self.__name = name
	def __repr__(self): return "<#%s: %s>" % (type(self).__name__, self.__name)
	def __str__(self): return self.__name

class DictObject(dict):
	def __init__(self, name="unnamed object"):
		self.__name = name
		super(DictObject, self).__init__()
	def __repr__(self): return "<#%s: %s>" % (type(self).__name__, self.__name)
	def __str__(self): return self.__name

class RecursiveStub(Object):
	"""
	The return value from :func:`mock`.

	An object that returns new instances of itself when attributes
	are accessed (unless create_unknown_children is False).

	Returns None (and saves the call information) when called
	"""
	def __init__(self, name="unnamed object", create_unknown_children=True):
		self.received_calls = []
		super(RecursiveStub, self).__init__(name)
		self._create_unknown_children = create_unknown_children

	def __getattr__(self, name):
		if not self._create_unknown_children:
			return super(RecursiveStub, self).__getattr__(name)
		obj = RecursiveStub(name=name)
		setattr(self, name, obj)
		return obj
	
	def __call__(self, *a, **kw):
		self.received_calls.append(Call(a,kw, stack=True))
		return None

	def with_children(self, **children):
		"""
		Set children via kwargs, e.g.:

			>>> mock("name").with_children(x=1, y='child y')
			>>> obj.x
			1
			>>> obj.y
			'child y'
		"""
		return assign_kwargs_children(self, **children)

	def with_methods(self, **methods):
		"""
		Set child methods via kwargs, e.g.:

			>>> mock("name").with_methods(x=1, y=mock('child y'))
			>>> obj.x()
			1
			>>> obj.y()
			'child y'
		"""
		return assign_kwargs_methods(self, **methods)

def stub_method(obj, name):
	assert MockTransaction.started, "Mock transaction has not been started. Make sure you are inheriting from mocktest.TestCase"
	if _special_method(name) and not isinstance(obj, type):
		ensure_singleton_class(obj)
		obj = type(obj)
	add_teardown_for(obj, name)
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
	"""
	This is the type that mocktest uses as a stand-in for a replaced (stubbed) method. For example:
		>>> when(obj).method().then_return(True)
	
	Will set ``obj.method`` to an instance of StubbedMethod (for the duration of the current test)

	.. data:: received_calls:

		The set of calls this stub has received, as a list of :class:`~mocktest.callrecord.Call` instances.
	"""
	def __init__(self, name):
		self._acts = []
		self._name = name
		self.received_calls = []
		MockTransaction.add_teardown(self._verify)
	
	def __repr__(self):
		return "stubbed method %r" %(self._name,)
	
	def _new_act(self, name):
		act = MockAct(name)
		self._acts.append(act)
		return act
	
	def __call__(self, *a, **kw):
		call = Call(a, kw, stack=True)
		self.received_calls.append(call)
		for act in reversed(self._acts):
			if act._matches(call):
				try:
					return act._act_upon(call)
				except ReturnValuesExhausted:
					raise AssertionError(
						"%r ran out of return values.\n"
						"Received %s"
						% (act, act.describe_reality(self.received_calls)))
		else:
			act_condition_descriptions = ["   - " + act.condition_description for act in reversed(self._acts)]
			raise TypeError(
				"stubbed method %r received unexpected arguments: %s\n"
				"Allowable argument conditions are:\n%s" % (
					self._name,
					call.desc(),
					"\n".join(act_condition_descriptions))
				)

	def _verify(self):
		for act in self._acts:
			if not act._satisfied_by(self.received_calls):
				raise AssertionError(act.summary(False, self.received_calls))

class NoopDelegator(object):
	def __init__(self, delegate):
		self._delegate = delegate

	def __call__(self):
		return self._delegate

	def __getattr__(self, attr):
		return getattr(self._delegate, attr)

class MockAct(object):
	"""
	The return type from :func:`when` and :func:`expect`.
	"""
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
		matched_calls = list(filter(self._matches, calls))
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
		Match only when `condition_func` returns true, when called with the same
		arguments as this method.
		"""
		self.__assert_not_set(self._cond_args, "argument condition")
		self._cond_args = func
		self._cond_description = "where arguments satisfy the supplied function: %r" % (func,)
		return self

	def exactly(self, n):
		"""
		Expect this act to be triggered exactly `number` times.
		Usually followed by `times()` for readability, as in:
			>>> expect(obj).meth.exactly(3).times()
		"""
		self._multiplicity = lambda x: x == n
		self._multiplicity_description = "exactly %s" % (n,)
		return self
	
	def at_least(self, n):
		"""Expect this act to match at least `number` times."""
		self._multiplicity = lambda x: x >= n
		self._multiplicity_description = "at least %s" % (n,)
		return self
	
	def at_most(self, n):
		"""Expect this act to match at most `number` times."""
		self._multiplicity = lambda x: x <= n
		self._multiplicity_description = "at most %s" % (n,)
		return self
	
	def between(self, start_range, end_range):
		"""Expect this act to match between `lower` and `upper` times."""
		self._multiplicity = lambda x: x >= start_range and x <= end_range
		self._multiplicity_description = "between %s and %s" % (start_range, end_range)
		return self
	
	def never(self):
		"""Alias for exactly(0).times"""
		return self.exactly(0)
		
	def once(self):
		"""Alias for exactly(1).times"""
		return self.exactly(1)
		
	def twice(self):
		"""Alias for exactly(2).times"""
		return self.exactly(2)
	
	def thrice(self):
		"""Alias for exactly(3).times"""
		return self.exactly(3)
	
	def __assert_not_set(self, var, msg="this value"):
		if var is not None:
			raise MockError("%s has already been set" % (msg,))

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
				splat_pos = [isinstance(x, SplatMatcher) for x in args].index(True)
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
			kwargs = kwargs.copy()
			wildcard_kwargs_matcher = kwargs.pop('__kwargs', None)
			if wildcard_kwargs_matcher is not None:
				def splitdict(d, keys):
					included, others = {}, {}
					for k, v in d.items():
						if k in keys:
							included[k] = v
						else:
							others[k] = v
					return included, others

				explicit_kwargs, wildcard_kwargs = splitdict(k, list(kwargs.keys()))
				return check_kwargs(explicit_kwargs, kwargs) and wildcard_kwargs_matcher.matches(wildcard_kwargs)

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
		return "Stubbed method %r" % (self._name,)
		
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

	def and_return(self, val, *subsequent_vals):
		"""
		When this act matches, return the given `result` to the caller.
		If provided with multiple arguments, those values will be returned in order. e.g:

			>>> expect(obj).foo().and_return(True, True, False)
			>>> obj.foo()
			True
			>>> obj.foo()
			True
			>>> obj.foo()
			False

		Once all return values have been used up, any further calls with throw a :class:`~mocktest.MockError`.


		**Note:** :func:`and_raise`, :func:`and_return` and :func:`and_call` each have a `then_*` alias
		for better readability when using :func:`when`. e.g:

			>>> expect(obj).foo().and_return(True)
		
		Is readable, however when using :func:`when`, the following is more readable:

			>>> when(obj).foo().then_return(True)
		
		Both `and_` and `then_` versions have the same effect however.
		"""
		if subsequent_vals:
			vals = [val] + list(subsequent_vals)
			def action(*a, **k):
				try:
					return vals.pop(0)
				except IndexError:
					raise ReturnValuesExhausted()
 
			self._action = action
		else:
			self._action = lambda *a, **k: val
		return self
	then_return = and_return
	
	def and_call(self, func):
		"""When this act matches, call the given `func` and return its value."""
		self._action = func
		return self
	then_call = and_call

	def and_raise(self, exc):
		"""When this act matches, raise the given exception instance."""
		def _do_raise(*a, **kw):
			raise exc
		self._action = _do_raise
		return self
	then_raise = and_raise
