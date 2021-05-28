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
from typing import Tuple, Any
import enum
from recordclass import recordclass

from .base_sliver import BaseSliver
from .interface_info import InterfaceInfo
from .switch_fabric import SFLayer


class LinkType(enum.Enum):
    """
    Possible Lin/Service types in FABRIC.
    """
    Patch = enum.auto() # DAC cable or patch fiber
    L1Path = enum.auto() # Wave
    L2Path = enum.auto() # provider L2 path
    L2STS = enum.auto() # FABRIC Site-to-Site service
    L2PTP = enum.auto() # FABRIC Port-to-Port service
    L2Multisite = enum.auto() # FABRIC multi-site service
    L2Bridge = enum.auto() # FABRIC L2 bridge within a site
    FABNetv4 = enum.auto() # FABRIC IPv4 routed network
    FABNetv6 = enum.auto() # FABRIC IPv6 routed network
    PortMirror = enum.auto() # FABRIC port mirroring service
    L3VPN = enum.auto() # FABRIC L3 VPN service

    def help(self) -> str:
        return NetworkLinkSliver.LinkServiceConstraints[self].desc

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


ServiceConstraints = recordclass('ServiceConstraints',
                                 ['layer', 'desc',
                                  'num_interfaces',
                                  'num_sites',
                                  'num_instances'])


class EROType(enum.Enum):
    """
    Explicit Route Object type - an ERO can be represented as a list or as a graph
    """
    List = enum.auto()   # ERO is a simple list
    Graph = enum.auto()  # ERO is a graph

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class NetworkLinkSliver(BaseSliver):

    # whenever there is no limit, num is set to 0
    NO_LIMIT = 0
    """
    Services can be limited by the number of interfaces/connection points they can connect
    The number of sites they may connect and the number of instances they may have in a slice.
    """
    LinkServiceConstraints = {
        LinkType.Patch: ServiceConstraints(layer=SFLayer.L0, num_interfaces=2, num_sites=1,
                                           num_instances=NO_LIMIT,
                                           desc='A patch or a cable within a site.'),
        LinkType.L1Path: ServiceConstraints(layer=SFLayer.L1, num_interfaces=2, num_sites=2,
                                            num_instances=NO_LIMIT,
                                            desc='A Wave or similar connecting two sites.'),
        LinkType.L2Path: ServiceConstraints(layer=SFLayer.L2, num_interfaces=2, num_sites=2,
                                            num_instances=NO_LIMIT,
                                            desc='A provider L2 Path e.g. from ESnet or Internet2.'),
        LinkType.L2STS: ServiceConstraints(layer=SFLayer.L2, num_interfaces=NO_LIMIT, num_sites=2,
                                           num_instances=NO_LIMIT,
                                           desc='A Site-to-Site service in FABRIC.'),
        LinkType.L2PTP: ServiceConstraints(layer=SFLayer.L2, num_interfaces=2, num_sites=2,
                                           num_instances=NO_LIMIT,
                                           desc='A Port-to-Port service in FABRIC.'),
        LinkType.L2Multisite: ServiceConstraints(layer=SFLayer.L2, num_interfaces=NO_LIMIT, num_sites=NO_LIMIT,
                                                 num_instances=NO_LIMIT,
                                                 desc='A Multi-Site L2 service in FABRIC.'),
        LinkType.L2Bridge: ServiceConstraints(layer=SFLayer.L2, num_interfaces=NO_LIMIT, num_sites=1,
                                              num_instances=NO_LIMIT,
                                              desc='An L2 bridge service within a single FABRIC site.'),
        LinkType.FABNetv4: ServiceConstraints(layer=SFLayer.L3, num_interfaces=NO_LIMIT, num_sites=NO_LIMIT,
                                              num_instances=1,
                                              desc='A routed IPv4 (RFC1918 addressed) FABRIC network.'),
        LinkType.FABNetv6: ServiceConstraints(layer=SFLayer.L3, num_interfaces=NO_LIMIT, num_sites=NO_LIMIT,
                                              num_instances=1,
                                              desc='A routed IPv6 (publicly addressed) FABRIC network.'),
        LinkType.PortMirror: ServiceConstraints(layer=SFLayer.L2, num_interfaces=2, num_sites=1,
                                                num_instances=1,
                                                desc='A port mirroring service in a site.'),
        LinkType.L3VPN: ServiceConstraints(layer=SFLayer.L3, num_interfaces=NO_LIMIT, num_sites=NO_LIMIT,
                                           num_instances=NO_LIMIT,
                                           desc='A L3 VPN service connecting to FABRIC.')
    }

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


class ERO:
    """
    Explicit Route Object class
    """
    def __init__(self, etype: EROType = EROType.List, strict: bool = False):
        # default is 'loose' list
        self.strict = strict
        self.type = etype
        self.payload = None

    def set(self, payload) -> None:
        """
        ERO payload can be a list of node/site identifiers
        or id of a graph built externally
        :param payload:
        :return:
        """
        if self.type == EROType.List:
            assert(isinstance(payload, list))
            self.payload = payload
        else:
            assert(isinstance(payload, str))
            self.payload = str

    def get(self) -> Tuple[EROType, Any]:
        """
        Return a tuple of type, payload of ERO (list or graph id)
        :return:
        """
        return self.type, self.payload

    def get_strict(self) -> bool:
        """
        Get the ERO strict flag
        :return:
        """
        return self.strict
