"""
Feanor - The ultimate CSV artisan
=================================

"""

from collections import namedtuple

VersionInfo = namedtuple('VersionInfo', 'major minor micro level serial')

# NOTE: the following line should be update by a script. Do not do any fancy stuff with it. Just use literals.
version_info = VersionInfo(0, 4, 0, 'final', 0)
__version__ = '.'.join(map(str, version_info[:3])) + ('-' + version_info.level if version_info.level != 'final' else '')
