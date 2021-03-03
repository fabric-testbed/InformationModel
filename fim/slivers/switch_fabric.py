#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2021 FABRIC Testbed
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
import enum

from .base_sliver import BaseSliver
from .interface_info import InterfaceInfo


class SFLayer(enum.Enum):
    L2 = enum.auto()
    L3 = enum.auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class SFType(enum.Enum):
    # only one subtype for now
    SwitchFabric = enum.auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class SwitchFabricSliver(BaseSliver):
    """
    SwitchFabrics are typically invisible to everyone, but provide
    the abstraction of switching across some number of ports
    """

    def __init__(self):
        super().__init__()
        self.layer = None
        self.interface_info = None

    def set_layer(self, layer: SFLayer):
        self.layer = layer

    def get_layer(self) -> SFLayer:
        return self.layer

    @staticmethod
    def layer_from_str(layer: str) -> SFLayer:
        if layer is None:
            return None
        for t in SFLayer:
            if layer == str(t):
                return t

    @staticmethod
    def type_from_str(ntype: str) -> SFType:
        if ntype is None:
            return None
        for t in SFType:
            if ntype == str(t):
                return t


class SwitchFabricInfo:

    def __init__(self):
        self.switch_fabrics = {}

    def add_switch_fabric(self, sf_info: SwitchFabricSliver):
        self.switch_fabrics[sf_info.resource_name] = sf_info

    def remove_switch_fabric(self, name: str):
        assert name is not None

        if name in self.switch_fabrics.keys():
            self.switch_fabrics.pop(name)

    def get_switch_fabric(self, name: str):
        assert name is not None

        return self.switch_fabrics.get(name, None)
