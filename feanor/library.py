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

import random
from abc import ABCMeta, abstractmethod

from .dsl.compiler import SimpleCompatibility


class Library(metaclass=ABCMeta):
    def __init__(self, global_configuration, random_funcs):
        self.global_configuration = global_configuration
        self.random_funcs = random_funcs

    def make_producer(self, name, config):
        factory = self.get_producer_factory(name)
        the_config = self.global_configuration.get(name, {})
        the_config.update(config)
        return factory(self.random_funcs, the_config)

    @abstractmethod
    def compatibility(cls):
        raise NotImplementedError

    @abstractmethod
    def env(cls):
        raise NotImplementedError

    @abstractmethod
    def func_env(cls):
        raise NotImplementedError

    @abstractmethod
    def get_producer_factory(self, name):
        raise NotImplementedError


class EmptyLibrary(Library):
    def __init__(self):
        super().__init__({}, random)

    def compatibility(cls):
        return SimpleCompatibility(lambda x, y: x)

    def env(cls):
        return {}

    def func_env(cls):
        return {}

    def get_producer_factory(self, name):
        return lambda random_funcs, config=None: None
