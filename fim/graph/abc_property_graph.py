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
Abstract Base class representing operations on a property graph of resources.
Could be a delegation, a broker view of resources or a slice.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set


class ABCPropertyGraph(ABC):
    """
    Abstract Base class representing operations on a property graph of resources.
    Could be a delegation, a broker view of resources or a slice.
    """

    FIELD_POOL = "pool"
    FIELD_CAPACITY_POOL = "capacity_pool"
    FIELD_LABEL_POOL = "label_pool"
    FIELD_DELEGATION = "delegation"
    PROP_CAPACITY_DELEGATIONS = "CapacityDelegations"
    PROP_LABEL_DELEGATIONS = "LabelDelegations"
    PROP_CAPACITIES = "Capacities"
    PROP_LABELS = "Labels"
    JSON_PROPERTY_NAMES = [PROP_LABELS, PROP_CAPACITIES, PROP_LABEL_DELEGATIONS, PROP_CAPACITY_DELEGATIONS]

    @abstractmethod
    def __init__(self, *, graph_id: str):
        """
        New graph with an id
        :param graph_id:
        """
        self.graph_id = graph_id

    def get_graph_id(self):
        return self.graph_id

    @abstractmethod
    def validate_graph(self) ->None:
        """
        validate graph according to a built-in set of rules
        :return: - None,
        """

    @abstractmethod
    def delete_graph(self) ->None:
        """
        delete a graph from the database
        :return: - None
        """

    @abstractmethod
    def get_node_properties(self, *, node_id: str) -> (List[str], Dict[str, Any]):
        """
        return all labels and properties of a node node_id in graph graph_id
        :param node_id:
        :return: dictionary[string, Any]
        """

    @abstractmethod
    def get_node_json_property_as_object(self, *, node_id: str, prop_name: str) -> Any:
        """
        Return node property as a python object (applies to JSON encoded properties), will
        fail on other property values.
        :param node_id:
        :param prop_name:
        :return:
        """

    @abstractmethod
    def get_link_properties(self, *, node_a: str, node_b: str) -> (str, Dict[str, Any]):
        """
        return a tuple of link kind and all properties of a link between two nodes node_a and node_b
        :param node_a:
        :param node_b:
        :param kind: kind of link/edge
        :return: (str, dictionary[string, Any])
        """

    @abstractmethod
    def update_node_property(self, *, node_id: str, prop_name: str,
                             prop_val: Any) -> None:
        """
        update a selected property of a node
        :param node_id:
        :param prop_name:
        :param prop_val:
        :return:
        """

    @abstractmethod
    def update_nodes_property(self, *, prop_name: str, prop_val: Any) -> None:
        """
        update a selected property on all nodes of the graph
        :param prop_name:
        :param prop_val:
        :return:
        """

    @abstractmethod
    def update_node_properties(self, *, node_id: str, props: Dict[str, Any]) -> None:
        """
        update multiple properties
        :param node_id:
        :param props:
        :return:
        """

    @abstractmethod
    def update_link_property(self, *, node_a: str, node_b: str, kind: str,
                             prop_name: str, prop_val: Any) -> None:
        """
        update a link property for a link between node_a and node_b
        :param node_a:
        :param node_b:
        :param kind: - link/relationship type
        :param prop_name:
        :param prop_val:
        :return:
        """

    @abstractmethod
    def update_link_properties(self, *, node_a: str, node_b: str, kind: str,
                               props: Dict[str, Any]) -> None:
        """
        update multiple properties on a link between node_a and node_b
        :param node_a:
        :param node_b:
        :param kind: - link/relationship type
        :param props:
        :return:
        """

    @abstractmethod
    def list_all_node_ids(self) -> List[str]:
        """
        list all NodeID properties of a given graph
        :return:
        """

    @abstractmethod
    def serialize_graph(self) -> str:
        """
        Serialize a given graph into a string
        :return:
        """

    @abstractmethod
    def clone_graph(self, *, new_graph_id: str):
        """
        clone a graph. unfortunately APOC procedures for cloning are not
        a good fit - they can omit, but not overwrite a property on clone.
        Instead this procedure serializes graph into a temporary file, then
        reloads it overwriting the GraphID property.
        :param new_graph_id:
        :return returns a graph:
        """

    @abstractmethod
    def graph_exists(self) -> bool:
        """
        Does the graph with this ID exist?
        :return:
        """

    @abstractmethod
    def get_nodes_on_shortest_path(self, *, node_a: str, node_z: str, rel: str = None) -> List:
        """
        Get a list of node ids that lie on a shortest path between two nodes. Return empty
        list if no path can be found. Optionally specify the type of relationship that path
        should consist of.
        :param node_a:
        :param node_z:
        :param rel:
        :return:
        """

    @abstractmethod
    def get_first_neighbor(self, *, node_id: str, rel: str, node_label: str) -> List:
        """
        Return a list of ids of nodes of this label related via relationship. List may be empty.
        :param node_id:
        :param rel:
        :param node_label:
        :return:
        """

    @abstractmethod
    def get_first_and_second_neighbor(self, *, node_id: str, rel1: str, node1_label: str,
                                      rel2: str, node2_label: str) -> List:
        """
        Return a list of 2-member lists of node ids related to this node via two specified relationships.
        List may be empty.
        :param node_id:
        :param rel1:
        :param node1_label:
        :param rel2:
        :param node2_label:
        :return:
        """

    @abstractmethod
    def delete_node(self, *, node_id: str):
        """
        Delete node from a graph (incident edges automatically deleted)
        :param node_id:
        :return:
        """

    @abstractmethod
    def find_matching_nodes(self, *, graph) -> Set:
        """
        Return a set of node ids that match between the two graphs
        :param graph:
        :return:
        """

    @abstractmethod
    def merge_nodes(self, node_id: str, graph, merge_properties=None):
        """
        Merge two nodes of the same id belonging to two graphs. Optionally
        specify merging behavior for individual properties
        :param node_id:
        :param graph:
        :param merge_properties:
        :return:
        """

    def __repr__(self):
        return f"Graph with id {self.graph_id}"


class ABCGraphImporter(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def import_graph_from_string(self, *, graph_string: str, graph_id: str = None) -> ABCPropertyGraph:
        """
        import a graph from string adding GraphID to each node (new graph_id is generated
        if graph_id is None)
        :param graph_string: - graph represented by a string (e.g. GraphML)
        :param graph_id: - optional id of the graph in the database
        :return: - an instantiation of a property graph
        """

    @abstractmethod
    def import_graph_from_string_direct(self, *, graph_string: str) -> ABCPropertyGraph:
        """
        import a graph from string without any manipulations
        :param graph_string:
        :return:
        """

    @abstractmethod
    def import_graph_from_file(self, *, graph_file: str, graph_id: str = None) -> ABCPropertyGraph:
        """
        import a graph from a file
        :param graph_file: - path to graph file (GraphML)
        :param graph_id: - optional id of the graph in the database
        :return: an instantiation of a property graph
        """

    @abstractmethod
    def import_graph_from_file_direct(self, *, graph_file: str) -> ABCPropertyGraph:
        """
        import a graph from file without any manipulations
        :param graph_file:
        :return:
        """

    @abstractmethod
    def enumerate_graph_nodes(self, *, graph_file: str, new_graph_file: str, node_id_prop: str) -> None:
        """
        Read in a graph and add a NodeId property to every node assigning a unique GUID.
        Save into a new file
        :param graph_file: original file containing graph
        :param new_graph_file: new file containing updated graph
        :param node_id_prop: name of the property of a node to which ID is assigned
        :return:
        """

    @abstractmethod
    def delete_all_graphs(self) -> None:
        """
        delete all graphs from the database
        :return:
        """


class PropertyGraphException(Exception):
    """
    base exception class for all graph exceptions
    """
    def __init__(self, *, graph_id: str, msg: Any = None):
        """
        initialize based on graph_id of the graph in question
        :param graph_id:
        :param msg:
        """
        if msg is None:
            super().__init__(f"Unspecified error importing graph {graph_id}")
        else:
            if graph_id is not None:
                super().__init__(f"{msg} in {graph_id}")
            else:
                super().__init__(msg)
        self.graph_id = graph_id
        self.msg = msg


class PropertyGraphImportException(PropertyGraphException):
    """
    import exception for a property graph
    """
    def __init__(self, *, graph_id: str,  msg: str, node_id: str = None):
        if node_id is None:
            super().__init__(graph_id=graph_id, msg=f"Error [{msg}] importing graph")
        else:
            super().__init__(graph_id=graph_id, msg=f"Error [{msg}] in node {node_id} importing graph")


class PropertyGraphQueryException(PropertyGraphException):
    """
    query exception for a property graph
    """
    def __init__(self, *, graph_id: str, node_id: str, msg: str, node_b: str = None, kind: str = None):
        """
        Query error for node or link
        :param graph_id:
        :param node_id:
        :param msg:
        :param node_b:
        :param kind:
        """
        if node_b is not None and node_id is not None:
            super().__init__(graph_id=graph_id, msg=f"[{msg}] in querying for link {kind} between {node_id} and {node_b}")
        elif node_b is None and node_id is not None:
            super().__init__(graph_id=graph_id, msg=f"[{msg}] in querying node {node_id}")
        else:
            super().__init__(graph_id=graph_id, msg=f"[{msg}]")
        self.node_id = node_id
