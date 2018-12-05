#!/usr/bin/env python

from setuptools import *
setup(
	packages = find_packages(exclude=['test', 'test.*']),
	description='mocking library for python, inspired by rspec',
	install_requires=['setuptools'],
	long_description="mocktest\n********\n... is a powerful and easy-to-use mocking library, inspired by rspec and\nsimilar in some ways to Michael Foord's popular Mock module.\n\nSource / Issues:\nhttp://github.com/gfxmonk/mocktest/tree/master\n\n\nZero install feed:\nhttp://gfxmonk.net/dist/0install/mocktest.xml\n(this is the preferred distribution method)\n\n\nCheese shop entry:\nhttp://pypi.python.org/pypi/mocktest\n\n\nDocumentation / Installation\n----------------------------\nPlease see the full documentation online at:\nhttp://gfxmonk.net/dist/doc/mocktest/doc/\n",
	name='mocktest',
	url='http://gfxmonk.net/dist/doc/mocktest/doc/',
	version='0.7.3',
classifiers=[
			"Programming Language :: Python",
			"Intended Audience :: Developers",
			"Topic :: Software Development :: Libraries :: Python Modules",
			"Topic :: Software Development :: Testing",
			"Programming Language :: Python :: 2",
			"Programming Language :: Python :: 3",
		],
		package_data = {"": ["LICENCE"]},
		keywords='test mock expect expectation stub rspec unittest',
)
