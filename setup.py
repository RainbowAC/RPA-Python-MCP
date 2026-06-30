"""
RPA for Python - Root Setup
"""

from setuptools import setup

setup(
    name='rpa',
    version='1.51.0',
    description='RPA for Python - simple and powerful API for robotic process automation',
    long_description='RPA for Python is a Python package for robotic process automation '
                     'with a simple and powerful API for automating websites, '
                     'desktop applications and the command line. '
                     'This package includes MCP (Model Context Protocol) integration for AI assistants.',
    author='Enterprise Technology',
    author_email='',
    url='',
    py_modules=['tagui'],
    packages=['rpa_package', 'rpa_package.core'],
    install_requires=[
        'mcp>=1.0.0',
    ],
    extras_require={
        'mcp': ['mcp>=1.0.0'],
    },
    entry_points={
        'console_scripts': [
            'rpa-mcp=mcp_server:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Healthcare Industry',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration',
        'Topic :: Office/Business :: Financial',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
    ],
    license='Apache License 2.0',
    keywords='rpa robotic process automation tagui mcp',
)