"""
MockAnchor provides a way to rollback mocks at the end of every unit test.
Instead of:
  os.system = mock
use:
  mock_on(os).system

after the current test is over, os.system will revert to its previous behaviour.

mock_on(parent) returns a MockAnchor. Every attribute accessed (or set) via this instance
will replace the parent's attribute of the same name, and return a MockWrapper for the newly
inserted mock.
"""

import sys

from lib.realsetter import RealSetter
from mockwrapper import MockWrapper
from silentmock import SilentMock, raw_mock
from lib import singletonclass

def mock_on(parent, quiet = False):
	return MockAnchor(parent, quiet)

def _special_method(name):
	return name.startswith('__') and name.endswith('__')

class MockAnchor(RealSetter):
	_active = []
	def __new__(cls, parent, quiet=False):
		for anchor in cls._active:
			if anchor._parent is parent:
				return anchor
		
		# this should use super, but I've no idea how...
		supertype = RealSetter
		self = supertype.__new__(cls)
		self._init_records()
		self._real_set(_parent = parent)
		self._real_set(_quiet = quiet)
		self.__class__._active.append(self)
		
		return self
		
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
			real_child = self._accessor_func(in_dict)(self._parent, name)
		except (AttributeError, KeyError):
			if not self._quiet:
				print >> sys.stderr, "Warning: object %s has no %s \"%s\"" % (self._parent, "key" if in_dict else "attribute", name)
			return
			
		if isinstance(real_child, SilentMock):
			raise TypeError("Replacing a mock with another mock is a profoundly bad idea.\n" +
			                "Try re-using mock \"%s\" instead" % (name,))
		self._real_child_store(in_dict)[name] = real_child
		return real_child
	
	def _make_mock_if_required(self, name, in_dict=False):
		if name not in self._children:
			real_child = self._backup_child(name, in_dict)
			new_child = MockWrapper(raw_mock(name=name), proxied=real_child)
			self._child_store(in_dict)[name] = new_child
			target = self._get_target_for_method(name, in_dict)
			self._insertion_func(in_dict)(target, name, new_child._mock)
		return self._child_store(in_dict)[name]
	
	def _should_ever_assign_to_super(self, in_dict):
		return not (in_dict or isinstance(self._parent, type))
	
	def _get_target_for_method(self, name, in_dict):
		if not self._should_ever_assign_to_super(in_dict):
			return self._parent
		
		if not _special_method(name):
			return self._parent
			
		# otherwise, we'll be assigning to the *class* of self._parent
		# - so we better make it unique
		singletonclass.ensure_singleton_class(self._parent)
		return type(self._parent)

	@classmethod
	def _reset_all(cls):
		for mock in cls._active:
			mock._reset()
		cls._active = []
	
	# interchangeable deletion, getter and setter methods
	def _insertion_func(self, in_dict):
		return self._setitem if in_dict else self._setattr

	def _deletion_func(self, in_dict):
		return self._delitem if in_dict else self._delattr
	
	def _accessor_func(self, in_dict):
		return self._getitem if in_dict else self._getattr
		
	@staticmethod
	def _setitem(target, name, val):
		target[name] = val
	
	@staticmethod
	def _setattr(target, name, val):
		setattr(target, name, val)
		
	@staticmethod
	def _getitem(target, name):
		return target[name]
	
	@staticmethod
	def _getattr(target, name):
		return getattr(target, name)
	
	@staticmethod
	def _delitem(target, name):
		try:
			del target[name]
		except StandardError:
			target[name] = None

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
		assign = self._insertion_func(in_dict)
		del_ = self._deletion_func(in_dict)
			
		for name in children:
			if name in real_children:
				assign(self._parent, name, real_children[name])
			else:
				del_(self._parent, name)
		
	def _reset(self):
		"""reset all children and items, then remove all record of them"""
		self._restore_parent_class()
		self._restore_children(in_dict = True)
		self._restore_children(in_dict = False)
		self._init_records()
	
	def _restore_parent_class(self):
		singletonclass.revert_singleton_class(self._parent)
			
	def __getattribute__(self, attr):
		try:
			ret = super(type(self), self).__getattribute__(attr)
		except AttributeError: ret = None

		# all special methods are accessed via type.__getattr__ when
		# used as a result of a python language feature
		#   (eg len(x) instead of x.__len__()).
		# So any time the instance receives __getattribute__, it must
		# be an explicit access (by the programmer), for the purpose of
		# stubbing it.
		# __class__ is special. Don't even try.
		if ret is not None:
			if (not _special_method(attr)) or attr == '__class__':
				return ret
			
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
