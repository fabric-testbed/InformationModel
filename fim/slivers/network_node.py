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
from .base_sliver import BaseSliver


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