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
        Set a property of a model element
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