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

class ResourcePropertyGraph(ABC):
    """
    Abstract Base class representing operations on a property graph of resources.
    Could be a delegation, a broker view of resources or a slice.
    """

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def import_graph_from_string(self, graph: str, graphId: str = None) ->str:
        """
        import a graph from string
        :param graph: - graph represented by a string (e.g. GraphML)
        :param graphId: - id this graph should have in the database (can be omitted)
        :return: - return graphId issued or same as was passed in
        """
        pass

    @abstractmethod
    def validate_graph(self, graphId: str) ->None:
        """
        validate graph according to a built-in set of rules
        :param graphId: - id of the graph to be validated
        :return: - None,
        """
        pass

    @abstractmethod
    def delete_graph(self, graphId: str) ->None:
        """
        delete a graph from the database
        :param graphId: - graphId of the graph
        :return: - None
        """
        pass

    @abstractmethod
    def get_node_properties(self, graphId: str, nodeId: str) -> Dict[str, Any]:
        """
        return all properties of a node nodeId in graph graphId
        :param graphId:
        :param nodeId:
        :return: dictionary[string, Any]
        """
        pass

    @abstractmethod
    def get_link_properties(self, graphId: str, nodeA: str, nodeB: str) -> Dict[str, Any]:
        """
        return all properties of a link between two nodes nodeA and nodeB
        :param graphId:
        :param nodeA:
        :param nodeB:
        :return: dictionary[string, Any]
        """
        pass

    @abstractmethod
    def update_node_property(self, graphId: str, nodeId: str, propName: str, propVal: Any) -> None:
        """
        update a selected property of a node
        :param graphId:
        :param nodeId:
        :param propName:
        :param propVal:
        :return:
        """
        pass

    @abstractmethod
    def update_node_properties(self, graphId: str, nodeId: str, props: Dict[str, Any]) -> None:
        """
        update multiple properties
        :param graphId:
        :param nodeId:
        :param props:
        :return:
        """
        pass

    @abstractmethod
    def update_link_property(self, graphId: str, nodeA: str, nodeB: str, propName: str, propVal: Any) -> None:
        """
        update a link property for a link between nodeA and nodeB
        :param graphId:
        :param nodeA:
        :param nodeB:
        :param propName:
        :param propVal:
        :return:
        """
        pass

    @abstractmethod
    def update_link_properties(self, graphId: str, nodeA: str, nodeB: str, props: Dict[str, Any]) -> None:
        """
        update multiple properties on a link between nodeA and nodeB
        :param graphId:
        :param nodeA:
        :param nodeB:
        :param props:
        :return:
        """
        pass



class PropertyGraphException(Exception):
    """
    base exception class for all graph exceptions
    """
    def __init__(self, graphId: str, msg: Any = None):
        """
        initialize based on graphId of the graph in question
        :param graphId:
        :param msg:
        """
        if msg is None:
            super(WorkflowError, self).__init__(("Unspecified error in graph %s " % graphId))
        else:
            super(WorkflowError, self).__init__(("Error %s in graph %s " % (msg, graphId)))
        self.graphId = graphId

class PropertyGraphImportException(PropertyGraphException):
    """
    import exception for a property graph
    """
    pass

class PropertyGraphQueryException(PropertyGraphException):
    """
    query exception for a property graph
    """
    pass