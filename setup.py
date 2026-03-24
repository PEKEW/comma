#!/usr/bin/env python3
"""Setup script for comma"""

from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='comma',
    version='0.1.0',
    description='natural shell with natural interaction way',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='',
    packages=find_packages(),
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'comma=llm_shell.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: System :: Shells',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='shell llm ai natural-language',
    project_urls={
        'Bug Reports': 'https://github.com/yourname/comma/issues',
        'Source': 'https://github.com/yourname/comma',
    },
)
