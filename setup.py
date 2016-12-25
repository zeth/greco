from __future__ import with_statement

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

greco_classifiers = [
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Topic :: Software Development :: Libraries",
    "Topic :: Utilities",
]

with open("README.rst", "r") as fp:
    greco_long_description = fp.read()

setup(name="greco",
      description = "a fun typing game for learning the Green Code visual language.",
      version="0.1.3",
      author="Zeth",
      author_email="theology@gmail.com",
      packages=["greco"],
      long_description=greco_long_description,
      license="GPL",
      classifiers=greco_classifiers,
      url = 'http://ledui.github.io/',
      install_requires=[
          'ledgrid',
          'greencode',
          'pygame'
      ],
      scripts=['bin/greco'],
      include_package_data = True
)
