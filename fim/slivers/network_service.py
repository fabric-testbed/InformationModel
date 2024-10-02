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
from .gateway import Gateway
from .interface_info import InterfaceType
from .topology_diff import TopologyDiff, TopologyDiffTuple, TopologyDiffModifiedTuple, WhatsModifiedFlag
from .capacities_labels import Labels


class NSLayer(enum.Enum):
    L0 = enum.auto()
    L1 = enum.auto()
    L2 = enum.auto()
    L3 = enum.auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, s: str):
        for la in NSLayer:
            if la.name == s:
                return cls(la)
        return None


class MirrorDirection(enum.Enum):
    Both = enum.auto()
    RX_Only = enum.auto()
    TX_Only = enum.auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, s: str):
        for md in MirrorDirection:
            if md.name == s:
                return cls(md)
        return None


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
    VLAN = enum.auto() # a local VLAN (internal to site)
    FABNetv4Ext = enum.auto() # externally reachable IPv4 service
    FABNetv6Ext = enum.auto() # externally reachable IPv6 service

    def help(self) -> str:
        return NetworkServiceSliver.ServiceConstraints[self].desc

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


ServiceConstraintRecord = recordclass('ServiceConstraintRecord',
                                      ['layer', 'desc',
                                       'min_interfaces',
                                       'num_interfaces',
                                       'num_sites',
                                       'num_instances', # instances **per site**
                                       'required_properties',
                                       'forbidden_properties',
                                       'required_interface_types'])


class NetworkServiceSliver(BaseSliver):

    NAME_REGEX = r'^[\w\-_\.]{2,255}$'

    # whenever there is no limit, num is set to 0
    NO_LIMIT = 0
    """
    Services can be limited by the number of interfaces/connection points they can connect
    The number of sites they may connect and the number of instances they may have in a slice.
    """
    ServiceConstraints = {
        ServiceType.P4: ServiceConstraintRecord(layer=NSLayer.L2, min_interfaces=1,
                                                num_interfaces=NO_LIMIT, num_sites=1,
                                                num_instances=NO_LIMIT, required_properties=[],
                                                forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                      'mirror_direction'],
                                                required_interface_types=[],
                                                desc='A P4 service.'),
        ServiceType.OVS: ServiceConstraintRecord(layer=NSLayer.L2, min_interfaces=1,
                                                 num_interfaces=NO_LIMIT, num_sites=1,
                                                 num_instances=NO_LIMIT, required_properties=[],
                                                 forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                       'mirror_direction'],
                                                 required_interface_types=[],
                                                 desc='An OVS generic service.'),
        ServiceType.VLAN: ServiceConstraintRecord(layer=NSLayer.L2, min_interfaces=1,
                                                  num_interfaces=NO_LIMIT, num_sites=1,
                                                  num_instances=NO_LIMIT, required_properties=[],
                                                  forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                        'mirror_direction',
                                                                        'controller_url'],
                                                  required_interface_types=[],
                                                  desc='An local VLAN service in a site.'),
        ServiceType.MPLS: ServiceConstraintRecord(layer=NSLayer.L2, min_interfaces=1,
                                                  num_interfaces=NO_LIMIT, num_sites=1,
                                                  num_instances=NO_LIMIT, desc='An MPLS generic service',
                                                  required_properties=[],
                                                  forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                        'mirror_direction',
                                                                        'controller_url'],
                                                  required_interface_types=[]),
        ServiceType.L2Path: ServiceConstraintRecord(layer=NSLayer.L2, min_interfaces=1,
                                                    num_interfaces=2, num_sites=2,
                                                    num_instances=NO_LIMIT,
                                                    desc='A provider L2 Path e.g. from ESnet or Internet2.',
                                                    required_properties=[],
                                                    forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                          'mirror_direction',
                                                                          'controller_url'],
                                                    required_interface_types=[]),
        ServiceType.L2STS: ServiceConstraintRecord(layer=NSLayer.L2, min_interfaces=2,
                                                   num_interfaces=NO_LIMIT, num_sites=2,
                                                   num_instances=NO_LIMIT,
                                                   desc='A Site-to-Site service in FABRIC.',
                                                   required_properties=[],
                                                   forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                         'mirror_direction',
                                                                         'controller_url',
                                                                         "ero"],
                                                   required_interface_types=[]),
        ServiceType.L2PTP: ServiceConstraintRecord(layer=NSLayer.L2, min_interfaces=2,
                                                   num_interfaces=2, num_sites=2,
                                                   num_instances=NO_LIMIT,
                                                   desc='A Port-to-Port service in FABRIC.',
                                                   required_properties=[],
                                                   forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                         'mirror_direction',
                                                                         'controller_url'],
                                                   required_interface_types=[InterfaceType.DedicatedPort,
                                                                             InterfaceType.FacilityPort]),
        ServiceType.L2Multisite: ServiceConstraintRecord(layer=NSLayer.L2, min_interfaces=1,
                                                         num_interfaces=NO_LIMIT, num_sites=NO_LIMIT,
                                                         num_instances=NO_LIMIT,
                                                         desc='A Multi-Site L2 service in FABRIC.',
                                                         required_properties=[],
                                                         forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                               'mirror_direction',
                                                                               'controller_url'],
                                                         required_interface_types=[]),
        ServiceType.L2Bridge: ServiceConstraintRecord(layer=NSLayer.L2, min_interfaces=1,
                                                      num_interfaces=NO_LIMIT, num_sites=1,
                                                      num_instances=NO_LIMIT,
                                                      desc='An L2 bridge service within a single FABRIC site.',
                                                      required_properties=[],
                                                      forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                            'mirror_direction',
                                                                            'controller_url'],
                                                      required_interface_types=[]),
        ServiceType.FABNetv4: ServiceConstraintRecord(layer=NSLayer.L3, min_interfaces=1,
                                                      num_interfaces=NO_LIMIT, num_sites=1,
                                                      num_instances=NO_LIMIT,
                                                      desc='A routed IPv4 (RFC1918 addressed) FABRIC network.',
                                                      required_properties=[],
                                                      forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                            'mirror_direction',
                                                                            'controller_url'],
                                                      required_interface_types=[]),
        ServiceType.FABNetv6: ServiceConstraintRecord(layer=NSLayer.L3, min_interfaces=1,
                                                      num_interfaces=NO_LIMIT, num_sites=1,
                                                      num_instances=NO_LIMIT,
                                                      desc='A routed IPv6 (publicly addressed) FABRIC network.',
                                                      required_properties=[],
                                                      forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                            'mirror_direction',
                                                                            'controller_url'],
                                                      required_interface_types=[]),
        ServiceType.PortMirror: ServiceConstraintRecord(layer=NSLayer.L2, min_interfaces=1,
                                                        num_interfaces=1, num_sites=1,
                                                        num_instances=NO_LIMIT,
                                                        desc='A port mirroring service in a FABRIC site.',
                                                        required_properties=['mirror_port',
                                                                             'mirror_direction', 'site'],
                                                        forbidden_properties=['controller_url'],
                                                        required_interface_types=[]),
        ServiceType.L3VPN: ServiceConstraintRecord(layer=NSLayer.L3, min_interfaces=1,
                                                   num_interfaces=NO_LIMIT, num_sites=NO_LIMIT,
                                                   num_instances=NO_LIMIT,
                                                   desc='A L3 VPN service connecting to FABRIC.',
                                                   required_properties=[],
                                                   forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                         'mirror_direction',
                                                                         'controller_url'],
                                                   required_interface_types=[]),
        ServiceType.FABNetv4Ext: ServiceConstraintRecord(layer=NSLayer.L3, min_interfaces=1,
                                                         num_interfaces=NO_LIMIT, num_sites=1,
                                                         num_instances=NO_LIMIT,
                                                         desc='A routed IPv4 publicly addressed FABRIC '
                                                              'network capable of external connectivity.',
                                                         required_properties=[],
                                                         forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                               'mirror_direction',
                                                                               'controller_url'],
                                                         required_interface_types=[]),
        ServiceType.FABNetv6Ext: ServiceConstraintRecord(layer=NSLayer.L3, min_interfaces=1,
                                                         num_interfaces=NO_LIMIT, num_sites=1,
                                                         num_instances=NO_LIMIT,
                                                         desc='A routed IPv6 publicly addressed FABRIC network '
                                                              'capable of external connectivity.',
                                                         required_properties=[],
                                                         forbidden_properties=['mirror_port', 'mirror_vlan',
                                                                               'mirror_direction',
                                                                               'controller_url'],
                                                         required_interface_types=[])
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
        self.site = None
        self.gateway = None
        self.mirror_port = None
        self.mirror_vlan = None
        self.mirror_direction = None

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

    def set_site(self, site: str):
        self.site = site

    def get_site(self) -> str:
        return self.site

    def set_gateway(self, gw: Gateway):
        self.gateway = gw

    def get_gateway(self) -> Gateway:
        return self.gateway

    def set_mirror_port(self, mirror_port: str):
        self.mirror_port = mirror_port

    def get_mirror_port(self) -> str:
        return self.mirror_port

    def set_mirror_vlan(self, mirror_vlan: str):
        self.mirror_vlan = mirror_vlan

    def get_mirror_vlan(self) -> str:
        return self.mirror_vlan

    def set_mirror_direction(self, mirror_direction: MirrorDirection):
        self.mirror_direction = mirror_direction

    def get_mirror_direction(self) -> MirrorDirection:
        return self.mirror_direction

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

    def diff(self, other_sliver) -> TopologyDiff or None:
        if not other_sliver:
            return None

        super().diff(other_sliver)

        ifs_added = set()
        ifs_removed = set()
        ifs_modified = list()

        # see if we ourselves have modified properties
        self_modified = list()
        self_modified_flags = self.prop_diff(other_sliver)
        if self.prop_diff(other_sliver) != WhatsModifiedFlag.NONE:
            self_modified.append((self, self_modified_flags))

        if self.interface_info and other_sliver.interface_info:
            diff_comps = self._dict_diff(self.interface_info.interfaces,
                                         other_sliver.interface_info.interfaces)
            ifs_added = set(diff_comps['added'].values())
            ifs_removed = set(diff_comps['removed'].values())
            # there are interfaces in common, so we check if they have been modified
            ifs_common = self._dict_common(self.interface_info.interfaces,
                                           other_sliver.interface_info.interfaces)
            for iA in ifs_common.values():
                iB = other_sliver.interface_info.get_interface(iA.resource_name)
                # compare properties
                flag = iA.prop_diff(iB)

                if iA.get_type() == InterfaceType.DedicatedPort:
                    if iA.diff(iB):
                        flag |= WhatsModifiedFlag.SUB_INTERFACES

                if flag != WhatsModifiedFlag.NONE:
                    ifs_modified.append((iA, flag))

        if not self.interface_info and other_sliver.interface_info:
            ifs_added = set(other_sliver.interface_info.interfaces.values())

        if self.interface_info and not other_sliver.interface_info:
            ifs_removed = set(self.interface_info.interfaces.values())

        if len(self_modified) > 0 or len(ifs_added) > 0 or len(ifs_removed) > 0 or len(ifs_modified) > 0:
            return TopologyDiff(added=TopologyDiffTuple(components=set(), services=set(), interfaces=ifs_added,
                                                        nodes=set()),
                                removed=TopologyDiffTuple(components=set(), services=set(),
                                                          interfaces=ifs_removed, nodes=set()),
                                modified=TopologyDiffModifiedTuple(
                                    nodes=list(),
                                    components=list(),
                                    services=self_modified,
                                    interfaces=ifs_modified)
                                )
        else:
            return None


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

    def list_services(self):
        return list(self.network_services.values())

