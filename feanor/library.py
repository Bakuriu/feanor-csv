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
        self.random_funcs = random_funcs
        self.global_configuration = global_configuration
        self._factories = {}
        self.definitions = {}

    def make_producer(self, name, config):
        name_chain = self._name_config_chain(name)
        factory = self._get_producer_factory(name_chain)
        the_config = {}
        for ancestor_name, ancestor_config in name_chain:
            the_config.update(ancestor_config)
            the_config.update(self.global_configuration.get(ancestor_name, {}))
        the_config.update(config)
        return factory(self.random_funcs, the_config)

    def _name_config_chain(self, name):
        name_chain = []
        while name in self.definitions:
            name_chain.append((name, self.definitions[name].get('config', {})))
            name = self.definitions[name]['producer']
        name_chain.append((name, {}))
        return list(reversed(name_chain))

    def _get_producer_factory(self, name_chain):
        for producer_name, _ in reversed(name_chain):
            try:
                return self.get_producer_factory(producer_name)
            except LookupError:
                pass
        raise LookupError('could not find producer {!r}'.format(name_chain[-1][0]))

    def get_producer_factory(self, name):
        return self._factories[name]

    def register_factory(self, name, factory):
        self._check_producer_uniqueness(name)
        self._factories[name] = factory

    def register_factories(self, factories):
        for factory_name, factory_func in factories.items():
            self.register_factory(factory_name, factory_func)

    def register_definition(self, name, definition):
        self._check_producer_uniqueness(name)
        self.definitions[name] = definition

    def register_definitions(self, definitions):
        for name, definition in definitions.items():
            self.register_definition(name, definition)

    def _check_producer_uniqueness(self, name):
        if name in self._factories:
            raise ValueError('A factory called {!r} already exists'.format(name))
        elif name in self.definitions:
            raise ValueError('A definition called {!r} already exists'.format(name))

    @abstractmethod
    def compatibility(self):
        raise NotImplementedError

    @abstractmethod
    def env(self):
        raise NotImplementedError

    @abstractmethod
    def func_env(self):
        raise NotImplementedError


class MockLibrary(Library):
    def __init__(self, factories=None, global_configuration=None, definitions=None):
        super().__init__(global_configuration or {}, random)
        if factories:
            self.register_factories(factories)
        if definitions:
            self.register_definitions(definitions)
        self._env = {}
        self._func_env = {}

    def compatibility(self):
        return SimpleCompatibility(lambda x, y: x)

    def env(self):
        return self._env

    def func_env(self):
        return self._func_env

    def register_function(self, name, func, arg_types, ret_type):
        self._func_env[name] = func
        func_env_types = self._func_env.setdefault('::types::', {})
        func_env_types[name] = (arg_types, ret_type)

    def register_variable(self, name, value, type):
        self._env[name] = value
        env_types = self._env.setdefault('::types::', {})
        env_types[name] = type
