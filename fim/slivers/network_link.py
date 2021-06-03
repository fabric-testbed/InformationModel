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
from recordclass import recordclass

from .base_sliver import BaseSliver
from .network_service import NSLayer


class LinkType(enum.Enum):
    """
    Possible Link types in FABRIC. Links are passive, cannot be instantiated
    on demand. Links can only connect two interfaces.
    """
    Patch = enum.auto() # DAC cable or patch fiber
    L1Path = enum.auto() # Wave
    L2Path = enum.auto() # provider L2 path

    def help(self) -> str:
        return self.name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


LinkConstraintRecord = recordclass('LinkConstraintRecord',
                                   ['layer', 'desc',
                                    'num_interfaces'])


class NetworkLinkSliver(BaseSliver):

    """
    Services can be limited by the number of interfaces/connection points they can connect
    The number of sites they may connect and the number of instances they may have in a slice.
    """
    # whenever there is no limit, num is set to 0
    NO_LIMIT = 0

    LinkConstraints = {
        LinkType.Patch: LinkConstraintRecord(layer=NSLayer.L2, num_interfaces=2,
                                             desc='A fiber patch or a cable.'),
        LinkType.L1Path: LinkConstraintRecord(layer=NSLayer.L1, num_interfaces=2,
                                             desc='A wavelength.'),
        LinkType.L2Path: LinkConstraintRecord(layer=NSLayer.L2, num_interfaces=NO_LIMIT,
                                              desc='A provider L2 path or service.')}

    def __init__(self):
        super().__init__()
        self.layer = None
        self.technology = None

    #
    # Setters are only needed for things we want users to be able to set
    #
    def get_layer(self) -> NSLayer:
        return self.layer

    def set_layer(self, layer: NSLayer):
        self.layer = layer

    def get_technology(self) -> str:
        return self.technology

    def set_technology(self, technology: str):
        self.technology = technology

    @staticmethod
    def type_from_str(ltype: str) -> LinkType or None:
        if ltype is None:
            return None
        for t in LinkType:
            if ltype == str(t):
                return t

    @staticmethod
    def layer_from_str(layer: str) -> NSLayer or None:
        if layer is None:
            return None
        for t in NSLayer:
            if layer == str(t):
                return t

