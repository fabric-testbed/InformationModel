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


class NetworkLink(BaseElement):
    def __init__(self):
        super().__init__()
        self.bandwidth = 0
        self.layer = None
        self.technology = None
        self.interface_info = None

    def get_bandwidth(self) -> int:
        return self.bandwidth

    def set_bandwidth(self, bandwidth: int):
        self.bandwidth = bandwidth

    def get_layer(self) -> str:
        return self.layer

    def set_layer(self, layer: str):
        self.layer = layer

    def get_technology(self) -> str:
        return self.technology

    def set_technology(self, technology: str):
        self.technology = technology

    def set_interface_info(self, interface_info: InterfaceInfo):
        self.interface_info = interface_info

    def get_interface_info(self) -> InterfaceInfo:
        return self.interface_info
