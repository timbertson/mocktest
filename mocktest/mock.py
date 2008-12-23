__all__ = (
	'mock',
	'mock_wrapper',
	'mock_on',
	'__version__'
)

__version__ = '0.2'

import sys
from mockmatcher import MockMatcher

DEFAULT = object()

# mocking methods
def mock(name = None):
	"""a silent mock object. use mock_of(silent_mock) to set expectations, etc"""
	kwargs = {}
	if name is not None:
		if not isinstance(name, str):
			raise TypeError("%r is not a string. did you mean to use mock_on(%r)?" % (name, name))
		kwargs['name'] = name
	return SilentMock(**kwargs)

def mock_wrapper(silent_mock):
	"""
	return a mock wrapper for the given silent mock
	you can use the mock wrapper to set expectations or get invocation details
	for a slent mock
	"""
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

class SilentMock(RealSetter):
	"""a mock object that minimises namespace collision"""
	def __init__(self, **kwargs):
		self._real_set(_mock_dict = {
			'action': None,
			'return_value':DEFAULT,
			'_orig_children':{},
			'_modifiable_children':True,
			'name':'unnamed mock',
			'_return_value_provided':False,
		})
		self._mock_reset()
		self._mock_set(**kwargs)
	
	def _mock_reset(self):
		resets = {
			'attrs':{},
			'call_list':[],
			'_children':self._mock_get('_orig_children'),
		}
		for key,val in resets.items():
			self._mock_dict[key] = val

	def _mock_set(self, **kwargs):
		for attr, val in kwargs.items():
			if not attr in self._mock_dict:
				raise KeyError, "no such mock attribute: %s" % (attr,)
			self._mock_dict[attr] = val
			hookname = '_mock_set_%s_hook' % (attr,)
			try:
				object.__getattr__(self, hookname)(val)
			except AttributeError: pass

	def _mock_get(self, attr):
		return self._mock_dict[attr]
	
	def _mock_del(self, attr):
		self._mock_dict.delattr(attr)
		hookname = '_mock_del_%s_hook' % (attr,)
		if hasattr(self, hookname):
			getattr(self, hookname)()
	
	def _mock_set_return_val_hook(self, val):
		self._set(_return_value_provided=True)
	
	def _mock_del_return_val_hook(self):
		self._set(_return_value_provided=False)
	
	def __call__(self, *args, **kwargs):
		self._mock_get('call_list').append((args, kwargs))
		retval = self._mock_get('return_value')

		if self._mock_get('action') is not None:
			side_effect_ret_val = self._mock_get('action')(*args, **kwargs)
			retval = side_effect_ret_val

		if self._mock_get('_return_value_provided'):
			# make sure the side_effect didn't get precedence
			retval = self._return_value
		return retval
	
	def __setattr__(self, attr, val):
		self._mock_get('attrs')[attr] = val

	def __getattribute__(self, name):
		if name.startswith('_'):
			try:
				return object.__getattribute__(self, name)
			except AttributeError:
				pass
			
		def _new():
			self._mock_get('_children')[name] = self._mock_make_child(name)
			return self._mock_get('_children')[name]

		if name not in self._mock_get('_children'):
			if not self._mock_get('_modifiable_children'):
				raise AttributeError, "object has no attribute '%s'" % (name,)
			child = _new()
		else:
			# child already exists
			child = self._mock_get('_children')[name]
			if child is DEFAULT:
				child = _new()
		return child

	def __str__(self):
		return 'mock: ' + str(self._mock_get('name'))

	def _mock_make_child(self, name, return_value=DEFAULT):
		return SilentMock(name=name)



class MockWrapper(RealSetter):
	"""
	a mock object wrapper for use in test cases
	 - allows expectations and mock actions to be set
	
	all setattr and getattr go via the attahced silent mock's _mock_get and _mock_set
	"""
	def __init__(self, wrapped_mock = None):
		if self.__class__._all_expectations is None:
			raise RuntimeError, "%s._setup has not been called. Make sure you are inheriting from mock.TestCase, not unittest.TestCase" % (self.__class__,)
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
		return MockMatcher(self)
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
		self._mock._mock_get(attr)

	def __reset_mock(self, obj):
		if isinstance(obj, self.__class__):
			obj._mock_reset()
	
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

	def with_spec(self, specitem):
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
			getattr(self, child)
		for child, val in kwchildren.items():
			setattr(self, child, val)
		return self
	
	def with_items(self, **kwargs):
		for k,v in kwargs.items():
			self[k] = v
		return self
	
	def frozen(self):
		self.frozen = True
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
