About mocktest
**************
mocktest is a powerful and easy-to-use mocking library, inspired by rspec and
similar in some ways to Michael Foord's popular Mock module.

The main features are:

 - expressive DSL for specifying expectations, stubs and replacement objects
 - powerful expectation matching behaviour for mock objects
 - automatic verification of expectations (before each test's tearDown)
 - automatic rollback of inserted mock objects after each test
 - descriptive error messages when something fails


It's released under the GPLv3 licence (see the LICENCE file).

| Source / Issues:
| http://github.com/gfxmonk/mocktest/tree/master


| Cheese shop entry:
| http://pypi.python.org/pypi/mocktest


| Zero install feed:
| http://gfxmonk.net/dist/0install/mocktest.xml

API reference
-----------------

This document is an introduction, if you are looking for an API reference
you should read the :mod:`mocktest module documentation <mocktest>`.

Installation
------------
The preferred distribution method is via `Zero Install <http://0install.net/>`_

If you just want to try it out and don't want to make a feed that
depends on mocktest, you can run::

  exec "`0launch http://gfxmonk.net/dist/0install/0path.xml http://gfxmonk.net/dist/0install/mocktest.xml`"

And your ``PYTHONPATH`` will be set up to contain ``mocktest``.

(**Note**: Obviously, this requires ``0launch`` to be installed. On ubuntu, this is part of the ``zeroinstall-injector`` package)

Important notes for this version
--------------------------------

Mocktest 0.5 is a fairly thorough rewrite. Most of the semantics and features
remain the same, but the implementation has been simplified. Some features are
no longer present, other (hopefully more useful) features have been added. I
apologise for those using mocktest <=0.3 - most of the features you use should
still work, they may just be written differently.

Most importantly, there is no longer any distinction between a raw mock and a
mock wrapper. Instead, mock expectations are specified by using one of the
global functions - :func:`~mocktest.mocking.expect` and
:func:`~mocktest.mocking.when`. The distinction turned out to be
confusing, and made many tests awkward.

Where did it come from?
-----------------------
I am a big fan of rspec, but less of a fan of ruby as a whole.
I wanted a to use rspec's powerful ``should_receive()`` and associated matchers
with my python mock objects.

mocktest is by no means a port of rspec - it is smaller and simpler, and a lot
more pythonic.

what *are* mocks?
-----------------

What are mocks used for? mocks can pretend to be pretty much any object. Mocks
record what happens to them (accessors, method calls, etc) and allow you to
verify that this is what you expected. Replace a database connection with a mock
and make sure the right commands are being sent to your database - without the
overhead and trouble of using an actual database. Replace os.system with a mock,
and supply your own response to shell commands. Mocks can be used to satisfy
dependencies or simulate external conditions in your program so you can focus
on unit-level testing.

mocktest usage
**************

When using mocktest, you should always use :class:`mocktest.TestCase` instead of
:class:`unittest.TestCase`. Mocktest's version is almost identical, but automatically
calls the required setup and teardown hooks for the mocktest library.

If you wish to use mocks outside test cases, you can use the mock transaction
manager directly to handle these checks for you.

	>>> from mocktest import MockTransaction
	>>> with MockTransaction:
	... 	# perform all your checks in here
	... 	# expectations will be verified once the indented block finishes

Or, if you are playing around on the console, you can manually call
``MockTransaction.__enter__()`` and ``MockTransaction.__exit()`` to start/end a
mock transaction.

There is one important addition to the :class:`~mocktest.mocktest.TestCase` class:

.. automethod:: mocktest.mocktest.TestCase.assertRaises
  :noindex:

This was adapted from http://code.activestate.com/recipes/307970/

Creating mocks
--------------

mocktest is still a young framework, and is likely to evolve. While the
inspiration is from rspec, a lot of the mechanics differ either necessarily
because of differences between ruby and python, or just to make things cleaner.

One important part of mocking is test isolation - that is, changes you make in
one test for the sake of mocking should never be visible outside that test
case. Mocktest takes care of all that for you, even when you mock or replace
attributes on global objects.

So, let's get started:

If you want to replace a method on an existing object, you can use :func:`~mocktest.mocking.when`:

	>>> when(some_object).method.then_return(True)

This will ensure that ``some_object.method()`` always returns True (and doesn't call
the previous implementation of ``method``, if there is one). This action will
take place regardless of the arguments passed in to ``method``.

To only deal with some of the calls made to method, you can specify under which
conditions your action should occur by just passing those arguments when call the
:func:`~mocktest.mocking.when` function's ``method``. For example:

	>>> when(some_object).method().then_return('no args')
	>>> when(some_object).method(1, 2, 3).then_return('one two three')

After this, you would see:

	>>> some_object.method()
	'no args'

	>>> some_object.method(1, 2, 3)
	'one two three'

	>>> some_object.method('unexpected arguments')
	TypeError: stubbed method 'method' received unexpected arguments: ('unexpected arguments')
	Allowable argument conditions are:
	  - arguments equal to: ()
	  - arguments equal to: (1, 2, 3)

In order to make sure that the method call you want to happen actually does, you
can use :func:`~mocktest.mocking.expect`. :func:`~mocktest.mocking.expect`
is exactly like :func:`~mocktest.mocking.when`, except once the test is complete,
it makes sure the method you were expecting really was called.

And finally, if you don't already have an object, you can quickly get one by calling
:func:`~mocktest.mocking.mock`:

	>>> obj = mock('my mock')

Mock customisation
------------------

A stubbed method has a number of options for specifying its behaviour including
return values and expectations. For the full API, see :ref:`setting-expectations`.

The basic setup of a test case is identical to using unittest.TestCase:

	>>> from mocktest import *
	>>> class MyTestClass(TestCase):
	... 	def setUp(self):
	... 		# common setup actions...
	...
	... 	def tearDown(self):
	... 		# common teardown actions...
	...
	... 	def test_feature_a(self):
	... 		#test the functionality in feature a
	...
	... 	def test_feature_b(self):
	... 		#test the functionality in feature b

Expecting calls
^^^^^^^^^^^^^^^

	>>> expect(os).system

This will fail your test unless os.system() is called at least once during
the current test case (the check is made right before the ``tearDown()`` method
is executed).

Expecting Arguments
^^^^^^^^^^^^^^^^^^^

| To specify what argument's you're expecting, just pass them in:
| ``expect(obj).method(<args>)``

e.g:

	>>> expect(obj).method(1, 2, 3)
	>>> expect(obj).method(1, 2, 3, foo='bar').once()
	>>> expect(obj).method()

Argument Constraints
^^^^^^^^^^^^^^^^^^^^

You don't have to pass in the exact arguments. You can use matchers, or even your own function:

	>>> expect(obj).method(any_string)
	>>> expect(obj).method(not_(any_int), **kwargs_containing(x=1))
	>>> expect(obj).method.where(lambda *a, **kw: len(a) + len(kw) == 3)

.. comment to fix vim highlights**

If you're going to use a checking function more than once, you should make a matcher.
You can either subclass :class:`~mocktest.matchers.base.Matcher`, or use
the utility :func:`~mocktest.matchers.base.matcher` function.

Post-checking
^^^^^^^^^^^^^
Specifying your expectations before anything happens is sometimes not the best
(or easiest) thing to do.

It's possible to just inspect the state of a stub or mock to see what's happened to it
so far. :data:`received_calls` provides access to the calls received so far. It is a
list of :class:`~mocktest.callrecord.Call` objects:

For a mock:

	>>> mock.foo.bar()
	>>> mock.foo.bar(1, 2, x=3)
	>>> mock.foo.bar.received_calls
	[<#Call: ((), {})>, <#Call: ((1, 2), {'x': 3})>]

And for a stubbed method:

	>>> expect(foo).bar
	>>> foo.bar(1, 2, x=3)
	>>> foo.bar.received_calls
	[<#Call: ((1, 2), {'x': 3})>]


Testing the mocktest library
----------------------------
I use `nosetests <http://code.google.com/p/python-nose/>`_, and just run it from
the root directory. You probably should too!

Thanks
------
`Michael Foord <http://www.voidspace.org.uk/python/mock.html>`_

