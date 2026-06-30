"""
RPA for Python - Sample Script

Demonstrates basic usage of RPA for Python.
"""

import rpa as r

r.init()
r.url('https://www.google.com')
r.type('q', 'decentralization[enter]')
r.close()