import sys, traceback, os

class Call(object):
	def __init__(self, args, kwargs, stack = True):
		self.tuple = (args, kwargs)
		self.args = args if len(args) > 0 else None
		self.kwargs = kwargs if len(kwargs) > 0 else None

		if stack is True:
			self._stack = traceback.extract_stack(sys._getframe())

	def _concise_stack(self):
		stack = self._stack
		relevant_line = stack[-3]
		return self._concise_stack_line(relevant_line)
	
	def _concise_stack_line(self, line):
		file_, line, func, code = line
		file_ = os.path.basename(file_)
		return "%s:%-3s :: %s" % (file_, line, code)
		
	def __eq__(self, other):
		other_tuple = None
		if isinstance(other, type(self)):
			other_tuple = other.tuple
		else:
			other_tuple = other
		return self.tuple == other_tuple
	
	@property
	def empty(self):
		return self.tuple == ((), {})
	
	def __ne__(self, other):
		return not self.__eq__(other)

	def play(self, function):
		return function(*self.args, **self.kwargs)
	
	def __str__(self):
		if self.empty:
			arg_desc = "No arguments"
		else:
			sep = ', '
			args = None if self.args is None else sep.join(map(repr, self.args))
			kwargs = None if self.kwargs is None else sep.join(["%s=%r" % (key, val) for key, val in self.kwargs.items()])
			arg_desc = sep.join(filter(lambda x: x is not None, (args, kwargs)))
		try:
			return "%-24ls // %s" % (arg_desc, self._concise_stack())
		except (IndexError, AttributeError):
			return arg_desc

