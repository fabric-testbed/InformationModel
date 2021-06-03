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
Abstract definition of ASM (Abstract Slice Model) functionality
"""

from typing import List, Tuple
from abc import ABCMeta, abstractmethod

import json

from fim.graph.abc_property_graph import ABCPropertyGraph, PropertyGraphQueryException


class ABCASMPropertyGraph(ABCPropertyGraph, metaclass=ABCMeta):
    """
    Interface for ASM
    """

    @abstractmethod
    def __init__(self, *, graph_id=str, importer, logger=None):
        super().__init__(graph_id=graph_id, importer=importer, logger=logger)

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'get_all_network_nodes') and
                callable(subclass.get_all_network_nodes) or NotImplemented)

    @abstractmethod
    def check_node_name(self, *, node_id: str, label: str, name: str) -> bool:
        """
        Check if a node with this ID of this class/label has this name
        :param node_id:
        :param label:
        :param name:
        :return:
        """

    @abstractmethod
    def find_node_by_name(self, *, node_name: str, label: str) -> str:
        """
        Get node id of node based on its name and class/label. Throw
        exception if multiple matches found.
        :param node_name:
        :param label: node label or class of the node
        :return:
        """

    def set_mapping(self, *, node_id: str, to_graph_id: str, to_node_id: str) -> None:
        """
        Create a mapping from a node to another graph, node
        :param node_id:
        :param to_graph_id:
        :param to_node_id:
        :return:
        """
        assert node_id is not None
        assert to_graph_id is not None
        assert to_node_id is not None

        # save tuple as JSON list of guids
        l = [to_graph_id, to_node_id]
        jsonl = json.dumps(l)
        self.update_node_property(node_id=node_id, prop_name=ABCASMPropertyGraph.PROP_NODE_MAP,
                                  prop_val=jsonl)

    def get_mapping(self, *, node_id: str) -> Tuple[str, str] or None:
        """
        Retrieve a mapping, if exists for this node to another graph, node
        :param node_id:
        :return: graph_id, node_id tuple or None
        """
        assert node_id is not None
        # retrieve tuple as a json 2-member list
        _, props = self.get_node_properties(node_id=node_id)
        jsonl = props.get(ABCASMPropertyGraph.PROP_NODE_MAP, None)
        if jsonl is not None:
            l = json.loads(jsonl)
            assert(len(l) == 2)
            return tuple(l)
        return None

    def find_node_by_name_as_child(self, *, node_name: str, label: str, rel: str, parent_node_id: str) -> str or None:
        """
        Get node id of node based on its name, class label, as child of a parent node via a specified relationship
        or None
        :param node_name: 
        :param label: 
        :param rel: 
        :param parent_node_id: 
        :return: 
        """
        assert node_name is not None
        assert label is not None
        assert rel is not None
        assert parent_node_id is not None

        neighbs = self.get_first_neighbor(node_id=parent_node_id, rel=rel, node_label=label)
        for n in neighbs:
            _, props = self.get_node_properties(node_id=n)
            if props.get(ABCPropertyGraph.PROP_NAME, None) is not None and \
                props[ABCPropertyGraph.PROP_NAME] == node_name:
                return n
        raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                          msg=f"Unable to find node with name {node_name} "
                                              f"class {label} as child of {parent_node_id}")

    def get_all_network_node_components(self, parent_node_id: str) -> List[str]:
        """
        Return a list of components, children of a prent (presumably network node)
        :param parent_node_id:
        :return:
        """
        assert parent_node_id is not None
        # check that parent is a NetworkNode
        labels, parent_props = self.get_node_properties(node_id=parent_node_id)
        if ABCPropertyGraph.CLASS_NetworkNode not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=parent_node_id,
                                              msg="Parent node type is not NetworkNode")
        return self.get_first_neighbor(node_id=parent_node_id, rel=ABCPropertyGraph.REL_HAS,
                                       node_label=ABCPropertyGraph.CLASS_Component)

    def get_all_network_node_or_component_nss(self, parent_node_id: str) -> List[str]:
        assert parent_node_id is not None
        # check that parent is a NetworkNode or Component
        labels, parent_props = self.get_node_properties(node_id=parent_node_id)
        if ABCPropertyGraph.CLASS_NetworkNode not in labels and \
            ABCPropertyGraph.CLASS_Component not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=parent_node_id,
                                              msg="Parent node type is not NetworkNode or Component")
        return self.get_first_neighbor(node_id=parent_node_id, rel=ABCPropertyGraph.REL_HAS,
                                       node_label=ABCPropertyGraph.CLASS_NetworkService)

    def find_component_by_name(self, *, parent_node_id: str, component_name: str) -> str:

        assert component_name is not None
        component_id_list = self.get_all_network_node_components(parent_node_id=parent_node_id)
        for cid in component_id_list:
            _, cprops = self.get_node_properties(node_id=cid)
            if cprops[ABCPropertyGraph.PROP_NAME] == component_name:
                return cid
        raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                          msg=f"Unable to find component with name {component_name}")

    def find_ns_by_name(self, *, parent_node_id: str, nsname: str) -> str:

        assert nsname is not None

        ns_id_list = self.get_all_network_node_or_component_nss(parent_node_id=parent_node_id)
        for cid in ns_id_list:
            _, cprops = self.get_node_properties(node_id=cid)
            if cprops[ABCPropertyGraph.PROP_NAME] == nsname:
                return cid
        raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                          msg=f"Unable to find NetworkService with name {nsname}")

    def find_connection_point_by_name(self, *, parent_node_id: str, iname: str) -> str:

        assert iname is not None

        if_id_list = self.get_all_ns_or_link_connection_points(link_id=parent_node_id)
        for cid in if_id_list:
            _, cprops = self.get_node_properties(node_id=cid)
            if cprops[ABCPropertyGraph.PROP_NAME] == iname:
                return cid
        raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                          msg=f"Unable to find ConnectionPoint with name {iname}")

    def find_peer_connection_point(self, *, node_id: str) -> str or None:
        """
        Find the id of the peer connection point to this one (connected over a Link)
        if it exists
        :param node_id: id of the interface/connection point
        :return:
        """
        assert node_id is not None

        # find id of connection point over a Link
        candidates = self.get_first_and_second_neighbor(node_id=node_id, rel1=ABCPropertyGraph.REL_CONNECTS,
                                                        node1_label=ABCPropertyGraph.CLASS_Link,
                                                        rel2=ABCPropertyGraph.REL_CONNECTS,
                                                        node2_label=ABCPropertyGraph.CLASS_ConnectionPoint)
        if len(candidates) == 0:
            return None
        if len(candidates) != 1:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg=f"Connection point is only expected to connect to one other"
                                                  f"connection point, instead connects to {len(candidates)}")
        return candidates[0][1]
