"""
RPA for Python - Root Setup
"""

from setuptools import setup

setup(
    name='rpa',
    version='1.51.1',
    description='Minimal desktop automation for Python with MCP wrapper',
    long_description='A minimal desktop automation package focused on cursor and keyboard operations '
                     'with MCP (Model Context Protocol) integration.',
    author='Enterprise Technology',
    author_email='',
    url='',
    py_modules=['mcp_server'],
    packages=['rpa_package', 'rpa_package.core'],
    install_requires=[
        'mcp>=1.0.0',
        'pyautogui>=0.9.54',
    ],
    extras_require={
        'mcp': ['mcp>=1.0.0'],
        'desktop': ['pyautogui>=0.9.54'],
    },
    entry_points={
        'console_scripts': [
            'rpa-mcp=mcp_server:main',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
    ],
    license='Apache License 2.0',
    keywords='desktop automation pyautogui mcp',
)