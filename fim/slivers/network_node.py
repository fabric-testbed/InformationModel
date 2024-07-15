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
import ipaddress
from recordclass import recordclass

from fim.slivers.capacities_labels import Location
from .attached_components import ComponentType
from .base_sliver import BaseSliver
from .topology_diff import TopologyDiff, TopologyDiffTuple, TopologyDiffModifiedTuple, WhatsModifiedFlag
from fim.slivers.maintenance_mode import MaintenanceInfo


class NodeType(enum.Enum):
    """
    Possible NetworkNode types in FABRIC.
    """
    Server = enum.auto()
    VM = enum.auto()
    Container = enum.auto()
    Switch = enum.auto()
    NAS = enum.auto()
    Facility = enum.auto()

    def help(self) -> str:
        return 'A ' + self.name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    @classmethod
    def from_string(cls, s: str):
        for nt in NodeType:
            if s == nt.name:
                return cls(nt)
        return None


NodeConstraintRecord = recordclass('NodeConstraintRecord',
                                   ['required_properties',
                                    'forbidden_properties'])


class NodeSliver(BaseSliver):

    NAME_REGEX = r'^[\w\-\.]{2,255}$'

    NodeConstraints = {
        NodeType.Server: NodeConstraintRecord(required_properties=['site'],
                                              forbidden_properties=[]),
        NodeType.VM: NodeConstraintRecord(required_properties=['site'],
                                          forbidden_properties=[]),
        NodeType.Container: NodeConstraintRecord(required_properties=['site'],
                                                 forbidden_properties=[]),
        NodeType.Switch: NodeConstraintRecord(required_properties=[],
                                              forbidden_properties=['attached_components_info',
                                                                    'image_type', 'image_ref']),
        NodeType.NAS: NodeConstraintRecord(required_properties=[],
                                           forbidden_properties=['attached_components_info',
                                                                 'image_type', 'image_ref']),
        NodeType.Facility: NodeConstraintRecord(required_properties=[],
                                                forbidden_properties=['attached_components_info',
                                                                      'image_type', 'image_ref',
                                                                      'management_ip'])
    }

    def __init__(self):
        super().__init__()
        self.management_ip = None
        self.attached_components_info = None
        self.allocation_constraints = None
        self.image_type = None
        self.image_ref = None
        self.service_endpoint = None
        self.network_service_info = None
        self.site = None
        self.location = None
        self.maintenance_info = None

    #
    # Setters are only needed for things we want users to be able to set
    #
    def set_management_ip(self, management_ip: str):
        if management_ip is None:
            self.management_ip = None
        else:
            self.management_ip = ipaddress.ip_address(management_ip)

    def get_management_ip(self) -> str:
        return self.management_ip

    def set_allocation_constraints(self, allocation_constraints: str):
        self.allocation_constraints = allocation_constraints

    def get_allocation_constraints(self) -> str:
        return self.allocation_constraints

    def set_image_type(self, image_type: str):
        self.image_type = image_type

    def get_image_type(self) -> str:
        return self.image_type

    def set_image_ref(self, image_ref: str):
        self.image_ref = image_ref

    def get_image_ref(self) -> str:
        return self.image_ref

    def set_service_endpoint(self, service_endpoint: str):
        self.service_endpoint = service_endpoint

    def get_service_endpoint(self) -> str:
        return self.service_endpoint

    def set_site(self, site: str):
        self.site = site

    def get_site(self) -> str:
        return self.site

    def set_location(self, location: Location):
        assert(location is None or isinstance(location, Location))
        self.location = location

    def get_location(self) -> Location:
        return self.location

    def set_maintenance_info(self, maintenance_info: MaintenanceInfo):
        assert(maintenance_info is None or isinstance(maintenance_info, MaintenanceInfo))
        if maintenance_info:
            maintenance_info.finalize()
        self.maintenance_info = maintenance_info

    def get_maintenance_info(self) -> MaintenanceInfo:
        return self.maintenance_info

    def diff(self, other_sliver) -> TopologyDiff or None:
        if not other_sliver:
            return None

        super().diff(other_sliver)

        comp_added = set()
        comp_removed = set()
        ns_added = set()
        ns_removed = set()
        comp_modified = list()
        ns_modified = list()

        # see if we ourselves have modified properties
        self_modified = list()
        self_modified_flags = self.prop_diff(other_sliver)
        if self.prop_diff(other_sliver) != WhatsModifiedFlag.NONE:
            self_modified.append((self, self_modified_flags))

        if self.attached_components_info and other_sliver.attached_components_info:
            diff_comps = self._dict_diff(self.attached_components_info.devices,
                                         other_sliver.attached_components_info.devices)
            comp_added = set(diff_comps['added'].values())
            comp_removed = set(diff_comps['removed'].values())
            # there are common components (by name) so we check their properties
            comp_common = self._dict_common(self.attached_components_info.devices,
                                            other_sliver.attached_components_info.devices)
            for cA in comp_common.values():
                cB = other_sliver.attached_components_info.get_device(cA.resource_name)
                # compare properties
                flag = cA.prop_diff(cB)

                # compare child interfaces
                if cA.get_type() == ComponentType.SmartNIC:
                    cAns = list(cA.network_service_info.network_services.values())[0]
                    cBns = list(cB.network_service_info.network_services.values())[0]
                    if cAns.diff(cBns):
                        flag |= WhatsModifiedFlag.SUB_INTERFACES

                if flag != WhatsModifiedFlag.NONE:
                    comp_modified.append((cA, flag))

        if not self.attached_components_info and other_sliver.attached_components_info:
            comp_added = set(other_sliver.attached_components_info.devices.values())

        if self.attached_components_info and not other_sliver.attached_components_info:
            comp_removed = set(self.attached_components_info.devices.values())

        if self.network_service_info and other_sliver.network_service_info:
            diff_ns = self._dict_diff(other_sliver.network_service_info.network_services,
                                      other_sliver.network_service_info.network_services)
            ns_added = set(diff_ns['added'].values())
            ns_removed = set(diff_ns['removed'].values())
            # there are common network services so we check their properties
            ns_common = self._dict_common(self.network_service_info.network_services,
                                          other_sliver.network_service_info.network_services)
            for nsA in ns_common.values():
                nsB = other_sliver.network_service_info.get_network_service(nsA.resource_name)
                # compare properties
                flag = nsA.prop_diff(nsB)
                if flag != WhatsModifiedFlag.NONE:
                    ns_modified.append((nsA, flag))

        if not self.network_service_info and other_sliver.network_service_info:
            ns_added = set(other_sliver.network_service_info.network_services.values())

        if self.network_service_info and not other_sliver.network_service_info:
            ns_removed = set(self.network_service_info.network_services.values())

        if len(comp_added) > 0 or len(comp_removed) > 0 or \
                len(ns_removed) > 0 or len(ns_added) > 0 or \
                len(comp_modified) > 0 or len(ns_modified) > 0 or len(self_modified) > 0:
            return TopologyDiff(added=TopologyDiffTuple(components=comp_added, services=ns_added, interfaces=set(),
                                                        nodes=set()),
                                removed=TopologyDiffTuple(components=comp_removed, services=ns_removed,
                                                          interfaces=set(), nodes=set()),
                                modified=TopologyDiffModifiedTuple(
                                    nodes=self_modified,
                                    components=comp_modified,
                                    services=ns_modified,
                                    interfaces=list()))
        else:
            return None

    @staticmethod
    def type_from_str(ntype: str) -> NodeType or None:
        if ntype is None:
            return None
        return NodeType.from_string(ntype)


class CompositeNodeSliver(NodeSliver):
    """
    Does the same thing as NodeSliver, but want to distinguish the class
    """
    def __init__(self):
        super().__init__()