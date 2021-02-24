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

"""
Defines various types of typed tuples: labels and capacities for things that are possible in our domain.
Labels and capacities are represented either as a single string "ltype:lval". Types are strings.
Values are simple strings for labels and integers for capacities.
Obviously ':' cannot be present in type names, however can be present in label values.
"""


import json
import importlib.resources as pkg_resources
from typing import List
from abc import ABC, abstractmethod

from . import data


class TypeValidator:
    """
    A sclass to help validate label types based on a
    JSON dictionaries
    """
    class __TypeValidator:
        def __init__(self, types_file: str):
            """
            load JSON dictionary from inside the package with possible types
            """
            types_json = pkg_resources.read_text(data, types_file)
            self.label_types = json.loads(types_json)

        def validate_type(self, atype: str) -> bool:
            """
            validate type against the dictionary
            :param atype:
            :return:
            """
            assert atype is not None
            return atype in self.label_types.keys()

        def get_type_description(self, atype: str):
            """
            get the description of a type
            :param atype:
            :return:
            """
            assert atype is not None
            return self.label_types[atype]

        def get_types(self) -> List:
            """
            returns a copy of available label types as list
            :return:
            """
            return list(self.label_types.keys())

    instances = dict()

    def __init__(self, cat: str, types_file: str):
        """
        create a type validator for category (e.g. "labels" or "capacities")
        from a given file
        :param cat:
        :param types_file:
        """
        assert cat is not None
        assert types_file is not None

        if cat not in TypeValidator.instances.keys():
            TypeValidator.instances[cat] = TypeValidator.__TypeValidator(types_file)
        else:
            pass

    def validate_type(self, cat: str, atype: str):
        """
        validate type in particular category
        :param cat:
        :param atype:
        :return:
        """
        assert cat is not None
        return self.instances[cat].validate_type(atype)

    def get_type_description(self, cat: str, atype: str):
        """
        return the description of a type in a category
        :param cat:
        :param atype:
        :return:
        """
        assert cat is not None
        assert atype is not None
        return self.instances[cat].get_type_description(atype)

    def get_types(self, cat: str):
        """
        list available types for a category
        :param cat:
        :return:
        """
        assert cat is not None
        return self.instances[cat].get_types()


class TypedTuple(ABC):
    """
    abstract typed tuple class (for labels and capacities e.g.)
    """
    LABEL_SEPARATOR = ":"

    @abstractmethod
    def __init__(self, **kwargs) -> None:
        """ assign, but validate against known types """
        # category and types file are expected to be overwritten
        # in subclasses
        self.lv = TypeValidator(self.category, self.types_file)
        if 'atype' in kwargs:
            atype = kwargs['atype']
            aval = kwargs['aval']
        elif 'fromstring' in kwargs:
            atype, aval = kwargs['fromstring'].strip().split(self.LABEL_SEPARATOR, 1)

        if self.lv.validate_type(self.category, atype):
            self.type = atype
            self.val = aval
        else:
            raise TypedTupleException(f"Tuple type {atype} is not among allowed types {self.lv.get_types()}")

    def get_type(self) -> str:
        """
        get label type
        :return:
        """
        return self.type

    def get_val(self) -> str:
        """
        get label value
        :return:
        """
        return self.val

    def get_as_string(self) -> str:
        """
        get label as string concatenation of type and value
        :return:
        """
        return ''.join(x for x in [self.type, self.LABEL_SEPARATOR, str(self.val)])

    def parse_from_string(self, alloc_str: str) -> None:
        """
        Parse allocatable from a string representatiaon
        :param alloc_str
        :return:
        """
        assert alloc_str is not None
        atype, aval = alloc_str.split(self.LABEL_SEPARATOR, 1)
        if self.lv.validate_type(self.category, atype):
            self.type = atype
            self.val = aval
        else:
            raise TypedTupleException(f"Invalid allocatable type in string {atype}, "
                                      f"allowed types {self.lv.get_types(self.category)}")

    def check_type(self, label) -> bool:
        """
        make sure we and the other label are of the same type
        :param label:
        :return:
        """
        return self.type == label.type

    def __repr__(self):
        return self.get_as_string()


class Label(TypedTuple):
    """
    Label expressed as a typed tuple
    """
    def __init__(self, **kwargs):
        self.category = "label"
        self.types_file = "label_types.json"
        super().__init__(**kwargs)


class Capacity(TypedTuple):
    """
    Capacity expressed as a typed tuple
    """
    def __init__(self, **kwargs):
        self.category = "cap"
        self.types_file = "capacity_types.json"
        super().__init__(**kwargs)


class Location(TypedTuple):
    """
    Location expressed as a typed tuple
    """

    def __init__(self, **kwargs):
        self.category = "location"
        self.types_file = "location_types.json"
        super().__init__(**kwargs)


class AllocationConstraint(TypedTuple):
    """
    Allocation constraint expressed as a typed tuple
    """
    def __init__(self, **kwargs):
        self.category = "constraint"
        self.types_file = "constraint_types.json"
        super().__init__(**kwargs)


class TypedTupleException(Exception):
    """
    Exception with a allocatable - label or capacity or other
    """
    @abstractmethod
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Typed Tuple exception: {msg}")


class CapacityException(TypedTupleException):
    """
    Exception with a capacity
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Capacity exception: {msg}")


class LabelException(TypedTupleException):
    """
    Exception with a label
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Label exception: {msg}")


class LabelOrCapacityException(TypedTupleException):
    """
    Exception with either label or capacity
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Label or Capacity exception {msg}")


class LocationException(TypedTupleException):
    """
    Exception with a location
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Label exception: {msg}")


class ConstraintException(TypedTupleException):
    """
    Exception with a constraint
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Label exception: {msg}")