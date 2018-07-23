"""
Feanor - The ultimate CSV artisan
=================================

"""

from collections import namedtuple

VersionInfo = namedtuple('VersionInfo', 'major minor micro releaselevel serial')

version_info = VersionInfo(0, 2, 1, 'final', 0)
__version__ = '.'.join(map(str, version_info[:3]))