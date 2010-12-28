"""
Call Records
------------
"""
import sys, traceback, os

__all__ = ['Call']

class Call(object):
	"""
	An encapsulation of call arguments.
	Can compare for equality with a tuple of
	(args, kwargs), e.g:

		>>> Call.like(1,2,3, x=4) == ((1,2,3), {'x':4})
		True
	
	:param args: non-keyword arguments
	:type args: tuple
	:param kwargs: keyword arguments
	:type kwargs: dict
	:param stack: If True, a stack trace is captured for reporting \
	where a given call was made.
	:members: args, kwargs
	"""
	def __init__(self, args, kwargs, stack = False):
		self.tuple = (args, kwargs)
		self.args = args
		self.kwargs = kwargs

		if stack is True:
			self._stack = traceback.extract_stack(sys._getframe())

	@classmethod
	def like(cls, *a, **kw):
		"""capture a call with the given arguments"""
		return cls(a, kw)

	def _concise_stack(self):
		stack = self._stack
		relevant_line = stack[-3]
		return self._concise_stack_line(relevant_line)
	
	def _concise_stack_line(self, line):
		file_, line, func, code = line
		file_ = os.path.basename(file_)
		return "%s:%-3s :: %s" % (file_, line, code)
		
	def __hash__(self):
		return hash(self.tuple)

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
		"""apply this call's arguments to the given callable"""
		return function(*self.args, **self.kwargs)

	def desc(self, include_stack=False):
		if self.empty:
			arg_desc = "()"
		else:
			sep = ', '
			args = sep.join(map(repr, self.args))
			kwargs = sep.join(["%s=%r" % (key, val) for key, val in self.kwargs.items()])
			arg_desc = "(%s)" % (sep.join(filter(None, (args, kwargs))),)
		try:
			if include_stack:
				arg_desc = "%-24ls // %s" % (arg_desc, self._concise_stack())
		finally:
			return arg_desc

	def __str__(self):
		return self.desc(include_stack=True)

	def __repr__(self):
		return "<#Call: %r>" % (self.tuple,)

