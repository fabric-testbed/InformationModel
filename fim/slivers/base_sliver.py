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
"""
Base class for all sliver types
"""
from typing import Any, Tuple, List, Dict
from abc import ABC, abstractmethod

from fim.slivers.capacities_labels import Capacities, CapacityHints, Labels, ReservationInfo, StructuralInfo, Flags
from fim.slivers.delegations import Delegations
from fim.slivers.tags import Tags
from fim.slivers.measurement_data import MeasurementData


class BaseSliver(ABC):
    """Base class for all sliver types"""

    BOOST_SCRIPT_SIZE = 1024

    @abstractmethod
    def __init__(self):
        self.resource_type = None
        self.resource_name = None
        self.resource_model = None
        self.capacities = None
        self.capacity_hints = None
        self.labels = None
        self.capacity_delegations = None
        self.label_delegations = None
        self.capacity_allocations = None
        self.label_allocations = None
        self.reservation_info = None
        self.structural_info = None
        # note that node_id is deliberately not settable to avoid being accidentally overwritten by user
        self.node_id = None
        self.details = None
        self.node_map = None
        self.stitch_node = False
        self.tags = None # list of strings, limited in length
        self.flags = None # various flags
        self.mf_data = None # opaque JSON object limited in length
        self.boot_script = None # string limited in length

    def set_type(self, resource_type):
        self.resource_type = resource_type

    def get_type(self):
        return self.resource_type

    def set_name(self, resource_name: str):
        assert(resource_name is None or isinstance(resource_name, str))
        self.resource_name = resource_name

    def get_name(self):
        return self.resource_name

    def set_model(self, resource_model: str):
        assert(resource_model is None or isinstance(resource_model, str))
        self.resource_model = resource_model

    def get_model(self):
        return self.resource_model

    def set_capacities(self, cap: Capacities) -> None:
        assert (cap is None or isinstance(cap, Capacities))
        assert(cap is None or isinstance(cap, Capacities))
        self.capacities = cap

    def get_capacities(self) -> Capacities:
        return self.capacities

    def set_capacity_hints(self, caphint: CapacityHints) -> None:
        assert(caphint is None or isinstance(caphint, CapacityHints))
        self.capacity_hints = caphint

    def get_capacity_hints(self) -> CapacityHints:
        return self.capacity_hints

    def set_labels(self, lab: Labels) -> None:
        assert(lab is None or isinstance(lab, Labels))
        self.labels = lab

    def get_labels(self) -> Labels:
        return self.labels

    def set_capacity_delegations(self, cdel: Delegations):
        assert(cdel is None or isinstance(cdel, Delegations))
        self.capacity_delegations = cdel

    def get_capacity_delegations(self) -> Delegations:
        return self.capacity_delegations

    def set_label_delegations(self, ldel: Delegations):
        assert(ldel is None or isinstance(ldel, Delegations))
        self.label_delegations = ldel

    def get_label_delegations(self) -> Delegations:
        return self.label_delegations

    def set_label_allocations(self, lab: Labels) -> None:
        assert(lab is None or isinstance(lab, Labels))
        self.label_allocations = lab

    def get_label_allocations(self) -> Labels:
        return self.label_allocations

    def set_capacity_allocations(self, cap: Capacities) -> None:
        assert(cap is None or isinstance(cap, Capacities))
        self.capacity_allocations = cap

    def get_capacity_allocations(self) -> Capacities:
        return self.capacity_allocations

    def set_reservation_info(self, ri: ReservationInfo) -> None:
        assert(ri is None or isinstance(ri, ReservationInfo))
        self.reservation_info = ri

    def get_reservation_info(self) -> ReservationInfo:
        return self.reservation_info

    def set_structural_info(self, si: StructuralInfo) -> None:
        assert (si is None or isinstance(si, StructuralInfo))
        self.structural_info = si

    def get_structural_info(self) -> StructuralInfo:
        return self.structural_info

    def set_details(self, desc: str) -> None:
        self.details = desc

    def get_details(self) -> str:
        return self.details

    def set_node_map(self, node_map: Tuple[str, str]) -> None:
        assert(node_map is None or isinstance(node_map, tuple) or
               isinstance(node_map, list))
        if node_map is not None:
            self.node_map = tuple(node_map)
        else:
            self.node_map = None

    def get_node_map(self) -> Tuple[str, str] or None:
        return tuple(self.node_map) if self.node_map is not None else None

    def set_stitch_node(self, stitch_node: bool) -> None:
        self.stitch_node = stitch_node

    def get_stitch_node(self) -> bool:
        return self.stitch_node

    def set_tags(self, tags: Tags) -> None:
        assert(tags is None or isinstance(tags, Tags))
        self.tags = tags

    def get_tags(self) -> Tags or None:
        return self.tags

    def set_flags(self, flags: Flags) -> None:
        assert(flags is None or isinstance(flags, Flags))
        self.flags = flags

    def get_flags(self) -> Flags or None:
        return self.flags

    def set_mf_data(self, mf_data: MeasurementData or None) -> None:
        assert(mf_data is None or
               isinstance(mf_data, MeasurementData))
        self.mf_data = mf_data

    def get_mf_data(self) -> MeasurementData or None:
        return self.mf_data

    def set_boot_script(self, boot_script: str):
        assert(boot_script is None or
               (isinstance(boot_script, str) and len(boot_script) < self.BOOST_SCRIPT_SIZE))
        self.boot_script = boot_script

    def get_boot_script(self) -> str:
        return self.boot_script

    def set_properties(self, **kwargs):
        """
        Lets you set multiple properties exposed via setter methods
        :param kwargs:
        :return:
        """
        # set any property on a sliver that has a setter
        for k, v in kwargs.items():
            # we can set anything the sliver model has a setter for
            self.__getattribute__('set_' + k)(v)

    @classmethod
    def list_properties(cls) -> Tuple[str]:
        """
        List properties available for setting/getting on a sliver (those exposing
        setters)
        :return:
        """
        ret = list()
        exclude_set = {"set_property", "set_properties"}
        for k in dir(cls):
            if k.startswith('set_') and k not in exclude_set:
                ret.append(k[4:])
        return tuple(ret)

    def set_property(self, prop_name: str, prop_val: Any):
        """
        Lets you set any property exposed via a setter
        :param prop_name:
        :param prop_val:
        :return:
        """
        return self.__getattribute__('set_' + prop_name)(prop_val)

    def get_property(self, prop_name: str):
        """
        Lets you get a property that is exposed via getter method
        :param prop_name:
        :return:
        """
        return self.__getattribute__('get_' + prop_name)()

    def __repr__(self):
        exclude_set = {"get_property", "get_stitch_node"}
        print_set = list()
        for k in dir(self):
            if k.startswith('get_') and k not in exclude_set:
                print_set.append(k[4:])
        print_set.sort()
        print_vals = dict()
        for p in print_set:
            try:
                pval = self.get_property(p)
                if pval is not None and len(str(pval)) != 0:
                    print_vals[p] = str(pval)
            except AttributeError:
                # sometimes a property is not available due to e.g. unpicking
                # an older version of the object, and that's ok.
                pass
        return str(print_vals)

    def __str__(self):
        return self.__repr__()


class BaseSliverWithDelegation(BaseSliver):
    """
    Intended to be used in advertisements
    """
    def __init__(self):
        super().__init__()
        self.capacity_delegations = None
        self.label_delegations = None

    def set_capacity_delegations(self, cap_del) -> None:
        self.capacity_delegations = cap_del

    def set_label_delegations(self, lab_del) -> None:
        self.label_delegations = lab_del
