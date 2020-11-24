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

from .base_sliver import BaseElement
from .interface_info import InterfaceInfo

class AttachedPCIDeviceEntry(BaseElement):
    def __init__(self, pci_id: str = None, pci_slot: str = None):
        super().__init__()
        self.pci_id = pci_id
        self.pci_slot = pci_slot
        self.disk_size = 0
        self.interface_info = None

    def set_pci_id(self, pci_id: str):
        self.pci_id = pci_id

    def get_pci_id(self) -> str:
        return self.pci_id

    def set_pci_slot(self, pci_slot: str):
        self.pci_slot = pci_slot

    def get_pci_slot(self) -> str:
        return self.pci_slot

    def set_disk_size(self, disk_size: int):
        self.disk_size = disk_size

    def get_disk_size(self) -> int:
        return self.disk_size

    def set_interface_info(self, interface_info: InterfaceInfo):
        self.interface_info = interface_info

    def get_interface_info(self) -> InterfaceInfo:
        return self.interface_info


class AttachedPCIDevices:
    def __init__(self):
        self.devices = {}

    def add_device(self, device_info: AttachedPCIDeviceEntry):
        self.devices[device_info.get_pci_id()] = device_info

    def remove_device(self, pci_id: str):
        if pci_id in self.devices:
            self.devices.pop(pci_id)

    def get_device(self, pci_id: str):
        return self.devices.get(pci_id, None)
