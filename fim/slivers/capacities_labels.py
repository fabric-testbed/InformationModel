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
from typing import List, Dict, Tuple
import json
import re

from abc import ABC, abstractmethod

import requests
import urllib.parse

from fim.graph.abc_property_graph_constants import ABCPropertyGraphConstants


class JSONField(ABC):

    @classmethod
    def update(cls, lab, **kwargs):
        """
        quasi-copy constructor if kwargs are ommitted,
        otherwise also sets additional fields. Creates a new
        instance of appropriate subclass and returns it.
        DOES NOT UPDATE IN PLACE!
        :param lab:
        :param kwargs:
        :return:
        """
        assert isinstance(lab, JSONField)
        inst = lab.__class__()
        for k, v in lab.__dict__.items():
            inst.__setattr__(k, v)
        inst._set_fields(**kwargs)
        return inst

    @abstractmethod
    def _set_fields(self, **kwargs):
        """
        Abstract private set_fields method
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
        ret._set_fields(**d)
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
    from JSON dictionaries of properties. Only ints are allowed.
    """
    UNITS = {'cpu': '', 'unit': '',
             'core': '', 'ram': 'G',
             'disk': 'G', 'bw': 'Gbps',
             'burst_size': 'Mbits',
             'mtu': 'B'}

    def __init__(self, **kwargs):
        self.cpu = 0
        self.core = 0
        self.ram = 0
        self.disk = 0
        self.bw = 0
        self.burst_size = 0
        self.unit = 0
        self.mtu = 0
        self._set_fields(**kwargs)

    def _set_fields(self, **kwargs):
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
                assert isinstance(v, int)
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

    def positive_fields(self, fields: List[str] or str) -> bool:
        """
        Return true if indicated fields are positive >0
        :param fields: string or list of strings
        :return:
        """
        assert fields is not None
        if isinstance(fields, str):
            fields = [fields]
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


class FreeCapacity:
    """
    This class takes two capacities objects (what is the total
    available and what is allocated) and allows accessing what is
    free (the difference between the two).
    """
    def __init__(self, *, total: Capacities, allocated: Capacities):
        assert total is not None
        if allocated is None:
            allocated = Capacities()
        self.total = total
        self.free = total - allocated

    def __str__(self):
        d2 = self.total.__dict__.copy()
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

    def __getattr__(self, item):
        """
        Provide access to same fields as capacities, computed as a difference between total and allocated
        i.e. available or free
        """
        return self.free.__getattribute__(item)


class CapacityHints(JSONField):
    """
    Capacity hints are strings representing something about the capacity of a sliver,
    e.g. an instance size name. They have to be mappable to actual capacities
    via e.g. a catalog.
    """
    def __init__(self, **kwargs):
        self.instance_type = None
        self._set_fields(**kwargs)

    def _set_fields(self, **kwargs):
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
    VALIDATORS = {
        'bdf': ('[0-9a-fA-F]{1,4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}.[0-9a-fA-F]+', "0000:00:00.0"),
        'mac': ('([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', "00:11:22:33:44:55"),
        'ipv4': (r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)',
                 "192.168.1.1"),
        'ipv4_range': (r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)-'
                      r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)',
                       "192.168.1.1-192.168.1.10"),
        'ipv4_subnet': (r'(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/[\d]{1,2}',
                        "192.168.1.0/24"),
        'ipv6': (r'(?:[a-fA-F0-9]{0,4}:){0,7}[a-fA-F0-9]{0,4}',
                 "2001:0db8:85a3:0000:0000:8a2e:0370:7334"),
        'ipv6_range': (r'(?:[a-fA-F0-9]{0,4}:){0,7}[a-fA-F0-9]{0,4}-(?:[a-fA-F0-9]{0,4}:){0,7}[a-fA-F0-9]{0,4}',
                      "2001:0db8:85a3:0000:0000:8a2e:0370:7334-2001:0db8:85a3:0000:0000:8a2e:0370:8334"),
        # we allow fewer than 128 (and not necessarily 64) bits to be specified, unlike ipv6 address
        # where we require the full 128 even if some of them are just ':::'
        'ipv6_subnet': (r'(?:[a-fA-F0-9]{0,4}:){0,7}[a-fA-F0-9]{0,4}/[\d]{1,2}',
                        "2001:0db8:85a3:0000:0000/48"),
        'asn': (r'[\d]+', "12345"),
        'vlan': (r'[\d]{1,4}', "1234"),
        'vlan_range': (r'[\d]{1,4}-[\d]{1,4}', "100-200"),
        'inner_vlan': (r'[\d]{1,4}', "1234")
    }
    LAMBDA_VALIDATORS = {
        'vlan': ((lambda v: True if 0 < int(v) <= 4096 else False), "1-4096"),
        'inner_vlan': ((lambda v: True if 0 < int(v) <= 4096 else False), "1-4096"),
        'vlan_range': ((lambda v: True if 0 < int(v.split('-')[0]) <= 4096 and
                                         0 < int(v.split('-')[1]) <= 4096 and
                                         int(v.split('-')[0]) < int(v.split('-')[1]) else False),
                       "1-4096"),
        'asn': ((lambda a: True if 0 < int(a) < 65536 else False), "1-65535")
    }

    def __init__(self, **kwargs):
        self.bdf = None
        self.mac = None
        self.ipv4 = None
        self.ipv4_range = None
        self.ipv4_subnet = None
        self.ipv6 = None
        self.ipv6_range = None
        self.ipv6_subnet = None
        self.asn = None
        self.vlan = None
        self.vlan_range = None
        self.inner_vlan = None
        self.instance = None
        self.instance_parent = None
        self.local_name = None
        self.local_type = None
        self.device_name = None
        self._set_fields(**kwargs)

    def _set_fields(self, **kwargs):
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
                if self.VALIDATORS.get(k, None) is not None:
                    if isinstance(v, list):
                        for i in v:
                            matches = re.match('^' + self.VALIDATORS[k][0] + '$', i)
                            if matches is None:
                                raise LabelException(f'Provided label value {i} for {k} does not match the allowed '
                                                     f'regular expression {self.VALIDATORS[k][0]}, valid example is '
                                                     f'{self.VALIDATORS[k][1]}')
                    else:
                        matches = re.match('^' + self.VALIDATORS[k][0] + '$', v)
                        if matches is None:
                            raise LabelException(f'Provided label value {v} for {k} does not match the allowed '
                                                 f'regular expression {self.VALIDATORS[k][0]}, valid example is '
                                                 f'{self.VALIDATORS[k][1]}')
                if self.LAMBDA_VALIDATORS.get(k, None) is not None:
                    if isinstance(v, list):
                        for i in v:
                            res = self.LAMBDA_VALIDATORS[k][0](i)
                            if res is False:
                                raise LabelException(f'Provided label value {i} for {k} must be in a valid '
                                                     f'range {self.LAMBDA_VALIDATORS[k][1]}')
                    else:
                        res = self.LAMBDA_VALIDATORS[k][0](v)
                        if res is False:
                            raise LabelException(f'Provided label value {v} for {k} must be in a valid '
                                                 f'range {self.LAMBDA_VALIDATORS[k][1]}')

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
        self.error_message = None
        self._set_fields(**kwargs)

    def _set_fields(self, **kwargs):
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
    def __init__(self, **kwargs):
        self.sub_graph_id = None
        self.parent_graph_id = None
        self.adm_graph_ids = None
        self._set_fields(**kwargs)

    def _set_fields(self, **kwargs):
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


class Location(JSONField):
    """
    Location representation (as address, coordinates or any other useful way)
    """
    def __init__(self, **kwargs):
        self.postal = None
        self._set_fields(**kwargs)

    def _set_fields(self, **kwargs):
        """
        Universal setter for location fields. Values are strings.
        :param kwargs:
        :return:
        """
        for k, v in kwargs.items():
            assert v is not None
            assert isinstance(v, str)
            try:
                # will throw exception if field is not defined
                self.__getattribute__(k)
                self.__setattr__(k, v)
            except AttributeError:
                raise LocationException(f"Unable to set field {k} of location, no such field available")
        return self

    def to_latlon(self) -> Tuple[float, float]:
        """
        Return a tuple of floats indicating Lat/Lon of the location. Uses Nomatim OpenStreetMaps
        service.
        :return:
        """
        url = 'https://nominatim.openstreetmap.org/search/' + urllib.parse.quote(self.postal) + '?format=json'
        # per terms of service set user agent
        headers = {'User-Agent': 'FABRIC FIM Utility'}
        response = requests.get(url, headers)
        if response.status_code != 200:
            raise LocationException(f"Unable to convert address to Lat/Lon via OpenStreetmaps due "
                                    f"to: {response.reason}")
        try:
            response_json = response.json()
            if not isinstance(response_json, list):
                raise ValueError
            if len(response_json) < 1:
                raise ValueError
        except ValueError:
            raise LocationException(f"Unable to interpret response from OpenStreetmaps for address {self.postal}")

        return float(response_json[0]['lat']), float(response_json[0]['lon'])


class Flags(JSONField):
    """
    JSON-ified representation of various flags that can be attached to slivers
    """
    def __init__(self, **kwargs):
        self.auto_config = False
        self._set_fields(**kwargs)

    def _set_fields(self, **kwargs):
        for k, v in kwargs.items():
            assert v is not None
            assert isinstance(v, bool)
            try:
                # will throw exception if field is not defined
                self.__getattribute__(k)
                self.__setattr__(k, v)
            except AttributeError:
                raise FlagException(f"Unable to set field {k} of location, no such field available")
        return self

    def to_json(self) -> str:
        """
        Dumps to JSON the __dict__ of the instance. Be careful as the fields in this
        class should only be those that can be present in JSON output.
        Specialized for boolean values from the generic implementation in JSONFields
        :return:
        """
        d = self.__dict__.copy()
        return json.dumps(d, skipkeys=True, sort_keys=True)


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


class LocationException(Exception):
    """
    Exception with location
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Location exception: {msg}")


class FlagException(Exception):
    """
    Exception with flags
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Flag exception: {msg}")