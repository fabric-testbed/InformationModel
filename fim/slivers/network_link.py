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
# Author: Komal Thareja (kthare10@renci.org)
import enum

from .base_sliver import BaseSliver
from .interface_info import InterfaceInfo
from .switch_fabric import SFLayer


class LinkType(enum.Enum):
    DAC = enum.auto()
    Wave = enum.auto()
    Patch = enum.auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class NetworkLinkSliver(BaseSliver):

    def __init__(self):
        super().__init__()
        self.layer = None
        self.technology = None
        self.interface_info = None
        self.allocation_constraints = None

    #
    # Setters are only needed for things we want users to be able to set
    #
    def get_layer(self) -> SFLayer:
        return self.layer

    def set_layer(self, layer: SFLayer):
        self.layer = layer

    def get_technology(self) -> str:
        return self.technology

    def set_technology(self, technology: str):
        self.technology = technology

    def set_allocation_constraints(self, allocation_constraints: str):
        self.allocation_constraints = allocation_constraints

    def get_allocation_constraints(self) -> str:
        return self.allocation_constraints

    @staticmethod
    def type_from_str(ltype: str) -> LinkType or None:
        if ltype is None:
            return None
        for t in LinkType:
            if ltype == str(t):
                return t

    @staticmethod
    def layer_from_str(layer: str) -> SFLayer or None:
        if layer is None:
            return None
        for t in SFLayer:
            if layer == str(t):
                return t
