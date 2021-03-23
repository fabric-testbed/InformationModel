#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2020 FABRIC Testbed
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Author: Ilya Baldin (ibaldin@renci.org)
"""
A pluggable interface for externally supplied implementations
for various algorithms operating on FIM. Examples include:
- Responding to controller queries and producing a BQM using CBM
- Partitioning slice model into slivers
- Implementing various modify operations
Various classes in FIM have hooks to call registered external implementations
at well-defined points. Any registered implementation subsumes the native FIM
implementation of the corresponding functionality. In case of multiple registered
implementations the last one takes precedence.
"""
from abc import ABC, abstractmethod
import inspect
from typing import List
from enum import Enum

from fim.graph.abc_property_graph import ABCPropertyGraph
from fim.graph.resources.abc_cbm import ABCCBMPropertyGraph
from fim.graph.resources.abc_bqm import ABCBQMPropertyGraph


class PluggableType(Enum):
    AM = 1
    Broker = 2
    Orchestrator = 3


class ABCPluggable(ABC):
    """
    Defines framework that can be used to override default behaviors in different
    parts of FIM. Such methods begin with 'plug_'
    A pluggable class doesn't have to implement all available methods nor does it have
    to inherit from this class or its subclasses.
    A single instance of a class implementing pluggable methods is created within a
    particular context (AM, Broker or Orchestrator), allowing in-memory state
    to be passed. Persistent state is derived from the attached Neo4j instance, currently
    a relational database interface would have to be implemented explicitly -
    extensions to support relational persistent storage abstractions for Pluggables
    may be added at a later time.
    """
    def __init__(self, *, actor):
        """
        Take actor pointer into the plugin
        :param actor:
        """
        self.actor = actor

    @classmethod
    def get_pluggable_methods(cls, detail: bool=True) -> List:
        """
        Return a list of tuples about pluggable methods that can be implemented.
        Each tuple is (method_name, signature, docstring).
        If detail is set to False, a simple list of names is returned
        :param detail:
        :return:
        """
        ret = list()
        for i in inspect.getmembers(cls):
            # returns tuples
            # ('__abstractmethods__', frozenset({'plug_partition_slice', 'plug_produce_bqm'}))
            # ('plug_produce_bqm', < function ABCPluggable.plug_produce_bqm at 0x105c8cd40 >)
            if i[0].startswith('plug_'):
                method = i[0]
                _callable = getattr(cls, method)
                docstring = inspect.getdoc(_callable)
                signature = inspect.signature(_callable)
                if detail:
                    ret.append((method, str(signature), docstring))
                else:
                    ret.append(method)
        return ret

    @staticmethod
    def get_implemented_methods(cls) -> List:
        """
        Get the pluggable methods a class implements as a list of method names.
        :param cls:
        :return:
        """
        ret = list()
        for i in inspect.getmembers(cls):
            # returns tuples
            # ('__abstractmethods__', frozenset({'plug_partition_slice', 'plug_produce_bqm'}))
            # ('plug_produce_bqm', < function ABCPluggable.plug_produce_bqm at 0x105c8cd40 >)
            if i[0].startswith('plug_'):
                method = i[0]
                ret.append(method)
        return ret


class BrokerPluggable(ABCPluggable):
    """
        Overridable Broker-specific methods for graph/resource manipulations in FIM
    """
    PLUGGABLE_PRODUCE_BQM = 'plug_produce_bqm'

    def __init__(self, *, actor):
        super().__init__(actor=actor)

    @abstractmethod
    def plug_produce_bqm(self, *, cbm: ABCCBMPropertyGraph, **kwargs) -> ABCBQMPropertyGraph:
        """
        Produce a Broker Query Model based on a Combined Broker Model and
        some unspecified query parameters
        :param cbm:
        :param kwargs:
        :return:
        """


class AMPluggable(ABCPluggable):
    """
    Overridable AM-specific methods for graph/resource manipulations in FIM
    """
    def __init__(self, *, actor):
        super().__init__(actor=actor)

class OrchestratorPluggable(ABCPluggable):
    """
    Overridable Controller-specific methods for graph/resource manipulations in FIM
    """
    PLUGGABLE_PARTITION_SLICE = 'plug_partition_slice'

    def __init__(self, *, actor):
        super().__init__(actor=actor)

    @abstractmethod
    def plug_partition_slice(self, *, slice: ABCPropertyGraph, **kwargs) -> List:
        """
        Partition slice into slivers using a slice model and some
        unspecified other parameters
        :param slice:
        :param kwargs:
        :return:
        """


class PluggableRegistry:
    """
    Singleton which accepts and stores a registration for external
    implementation defined by Pluggable. Those wishing to override
    default FIM behaviors should see the return of Pluggable.get_pluggable_methods(),
    implement desired methods in their class and register it with PluggableRegistry.
    An instance of this class will be created as a singleton and the methods
    will be invoked at appropriate points within FIM.
    A pluggable class does not have to inherit from Pluggable.
    """
    PLUGGABLE_MAP = {PluggableType.AM: (AMPluggable,
                                        set(AMPluggable.get_pluggable_methods(detail=False))),
                     PluggableType.Orchestrator: (OrchestratorPluggable,
                                                  set(OrchestratorPluggable.get_pluggable_methods(detail=False))),
                     PluggableType.Broker: (BrokerPluggable,
                                            set(BrokerPluggable.get_pluggable_methods(detail=False)))}

    class __Pluggable:
        def __init__(self, t: PluggableType, p, **kwargs):
            self.pluggable = p
            # figure out which methods it implements
            pluggable_type, pluggable_methods = PluggableRegistry.PLUGGABLE_MAP[t]
            self.implemented_methods = pluggable_type.get_implemented_methods(p)
            if len(self.implemented_methods) == 0 or \
                    len(pluggable_methods.intersection(self.implemented_methods)) == 0:
                raise RuntimeError(f"Plugin {p} does not implement any of the expected methods: "
                                   f"{pluggable_methods}")
            self.pluggable_instance = p(**kwargs)

        def get_implemented_methods(self):
            return self.implemented_methods

        def get_method_callable(self, method):
            if method not in self.implemented_methods:
                raise RuntimeError(f"Method {method} is not implemented by the plugin {self.pluggable}")
            return getattr(self.pluggable_instance, method)

    instance = dict()

    def __init__(self):
        pass

    def register_pluggable(self, *, t: PluggableType, p, **kwargs):
        """
        Register a pluggable interface
        :param t:
        :param p:
        :return:
        """
        if PluggableRegistry.instance.get(t, None) is None:
            PluggableRegistry.instance[t] = PluggableRegistry.__Pluggable(t, p, **kwargs)
        else:
            raise RuntimeError(f"Another plugin {PluggableRegistry.instance[t].pluggable} "
                               f"class is already registered for type {t.name}")

    def unregister_pluggable(self, *, t: PluggableType):
        PluggableRegistry.instance.pop(t, None)

    def pluggable_registered(self, *, t: PluggableType) -> bool:
        """
        Return true if a pluggable already is registered
        :param t:
        :return:
        """
        return PluggableRegistry.instance.get(t, None) is not None

    def get_implemented_methods(self, *, t: PluggableType) -> List:
        """
        Get implemented methods for a pluggable type as a list of strings
        :param t:
        :return:
        """
        return PluggableRegistry.instance[t].get_implemented_methods()

    def get_method_callable(self, *, t: PluggableType, method):
        """
        Get a callable for a given method name
        :param t:
        :param method:
        :return:
        """
        return PluggableRegistry.instance[t].get_method_callable(method=method)
