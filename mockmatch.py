class MockMatcher(object):
	_multiplicity = None
	_cond_args = None
	
	def __init__(self, mock_obj):
		self._mock = mock_obj
	
	def with_args(self, *args, **kwargs):
		"""
		restrict the checked set of function calls to those with
		arguments equal to (args, kwargs)
		"""
		self.__assert_not_set(self._cond_args, "argument condition")
		self._cond_args = self._args_equal_func(args, kwargs)
		return self
	
	def where_args(self, func):
		"""
		restrict the checked set of function calls to those where
		func(*args, **kwargs) is True
		"""
		self.__assert_not_set(self._cond_args, "argument condition")
		self._cond_args = func
		return self

	def exactly(self, n):
		"""set the allowed number of calls made to this function"""
		self.__assert_not_set(self._multiplicity, "number of calls")
		self._multiplicity = (self._eq, n)
		return self
	
	def at_least(self, n):
		"""set the allowed number of calls made to this function"""
		self.__assert_not_set(self._multiplicity, "number of calls")
		self._multiplicity = (self._gte, n)
		return self
	
	def at_most(self, n):
		"""set the allowed number of calls made to this function"""
		self.__assert_not_set(self._multiplicity, "number of calls")
		self._multiplicity = (self._lte, n)
		return self
	
	def between(self, start_range, end_range):
		"""set the allowed number of calls made to this function"""
		self.__assert_not_set(self._multiplicity, "number of calls")
		self._multiplicity = (self._btwn, start_range, end_range)
		return self

	def get_calls(self):
		"""
		return all the function calls this matcher applies to in the format:
		  [ ((call1_arg1, call1_arg2), {'call_1_key':'value_1'}), ... ]
		Note that empty args or kwargs are replaced with None, i.e:
		  [ (None, {'key':'value'}), ... ]
		
		If the conditions on this matcher are not satisfied, returns None
		"""
		if not self._matches():
			return None
		return tuple([self._clean_args(call) for call in self._mock.call_args_list if self._args_match(call)])
	
	def get_args(self):
		"""
		returns the arguments this function was called with.
		this is an alias for:
		  get_calls()[0]
		except it will fail if the expected number of times for this
		function to be called is not exactly one
		"""
		
		if self._multiplicity != (self._eq, 1):
			raise ValueError, "get_args() can only be used when you are expecting exactly one call"
		
		calls = self.get_calls()
		return calls[0]

	# syntactic sugar to make more readabale expressions
	def __get_times(self): return self
	times = property(__get_times)
	
	def once(self):
		"""alias for exactly(1).times"""
		return self.exactly(1)
		
	def twice(self):
		"""alias for exactly(2).times"""
		return self.exactly(2)
	
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
	
	# evaluating matches
	def _matches(self):
		"""
		returns a boolean of whether this matcher is satisfied,
		given the multiplicities and argument checks it has been
		configured with
		"""
		call_args_list = self._mock.call_args_list
		if self._cond_args is not None:
			call_args_list = filter(self._args_match, call_args_list)
		return self._multiplicities_match(len(call_args_list))
	
	def _args_match(self, call_args):
		"""
		return true if the given call_args matches this matcher's
		argument check condition
		  
		call_args = (args, kwargs)
		  e.g: call_args = ((arg1, arg2), {'key1':'value'})
		"""
		print "args match for a single call? given arguments are"
		print "args: %r" % (call_args[0],)
		if self._cond_args is None:
			return True
		
		args, kwargs = call_args
		return self._cond_args(*args, **kwargs)
	
	def _multiplicities_match(self, num_calls):
		"""
		returns whether the *actual* number of calls (num_calls) this
		function has received satisfies the (function, arg1, ...) tuple
		stored in self._multipicity
		
		i.e returns function(num_calls, arg1, ... )
		"""
		
		if self._multiplicity is None:
			# default operation
			self._multiplicity = (self._gte, 1)
		operator = self._multiplicity[0]
		operator_args = self._multiplicity[1:]
		return operator(num_calls, *operator_args)
	
	def _args_equal_func(self, args, kwargs):
		"""
		returns a function that returns whether its arguments match the
		args (tuple), and its kewyord arguments match the kwargs (dict)
		"""
		def check(*a, **k):
			print "Comapring args:"
			print "%r      %r" % (a, k)
			print "%r      %r" % (args, kwargs)
			return a == args and k == kwargs
		return check

	
	def _clean_args(self, call_args):
		"""
		replaces empty tuples and dicts with None, for the sake of
		making test assertions more readable / obvious
		"""
		args, kwargs = call_args
		if len(args) == 0:
			args = None
		if len(kwargs) == 0:
			kwargs = None
		return (args, kwargs)

	# multiplicity-checking operators
	def _eq(self, a, b):
		return a == b
	def _lte(self, a, b):
		return a <= b
	def _gte(self, a, b):
		return a >= b
	def _btwn(self, a, b, c):
		ends = (b,c)
		return a >= min(ends) and a <= max(ends)

# class MockExpectations(object):
# 	def called():
# 		return MockMatcher(self)
# 
# extend the Mock class:
#mock.Mock.__bases__ = (MockExpectations,) # + mock.Mock.__bases__