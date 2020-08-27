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
from typing import List, Dict, Tuple, Any, Set


class ABCPropertyGraph(ABC):
    """
    Abstract Base class representing operations on a property graph of resources.
    Could be a delegation, a broker view of resources or a slice.
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def import_graph_from_string(self, *, graph_string: str, graph_id: str = None) ->str:
        """
        import a graph from string
        :param graph: - graph represented by a string (e.g. GraphML)
        :param graph_id: - optional id of the graph in the database
        :return: - assigned graph id (or same as passed in)
        """

    @abstractmethod
    def import_graph_from_file(self, *, graph_file: str, graph_id: str = None) ->str:
        """
        import a graph from a file
        :param graph_file: - path to graph file (GraphML)
        :param graph_id: - optional id of the graph in the database
        :return: - assigned graph id (or same as passed in)
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
    def validate_graph(self, *, graph_id: str) ->None:
        """
        validate graph according to a built-in set of rules
        :param graph_id: - id of the graph to be validated
        :return: - None,
        """

    @abstractmethod
    def delete_graph(self, *, graph_id: str) ->None:
        """
        delete a graph from the database
        :param graph_id: - graph_id of the graph
        :return: - None
        """

    @abstractmethod
    def delete_all_graphs(self) -> None:
        """
        delete all graphs from the database
        :return:
        """

    @abstractmethod
    def get_node_properties(self, *, graph_id: str, node_id: str) -> Dict[str, Any]:
        """
        return all properties of a node node_id in graph graph_id
        :param graph_id:
        :param node_id:
        :return: dictionary[string, Any]
        """

    @abstractmethod
    def get_link_properties(self, *, graph_id: str, node_a: str, node_b: str, kind: str) -> Dict[str, Any]:
        """
        return all properties of a link between two nodes node_a and node_b
        :param graph_id:
        :param node_a:
        :param node_b:
        :param kind: kind of link/edge
        :return: dictionary[string, Any]
        """

    @abstractmethod
    def update_node_property(self, *, graph_id: str, node_id: str, prop_name: str,
                             prop_val: Any) -> None:
        """
        update a selected property of a node
        :param graph_id:
        :param node_id:
        :param prop_name:
        :param prop_val:
        :return:
        """

    @abstractmethod
    def update_node_properties(self, *, graph_id: str, node_id: str, props: Dict[str, Any]) -> None:
        """
        update multiple properties
        :param graph_id:
        :param node_id:
        :param props:
        :return:
        """

    @abstractmethod
    def update_link_property(self, *, graph_id: str, node_a: str, node_b: str, kind: str,
                             prop_name: str, prop_val: Any) -> None:
        """
        update a link property for a link between node_a and node_b
        :param graph_id:
        :param node_a:
        :param node_b:
        :param kind: - link/relationship type
        :param prop_name:
        :param prop_val:
        :return:
        """

    @abstractmethod
    def update_link_properties(self, *, graph_id: str, node_a: str, node_b: str, kind: str,
                               props: Dict[str, Any]) -> None:
        """
        update multiple properties on a link between node_a and node_b
        :param graph_id:
        :param node_a:
        :param node_b:
        :param kind: - link/relationship type
        :param props:
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
            super().__init__(("Unspecified error in graph %s " % graph_id))
        else:
            super().__init__(("Error %s in graph %s " % (msg, graph_id)))
        self.graph_id = graph_id
        self.msg = msg


class PropertyGraphImportException(PropertyGraphException):
    """
    import exception for a property graph
    """


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
        if node_b is not None:
            super().__init__(graph_id=graph_id, msg=f"{msg} in querying for link {kind} between {node_id} and {node_b}")
        else:
            super().__init__(graph_id=graph_id, msg=f"{msg} in querying node {node_id}")
        self.node_id = node_id
