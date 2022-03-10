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
from typing import Any, List
import enum

from .base_sliver import BaseSliver
from .network_service import NetworkServiceInfo


@enum.unique
class ComponentType(enum.Enum):
    GPU = enum.auto()
    SmartNIC = enum.auto()
    SharedNIC = enum.auto()
    FPGA = enum.auto()
    NVME = enum.auto()
    Storage = enum.auto()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class ComponentSliver(BaseSliver):

    def __init__(self):
        super().__init__()
        self.network_service_info = None

    def set_network_service_info(self, ns_info: NetworkServiceInfo):
        self.network_service_info = ns_info

    @staticmethod
    def type_from_str(ctype: str) -> ComponentType or None:
        if ctype is None:
            return None
        for t in ComponentType:
            if ctype == str(t):
                return t


class AttachedComponentsInfo:
    """
    Stores attached components as a dictionary by PCI ID and name
    """
    def __init__(self):
        self.devices = {}
        self.by_type = {}

    def add_device(self, device_info: ComponentSliver) -> None:
        assert device_info.resource_name is not None
        assert device_info.resource_type is not None

        self.devices[device_info.resource_name] = device_info
        devices = self.by_type.get(device_info.resource_type, list())
        devices.append(device_info)
        self.by_type[device_info.resource_type] = devices

    def remove_device(self, name: str) -> None:
        assert name is not None

        if name in self.devices:
            device_info = self.devices.pop(name)
            devices = self.by_type.get(device_info.resource_type, list())
            devices.remove(device_info)

    def get_device(self, name: str) -> ComponentSliver or None:
        assert name is not None

        return self.devices.get(name, None)

    def get_devices_by_type(self, resource_type: Any) -> List[ComponentSliver]:
        """
        Returns a copy of list of devices of this type
        :param resource_type:
        :return:
        """
        assert resource_type is not None

        return list(self.by_type.get(resource_type, list()))

    def list_devices(self):
        return list(self.devices.values())
