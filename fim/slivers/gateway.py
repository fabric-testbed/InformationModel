#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2021 FABRIC Testbed
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
# Author: Ilya Baldin (ibaldin@renci.org)
from fim.slivers.capacities_labels import Labels


class Gateway:

    def __init__(self, lab: Labels or None):
        """
        Labels specify IPv4 or IPv6 subnet, IPv4 or IPv6 gateway address and an optional MAC.
        Specify the following fields on Labels object:
        - ipv4_subnet and ipv4
        or
        - ipv6_subnet and ipv6
        and an optional mac
        :param lab:
        """
        if lab is None:
            self.lab = None
            return
        # labels must only specify IPv4 or v6 subnet and optional mac
        if lab.ipv4_subnet is not None and lab.ipv4 is not None:
            self.lab = Labels(ipv4_subnet=lab.ipv4_subnet, ipv4=lab.ipv4)
        elif lab.ipv6_subnet is not None and lab.ipv6 is not None:
            self.lab = Labels(ipv6_subnet=lab.ipv6_subnet, ipv6=lab.ipv6)
        else:
            raise GatewayException('Gateway must specify IPv4 or IPv6 subnet, gateway address and an optional MAC')
        if lab.mac is not None:
            self.lab.mac = lab.mac

    @property
    def gateway(self) -> str:
        if self.lab is not None:
            return self.lab.ipv4 if self.lab.ipv4 is not None else self.lab.ipv6
        return None

    @property
    def subnet(self) -> str:
        if self.lab is not None:
            return self.lab.ipv4_subnet if self.lab.ipv4_subnet is not None else self.lab.ipv6_subnet
        return None

    @property
    def mac(self) -> str:
        if self.lab is not None:
            return self.lab.mac
        return None

    def to_json(self) -> str:
        if self.lab is not None:
            return self.lab.to_json()
        return None

    @classmethod
    def from_json(cls, json_string: str):
        return Gateway(Labels.from_json(json_string))

    def __str__(self):
        ar = list()
        if self.lab is None:
            return ""
        if self.lab.ipv4_subnet is not None:
            ar.append("IPv4 subnet: " + self.lab.ipv4_subnet + " GW: " + self.lab.ipv4)
        else:
            ar.append("IPv6: " + self.lab.ipv6_subnet + " GW: " + self.lab.ipv6)

        if self.lab.mac is not None:
            ar.append("(MAC: " + self.lab.mac + ")")
        return " ".join(ar)

    def __repr__(self):
        return self.__str__()


class GatewayException(Exception):

    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Gateway exception: {msg}")