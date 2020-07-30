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
import uuid

from .base_sliver import BaseElement


class InterfaceInfoEntry(BaseElement):
    def __init__(self, interface_id: str = None, interface_name: str = None):
        super().__init__()
        if interface_id is not None:
            self.interface_id = interface_id
        else:
            self.interface_id = uuid.uuid4().__str__()
        self.interface_name = interface_name
        self.interface_ips = []

    def set_interface_name(self, interface_name: str):
        self.interface_name = interface_name

    def get_interface_name(self) -> str:
        return self.interface_name

    def set_interface_id(self, interface_id: str):
        self.interface_id = interface_id

    def get_interface_id(self) -> str:
        return self.interface_id

    def set_interface_ips(self, interface_ips: list):
        self.interface_ips = interface_ips

    def get_interface_ips(self) -> list:
        return self.interface_ips

    def add_interface_ip(self, interface_ip: str):
        ip = ipaddress.ip_address(interface_ip)
        self.interface_ips.append(ip)

    def remove_interface_ip(self, interface_ip: str):
        ip = ipaddress.ip_address(interface_ip)
        self.interface_ips.remove(ip)


class InterfaceInfo:
    def __init__(self):
        self.interfaces = {}

    def add_interface(self, interface_info: InterfaceInfoEntry):
        self.interfaces[interface_info.get_interface_id()] = interface_info

    def remove_interface(self, interface_id: str):
        if interface_id in self.interfaces:
            self.interfaces.pop(interface_id)

    def get_interface(self, interface_id: str):
        return self.interfaces.get(interface_id, None)
