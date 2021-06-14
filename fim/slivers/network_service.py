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
from typing import Tuple, Any
import enum
from recordclass import recordclass

from .base_sliver import BaseSliver
from .path_info import PathRepresentationType, ERO, PathInfo


class NSLayer(enum.Enum):
    L0 = enum.auto()
    L1 = enum.auto()
    L2 = enum.auto()
    L3 = enum.auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class ServiceType(enum.Enum):
    """
    Possible Service types in FABRIC. Unlike links,
    Services can be instantiated on demand.
    """
    P4 = enum.auto()
    MPLS = enum.auto()
    OVS = enum.auto() # OVS service typically inside a NIC
    L2Path = enum.auto() # provider L2 path (overlap with link types -
    # it may be possible to select provider path as a service)
    L2STS = enum.auto() # FABRIC Site-to-Site service
    L2PTP = enum.auto() # FABRIC Port-to-Port service
    L2Multisite = enum.auto() # FABRIC multi-site service
    L2Bridge = enum.auto() # FABRIC L2 bridge within a site
    FABNetv4 = enum.auto() # FABRIC IPv4 routed network
    FABNetv6 = enum.auto() # FABRIC IPv6 routed network
    PortMirror = enum.auto() # FABRIC port mirroring service
    L3VPN = enum.auto() # FABRIC L3 VPN service

    def help(self) -> str:
        return NetworkServiceSliver.ServiceConstraints[self].desc

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


ServiceConstraintRecord = recordclass('ServiceConstraintRecord',
                                      ['layer', 'desc',
                                       'num_interfaces',
                                       'num_sites',
                                       'num_instances'])


class NetworkServiceSliver(BaseSliver):

    # whenever there is no limit, num is set to 0
    NO_LIMIT = 0
    """
    Services can be limited by the number of interfaces/connection points they can connect
    The number of sites they may connect and the number of instances they may have in a slice.
    """
    ServiceConstraints = {
        ServiceType.P4: ServiceConstraintRecord(layer=NSLayer.L2, num_interfaces=NO_LIMIT, num_sites=1,
                                                num_instances=NO_LIMIT,
                                                desc='A P4 service.'),
        ServiceType.OVS: ServiceConstraintRecord(layer=NSLayer.L2, num_interfaces=NO_LIMIT, num_sites=1,
                                                 num_instances=NO_LIMIT,
                                                 desc='An OVS generic service.'),
        ServiceType.MPLS: ServiceConstraintRecord(layer=NSLayer.L2, num_interfaces=NO_LIMIT, num_sites=1,
                                                  num_instances=NO_LIMIT, desc='An MPLS generic service'),
        ServiceType.L2Path: ServiceConstraintRecord(layer=NSLayer.L2, num_interfaces=2, num_sites=2,
                                                    num_instances=NO_LIMIT,
                                                    desc='A provider L2 Path e.g. from ESnet or Internet2.'),
        ServiceType.L2STS: ServiceConstraintRecord(layer=NSLayer.L2, num_interfaces=NO_LIMIT, num_sites=2,
                                                   num_instances=NO_LIMIT,
                                                   desc='A Site-to-Site service in FABRIC.'),
        ServiceType.L2PTP: ServiceConstraintRecord(layer=NSLayer.L2, num_interfaces=2, num_sites=2,
                                                   num_instances=NO_LIMIT,
                                                   desc='A Port-to-Port service in FABRIC.'),
        ServiceType.L2Multisite: ServiceConstraintRecord(layer=NSLayer.L2, num_interfaces=NO_LIMIT, num_sites=NO_LIMIT,
                                                         num_instances=NO_LIMIT,
                                                         desc='A Multi-Site L2 service in FABRIC.'),
        ServiceType.L2Bridge: ServiceConstraintRecord(layer=NSLayer.L2, num_interfaces=NO_LIMIT, num_sites=1,
                                                      num_instances=NO_LIMIT,
                                                      desc='An L2 bridge service within a single FABRIC site.'),
        ServiceType.FABNetv4: ServiceConstraintRecord(layer=NSLayer.L3, num_interfaces=NO_LIMIT, num_sites=NO_LIMIT,
                                                      num_instances=1,
                                                      desc='A routed IPv4 (RFC1918 addressed) FABRIC network.'),
        ServiceType.FABNetv6: ServiceConstraintRecord(layer=NSLayer.L3, num_interfaces=NO_LIMIT, num_sites=NO_LIMIT,
                                                      num_instances=1,
                                                      desc='A routed IPv6 (publicly addressed) FABRIC network.'),
        ServiceType.PortMirror: ServiceConstraintRecord(layer=NSLayer.L2, num_interfaces=2, num_sites=1,
                                                        num_instances=1,
                                                        desc='A port mirroring service in a site.'),
        ServiceType.L3VPN: ServiceConstraintRecord(layer=NSLayer.L3, num_interfaces=NO_LIMIT, num_sites=NO_LIMIT,
                                                   num_instances=NO_LIMIT,
                                                   desc='A L3 VPN service connecting to FABRIC.')
    }

    def __init__(self):
        super().__init__()
        self.layer = None
        self.technology = None
        self.interface_info = None
        self.allocation_constraints = None
        self.ero = None
        self.path_info = None
        self.controller_url = None

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

    def set_allocation_constraints(self, allocation_constraints: str):
        self.allocation_constraints = allocation_constraints

    def get_allocation_constraints(self) -> str:
        return self.allocation_constraints

    def set_ero(self, ero: ERO) -> None:
        self.ero = ero

    def get_ero(self) -> ERO:
        return self.ero

    def set_path_info(self, path_info: PathInfo) -> None:
        self.path_info = path_info

    def get_path_info(self) -> PathInfo:
        return self.path_info

    def set_controller_url(self, curl: str) -> None:
        self.controller_url = curl

    def get_controller_url(self) -> None:
        return self.controller_url

    @staticmethod
    def type_from_str(ltype: str) -> ServiceType or None:
        if ltype is None:
            return None
        for t in ServiceType:
            if ltype == str(t):
                return t

    @staticmethod
    def layer_from_str(layer: str) -> NSLayer or None:
        if layer is None:
            return None
        for t in NSLayer:
            if layer == str(t):
                return t


class NetworkServiceInfo:

    def __init__(self):
        self.network_services = {}

    def add_network_service(self, ns_sliver: NetworkServiceSliver):
        self.network_services[ns_sliver.resource_name] = ns_sliver

    def remove_network_service(self, name: str):
        assert name is not None

        if name in self.network_services.keys():
            self.network_services.pop(name)

    def get_network_service(self, name: str):
        assert name is not None

        return self.network_services.get(name, None)

    def get_network_service_names(self):
        return list(self.network_services.keys())

