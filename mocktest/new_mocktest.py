#!/usr/bin/env python

from unittest import TestCase

class mock(object):
	def __init__(self, name="mock"):
		self.__name = name

	def __getattr__(self, name):
		return type(self)(".".join(self.__name, name))

def when(obj):
	return GetWrapper(lambda name: MockWhen(obj, name))

def expect(obj):
	return GetWrapper(lambda name: MockExpect(obj, name))

def replace(obj):
	return AssignmentWrapper(lambda name, val: MockReplace(obj, name, val))

class AssignmentWrapper(object):
	def __init__(self, callback):
		self.__callback = callback
		self.__used = False

	def __setattr__(self, name, val):
		if self.__used: raise RuntimeError("already used!")
		self.__used = True
		return self.__callback(name, val)

class GetWrapper(object):
	def __init__(self, callback):
		self.__callback = callback
		self.__used = False

	def __getattr__(self, name):
		if self.__used: raise RuntimeError("already used!")
		self.__used = True
		return self.__callback(name)

class MockReplace(object):
	def __init__(self, obj, name, value):
		assert not isinstance(obj, mock)
		try:
			original_value = getattr(obj, name)
			self.revert = lambda: setattr(obj, name, original_value)
		except AttributeError:
			self.revert = lambda: delattr(obj, name)
			pass
		self.__obj = obj
		self.__value = value
		self.__name = name
		MockRunner.on_complete(self.revert)
		setattr(self.__obj, self.__name, self.__value)

from mocktest import core
class MockRunner(object):
	@classmethod
	def __enter__(cls):
		core._setup()
		return cls

	@classmethod
	def __exit__(cls, *a):
		core._teardown()
		return False


class Object(object):pass

class TestReplace(TestCase):
	def test_replace_existing(self):
		x = Object()
		x.foo = "foo"
		with MockRunner:
			replace(x).foo.with_("bar")
			assert x.foo == "bar"
		assert x.foo == "foo"

	def test_replace_nonexistant(self):
		x = Object()
		with MockRunner:
			replace(x).foo.with_("bar")
			assert x.foo == "bar"
		assert not hasattr(x, "foo")


# ----------- interals ----------------------------

class Call(object):
	@classmethod
	def like(cls, *a, **kw):
		return cls(a, kw)

	def __init__(self, args, kwargs):
		self.args = args
		self.kwargs = kwargs
	
	def play(self, function):
		return function(*self.args, **self.kwargs)

Unset = object()
class MockAct(object):
	def __init__(self):
		super(type(self), self).__setattr__('_dict', {})
		self.match_filter = Unset

	def __setattr__(self, name, val):
		if name in self._dict and self._dict[name] is not Unset:
			raise AttributeError("already assigned %s" % (name,))
		self._dict[name] = val

	def __getattr__(self, name):
		try:
			return self._dict[name]
		except KeyError:
			raise AttributeError(name)

	def at_least(self, num):
		self.expected = lambda x: x >= num
		return self

	def at_most(self, num):
		self.expected = lambda x: x <= num
		return self

	def exactly(self, num):
		self.expected = lambda x: x == num
		return self
	
	def when(self, args_cond):
		self.match_filter = args_cond
		return self
	
	def _create_matcher(self, *expected_args, **expected_kw):
		def matches(*a, **kw):
			if len(a) != len(expected_args):
				return False
			if sorted(expected_kw.keys()) != sorted(kw.keys()):
				return False
			args_match = all(expected == got for expected, got in zip(expected_args, a))
			kwargs_match = all(expected == kw[key] for key, expected in expected_kw.items())
			return args_match and kwargs_match
		return matches

	when_args = when

	def with_args(self, *expected_a, **expected_kw):
		self.when_args(self._create_matcher(*expected_a, **expected_kw))
		return self
		
	def matches(self, call):
		if self.match_filter is not None:
			try:
				return call.play(self.match_filter)
			except TypeError:
				return False
		return True
	
	def satisfied_by(self, calls):
		if self.matches is None or self.expected is None:
			return True
		matched_calls = filter(self.matches, calls)
		return self.expected(len(matched_calls))

	def act_upon(self, call):
		if self.matches is not None and (not self.matches(call)):
			return (False,None)
		if self._isset('return_value'):
			return (True, self.return_value)
		if self.action is not None:
			return (True, call.play(self.action))
		return (True, None)

	def set_name(self, name):
		self.name = name
		return self

# -------
Act = MockAct
class TestMatching(TestCase):
	def test_should_match_everything_by_default(self):
		self.assertTrue(Act().matches(Call.like()))
		self.assertTrue(Act().matches(Call.like(1, 2, 3)))
		self.assertTrue(Act().matches(Call.like(1, x=1)))
		self.assertTrue(Act().matches(Call.like(y=2)))

	def test_should_allow_expected_args_to_override_eql_when_arity_is_correct(self):
		self.assertTrue(Act().with_args(Anything()).matches(Call.like("something")))
		self.assertFalse(Act().with_args(Anything()).matches(Call.like("too", "many", "args")))

	def test_should_allow_custom_matcher(self):
		def _one(arg):
			return arg == 1
		self.assertTrue(Act().when(_one).matches(Call.like(1)))
		self.assertFalse(Act().when(_one).matches(Call.like(2)))
		self.assertFalse(Act().when(_one).matches(Call.like(1, 2)))

class TestActing(TestCase):
	def test_should_not_act_upon_non_matching_calls(self):
		acted, result = Act().when(lambda *a, **k: False).act_upon(Call.like())
		self.assertFalse(acted)

class TestSatisfaction(TestCase):
	def test_at_least(self):
		act = Act().at_least(2)
		call = Call.like()
		self.assertFalse(act.satisfied_by([call]))
		self.assertTrue(act.satisfied_by([call, call]))
		self.assertTrue(act.satisfied_by([call, call, call]))

	def test_at_most(self):
		act = Act().at_most(2)
		call = Call.like()
		self.assertTrue(act.satisfied_by([call]))
		self.assertTrue(act.satisfied_by([call, call]))
		self.assertFalse(act.satisfied_by([call, call, call]))

	def test_exactly(self):
		act = Act().exactly(2)
		call = Call.like()
		self.assertFalse(act.satisfied_by([call]))
		self.assertTrue(act.satisfied_by([call, call]))
		self.assertFalse(act.satisfied_by([call, call, call]))

	def test_should_only_count_matching_calls(self):
		arg = "argument"
		matching_call = Call.like(arg)
		nonmatching_call = Call.like()
		act = Act().exactly(1).with_args(arg)

		self.assertTrue(act.satisfied_by([matching_call]))
		self.assertFalse(act.satisfied_by([nonmatching_call]))

class TestWhen(TestCase):
	def test_matching_multiple_actions(self):
		a = []
		b = Object()
		when(b).foo(1).then_call(lambda x: a.append(1))
		when(b).foo(2).then_call(lambda x: a.append(2))
		when(b).foo(1, 2).then_call(lambda x: a.append(12))
		when(b).foo(1, 3).then_call(lambda x: a.append(13))
		when(b).foo.where_args(lambda *a: len(a) == 2).then_call(lambda x: a.append("xx"))
		b.foo(1)
		b.foo(2)
		b.foo(1, 2)
		b.foo(1, 3)
		b.foo(1, 4)
		b.foo(1)
		b.foo()
		assert a == [1, 2, 12, 13, "xx", 1]

	def test_responding_to_arguments(self):
		b = Object()
		when(b).foo(1).then_return(1)
		when(b).foo(2).then_call(lambda x: 2)
		assert b.foo(1) == 1
		assert b.foo(2) == 1
		with assertRaises(TypeError):
			b.foo()

	def test_responding_to_any(self):
		b = Object()
		c = Object()
		when(b).foo.with_anything.then_return(1)
		when(c).foo.with_(anything).then_return(2)
		assert b(1,2,3) == 1
		assert c(1,2,3) == 2

if __name__ == '__main__':
	import unittest
	unittest.main()
#		vi:et syntax=python

