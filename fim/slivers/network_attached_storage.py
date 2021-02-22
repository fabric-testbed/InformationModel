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
import fim.slivers.base_sliver
import fim.slivers.interface_info
from .base_sliver import BaseSliver
from .interface_info import InterfaceInfo


class NetworkAttachedStorageSliver(BaseSliver):
    # maps onto NetworkNode
    GRAPH_LABEL = 'NetworkNode'

    def __init__(self):
        super().__init__()
        self.technology = None
        self.service_endpoint = None
        self.size = 0
        self.interface_info = None

    def get_technology(self) -> str:
        return self.technology

    def set_technology(self, technology: str):
        self.technology = technology

    def set_service_endpoint(self, service_endpoint: str):
        self.service_endpoint = service_endpoint

    def get_service_endpoint(self) -> str:
        return self.service_endpoint

    def set_size(self, size: int):
        self.size = size

    def get_size(self) -> int:
        return self.size

    def set_interface_info(self, interface_info: InterfaceInfo):
        self.interface_info = interface_info

    def get_interface_info(self) -> InterfaceInfo:
        return self.interface_info
