# mock.py
# Test tools for mocking and patching.
# Copyright (C) 2007-2008 Michael Foord
# E-mail: fuzzyman AT voidspace DOT org DOT uk

# mock 0.4.0
# http://www.voidspace.org.uk/python/mock.html

# Released subject to the BSD License
# Please see http://www.voidspace.org.uk/python/license.shtml

# modified by Tim Cuthbertson to integrate MockMatcher functionality

__all__ = (
	'Mock',
	'patch',
	'patch_object',
	'sentinel',
	'__version__'
)

__version__ = '0.4.0'

from mockmatcher import MockMatcher

DEFAULT = object()

#TODO: you should be able to use both children and methods

class Mock(object):
	def __init__(self, _polymorphic_spec=None, name=None,
				 methods=None, spec=None, action=None,
				 children=None, return_value=DEFAULT, parent=None):

		if _polymorphic_spec is not None:
			# depending on the type of the first argument, us it as name / methods / spec
			polymorphic_type = type(_polymorphic_spec)
			if polymorphic_type == str:
				if name is not None:
					raise RuntimeError, "first argument looks like a name, but name was also provided"
				name = _polymorphic_spec
			else:
				if not (methods is spec is children is None):
					raise TypeError, "type of first argument (%s) implies  methods / children / spec, "\
					                 "but one of these was also provided as a keyword argument" % (type(_polymorphic_spec),)
				if polymorphic_type == dict or polymorphic_type == list:
					methods = _polymorphic_spec
				else:
					spec = _polymorphic_spec
		
		self._parent = parent
		self._name = name
		self._children = self._make_children(children=children, methods=methods, spec=spec)
		self._return_value = return_value
		self._side_effect = action
		
		self.reset()
		
		self.__initted = True
	
	_all_expectations = None
	@classmethod
	def _setup(cls):
		cls._all_expectations = []
	
	@classmethod
	def _teardown(cls):
		for expectation in cls._all_expectations:
			assert expectation, expectation
		cls._all_expectations = None

	def __called_matcher(self):
		return MockMatcher(self)
	called = property(__called_matcher)
	
	def __str__(self):
		return str(self._name) if self._name is not None else "unknown-mock"

	def __expect_call_matcher(self):
		if self.__class__._all_expectations is None:
			raise RuntimeError, "Mock._setup has not been called. Make sure you are inheriting from mock.TestCase, not unittest.TestCase"
		matcher = MockMatcher(self)
		self.__class__._all_expectations.append(matcher)
		return matcher
	is_expected = property(__expect_call_matcher)

	def __reset_mock(self, obj):
		if isinstance(obj, Mock):
			obj.reset()
			
	def reset(self):
		self.call_args = None
		self.call_count = 0
		self.call_args_list = []
		self.method_calls = []
		for child in self._children.itervalues():
			self.__reset_mock(child)
		self.__reset_mock(self._return_value)
		
	
	def __get_return_value(self):
		if self._return_value is DEFAULT:
			self._return_value = Mock()
		return self._return_value
	
	def __set_return_value(self, value):
		self._return_value = value
		
	return_value = property(__get_return_value, __set_return_value)
	
	def __call__(self, *args, **kwargs):
		self.call_count += 1
		self.call_args = (args, kwargs)
		self.call_args_list.append((args, kwargs))
		
		parent = self._parent
		name = self._name
		while parent is not None:
			parent.method_calls.append((name, args, kwargs))
			if parent._parent is None:
				break
			name = parent._name + '.' + name
			parent = parent._parent

		retval = self.return_value
		if self._side_effect is not None:
			side_effect_ret_val = self._side_effect(*args, **kwargs)
			if isinstance(self._return_value,Mock):
				retval = side_effect_ret_val
		
		return retval
	
	def _make_children(self, children = None, spec = None, methods = None):
		"""
		return children (as a dict) given any of the three types of information

		* children (list) -> a dict is returned where all values are set to DEFAULT
		* children (dict) -> returned as-is

		* methods (list) -> as for a list of children
		* methods (dict) -> returns a dict, where values are Mock
		                    objects with their return_values set appropriately
		
		* spec -> as for a list of children, except the keys are set to all available
		          methods on 'spec'
		
		If one argument is given, self._modifiable_children is set to False
		If no arguments are given, self._modifiable_children is set to True and the
		empty dict is returned.
		If more than one argument is given, a RuntimeError is raised
		"""
		specified = filter(lambda x: x is not None, (children, spec, methods))
		if len(specified) == 0:
			self._modifiable_children = True
			return {}
		if len(specified) != 1:
			raise RuntimeError, "only one of (spec, children, methods) can be set on a mock object"
		
		self._modifiable_children = False
		
		# grab methods from a spec object
		if spec is not None:
			methods = [member for member in dir(spec) if not 
					   (member.startswith('__') and	 member.endswith('__'))]

		if isinstance(children, list):
			# a list of children is the same as a list of methods
			methods = children
			children = None
			
		# if methods don't have return values, give them some:
		if methods is not None:
			children = {}
			if isinstance(methods, list):
				for name in methods:
					children[name] = DEFAULT
			elif isinstance(methods, dict):
				# populate methods as mocks with return values
				for name, retval in methods.items():
					children[name] = self._make_child(name, retval)
			else:
				raise "expected methods to be a list or dict, got '%s'" % (type(methods),)

		if not isinstance(children, dict):
			raise TypeError, "expected children to be a dict, got '%s'" % (type(children),)

		return children
		
	def _make_child(self, name, return_value=DEFAULT):
		return Mock(parent=self, name=name, return_value=return_value)

	def __has_attr(self, attr):
		try:
			a = object.__getattribute__(self, attr)
			return True
		except AttributeError:
			return False

	def __setattr__(self, attr, val):
		if self.__has_attr(attr) or not self.__has_attr('_Mock__initted'):
			object.__setattr__(self, attr, val)
			return

		if not self._modifiable_children:
			raise AttributeError, "Cannot set attribute %r (to %r) on mock '%s'" % (attr, val, self)
		self._children[attr] = val

	def __getattr__(self, name):
		def _new():
			self._children[name] = self._make_child(name)
			return self._children[name]

		if not self.__has_attr('_children'):
			return object.__getattribute__(self, name)
			
		if name not in self._children:
			if not self._modifiable_children:
				raise AttributeError, "object has no attribute '%s'" % (name,)
			child = _new()
		else:
			# child already exists
			child = self._children[name]
			if child is DEFAULT:
				child = _new()
		return child
		

def _dot_lookup(thing, comp, import_path):
	try:
		return getattr(thing, comp)
	except AttributeError:
		__import__(import_path)
		return getattr(thing, comp)


def _importer(target):
	components = target.split('.')
	import_path = components.pop(0)
	thing = __import__(import_path)

	for comp in components:
		import_path += ".%s" % comp
		thing = _dot_lookup(thing, comp, import_path)
	return thing


def _patch(target, attribute, new):
		
	def patcher(func):
		original = getattr(target, attribute)
		if hasattr(func, 'restore_list'):
			func.restore_list.append((target, attribute, original))
			func.patch_list.append((target, attribute, new))
			return func
		
		func.restore_list = [(target, attribute, original)]
		func.patch_list = [(target, attribute, new)]
		
		def patched(*args, **keywargs):
			for target, attribute, new in func.patch_list:
				if new is DEFAULT:
					new = Mock()
					args += (new,)
				setattr(target, attribute, new)
			try:
				return func(*args, **keywargs)
			finally:
				for target, attribute, original in func.restore_list:
					setattr(target, attribute, original)
					
		patched.__name__ = func.__name__ 
		patched.compat_co_firstlineno = getattr(func, "compat_co_firstlineno", 
												func.func_code.co_firstlineno)
		return patched
	
	return patcher


def patch_object(target, attribute, new=DEFAULT):
	return _patch(target, attribute, new)


def patch(target, new=DEFAULT):
	try:
		target, attribute = target.rsplit('.', 1)	 
	except (TypeError, ValueError):
		raise TypeError("Need a valid target to patch. You supplied: %s" % (target,))
	target = _importer(target)
	return _patch(target, attribute, new)


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
