## mocktest (version 0.2)
... is a powerful and easy-to-use mocking library, inspired by rspec and
similar in many ways to Michael Foord's popular Mock module.

The main features are:
 - powerful expectation matching behaviour for mock objects
 - automatic verification of expectations (before each test's tearDown)
 - automatic rollback of inserted mock objects after each test

It's released under the BSD licence (see the LICENCE file).

Source / Readme:
[http://github.com/gfxmonk/mocktest/tree/master](http://github.com/gfxmonk/mocktest/tree/master)

Issues / discussion:
[http://code.google.com/p/python-mocktest/](http://code.google.com/p/python-mocktest/)

Cheese shop entry:
[http://pypi.python.org/pypi/mocktest](http://pypi.python.org/pypi/mocktest/0.1)

### Where did it come from?
I am a big fan of rspec, but less of a fan of ruby as a whole.
I wanted a to use rspec's powerful `should_receive()` and associated matchers
with my python mock objects.

mocktest is by no means a port of rspec - it is smaller and simpler, and a lot
more pythonic.

### what *are* mocks?

What are mocks used for? mocks can pretend to be pretty much any object. Mocks
record what happens to them (accessors, method calls, etc) and allow you to
verify that this is what you expected. Replace a database connection with a mock
and make sure the right commands are being sent to your database - without the
overhead and trouble of using an actual database. Replace os.system with a mock,
and supply your own response to shell commands. Mocks can be used to satisfy
dependencies or simulate external conditions in your program so you can focus
on unit-level testing.

---
<!--tableofcontents-->

# mocktest

## TestCase

When using mocktest, you should always use `mocktest.TestCase` instead of
`unittest.TestCase`. Mocktest's version is almost identical, but automatically
calls the required setup and teardown hooks for the mocktest library.

There is one important addition to the `mocktest.TestCase` class:

 * `assertRaises(exception_type, callable, < ... >)`

Where additional args can be:

 * `args=(arg1,arg2)`
 ** Fails unless the arguments provided to the exception constructor match the
    given args
 * `message="some string"`
 ** Fails unless the error message (i.e. str(exception)) is equal to this
    message
 * `matches="string"` or `matches=re.compile("match_string", custom_flags)`
 ** Just like message, except a regex.search is required to return a match
    instead of requiring the strings to be identical

This was adapted from [http://code.activestate.com/recipes/307970/](http://code.activestate.com/recipes/307970/)

## mocks

mocktest is still a young framework, and is likely to evolve. While the
inspiration is from rspec, a lot of the mechanics differ either necessarily
because of differences between ruby and python, and a bunch of things were done
differently to make things cleaner.

mocks in mocktest have 3 components. This might sound like two more than you
would need, but bear with me:

 * **raw mock**: a raw mock is a minimal mock object that can be put wherever
   you need it. It records interaction that happens to it, but it can't
   distinguish between interaction as part of your test and interaction caused
   by the rest of the program.
   
   Some mock frameworks only have this object, but adding methods for
   controlling and inspecting a mock interferes with the actual mock behaviour
   itself. For this reason, mocktest has a puppet-master of sorts:

 * **mock wrapper**: a mock wrapper is how you talk to a raw mock
   behind-the-scenes. It allows you to set the return value for a method,
   or see how many times and with what arguments a raw mock has been called.
   In your unit test source code, you will mostly be interacting with mock
   wrappers to define behaviour and specify your expectations.

 * **mock anchor**: finally, there is one piece missing in the puzzle. You
   have a mock, and you talk to it through a mock wrapper. But how do you
   insert it where it needs to go? A mock anchor latches on to a root
   object, and records every mock you create on it. Creating a mock called
   "some\_method" on a mock anchor will attach it to parent.some\_method.
   And more importantly, when your unit test is done it will revert
   parent.some_method to what it was before.
   
   By using a mock anchor, you ensure that your mocks never live past the
   lifespan of your test case - this can cause havok in other mock
   frameworks.

So, how do you use all of these things?

	anchor = mock_on(some_object)

creates a **mock anchor** attached to some\_object.

	wrapper = anchor.foo

creates a **raw mock** called `foo`, and attaches it to some\_object.foo. The
value of this expression is a **mock wrapper** linked to the newly-created
some_object.foo raw mock.

If your mock is not attached to anything, you can create a standalone mock
wrapper:
	
	wrapper = mock_wrapper()

you can get the raw mock (to provide to your code) with:

	raw_mock = wrapper.mock

and if you just have a raw mock object, you can get a wrapper for it by calling:

	wrapper = mock_wrapper(raw_mock)

This might seem a little confusing, but hopefully the examples below will help.

### Mock customisation

A mock has a few options for specifying its behaviour:

	wrapper = mock_wrapper()
	wrapper.name = "my mock"
	wrapper.return_value = "result!"

which will result in:

	>>> raw_mock = wrapper.mock
	>>> str(raw_mock)
	'my mock'
	
	>>> raw_mock()
	'result!'

The other property your mock wrapper has is:

	def my_action(*args):
		print "called with: %r" % (args,)
		return "result..."
	wrapper.action = my_action

resulting in:
	
	>>> wrapper.mock('a','b','c')
	called with: ['a','b','c']
	'result...'

*note*: If you use both action and return_value, action will be called but
return_value will be returned instead of anything action returns. If you only
have action, the return value will come from that (even if it doesn't return
anything; the return value will be None)

Because setting properties like this is a little verbose, mock wrapper objects
provide some helpful methods. These methods all return the mock wrapper itself,
so you can chain them together.

	mock_wrapper().named('my mock')
	mock_wrapper().returning(10)
	mock_wrapper().with_action(lambda x: x + 1)

In addition, there are some additional methods which don't directly
relate to attributes:

	mock_wrapper().raising(IOError)
	mock_wrapper().raising(IOError('permission denied'))

`raising` takes an exception class or instance and raises it when the mock is
called. This overwrites the mock's action attribute, and makes return_value
irrelevant.


By default, calling `raw_mock.some_attribute` will force `some_attribute` to be
added to the mock. If you don't want this behaviour, you can lock down the mock
using:

	mock_wrapper.frozen()

This will raise an `AttributeError` when any new attribute is accessed (or set)
on the mock.

	mock_wrapper().with_children('x', 'y', z='zed')
	mock_wrapper().with_methods('x','y', z='zed')
	mock_wrapper().with_spec(some_object)

Children and methods are similar. They take in any number of string arguments
and keyword arguments. String arguments ensure that an attribute of that name
exists on the mock. Keyword arguments specify its value, as well.

The difference between `methods` and `children` is that the value of a method
is used for a child's return_value:

	>>> wrapper = mock_wrapper().with_methods('y', z='zed')
	>>> wrapper.mock.z()
	'zed'

whereas child values are used as-is:

	>>> wrapper = mock_wrapper().with_children('y', z='zed')
	>>> wrapper.mock.z
	'zed'

If you have an object that you want to mimic, you can use:

	mock_wrapper().with_spec(some_object)

If `some_object` has attributes "foo" and "bar", so too will your mock. The
values for these attributes are mocks; they do not copy the `spec_object`'s
attribute values.

Calling `with_methods`, `with_children` or `with_spec` has the side effect of
freezing the mock. Any attributes that aren't already on the mock cannot be
added. If you want to control this yourself, use `wrapper.frozen()` and
`wrapper.unfrozen()`


If you want to get advanced, you can also override special methods on a mock:

	>>> wrapper = mock_wrapper().with_special( __len__ = lambda x: 5 )
	>>> len(wrapper.mock)
	5

You can't override `__str__` or `__init__` (but there's little point to those),
and you also can't override `__getattribute__` or `__setattr__`. Are you that
much of a masochist?

### Expectations

Having earlier said that mocktest is not rspec, here are a bunch of useful
examples ported from the
[rspec documentation](http://rspec.info/documentation/mocks/message_expectations.html)

The basic setup of a test case is identical to using unittest.TestCase:

	from mocktest import *
	
		class MyTestClass(TestCase):
			def setUp(self):
				# common setup actions...
			
			def tearDown(self):
				# common teardown actions...
			
			def test_feature_a(self):
				#test the functionality in feature a
				
			def test_feature_b(self):
				#test the functionality in feature b

#### Expecting calls

	mock_os = mock_on(os)
	mock_os.system.is_expected

This will fail your test unless os.system() is called at least once during
the current test case (the check is made right before the `tearDown()` method
is executed)

If you don't want an anchored mock, you can use:

	wrapper = mock_wrapper()
	raw_mock = wrapper.mock
	wrapper.is_expected

You can then pass raw_mock into a function and ensure that it is called. But
you should **not** set `os.system = raw_mock`. This will change `os.system`
for the life of your tests, and will almost certainly mess up the rest of your
test cases. That is why the `mock_on()` function exists to automatically
clean up your mocks.

#### Multiplicites of calls

The default `is_expected` ensures that your method is called at least once.
There are other options:

	mock_anchor.method.is_expected.no_times() # shouldn't be called
	mock_anchor.method.is_expected.once() # once (and no more)
	mock_anchor.method.is_expected.twice()
	mock_anchor.method.is_expected.thrice() # (isn't thrice a great word?)

	mock_anchor.method.is_expected.exactly(4).times
	mock_anchor.method.is_expected.at_least(10).times
	mock_anchor.method.is_expected.at_most(2).times

this also works just fine:

	mock_anchor.method.is_expected.at_most(2)

("times" is unnecessary, but it helps for readability)

#### Expecting Arguments

	mock_anchor.method.is_expected.with(<args>)

e.g:

	mock_anchor.method.is_expected.with_args(1, 2, 3)
	mock_anchor.method.is_expected.with_args(1, 2, 3, foo='bar').once()
	mock_anchor.method.is_expected.with_args() # No arguments allowed

*Note:* When adding conditions to a call, the multiplicity (number of
calls) is checked _after_ the other conditions.
This means that while the following will fail:

	mock_anchor.method.is_expected.once()
	myobj.action('a')
	myobj.action('b')

this will succeed:

	mock_anchor.method.is_expected.once().with('a')
	myobj.action('a')
	myobj.action('b')

This is the same way that rspec works, and it is the most flexible,
since you can always put a bound on the total invocations by adding a
non-conditional multiplicity check:

	mock_anchor.method.is_expected.twice()

(you can apply as many `is_expected`'s to a single mock as you like)

#### Argument Constraints

When you don't know the exact arguments, you can supply a checking function.
If this function does not return True, the expectation fails:

	mock_anchor.method.is_expected.where_args(lambda arg1, arg2: arg1 == arg2)
	mock_anchor.method.is_expected.where_args(lambda arg: isinstance(arg, dict))

It doesn't have to be an inline lambda expression:

	def check_args(*args, **kwargs):
		if len(args) > 3:
			return False
		if 'bad_argument' in kwargs:
			return False
		return True
		
	mock_anchor.method.is_expected.where_args(check_args)

#### Post-checking
Specifying your expectations before anything happens is sometimes not the best
(or easiest) thing to do.

It's possible to just inspect the state of a mock to see what's happened to it
so far. `called` is almost identical to `is_expected`. Unlike an expectation
object, The result of a `called` expression should be compared to `True` or
`False` to check whether the expressed call(s) did indeed happen.

	self.assertTrue(mock_wrapper.called.once().with_args('foo'))
	if not mock_wrapper.called.once():
		assert False, "Things went bad!"

But the most useful feature of of `called` is its ability to retrieve the calls
that the mock has received. So in the following example:

	wrapper = mock_wrapper()
	mock = wrapper.mock

	mock('a', b='foo')
	mock('b')
	mock(b='bar')
	
	>>> wrapper.called.thrice().get_calls()
	[(('a',), {'b': 'foo'}), ('b',), (None, {'b': 'bar'})]

Note that where a call has no arguments or has no keyword-arguments, the
first or second element (respectively) in the call tuple is None instead of an
empty tuple or dict. This is mostly for readability, because there are already
enough parentheses in the mix.

**Note**: get_calls will fail if the assertions made after `called` are not met.
e.g: if mock has been called once and you ask for
`wrapper.called.twice().get_calls()`, then you'll get an AssertionError.

If you're only expecting one call, you can use `get_args`:

	mock(b='bar')
	>>> wrapper.called.once().get_args()

**Note** that `get_args` requires you to explicitly specify `once()`.
	
---
# Testing the mocktest library
I use [nosetests](http://code.google.com/p/python-nose/), and just run it from
the root directory. You probably should too!

#Thanks
[Michael Foord](http://www.voidspace.org.uk/python/mock.html)
