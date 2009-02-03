import sys, os
toplevel = os.path.join(os.path.dirname(__file__),'..')
if toplevel not in sys.path:
	sys.path.insert(0,toplevel)