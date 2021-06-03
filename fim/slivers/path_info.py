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
from typing import List, Tuple, Any, Dict
import enum

import json


class PathRepresentationType(enum.Enum):
    """
    Path Representation type - can be represented as a list or as a graph
    """
    Path = enum.auto()   # PathInfo is a pair of uni-directional lists
    Graph = enum.auto()  # PathInfo is a graph reference (graph ID)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


class Path:
    """
    Path object expressed as two lists of entities on the path
    """
    def __init__(self):
        self.a2z = None
        self.z2a = None

    def set(self, *, a2z: List = None, z2a: List = None):
        self.a2z = a2z
        self.z2a = z2a

    def set_symmetric(self, a2z: List):
        assert a2z is not None
        assert isinstance(a2z, list)
        self.a2z = a2z
        self.z2a = a2z.copy()
        self.z2a.reverse()

    def get(self) -> Tuple[List, List]:
        """
        Return a tuple a2z, z2a
        :return:
        """
        return self.a2z, self.z2a

    def to_dict(self) -> Dict:
        return {'a2z': self.a2z, 'z2a': self.z2a}

    @classmethod
    def from_dict(cls, d: Dict):
        assert isinstance(d, dict)
        assert 'a2z' in d.keys() and 'z2a' in d.keys()
        pi = cls()
        pi.set(a2z=d['a2z'], z2a=d['z2a'])
        return pi

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return json.dumps(self.to_dict())


class PathInfo:
    """
    PathInfo encodes information about paths. Most of the time lists (a2z, z2a) are used,
    however we can also do it as an external graph (by reference).
    """
    def __init__(self, ptype: PathRepresentationType = PathRepresentationType.Path):
        self.payload = None
        self.type = ptype

    def set(self, payload) -> None:
        """
        Path payload can be a Path or id of a graph built externally (string name is payload)
        :param payload:
        :return:
        """
        if self.type == PathRepresentationType.Path:
            assert(isinstance(payload, Path))
        else:
            assert(isinstance(payload, str))
        self.payload = payload

    def get(self) -> Tuple[PathRepresentationType, Any]:
        """
        Return a tuple of type, payload of Path (tuple of lists or a graph id)
        :return:
        """
        return self.type, self.payload

    @staticmethod
    def type_from_str(etype: str) -> PathRepresentationType or None:
        if etype is None:
            return None
        for t in PathRepresentationType:
            if etype == str(t):
                return t

    def to_json(self) -> str:
        """
        Convert to JSON dictionary:
        { "type": "list"|"graph", "payload": <payload> }
        payload can be a graph identifier string or a dict with 'a2z' and 'z2a' lists
        :return:
        """
        json_dict = dict()
        json_dict['type'] = str(self.type)
        json_dict['payload'] = self.payload if self.type == PathRepresentationType.Graph else self.payload.to_dict()
        return json.dumps(json_dict)

    @classmethod
    def from_json(cls, json_string: str):
        """
        Set fields from json string and returns a new object
        :param json_string:
        :return: object
        """
        if json_string is None or len(json_string) == 0:
            return None
        d = json.loads(json_string)
        ptype_str = d.get('type', None)
        if ptype_str is None:
            return None

        ptype = PathInfo.type_from_str(ptype_str)
        ret = cls(ptype)
        ret.payload = d['payload'] if ptype == PathRepresentationType.Graph else Path.from_dict(d['payload'])
        return ret

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return self.to_json()


class ERO(PathInfo):
    """
    Explicit Route Object class which adds 'strict' flag compared to PathInfo
    """
    def __init__(self, etype: PathRepresentationType = PathRepresentationType.Path, strict: bool = False):
        # default is 'loose' list
        super().__init__(etype)
        self.strict = strict

    def get_strict(self) -> bool:
        """
        Get the ERO strict flag
        :return:
        """
        return self.strict

    def to_json(self) -> str:
        """
        Convert to JSON dictionary:
        { "type": "Path"|"Graph", "payload": <payload> }
        payload can be a graph identifier string or a dict with 'a2z' and 'z2a' lists
        :return:
        """
        json_dict = dict()
        json_dict['type'] = str(self.type)
        json_dict['strict'] = str(self.strict)
        json_dict['payload'] = self.payload if self.type == PathRepresentationType.Graph else self.payload.to_dict()
        return json.dumps(json_dict)

    @classmethod
    def from_json(cls, json_string: str):
        """
        Set fields from json string and returns a new object
        :param json_string:
        :return: object
        """
        if json_string is None or len(json_string) == 0:
            return None
        d = json.loads(json_string)
        ptype_str = d.get('type', None)
        if ptype_str is None:
            return None

        ptype = PathInfo.type_from_str(ptype_str)
        ret = cls(ptype)
        ret.payload = d['payload'] if ptype == PathRepresentationType.Graph else Path.from_dict(d['payload'])
        ret.strict = True if d.get('strict', None) in {'True', 'true'} else False
        return ret

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return self.to_json()
