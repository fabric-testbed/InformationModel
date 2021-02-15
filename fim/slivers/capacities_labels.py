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
# Author: Ilya Baldin (ibaldin@renci.org)
from typing import List
import json

from abc import ABC, abstractmethod


class JSONField(ABC):

    @abstractmethod
    def set_fields(self, **kwargs):
        """
        Set the fields of this object
        :param kwargs:
        :return:
        """

    def to_json(self) -> str:
        """
        Dumps to JSON the __dict__ of the instance. Be careful as the fields in this
        class should only be those that can be present in the dictionary.
        :return:
        """
        d = self.__dict__.copy()
        for k in self.__dict__:
            if d[k] == 0:
                d.pop(k)
        return json.dumps(d, skipkeys=True, sort_keys=True)

    def from_json(self, json_string: str):
        d = json.loads(json_string)
        self.set_fields(**d)


class Capacities(JSONField):
    """
    Implements basic capacity field handling - encoding and decoding
    from JSON dictionaries of properties
    """
    def __init__(self):
        self.cpu = 0
        self.core = 0
        self.ram = 0
        self.disk = 0
        self.bw = 0
        self.unit = 0

    def set_fields(self, **kwargs) -> None:
        """
        Universal integer setter for all fields.
        Values should be non-negative integers. Throws a RuntimeError
        if you try to set a non-existent field.
        :param kwargs:
        :return:
        """
        for k, v in kwargs.items():
            assert v >= 0
            try:
                # will toss an exception if field is not defined
                self.__getattribute__(k)
                self.__setattr__(k, v)
            except AttributeError:
                raise RuntimeError(f"Unable to set field {k} of capacity, no such field available")


class Labels(JSONField):
    """
    Class implementing various encodings of labels field, encoding
    and decoding from JSON dictionaries of properties
    """
    def __init__(self):
        self.l_bdf = None
        self.l_mac = None
        self.l_ipv4 = None
        self.l_ipv4_range = None
        self.l_ipv6 = None
        self.l_ipv6_range = None
        self.l_asn = None
        self.l_vlan = None
        self.l_vlan_range = None
        self.l_node = None

    def set_fields(self, **kwargs) -> None:
        """
        Universal setter for all fields (just strip the l_ from the field
        name of the field). Values should be strings or lists of strings.
        Throws a RuntimeError if you try to set a non-existent field.
        :param kwargs:
        :return:
        """
        for k, v in kwargs.items():
            assert v is not None  # could be strings or lists of strings
            assert isinstance(v, str) or isinstance(v, list)
            try:
                # will toss an exception if field is not defined
                self.__getattribute__('l_' + k)
                self.__setattr__('l_' + k, v)
            except AttributeError:
                raise RuntimeError(f"Unable to set field {k} of labels, no such field available")