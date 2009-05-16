__all__ = ['stub']

from mockwrapper import MockWrapper
def stub(name=None):
	"""create a new stub - a frozen mock with no methods or children"""
	return MockWrapper(name=name).frozen().raw

