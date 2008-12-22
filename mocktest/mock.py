# mock.py
# Test tools for mocking and patching.
# Copyright (C) 2007-2008 Michael Foord
# E-mail: fuzzyman AT voidspace DOT org DOT uk

# mock 0.4.0
# http://www.voidspace.org.uk/python/mock.html

# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# modified by Tim Cuthbertson to integrate MockMatcher functionality

# __all__ = (
# 	'Mock',
# 	'patch',
# 	'patch_object',
# 	'sentinel',
# 	'__version__'
# )

__version__ = '0.4.0'

from mockmatcher import MockMatcher

DEFAULT = object()

# class Mock(object):
# 	def __set(self, **kwargs):
# 		"""
# 		self.__set(foo=bar) is just like self.foo='bar', except
# 		it bypasses Mock's __setattr__ magic
# 		"""
# 		for attr, val in kwargs.items():
# 			object.__setattr__(self, attr, val)
# 
# 	def __init__(self, _polymorphic_spec=None, name=None,
# 				 methods=None, spec=None, action=None,
# 				 children=None, return_value=DEFAULT, parent=None,
# 				 frozen=None):
# 		if _polymorphic_spec is not None:
# 			# depending on the type of the first argument, use it as:
# 			# dict -> methods
# 			# list -> methods
# 			# str -> name
# 			# everyhing else -> spec
# 			polymorphic_type = type(_polymorphic_spec)
# 			polymorphic_err = ValueError("type of first argument (%s) conflicts with a provided keyword argument" % (polymorphic_type,))
# 			if polymorphic_type == str:
# 				if name is not None:
# 					raise ValueError, "first argument looks like a name, but name was also provided"
# 				name = _polymorphic_spec
# 			else:
# 				if (methods is not None or children is not None) and spec is not None:
# 					# spec and (methods OR chilren) collide
# 					raise polymorphic_err
# 				if polymorphic_type == dict or polymorphic_type == list:
# 					if methods is not None:
# 						raise polymorphic_err
# 					methods = _polymorphic_spec
# 				else:
# 					spec = _polymorphic_spec
# 		
# 		self.__set(_parent = parent)
# 		self.__set(_name = name)
# 		children = self._make_children(children=children, methods=methods, spec=spec)
# 		self.__set(_orig_children = children, _children = children)
# 		if frozen is not None:
# 			self.__set(_modifiable_children = not frozen)
# 		self.__set_return_value(return_value)
# 		self.__set(_return_value_provided = (return_value is not DEFAULT))
# 		self.__set(_side_effect = action)
# 		
# 		self.reset()
# 		
# 	# mockExpecation integration
# 	_all_expectations = None
# 	@classmethod
# 	def _setup(cls):
# 		cls._all_expectations = []
# 	
# 	@classmethod
# 	def _teardown(cls):
# 		for expectation in cls._all_expectations:
# 			assert expectation, expectation
# 		cls._all_expectations = None
# 
# 	def __called_matcher(self):
# 		return MockMatcher(self)
# 	called = property(__called_matcher)
# 	
# 	def __expect_call_matcher(self):
# 		if self.__class__._all_expectations is None:
# 			raise RuntimeError, "Mock._setup has not been called. Make sure you are inheriting from mock.TestCase, not unittest.TestCase"
# 		matcher = MockMatcher(self)
# 		self.__class__._all_expectations.append(matcher)
# 		return matcher
# 	is_expected = property(__expect_call_matcher)
# 
# 	def __str__(self):
# 		return str(self._name) if self._name is not None else "unknown-mock"
# 
# 	def __reset_mock(self, obj):
# 		if isinstance(obj, Mock):
# 			obj.reset()
# 			
# 	def reset(self):
# 		self.__set(call_args = None)
# 		self.__set(call_count = 0)
# 		self.__set(call_args_list = [])
# 		self.__set(method_calls = [])
# 		for child in self._children.itervalues():
# 			self.__reset_mock(child)
# 		self.__reset_mock(self._return_value)
# 
# 		self.__set(_children = self._orig_children.copy())
# 	
# 	def __get_return_value(self):
# 		if self._return_value is DEFAULT:
# 			self.__set(_return_value = Mock())
# 		return self._return_value
# 	
# 	def __set_return_value(self, value):
# 		self.__set(_return_value = value)
# 		self.__set(_return_value_provided = True)
# 	return_value = property(__get_return_value, __set_return_value)
# 	
# 	def __call__(self, *args, **kwargs):
# 		self.call_count += 1
# 		self.call_args = (args, kwargs)
# 		self.call_args_list.append((args, kwargs))
# 		
# 		parent = self._parent
# 		name = self._name
# 		while parent is not None:
# 			parent.method_calls.append((name, args, kwargs))
# 			if parent._parent is None:
# 				break
# 			name = parent._name + '.' + name
# 			parent = parent._parent
# 
# 		retval = self.return_value
# 		if self._side_effect is not None:
# 			side_effect_ret_val = self._side_effect(*args, **kwargs)
# 			retval = side_effect_ret_val
# 
# 		if self._return_value_provided:
# 			# make sure the side_effect didn't get precedence
# 			retval = self._return_value
# 		return retval
# 	
# 	def _make_children(self, children = None, spec = None, methods = None):
# 		if methods is children is spec is None:
# 			# none provided
# 			self.__set(_modifiable_children = True)
# 			return {}
# 
# 		if (methods is not None or children is not None) and spec is not None:
# 			raise ValueError, "you cannot provide both spec and methods/children"
# 		
# 		# get rid of Nones, and ensure types are okay
# 		methods, children = [[] if x is None else x for x in (methods, children)]
# 		for x in (methods, children):
# 			if not (isinstance(x, list) or isinstance(x, dict)):
# 				raise TypeError, "expecting methods/children to be a list or dict, it is a %s" % (x.__class__,)
# 		
# 		self.__set(_modifiable_children = False)
# 		
# 		child_hash = {}
# 		
# 		# grab methods from a spec object
# 		if spec is not None:
# 			children = [member for member in dir(spec) if not 
# 				(member.startswith('__') and member.endswith('__'))]
# 
# 		def assert_uniq(name):
# 			if name in child_hash:
# 				raise ValueError, "%s specified as both method and child attribute"
# 
# 		# children
# 		if isinstance(children, list):
# 			for name in children:
# 				assert_uniq(name)
# 				child_hash[name] = DEFAULT
# 		else:
# 			child_hash = children
# 
# 		# methods
# 		if isinstance(methods, list):
# 			for name in methods:
# 				assert_uniq(name)
# 				child_hash[name] = DEFAULT
# 		else:
# 			for name, retval in methods.items():
# 				assert_uniq(name)
# 				child_hash[name] = self._make_child(name, retval)
# 
# 		return child_hash
# 		
# 	def _make_child(self, name, return_value=DEFAULT):
# 		return Mock(parent=self, name=name, return_value=return_value)
# 
# 	def __has_attr(self, attr):
# 		try:
# 			object.__getattribute__(self, attr)
# 			return True
# 		except AttributeError:
# 			return False
# 
# 	def __setattr__(self, attr, val):
# 		if self.__has_attr(attr):
# 			object.__setattr__(self, attr, val)
# 			return
# 
# 		if not self._modifiable_children:
# 			raise AttributeError, "Cannot set attribute %r (to %r) on mock '%s'" % (attr, val, self)
# 		self._children[attr] = val
# 
# 	def __getattr__(self, name):
# 		def _new():
# 			self._children[name] = self._make_child(name)
# 			return self._children[name]
# 
# 		if name not in self._children:
# 			if not self._modifiable_children:
# 				raise AttributeError, "object has no attribute '%s'" % (name,)
# 			child = _new()
# 		else:
# 			# child already exists
# 			child = self._children[name]
# 			if child is DEFAULT:
# 				child = _new()
# 		return child


# ---------------------------------------

# def _dot_lookup(thing, comp, import_path):
# 	try:
# 		return getattr(thing, comp)
# 	except AttributeError:
# 		__import__(import_path)
# 		return getattr(thing, comp)
# 

# def _importer(target):
# 	components = target.split('.')
# 	import_path = components.pop(0)
# 	thing = __import__(import_path)
# 
# 	for comp in components:
# 		import_path += ".%s" % comp
# 		thing = _dot_lookup(thing, comp, import_path)
# 	return thing
# 
# 
# def _patch(target, attribute, new):
# 		
# 	def patcher(func):
# 		original = getattr(target, attribute)
# 		if hasattr(func, 'restore_list'):
# 			func.restore_list.append((target, attribute, original))
# 			func.patch_list.append((target, attribute, new))
# 			return func
# 		
# 		func.restore_list = [(target, attribute, original)]
# 		func.patch_list = [(target, attribute, new)]
# 		
# 		def patched(*args, **keywargs):
# 			for target, attribute, new in func.patch_list:
# 				if new is DEFAULT:
# 					new = Mock()
# 					args += (new,)
# 				setattr(target, attribute, new)
# 			try:
# 				return func(*args, **keywargs)
# 			finally:
# 				for target, attribute, original in func.restore_list:
# 					setattr(target, attribute, original)
# 					
# 		patched.__name__ = func.__name__ 
# 		patched.compat_co_firstlineno = getattr(func, "compat_co_firstlineno", 
# 												func.func_code.co_firstlineno)
# 		return patched
# 	
# 	return patcher
# 
# 
# def patch_object(target, attribute, new=DEFAULT):
# 	return _patch(target, attribute, new)
# 
# 
# def patch(target, new=DEFAULT):
# 	try:
# 		target, attribute = target.rsplit('.', 1)	 
# 	except (TypeError, ValueError):
# 		raise TypeError("Need a valid target to patch. You supplied: %s" % (target,))
# 	target = _importer(target)
# 	return _patch(target, attribute, new)


class SentinelObject(object):
	def __init__(self, name):
		self.name = name
		
	def __repr__(self):
		return '<SentinelObject "%s">' % self.name


class Sentinel(object):
	def __init__(self):
		self._sentinels = {}
		
	def __getattr__(self, name):
		return self._sentinels.setdefault(name, SentinelObject(name))
	
	
sentinel = Sentinel()




class AliasedSetter(object):
	def _real_set(self, **kwargs):
		for k,v in kwargs.items():
			object.__setattr__(self, k, v)

class SilentMock(AliasedSetter):
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
		self._real_set(_mock_dict = {
			'attrs':{},
			'call_args_list':[],
			'_children':self._mock_get('_orig_children'),
		})

	def _mock_set(self, **kwargs):
		for attr, val in kwargs.items():
			if not attr in self._mock_dict:
				raise KeyError, attr
			self._mock_dict[attr] = val
			hookname = '_mock_set_%s_hook' % (attr,)
			try:
				object.__getattr__(self, hookname)(val)
			except AttributeError: pass

	def _mock_get(self, attr):
		print "getting %s" % attr
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
		self._mock_get('call_args_list').append((args, kwargs))
		retval = self._mock_get('return_value')

		if self._mock_get('action') is not None:
			side_effect_ret_val = self._mock_get('action')(*args, **kwargs)
			retval = side_effect_ret_val

		if self._mock_get('_return_value_provided'):
			# make sure the side_effect didn't get precedence
			retval = self._return_value
		return retval
	
	def __setattr__(self, attr, val):
		print "setting %s" % attr
		self._mock_get('attrs')[attr] = val

	def __getattr__(self, name):
		def _new():
			self._mock_get('_children')[name] = self._mock_make_child(name)
			return self._mock_get('_children')[name]

		print "gettattr: %s" % name
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





class MockWrapper(AliasedSetter):
	"""
	a mock object wrapper for use in test cases
	 - allows expectations and mock actions to be set
	"""
	def __init__(self, wrapped_mock):
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
		MockOn._reset_all()

	def __called_matcher(self):
		return MockMatcher(self)
	called = property(__called_matcher)
	
	def __expect_call_on(self, obj):
		if self.__class__._all_expectations is None:
			raise RuntimeError, "%s._setup has not been called. Make sure you are inheriting from mock.TestCase, not unittest.TestCase" % (self.__class__,)
		matcher = MockMatcher(obj)
		self.__class__._all_expectations.append(matcher)
		return matcher
	
	def __expect_call_matcher(self):
		return self.__expect_call_on(self._mock)
	is_expected = property(__expect_call_matcher)

	def expects(self, methodname):
		return self.__expect_call_on(getattr(self._mock, methodname))

	def __str__(self):
		return 'mock wrapper: ' + str(self._get('name'))

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

	def doing(self, val):
		self.action = val
		return self
	
	def named(self, val):
		self.name = val
		return self
	
	def frozen(self):
		self.frozen = True
		return self


def mock():
	return SilentMock()

def mock_of(parent):
	if isinstance(mock_, SilentMock):
		return MockWrapper(mock_)
	raise TypeError("expected a SilentMock instance, got %s" % (mock_.__class__,))

def mock_on(parent):
	mock_ = MockOn(parent)
	

class MockOn(AliasedSetter):
	_active = []
	def __init__(self, parent):
		self._init_records()
		self._real_set(_parent = parent)
		self.__class__._active.append(self)
	
	def _init_records(self):
		self._real_set(_children = {})
		self._real_set(_real_children = {})
	
	def make_mock_if_required(self, name):
		if name not in self._children:
			if hasattr(self._parent, name):
				# it's replacing a real object - store it here for later
				real_child = getattr(self._parent, name)
				if isinstance(real_child, SilentMock):
					raise TypeError("replacing a mock with another mock is dangerous!")
				self._real_children[name] = real_child
			self._children[name] = MockWrapper(SilentMock(name=name))
			# insert its SilentMock into the parent
			setattr(self._parent, name, self._children[name]._mock)
		return self._children[name]

	@classmethod
	def _reset_all(cls):
		for mock in cls._active:
			mock._reset()
		cls._active = []
		
	def _reset(self):
		for child in self._children:
			if child not in self._real_children:
				try:
					delattr(self._parent, child)
				except StandardError:
					setattr(self._parent, None)
			else:
				setattr(self._parent, self._real_children[child])
		self._init_records()
			
	def __getattr__(self, attr):
		print "getting %s" % attr
		return self.make_mock_if_required(attr)
		
	def __setattr__(self, attr, val):
		print "setting %s" % attr
		child = self.make_mock_if_required(attr)
		child.return_value = val
	
	def expects(self, methodname):
		return getattr(self, methodname).is_expected


