DEFAULT = object()
from lib.realsetter import RealSetter

def raw_mock(name = None):
	"""a silent mock object. use mock_of(silent_mock) to set expectations, etc"""
	kwargs = {}
	if name is not None:
		if not isinstance(name, str):
			raise TypeError("%r is not a string. did you mean to use mock_on(%r)?" % (name, name))
		kwargs['name'] = name
	return SilentMock(**kwargs)


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
	
	def _mock_set(self, **kwargs):
		for attr, val in kwargs.items():
			if not attr in self._mock_dict:
				raise KeyError, "no such mock attribute: %s" % (attr,)
			self._mock_dict[attr] = val
			hookname = '_mock_set_%s_hook' % (attr,)
			try:
				self._real_get(hookname)(val)
			except AttributeError: pass

	def _mock_get(self, attr):
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
		self._mock_set(return_value=DEFAULT)
		self._mock_set(_return_value_provided=False)
	
	def __call__(self, *args, **kwargs):
		self._mock_get('call_list').append((args, kwargs))
		retval_done = False
		if self._mock_get('action') is not None:
			side_effect_ret_val = self._mock_get('action')(*args, **kwargs)
			if not self._mock_get('_return_value_provided'):
				retval = side_effect_ret_val
				retval_done = True

		if not retval_done:
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
		return str(self._mock_get('name'))