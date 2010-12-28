"""
.. automodule:: mocktest.mocktest
	:members:

.. automodule:: mocktest.mocking
	:members:


.. _setting-expectations:

Setting expectations
--------------------

The return type from :func:`when` and :func:`expect` is of type MockAct.

.. class:: mocktest.mocking.MockAct

	.. method:: __call__(*a, **kw)

		Set the conditions under which this act will apply. Arguments can
		be normal objects (checked for equality), or :class:`Matcher` instances.

	.. method:: where(condition_func)

		Match only when `condition_func` returns true, when called with the same
		arguments as this method.
	
	.. method:: exactly(number)

		Expect this act to be triggered exactly `number` times.
		Usually followed by `times()` for readability, as in:
			>>> expect(obj).meth.exactly(3).times()
	
	.. method:: at_least(number)

		Expect this act to match at least `number` times.

	.. method:: at_most(number)

		Expect this act to match at most `number` times.

	.. method:: between(lower, upper)

		Expect this act to match between `lower` and `upper` times.
	
	.. method:: never()

		Alias for exactly(0).times()

	.. method:: once()

		Alias for exactly(1).time()

	.. method:: twice()

		Alias for exactly(2).times()

	.. method:: thrice()

		Alias for exactly(3).times()
	
	.. method:: and_return(result)

		When this act matches, return the given `result` to the caller.
	
	.. method:: and_raise(exc)

		When this act matches, raise the given exception instance.

	.. method:: and_call(func)

		When this act matches, call the given `func` and return its value.
	
	**Note:** `and_raise`, `and_return` and `and_call` each have a `then_*` alias
	for better readability when using `when`. e.g:

		>>> expect(obj).foo().and_return(True)
	
	Is readable, however when using `when`, the following is more readable:

		>>> when(obj).foo().then_return(True)
	
	Both `and_` and `then_` versions have the same effect however.




.. class mocktest.mocking.StubbedMethod
This is the type that mocktest uses as a stand-in for a replaced (stubbed) method. For example:
	>>> when(obj).method().then_return(True)
	:members:

.. automodule:: mocktest.transaction
	:members:

.. automodule:: mocktest.matchers
	:members:

.. automodule:: mocktest.callrecord
	:members:

"""
from core import *
from mocktest import *
from mocking import *
from matchers import *
from callrecord import *
