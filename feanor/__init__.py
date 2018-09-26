# Copyright 2018 Giacomo Alzetta <giacomo.alzetta+feanor@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
