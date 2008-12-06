#!/usr/bin/env python

from setuptools import setup

setup(
	name='mocktest',
	version='0.1',
	description='a mocking and expectation test library for python, inspired by rspec',
	author='Tim Cuthbertson',
	author_email='tim3d.junk+mocktest@gmail.com',
	url='http://github.com/gfxmonk/mocktest/tree',
	packages=['mocktest'],
	
	long_description="""\
	mocktest is a mocking and expectation test library for python.
	It is similar to rspec's should_receive and associated matchers, and
	can be used with the standard unittest library.
	""",
	classifiers=[
		"License :: OSI Approved :: BSD License",
		"Programming Language :: Python",
		"Development Status :: 4 - Beta",
		"Intended Audience :: Developers",
		"Topic :: Software Development :: Libraries :: Python Modules",
		"Topic :: Software Development :: Testing",
	],
	keywords='test mock expect expectation stub rspec unittest',
	license='BSD',
	install_requires=[
		'setuptools',
	],
)
