__all__ = (
	'raw_mock',
	'mock_wrapper',
	'mock_on',
	'__version__'
)

__version__ = '0.2'

import sys
from mockmatcher import MockMatcher

DEFAULT = object()

def _setup():
	MockWrapper._setup()

def _teardown():
	MockWrapper._teardown()


def expect(mock_wrapper):
	if not isinstance(mock_wrapper, MockWrapper):
		raise TypeError("Expected %s, got %s" % (MockWrapper, mock_wrapper.__class__))
	return mock_wrapper.is_expected

# mocking methods
def raw_mock(name = None):
	"""a silent mock object. use mock_of(silent_mock) to set expectations, etc"""
	kwargs = {}
	if name is not None:
		if not isinstance(name, str):
			raise TypeError("%r is not a string. did you mean to use mock_on(%r)?" % (name, name))
		kwargs['name'] = name
	return SilentMock(**kwargs)

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

def mock_on(parent, quiet = False):
	"""
	mock interface of parent.
	All attributes and items accessed through this returned object will become mocks on parent
	All mocks set via this mechanism will be rolled back at the end of your test case
	"""
	return AnchoredMock(parent, quiet)

class RealSetter(object):
	def _real_set(self, **kwargs):
		for k,v in kwargs.items():
			object.__setattr__(self, k, v)
	
	def _real_get(self, attr):
		return object.__getattribute__(self, attr)

class SilentMock(RealSetter):
	"""a mock object that minimises namespace collision"""
	def __init__(self, **kwargs):
		self._real_set(_mock_dict = {
			'action': None,
			'return_value':DEFAULT,
			'attrs':{},
			'_children':{},
			'_modifiable_children':True,
			'name':'unnamed mock',
			'_return_value_provided':False,
		})
		self._mock_reset()
		self._mock_set(**kwargs)
	
	def _mock_reset(self):
		resets = {
			'call_list':[],
		}
		for key,val in resets.items():
			self._mock_dict[key] = val
		print self._mock_get('call_list')
	
	def _mock_set(self, **kwargs):
		for attr, val in kwargs.items():
			print "setting %s on %r to %s" % (attr, self, val)
			if not attr in self._mock_dict:
				raise KeyError, "no such mock attribute: %s" % (attr,)
			self._mock_dict[attr] = val
			hookname = '_mock_set_%s_hook' % (attr,)
			try:
				print "trying hook: %s" % hookname
				self._real_get(hookname)(val)
				print "%s worked!" % hookname
			except AttributeError: pass

	def _mock_get(self, attr):
		return self._mock_dict[attr]
	
	def _mock_del(self, attr):
		hookname = '_mock_del_%s_hook' % (attr,)
		try:
			print "trying hook: %s" % hookname
			self._real_get(hookname)()
			print "%s worked!" % hookname
		except AttributeError: pass
	
	# hooks on mock attributes
	def _mock_set_return_value_hook(self, val):
		print "setting return value provided = true"
		self._mock_set(_return_value_provided=True)
	
	def _mock_del_return_value_hook(self):
		print "setting return value provided = false"
		self._mock_set(return_value=DEFAULT)
		self._mock_set(_return_value_provided=False)
	
	def __call__(self, *args, **kwargs):
		self._mock_get('call_list').append((args, kwargs))
		retval_done = False
		if self._mock_get('action') is not None:
			side_effect_ret_val = self._mock_get('action')(*args, **kwargs)
			print "return provided = %r" % (self._mock_get('_return_value_provided'),)
			if not self._mock_get('_return_value_provided'):
				retval = side_effect_ret_val
				retval_done = True
				print "retval side effected to %s" % (retval)

		if not retval_done:
			print "retval set to mocks return_value"
			retval = self._mock_get('return_value')

		if retval is DEFAULT:
			self._mock_set(return_value = SilentMock(name="return value for (%s)" % (self._mock_get('name'))))
			retval = self._mock_get('return_value')

		return retval

	def __fail_if_no_child_allowed(self, name):
		if name not in self._mock_get('_children'):
			if not self._mock_get('_modifiable_children'):
				raise AttributeError, "object (%s) has no attribute '%s'" % (self, name,)

	def __setattr__(self, attr, val):
		self.__fail_if_no_child_allowed(attr)
		self._mock_get('_children')[attr] = val

	def __getattribute__(self, name):
		if name.startswith('_'):
			try:
				return object.__getattribute__(self, name)
			except AttributeError:
				pass
			
		print "getting pretend attr %s" % name
		def _new():
			self._mock_get('_children')[name] = SilentMock(name=name)
			return self._mock_get('_children')[name]

		if name not in self._mock_get('_children'):
			self.__fail_if_no_child_allowed(name)
			child = _new()
		else:
			# child already exists
			child = self._mock_get('_children')[name]
			if child is DEFAULT:
				child = _new()
		return child

	def __str__(self):
		return 'mock: ' + str(self._mock_get('name'))

class MockWrapper(RealSetter):
	"""
	a mock object wrapper for use in test cases
	 - allows expectations and mock actions to be set
	
	all setattr and getattr go via the attahced silent mock's _mock_get and _mock_set
	"""
	def __init__(self, wrapped_mock = None):
		if self.__class__._all_expectations is None:
			raise RuntimeError("%s._setup has not been called. " +
				"Make sure you are inheriting from mock.TestCase, " +
				"not unittest.TestCase" % (self.__class__,))
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
	_all_expectations = None
	@classmethod
	def _setup(cls):
		cls._all_expectations = []
	
	@classmethod
	def _teardown(cls):
		for expectation in cls._all_expectations:
			assert expectation, expectation
		cls._all_expectations = None
		AnchoredMock._reset_all()

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
		print "resetting..."
		self.mock._mock_reset()
		
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
		print "adding children: %r and %r" % (children, kwchildren)
		for child in children:
			getattr(self.mock, child)
		for child, val in kwchildren.items():
			print "setting %s=%r" % (child, val)
			setattr(self.mock, child, val)
		print self._children
		return self
	
	def frozen(self):
		self._modifiable_children = False
		return self

	def unfrozen(self):
		self._modifiable_children = True
		return self



class AnchoredMock(RealSetter):
	_active = []
	def __init__(self, parent, quiet=False):
		self._init_records()
		self._real_set(_parent = parent)
		self._real_set(_quiet = quiet)
		self.__class__._active.append(self)
	
	def _init_records(self):
		self._real_set(_children = {})
		self._real_set(_items = {})
		self._real_set(_real_children = {})
		self._real_set(_real_items = {})
	
	def _child_store(self, in_dict):
		return self._items if in_dict else self._children

	def _real_child_store(self, in_dict):
		return self._real_items if in_dict else self._real_children
	
	def _backup_child(self, name, in_dict):
		try:
			# if it's replacing a real object, store it here for later
			real_child = getattr(self._parent, name) if not in_dict else self._parent[name]
		except (AttributeError, KeyError):
			if not self._quiet:
				print >> sys.stdout, "Warning: object %s has no %s \"%s\"" % (self._parent, "key" if in_dict else "attribute", name)
			return
			
		if isinstance(real_child, SilentMock):
			raise TypeError("Replacing a mock with another mock is a profoundly bad idea.\n" +
			                "Try re-using mock \"%s\" instead" % (name,))
		self._real_child_store(in_dict)[name] = real_child
	
	def _make_mock_if_required(self, name, in_dict=False):
		if name not in self._children:
			self._backup_child(name, in_dict)
			new_child = MockWrapper(SilentMock(name=name))
			self._child_store(in_dict)[name] = new_child
			# insert its SilentMock into the parent
			setattr(self._parent, name, new_child._mock)
		return self._child_store(in_dict)[name]

	@classmethod
	def _reset_all(cls):
		for mock in cls._active:
			mock._reset()
		cls._active = []
	
	# interchangeable deletion and setter methods
	@staticmethod
	def _setitem(target, name, val):
		target[name] = val
	
	@staticmethod
	def _setattr(target, name, val):
		setattr(target, name, val)
	
	@staticmethod
	def _delitem(target, name):
		del target[name]

	@staticmethod
	def _delattr(target, name):
		try:
			delattr(target, name)
		except StandardError:
			setattr(target, name, None)
	
	def _restore_children(self, in_dict):
		"""
		Restore all children from _real_children / _real_items
		(depending on in_dict) to self._parent.
		If a child does not appear in _real_*, it is deleted from self._parent.
		If that fails, it's set to None.
		"""
		children = self._child_store(in_dict)
		real_children = self._real_child_store(in_dict)
		if in_dict:
			assign = self._setitem
			del_ = self._delitem
		else:
			assign = self._setattr
			del_ = self._delattr
			
		for name in children:
			if name in real_children:
				assign(self._parent, name, real_children[name])
			else:
				del_(self._parent, name)
		
	def _reset(self):
		"""reset all children and items, then remove all record of them"""
		self._restore_children(in_dict = True)
		self._restore_children(in_dict = False)
		self._init_records()
			
	def __getattr__(self, attr):
		return self._make_mock_if_required(attr)
		
	def __setattr__(self, attr, val):
		child = self._make_mock_if_required(attr)
		child.return_value = val
	
	def __getitem__(self, attr):
		return self._make_mock_if_required(attr, in_dict=True)
	
	def __setitem__(self, attr, val):
		child = self._make_mock_if_required(attr, in_dict= True)
		child.return_value = val
	
	def expects(self, methodname):
		return getattr(self, methodname).is_expected
