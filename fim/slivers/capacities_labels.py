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

from fim.graph.abc_property_graph_constants import ABCPropertyGraphConstants


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

    @classmethod
    def from_json(cls, json_string: str):
        """
        Set fields from json string and returns a new object
        :param json_string:
        :return: object
        """
        if json_string is None or len(json_string) == 0 or json_string == ABCPropertyGraphConstants.NEO4j_NONE:
            return None
        d = json.loads(json_string)
        ret = cls()
        ret.set_fields(**d)
        return ret

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
    UNITS = {'cpu': '', 'unit': '', 'core': '', 'ram': 'G', 'disk': 'G', 'bw': 'Gbps', 'burst_size': 'Mbits'}

    def __init__(self, **kwargs):
        self.cpu = 0
        self.core = 0
        self.ram = 0
        self.disk = 0
        self.bw = 0
        self.burst_size = 0
        self.unit = 0
        self.set_fields(**kwargs)

    def set_fields(self, **kwargs):
        """
        Universal integer setter for all fields.
        Values should be non-negative integers. Throws a CapacityException
        if you try to set a non-existent field.
        :param kwargs:
        :return: self to support call chaining
        """
        for k, v in kwargs.items():
            if v is not None:
                assert v >= 0
            try:
                # will toss an exception if field is not defined
                self.__getattribute__(k)
                self.__setattr__(k, v)
            except AttributeError:
                raise CapacityException(f"Unable to set field {k} of capacity, no such field available "
                                        f"{[k for k in self.__dict__.keys()]}")
        return self

    def __add__(self, other):
        assert isinstance(other, Capacities)
        ret = Capacities()
        for f, v in self.__dict__.items():
            ret.__dict__[f] = self.__dict__[f] + other.__dict__[f]

        return ret

    def __sub__(self, other):
        assert isinstance(other, Capacities)
        ret = Capacities()

        for f, v in self.__dict__.items():
            ret.__dict__[f] = self.__dict__[f] - other.__dict__[f]

        return ret

    def __gt__(self, other):
        assert isinstance(other, Capacities)
        for f, v in self.__dict__.items():
            if v < other.__dict__[f]:
                return False
        return True

    def __lt__(self, other):
        assert isinstance(other, Capacities)
        for f, v in self.__dict__.items():
            if v > other.__dict__[f]:
                return False
        return True

    def __eq__(self, other):
        assert isinstance(other, Capacities)
        for f, v in self.__dict__.items():
            if v != other.__dict__[f]:
                return False
        return True

    def negative_fields(self) -> List[str]:
        """
        returns list of fields that are negative
        :return:
        """
        ret = list()
        for f, v in self.__dict__.items():
            if v < 0:
                ret.append(f)

        return ret

    def positive_fields(self, fields: List[str]) -> bool:
        """
        Return true if indicated fields are positive >0
        :param fields:
        :return:
        """
        assert fields is not None
        for f in fields:
            if self.__dict__[f] <= 0:
                return False
        return True

    def __str__(self):
        d = self.__dict__.copy()
        for k in self.__dict__:
            if d[k] is None or d[k] == 0:
                d.pop(k)
        if len(d) == 0:
            return ''
        ret = "{ "
        for i, v in d.items():
            ret = ret + i + ": " + f'{v:,} ' + self.UNITS[i] + ", "
        return ret[:-2] + "}"


class CapacityTuple:
    """
    This class takes two capacities objects (what is the total
    available and what is free) and helps print them.
    """
    def __init__(self, *, total: Capacities, allocated: Capacities):
        assert total is not None
        if allocated is None:
            allocated = Capacities()
        self.available = total
        self.free = total - allocated

    def __str__(self):
        d2 = self.available.__dict__.copy()
        d1 = self.free.__dict__.copy()

        for k in self.free.__dict__:
            if d1[k] == 0 and d2[k] == 0:
                d1.pop(k)
                d2.pop(k)
        if len(d1) == 0:
            return ''
        ret = '{ '
        for k in d1:
            ret = ret + k + ": " + f'{d1[k]:,}' + "/" + f'{d2[k]:,} ' + Capacities.UNITS[k] + ", "
        return ret[:-2] + '}'


class CapacityHints(JSONField):
    """
    Capacity hints are strings representing something about the capacity of a sliver,
    e.g. an instance size name. They have to be mappable to actual capacities
    via e.g. a catalog.
    """
    def __init__(self, **kwargs):
        self.instance_type = None
        self.set_fields(**kwargs)

    def set_fields(self, **kwargs):
        """
        Universal setter for all fields. Values should be strings.
        Throws a LabelException if you try to set a non-existent field.
        :param kwargs:
        :return: self to support call chaining
        """
        for k, v in kwargs.items():
            assert v is not None  # could be strings
            assert isinstance(v, str)
            try:
                # will toss an exception if field is not defined
                self.__getattribute__(k)
                self.__setattr__(k, v)
            except AttributeError:
                raise CapacityHintException(f"Unable to set field {k} of capacity hints, no such field available")
        # to support call chaining
        return self

    def __add__(self, other):
        assert isinstance(other, Labels)
        raise RuntimeError("Not Implemented")

    def __str__(self):
        d = self.__dict__.copy()
        for k in self.__dict__:
            if d[k] is None:
                d.pop(k)
        if len(d) == 0:
            return ''
        ret = "{ "
        for i, v in d.items():
            ret = ret + i + ": " + str(v) + ", "
        return ret[:-2] + "}"


class Labels(JSONField):
    """
    Class implementing various encodings of labels field, encoding
    and decoding from JSON dictionaries of properties
    """
    def __init__(self, **kwargs):
        self.bdf = None
        self.mac = None
        self.ipv4 = None
        self.ipv4_range = None
        self.ipv6 = None
        self.ipv6_range = None
        self.asn = None
        self.vlan = None
        self.vlan_range = None
        self.inner_vlan = None
        self.instance = None
        self.instance_parent = None
        self.local_name = None
        self.local_type = None
        self.device_name = None
        self.set_fields(**kwargs)

    def set_fields(self, **kwargs):
        """
        Universal setter for all fields. Values should be strings or lists of strings.
        Throws a LabelException if you try to set a non-existent field.
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
                raise LabelException(f"Unable to set field {k} of labels, no such field available "
                                     f"{[k for k in self.__dict__.keys()]}")
        # to support call chaining
        return self

    def __add__(self, other):
        assert isinstance(other, Labels)
        # FIXME: does ADD mean finding a union of label sets per type?
        raise RuntimeError("Not Implemented")

    def __str__(self):
        d = self.__dict__.copy()
        for k in self.__dict__:
            if d[k] is None:
                d.pop(k)
        if len(d) == 0:
            return ''
        ret = "{ "
        for i, v in d.items():
            ret = ret + i + ": " + str(v) + ", "
        return ret[:-2] + "}"


class ReservationInfo(JSONField):
    """
    Reservation info structure for ASM sliver objects
    """

    def __init__(self, **kwargs):
        self.reservation_id = None
        self.reservation_state = None
        self.set_fields(**kwargs)

    def set_fields(self, **kwargs):
        """
        Universal setter for all fields. Values should be strings or lists of strings.
        Throws a ReservationInfoException if you try to set a non-existent field.
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
                raise ReservationInfoException(f"Unable to set field {k} of reservation info, no such field "
                                               f"available {[k for k in self.__dict__.keys()]}")
        # to support call chaining
        return self


class StructuralInfo(JSONField):
    """
    Structural info on the for sliver objects (things like - is it a stitching node,
    what is parent graph or subgraph)
    """
    def __init__(self):
        self.sub_graph_id = None
        self.parent_graph_id = None
        self.adm_graph_ids = None

    def set_fields(self, **kwargs):
        """
        Universal setter for all fields. Values are strings or boolean.
        Throws a
        :param kwargs:
        :return:
        """
        for k, v in kwargs.items():
            assert v is not None  # could be strings or lists of strings
            assert isinstance(v, str) or isinstance(v, list)
            try:
                # will toss an exception if field is not defined
                self.__getattribute__(k)
                self.__setattr__(k, v)
            except AttributeError:
                raise StructuralInfoException(f"Unable to set field {k} of structural info, no such field available")
        # to support call chaining
        return self


class CapacityException(Exception):
    """
    Exception with a capacity
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Delegation exception: {msg}")


class CapacityHintException(Exception):
    """
    Exception with a capacity
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Delegation exception: {msg}")


class LabelException(Exception):
    """
    Exception with a label
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Label exception: {msg}")


class ReservationInfoException(Exception):
    """
    Exception with a reservation info
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"ReservationInfo exception: {msg}")


class StructuralInfoException(Exception):
    """
    Exception with a structural info
    """

    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"ReservationInfo exception: {msg}")