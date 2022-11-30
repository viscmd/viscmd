#!/usr/bin/env python3

from setuptools import setup, find_packages
from os import path

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='viscmd',
      packages=['viscmd'],
      version='0.9.7',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Intended Audience :: End Users/Desktop',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3.7',
      ],
      install_requires=[],
      entry_points={'console_scripts': ['viscmd=viscmd.__main__:main']},
      package_data={'': ['*.png']},
      author='gaory',
      author_email='gaory1@qq.com',
      description='visual command',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/gaory1/viscmd',
      license='MIT',
      keywords='visual command completion')
