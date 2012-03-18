"""
.. automodule:: mocktest.mocktest
	:members:


Mock Objects
------------
.. automodule:: mocktest.mocking
	:members:

Indirectly-used classes
^^^^^^^^^^^^^^^^^^^^^^^
These classes are not exposed for you to instantiate, but
instances are returned instances from other (public) methods:

.. autoclass:: mocktest.mocking.RecursiveStub
	:members:

.. autoclass:: mocktest.mocking.RecursiveAssignmentWrapper
	:members:


.. _setting-expectations:

Setting expectations
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: mocktest.mocking.MockAct
	:members:

	.. method:: __call__(*a, **kw)

		Set the conditions under which this act will apply. Arguments can
		be normal objects (checked for equality), or :class:`Matcher` instances.

.. autoclass:: mocktest.mocking.StubbedMethod
	:members:


Mock Transaction
----------------

.. automodule:: mocktest.transaction
	:members:

.. automodule:: mocktest.matchers
	:members:

.. automodule:: mocktest.callrecord
	:members:

"""
from .core import *
from .mocktest import *
from .mocking import *
from .matchers import *
from .callrecord import *
