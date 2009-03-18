"""
SilentMock makes many attempts to hide the fact that it is a mock object.
Attribute accesses, sets and object calls are recorded internally, and can be
inspected passing the silent mock into a MockWrapper object.
"""

from lib.realsetter import RealSetter
from callrecord import CallRecord
from mockerror import MockError

DEFAULT = object()

def raw_mock(name = None, **kwargs):
	"""a silent mock object. use mock_of(silent_mock) to set expectations, etc"""
	if name is not None:
		if not isinstance(name, str):
			raise TypeError("%r is not a string. did you mean to use mock_on(%r)?" % (name, name))
		kwargs['name'] = name
	return SilentMock(**kwargs)

class SilentMock(RealSetter):
	def __init__(self, **kwargs):
		# make self the only instance of a brand new class,
		# allowing for special method assignment
		self.__class__ = type(self.__class__.__name__, (self.__class__,), {})

		self._real_set(_mock_dict = {
					'action': None,
					'return_value':DEFAULT,
					'name':'unnamed mock',
					'_children':{},
					'_modifiable_children':True,
					'_return_value_provided':False,
					'should_intercept':True,
					'_proxied': None,
				})
		self._mock_reset()
		self._mock_set(**kwargs)

	def _mock_reset(self):
		resets = {
			'call_list':[],
		}
		for key,val in resets.items():
			self._mock_dict[key] = val
	
	def _mock_set(self, **kwargs):
		for attr, val in kwargs.items():
			if not attr in self._mock_dict:
				raise KeyError, "no such mock attribute: %s" % (attr,)
			self._mock_assert_can_set(attr, val)
			self._mock_dict[attr] = val
			hookname = '_mock_set_%s_hook' % (attr,)
			try:
				self._real_get(hookname)(val)
			except AttributeError: pass
	
	def _mock_has_a_result_set(self):
		if self._mock_get('action', default=None) is not None:
			return 'action'
		elif self._mock_get('return_value', default=DEFAULT) is not DEFAULT:
			return 'return_value'
	
	def _mock_assert_can_set(self, attr, val):
		result_set = self._mock_has_a_result_set()
		if attr in ['action', 'return_value'] and result_set is not None:
			raise MockError("Cannot set %s on mock %r: %s has already been set" % (
				attr.replace('_',' '),
				self._mock_get('name'),
				"a return value" if result_set == 'return_value' else 'an action'))

	def _mock_set_special(self, **kwargs):
		"""set special methods"""
		for k,v in kwargs.items():
			print "k = %s" % k
			if not (k.startswith('__') and k.endswith('__')):
				raise ValueError("%s is not a magic method" % (k,))
			
			allowable = True
			try:
				allowable = getattr(self.__class__, k) == getattr(object, k)
			except AttributeError:
				pass
			if not allowable:
				# we overrode object's method - for a good reason
				raise AttributeError("cannot override %s special method '%s'" % (self.__class__.__name__, k))

			# we need to override the whole class' method
			# in order for special methods to be used
			setattr(self.__class__, k, v)

	def _mock_get(self, attr, **kwargs):
		if 'default' in kwargs:
			return self._mock_dict.get(attr, kwargs['default'])
		return self._mock_dict[attr]
	
	def _mock_del(self, attr):
		hookname = '_mock_del_%s_hook' % (attr,)
		try:
			self._real_get(hookname)()
		except AttributeError: pass
	
	# hooks on mock attributes
	def _mock_set_return_value_hook(self, val):
		self._mock_set(_return_value_provided=True)
	
	def _mock_del_return_value_hook(self):
		self._mock_dict['return_value'] = DEFAULT
		self._mock_dict['_return_value_provided'] = False
		
	def _mock_del_action_hook(self):
		self._mock_dict['action'] = None
		
	def _mock_should_intercept(self, *args, **kwargs):
		should_intercept = self._mock_get('should_intercept')
		if isinstance(should_intercept, bool):
			return should_intercept
		try:
			return should_intercept(*args, **kwargs)
		except TypeError:
			return False
	
	def __call__(self, *args, **kwargs):
		if not self._mock_should_intercept(*args, **kwargs):
			# call the real (proxied) object
			#TODO: catch StandardError, and trim a few lines off the stacktrace
			#      so end users don't have to care about the internals of SilentMock
			return self._mock_get('_proxied')(*args, **kwargs)
		self._mock_get('call_list').append(CallRecord(args, kwargs))
		retval_done = False
		if self._mock_get('action') is not None:
			side_effect_ret_val = self._mock_get('action')(*args, **kwargs)
			if not self._mock_get('_return_value_provided'):
				retval = side_effect_ret_val
				retval_done = True

		if not retval_done:
			retval = self._mock_get('return_value')

		if retval is DEFAULT:
			self._mock_set(return_value = raw_mock(name="return value for (%s)" % (self._mock_get('name'))))
			retval = self._mock_get('return_value')

		return retval

	def _mock_fail_if_no_child_allowed(self, name):
		if name not in self._mock_get('_children'):
			if not self._mock_get('_modifiable_children'):
				raise AttributeError, "object (%s) has no attribute '%s'" % (self, name,)

	def __setattr__(self, attr, val):
		if attr.startswith('__') and attr.endswith('__'):
			return object.__setattr__(self, attr, val)
		else:
			self._mock_fail_if_no_child_allowed(attr)
			self._mock_get('_children')[attr] = val

	def __getattribute__(self, name):
		if name.startswith('__') and name.endswith('__'):
			# Attempt to get special methods directly, without exception
			# handling
			return object.__getattribute__(self, name)
		elif name.startswith('_'):
			try:
				# Attempt to get the attribute, if that fails
				# treat it as a child
				return object.__getattribute__(self, name)
			except AttributeError:
				pass
			
		def _new():
			self._mock_get('_children')[name] = raw_mock(name=name)
			return self._mock_get('_children')[name]
		
		if name not in self._mock_get('_children'):
			self._mock_fail_if_no_child_allowed(name)
			child = _new()
		else:
			# child already exists
			child = self._mock_get('_children')[name]
			if child is DEFAULT:
				child = _new()
		return child

	def __str__(self):
		return str(self._mock_get('name'))
