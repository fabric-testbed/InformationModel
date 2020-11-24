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
import ipaddress

from .base_sliver import BaseElement
from .attached_pci_devices import AttachedPCIDevices
from .interface_info import InterfaceInfo


class Node(BaseElement):
    def __init__(self):
        super().__init__()
        self.management_ip = None
        self.cpu_cores = 0
        self.ram_size = 0
        self.disk_size = 0
        self.attached_pci_devices = None
        self.allocation_constraints = {}
        self.image_type = None
        self.image_ref = None
        self.service_endpoint = None
        self.interface_info = None

    def set_management_ip(self, management_ip: str):
        self.management_ip = ipaddress.ip_address(management_ip)

    def get_management_ip(self) -> ipaddress.ip_address:
        return self.management_ip

    def set_cpu_cores(self, cpu_cores: int):
        self.cpu_cores = cpu_cores

    def get_cpu_cores(self) -> int:
        return self.cpu_cores

    def set_ram_size(self, ram_size: int):
        self.ram_size = ram_size

    def get_ram_size(self) -> int:
        return self.ram_size

    def set_disk_size(self, disk_size: int):
        self.disk_size = disk_size

    def get_disk_size(self) -> int:
        return self.disk_size

    def set_attached_pci_devices(self, attached_pci_devices: AttachedPCIDevices):
        self.attached_pci_devices = attached_pci_devices

    def get_attached_pci_devices(self) -> AttachedPCIDevices:
        return self.attached_pci_devices

    def set_allocation_constraints(self, pci_id: str, allocation_constraints:str):
        self.allocation_constraints[pci_id] = allocation_constraints

    def get_allocation_constraints(self, pci_id: str):
        return self.allocation_constraints.get(pci_id, Node)

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

    def set_interface_info(self, interface_info: InterfaceInfo):
        self.interface_info = interface_info

    def get_interface_info(self) -> InterfaceInfo:
        return self.interface_info