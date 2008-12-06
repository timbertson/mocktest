# mocktest

## What is it?

## Where did it come from?
I am a big fan of rspec, but less of a fan of ruby as a whole.
I wanted a to use rspec's powerful should_receive() and associated matchers with my python mock objects.

mocktest is by no means a port of rspec - it is much smaller and simpler

## Mocks
The Mock part of mocktest is an almost exact copy of Michael Foord's
[Mock](http://www.voidspace.org.uk/python/modules.shtml#mock).
Because it's pretty much identical, I won't cover its usage here.

The only differences are:

	Mock().is_expected
	Mock().called

both return MockMatcher objects, which are detailed below in the "expectations" section.
The difference between these two attributes is:

 * `is_expected` appends the expectation to the current list of
   expectations, which will be asserted at the end of the current test case
   (if you are subclassing mocktest.TestCase)

 * `called` is a matcher object that you can evaluate immediately,
   which means it's only useful to call it *after* the expected calls
   have already happened

In the below "expectation" examples, I use `Mock().is_expected`.
The exact same syntax works for Mock().called, with the only difference being
that the exprssion will simply evaluate to True or False. So you should do
something like self.assertTrue(obj.called.once()) to actually assert that
the call has occurred.

Additionally, `Mock().side_effect` has been moved to `Mock()._side_effect`
and is now set using the action init argument: `Mock(action=doSomething)`

## Expectations
Having said that mocktest is not rspec, here are a bunch of useful examples ported from the [rspec documentation](http://rspec.info/documentation/mocks/message_expectations.html)

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

## Expecting calls

	myobj = Mock()
	myobj.action.is_expected

This will fail your test unless myobj.action() is called at least once during the current test case
(the check is made right before the tearDown() method is executed)

## Multiplicites of calls

The default `is_expected` ensures that your method is called at least once. There are other options:

	myobj.action.is_expected.once() # once (and no more)
	myobj.action.is_expected.twice()
	myobj.action.is_expected.thrice() # (isn't thrice a great word?)

	myobj.action.is_expected.exactly(4).times
	myobj.action.is_expected.at_least(10).times
	myobj.action.is_expected.at_most(2).times

this also works just fine:

	myobj.action.is_expected.at_most(2)

("times" is unnecessary, but it helps for readability)

## Expecting Arguments

	myobj.action.is_expected.with(<args>)

e.g:

	myobj.action.is_expected.with_args(1, 2, 3)
	myobj.action.is_expected.with_args(1, 2, 3, foo='bar').once()
	myobj.action.is_expected.with_args() # No arguments allowed

*Note:* When adding conditions to a call, the multiplicity (number of
calls) is checked _after_ the other conditions.
This means that while the following will fail:

	myobj.action.is_expected.once()
	myobj.action('a')
	myobj.action('b')

this will succeed:

	myobj.action.is_expected.once().with('a')
	myobj.action('a')
	myobj.action('b')

This is the same way that rspec works, and it is the most flexible,
since you can always put a bound on the total invocations by adding a
non-conditional multiplicity check:

	myobj.action.is_expected.twice()

(you can apply as many `is_expected`'s to a single function as you like)

### Argument Constraints

When you don't know the exact arguments, you can supply a checking function.
If this function does not return True, the expectation fails

	myobj.action.is_expected.where_args(lambda arg1, arg2: arg1 == arg2)
	myobj.action.is_expected.where_args(lambda arg: isinstance(arg, dict))

It doesn't have to be an inline lambda expression:

	def check_args(*args, **kwargs):
		if len(args) > 3:
			return False
		if 'bad_argument' in kwargs:
			return False
		return True
		
	myobj.action.is_expected.where_args(check_args)

## Callbacks

If argument contraints aren't enough, or you need to do something
else when a mock is called, you can supply the action to your Mock
constructor:

	
	def print_arg(arg):
		print "Called with: arg"

	myobj.method = Mock(action=print_arg)

Each time myobj.method is called, print_arg will be called along with it (with all arguments that were passed to `myobj.method`)

This can be handy for raising exceptions to simulate failure.

## Returning values


	Mock().return_value = "result"

