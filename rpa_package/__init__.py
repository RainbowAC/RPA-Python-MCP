"""
RPA for Python - Package

A Python package for Robotic Process Automation (RPA).

Usage:
    import rpa as r
    r.init()
    r.url('https://www.google.com')
    r.type('q', 'decentralization[enter]')
    r.close()
"""

from .rpa import *

__version__ = '1.51.0'