import sys, traceback, os

class CallRecord(object):
	def __init__(self, args, kwargs, stack = True):
		self.raw_tuple = (args, kwargs)
		self.args = args if len(args) > 0 else None
		self.kwargs = kwargs if len(kwargs) > 0 else None

		if self.kwargs is None:
			self.tuple = self.args
		else:
			self.tuple = (self.args, self.kwargs)

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
		if isinstance(other, self.__class__):
			other_tuple = other.tuple
		else:
			other_tuple = other
		return self.tuple == other_tuple
	
	def is_empty(self):
		return self.tuple is None
	
	def __repr__(self):
		return repr(self.tuple)
	
	def __str__(self):
		if self.is_empty():
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

