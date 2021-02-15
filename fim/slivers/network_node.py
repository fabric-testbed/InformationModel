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

from .base_sliver import BaseElement
from .attached_components import AttachedComponentsInfo
from .interface_info import InterfaceInfo
from .switch_fabric import SwitchFabricInfo


class NodeType(enum.Enum):
    SERVER = enum.auto()
    VM = enum.auto()
    CONTAINER = enum.auto()
    SWITCH = enum.auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class NodeSliver(BaseElement):

    def __init__(self):
        super().__init__()
        self.management_ip = None
        self.attached_components_info = None
        self.allocation_constraints = None
        self.image_type = None
        self.image_ref = None
        self.service_endpoint = None
        self.switch_fabric_info = None
        self.site = None

    def set_management_ip(self, management_ip: str):
        self.management_ip = ipaddress.ip_address(management_ip)

    def set_attached_components(self, attached_components: AttachedComponentsInfo):
        self.attached_components_info = attached_components

    def set_allocation_constraints(self, allocation_constraints:str):
        self.allocation_constraints = allocation_constraints

    def set_image_type(self, image_type: str):
        self.image_type = image_type

    def set_image_ref(self, image_ref: str):
        self.image_ref = image_ref

    def set_service_endpoint(self, service_endpoint: str):
        self.service_endpoint = service_endpoint

    def set_switch_fabric_info(self, sf_info: SwitchFabricInfo):
        self.switch_fabric_info = sf_info

    def set_site(self, site: str):
        self.site = site

    @staticmethod
    def type_from_str(ctype: str) -> NodeType:
        for t in NodeType:
            if ctype == str(t):
                return t

    def __repr__(self):
        # FIXME
        return super().__repr__() + \
               '\nSite:' + self.site + \
               '\nImage Ref:' + str(self.image_ref)