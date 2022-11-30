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

from typing import Any, List
from abc import ABC, abstractmethod
import enum

from ..graph.abc_property_graph import ABCPropertyGraph
from ..slivers.capacities_labels import Capacities, Labels, ReservationInfo
from ..slivers.json_data import MeasurementData, UserData, LayoutData


class ElementType(enum.Enum):
    EXISTING = enum.auto()
    NEW = enum.auto()


class ModelElement(ABC):
    """
    Abstract element of a model
    """

    @abstractmethod
    def __init__(self, *, name: str, node_id: str, topo: Any):
        """
        An element of topology relates to the topology object
        :param name:
        :param node_id:
        :param topo: Topology
        """
        assert name is not None
        assert node_id is not None
        assert topo is not None
        self.name = name
        self.topo = topo
        self.node_id = node_id

    def __eq__(self, other):
        if not isinstance(other, ModelElement):
            return False
        return other.name == self.name and other.node_id == self.node_id

    def __hash__(self):
        return hash((self.name, self.node_id))

    def rename(self, new_name: str):
        """
        Rename the model element in the model graph
        :param new_name:
        :return:
        """
        assert new_name is not None
        self.name = new_name
        self.topo.graph_model.update_node_property(node_id=self.node_id,
                                                   prop_name=ABCPropertyGraph.PROP_NAME,
                                                   prop_val=new_name)

    def unset_property(self, pname: str):
        """
        Unset a property
        :param pname:
        :return:
        """
        assert pname is not None
        prop_name = self.topo.graph_model.map_sliver_property_to_graph(pname)
        if prop_name is not None:
            self.topo.graph_model.unset_node_property(node_id=self.node_id, prop_name=prop_name)

    def __repr__(self):
        labels, node_props = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        # filter out some properties we don't need
        node_props.pop(ABCPropertyGraph.GRAPH_ID)
        if str(self.topo.__class__) == "<class 'fim.user.topology.ExperimentTopology'>":
            node_props.pop(ABCPropertyGraph.NODE_ID)
            node_props.pop(ABCPropertyGraph.PROP_STITCH_NODE)
        ret = str(labels) + str(node_props)
        return ret

    def __str__(self):
        return self.__repr__()

    @abstractmethod
    def set_property(self, pname: str, pval):
        """
        Set a property of a model element or unset if pval is None
        :param pname:
        :param paval:
        :return:
        """

    @abstractmethod
    def get_property(self, pname: str) -> Any:
        """
        Get a property of a model element
        :param pname:
        :return:
        """

    @abstractmethod
    def set_properties(self, **kwargs):
        """
        Set multiple properties of a model element
        :param kwargs:
        :return:
        """

    @abstractmethod
    def get_sliver(self):
        """
        Return sliver of appropriate type for this element
        """

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value
        if self.__dict__.get('topo', None) is not None:
            self.set_property('name', value)

    @property
    def capacities(self):
        return self.get_property('capacities') if self.__dict__.get('topo', None) is not None else None

    @capacities.setter
    def capacities(self, value: Capacities):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('capacities', value)

    @property
    def capacity_allocations(self):
        return self.get_property('capacity_allocations') if self.__dict__.get('topo', None) is not None else None

    @property
    def labels(self):
        return self.get_property('labels') if self.__dict__.get('topo', None) is not None else None

    @labels.setter
    def labels(self, value: Labels):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('labels', value)

    @property
    def details(self):
        return self.get_property('details') if self.__dict__.get('topo', None) is not None else None

    @details.setter
    def details(self, value: str):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('details', value)

    @property
    def node_map(self):
        return self.get_property('node_map') if self.__dict__.get('topo', None) is not None else None

    @node_map.setter
    def node_map(self, value):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('node_map', value)

    @property
    def tags(self):
        return self.get_property('tags') if self.__dict__.get('topo', None) is not None else None

    @tags.setter
    def tags(self, value):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('tags', value)

    @property
    def flags(self):
        return self.get_property('flags') if self.__dict__.get('topo', None) is not None else None

    @flags.setter
    def flags(self, value):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('flags', value)

    @property
    def mf_data(self):
        d = self.get_property('mf_data') if self.__dict__.get('topo', None) is not None else None
        return d.data if d is not None else None

    @mf_data.setter
    def mf_data(self, value):
        if self.__dict__.get('topo', None) is not None:
            if value is None or isinstance(value, MeasurementData):
                self.set_property('mf_data', value)
            else:
                self.set_property('mf_data', MeasurementData(value))

    @property
    def user_data(self):
        d = self.get_property('user_data') if self.__dict__.get('topo', None) is not None else None
        return d.data if d is not None else None

    @user_data.setter
    def user_data(self, value):
        if self.__dict__.get('topo', None) is not None:
            if value is None or isinstance(value, UserData):
                self.set_property('user_data', value)
            else:
                self.set_property('user_data', UserData(value))

    @property
    def layout_data(self):
        d = self.get_property('layout_data') if self.__dict__.get('topo', None) is not None else None
        return d.data if d is not None else None

    @layout_data.setter
    def layout_data(self, value):
        if self.__dict__.get('topo', None) is not None:
            if value is None or isinstance(value, LayoutData):
                self.set_property('layout_data', value)
            else:
                self.set_property('layout_data', LayoutData(value))

    @property
    def boot_script(self):
        return self.get_property('boot_script') if self.__dict__.get('topo', None) is not None else None

    @boot_script.setter
    def boot_script(self, value: str):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('boot_script', value)

    @property
    def reservation_info(self):
        return self.get_property('reservation_info') if self.__dict__.get('topo', None) is not None else None

    @reservation_info.setter
    def reservation_info(self, value: ReservationInfo):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('reservation_info', value)

    def update_labels(self, **kwargs):
        """
        Take current labels field (even empty) and add/overwrite additional values into it
        :param kwargs:
        :return:
        """
        if self.labels is None:
            self.set_property('labels', Labels(**kwargs))
        else:
            new_lab = Labels.update(self.labels, **kwargs)
            self.set_property('labels', new_lab)

    def update_capacities(self, **kwargs):
        """
        Take current capacities field (even empty) and add/overwrite additional values into it
        :param kwargs:
        :return:
        """
        if self.capacities is None:
            self.set_property('capacities', Capacities(**kwargs))
        else:
            new_cap = Capacities.update(self.capacities, **kwargs)
            self.set_property('capacities', new_cap)


class TopologyException(Exception):

    def __init__(self, msg: str):
        super().__init__(msg)