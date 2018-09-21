"""
Feanor - The ultimate CSV artisan
=================================

"""

from collections import namedtuple  # pragma: no cover

VersionInfo = namedtuple('VersionInfo', 'major minor micro level serial')  # pragma: no cover

# NOTE: the following line should be update by a script. Do not do any fancy stuff with it. Just use literals.
version_info = VersionInfo(0, 5, 0, 'final', 0)  # pragma: no cover
__version__ = (  # pragma: no cover
        '.'.join(map(str, version_info[:3]))
        + ('-' + version_info.level if version_info.level != 'final' else '')
)
