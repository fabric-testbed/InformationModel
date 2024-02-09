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

from typing import Dict, Any, List, Tuple

from fim.view_only_dict import ViewOnlyDict
from .node import Node
from .model_element import TopologyException
from .interface import Interface

from ..graph.abc_property_graph import ABCPropertyGraph


class CompositeNode(Node):
    """
    A composite node of the topology. In addition to public methods the following calls
    return various dictionaries or lists:
    node.components - a dictionary of components
    node.interfaces - a dictionary of all interfaces
    node.interface_list - a list of all interfaces
    """

    def __init__(self, *, name: str, node_id: str, topo: Any, check_existing: bool = False):
        """
        Don't call this method yourself, call topology.add_node()
        node_id will be generated if not provided for experiment topologies

        :param name:
        :param node_id:
        :param topo:
        :param check_existing:
        """
        assert name is not None
        assert topo is not None
        assert node_id is not None

        # skip one level of constructor
        super(Node, self).__init__(name=name, node_id=node_id, topo=topo)
        if check_existing:
            # check that this node exists
            existing_node_id = self.topo.graph_model.find_node_by_name(node_name=name,
                                                                       label=str(ABCPropertyGraph.CLASS_CompositeNode))
            if existing_node_id != node_id:
                raise TopologyException(f'Composite Node name {name} is not unique within the topology')

    def __list_components(self) -> ViewOnlyDict:
        """
        List all Components children of a node in the topology as a dictionary
        organized by component name. Modifying the dictionary will not affect
        the underlying model, but modifying Components in the dictionary will.
        :return:
        """
        node_id_list = self.topo.graph_model.get_all_composite_node_components(parent_node_id=self.node_id)
        ret = dict()
        for nid in node_id_list:
            c = self._get_component_by_id(nid)
            ret[c.name] = c
        return ViewOnlyDict(ret)

    def __get_interface_by_id(self, node_id: str) -> Interface:
        """
        Get an interface of a node by its node_id, return Interface object
        :param node_id:
        :return:
        """
        assert node_id is not None
        clazzes, node_props = self.topo.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        assert ABCPropertyGraph.CLASS_ConnectionPoint in clazzes
        return Interface(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id,
                         topo=self.topo)

    def __list_interfaces(self) -> ViewOnlyDict:
        """
        List all interfaces of composite node ignoring the components
        :return:
        """
        # immediately-attached interfaces only for composite nodes
        # FIXME: note that due to interface name collisions this may not return
        # all the interfaces. Better to use list_of_interfaces
        node_if_list = self.topo.graph_model.get_all_node_or_component_connection_points(parent_node_id=self.node_id)
        direct_interfaces = dict()
        for nid in node_if_list:
            i = self.__get_interface_by_id(nid)
            direct_interfaces[i.name] = i
        return ViewOnlyDict(direct_interfaces)

    def __list_of_interfaces(self) -> Tuple[Interface]:
        """
        List all interfaces of node and its components
        :return:
        """
        node_if_list = self.topo.graph_model.get_all_node_or_component_connection_points(parent_node_id=self.node_id)
        direct_interfaces = list()
        for nid in node_if_list:
            i = self.__get_interface_by_id(nid)
            direct_interfaces.append(i)
        return tuple(direct_interfaces)

    def __dict_of_children(self) -> ViewOnlyDict:
        """
        List of children Node objects that are connected to CompositeNode
        representing site in ABQM via 'has' relationship
        """
        node_id_list = self.topo.graph_model.get_first_neighbor(node_id=self.node_id, rel=ABCPropertyGraph.REL_HAS,
                                                                node_label=ABCPropertyGraph.CLASS_NetworkNode)
        ret = dict()
        for nid in node_id_list:
            _, node_props = self.topo.graph_model.get_node_properties(node_id=nid)
            n = Node(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=nid, topo=self.topo)
            # exclude Facility nodes
            from fim.user import NodeType
            if n.type != NodeType.Facility:
                ret[n.name] = n
        return ViewOnlyDict(ret)

    @property
    def components(self):
        return self.__list_components()

    @property
    def interfaces(self):
        return self.__list_interfaces()

    @property
    def interface_list(self):
        return self.__list_of_interfaces()

    @property
    def children(self) -> ViewOnlyDict:
        # Composite nodes typically are in ABQM denoting sites
        # and have 'has' relationship to Node children
        # representing worker nodes in a site
        return self.__dict_of_children()

    def __repr__(self):
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        node_sliver = self.topo.graph_model.node_sliver_from_graph_properties_dict(node_properties)
        return node_sliver.__repr__()

    def __str__(self):
        return self.__repr__()


