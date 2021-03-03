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
from typing import List, Dict
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
        class should only be those that can be present in JSON output.
        If there are no values in the object, returns empty string.
        :return:
        """
        d = self.__dict__.copy()
        for k in self.__dict__:
            if d[k] is None or d[k] == 0:
                d.pop(k)
        if len(d) == 0:
            return ''
        return json.dumps(d, skipkeys=True, sort_keys=True)

    def from_json(self, json_string: str):
        """
        Set fields from json string (if string is none or empty,
        nothing happens)
        :param json_string:
        :return: self for call chaining
        """
        if json_string is None or len(json_string) == 0:
            return self
        d = json.loads(json_string)
        self.set_fields(**d)
        return self

    def to_dict(self) -> Dict[str, str] or None:
        """
        Convert to a dictionary skipping empty fields. Returns None
        if all fields are empty
        :return:
        """
        d = self.__dict__.copy()
        for k in self.__dict__:
            if d[k] is None or d[k] == 0:
                d.pop(k)
        if len(d) == 0:
            return None
        return d

    def __repr__(self):
        return self.to_json()

    def __str__(self):
        return self.to_json()

    def list_fields(self):
        l = list(self.__dict__.keys())
        l.sort()
        return l


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

    def set_fields(self, **kwargs):
        """
        Universal integer setter for all fields.
        Values should be non-negative integers. Throws a RuntimeError
        if you try to set a non-existent field.
        :param kwargs:
        :return: self to support call chaining
        """
        for k, v in kwargs.items():
            assert v >= 0
            try:
                # will toss an exception if field is not defined
                self.__getattribute__(k)
                self.__setattr__(k, v)
            except AttributeError:
                raise RuntimeError(f"Unable to set field {k} of capacity, no such field available")
        return self


class Labels(JSONField):
    """
    Class implementing various encodings of labels field, encoding
    and decoding from JSON dictionaries of properties
    """
    def __init__(self):
        self.bdf = None
        self.mac = None
        self.ipv4 = None
        self.ipv4_range = None
        self.ipv6 = None
        self.ipv6_range = None
        self.asn = None
        self.vlan = None
        self.vlan_range = None
        self.node = None

    def set_fields(self, **kwargs):
        """
        Universal setter for all fields (just strip the l_ from the field
        name of the field). Values should be strings or lists of strings.
        Throws a RuntimeError if you try to set a non-existent field.
        :param kwargs:
        :return: self to support call chaining
        """
        for k, v in kwargs.items():
            assert v is not None  # could be strings or lists of strings
            assert isinstance(v, str) or isinstance(v, list)
            try:
                # will toss an exception if field is not defined
                self.__getattribute__(k)
                self.__setattr__(k, v)
            except AttributeError:
                raise RuntimeError(f"Unable to set field {k} of labels, no such field available")
        # to support call chaining
        return self
