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
from typing import List
import networkx_query as nxq

from .abc_asm import ABCASMPropertyGraph
from ..abc_property_graph import ABCPropertyGraph, PropertyGraphQueryException
from ..networkx_property_graph import NetworkXPropertyGraph, NetworkXGraphImporter


class NetworkxASM(ABCASMPropertyGraph, NetworkXPropertyGraph):
    """
    Class implementing Abstract Slice Model on top of NetworkX
    """
    def __init__(self, *, graph_id: str, importer: NetworkXGraphImporter, logger=None):
        super().__init__(graph_id=graph_id, importer=importer, logger=logger)

    def find_node_by_name(self, node_name: str, label: str) -> str:
        """
        Return a node id of a node with this name
        :param node_name:
        :param label: label/class of the node
        :return:
        """
        assert node_name is not None
        my_graph = self.storage.get_graph(self.graph_id)
        graph_nodes = list(nxq.search_nodes(my_graph,
                                            {'and': [
                                                {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraph.PROP_NAME, node_name]},
                                                {'eq': [ABCPropertyGraph.PROP_CLASS, label]}
                                            ]}))
        if len(graph_nodes) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg=f"Unable to find node with name {node_name} class {label}")
        if len(graph_nodes) > 1:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg=f"Graph contains multiple nodes with name {node_name} class {label}")

        return my_graph.nodes[graph_nodes[0]][ABCPropertyGraph.NODE_ID]

    def check_node_name(self, *, node_id: str, label: str, name: str) -> bool:
        assert node_id is not None
        assert name is not None
        assert label is not None

        graph_nodes = list(nxq.search_nodes(self.storage.get_graph(self.graph_id),
                                            {'and': [
                                                {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraph.PROP_NAME, name]},
                                                {'eq': [ABCPropertyGraph.PROP_CLASS, label]},
                                                {'eq': [ABCPropertyGraph.NODE_ID, node_id]}
                                            ]}))
        return len(graph_nodes) > 0


class NetworkXASMFactory:
    """
    Help convert graphs between formats so long as they are rooted in NetworkXPropertyGraph
    """
    @staticmethod
    def create(graph: NetworkXPropertyGraph) -> NetworkxASM:
        assert graph is not None
        assert isinstance(graph.importer, NetworkXGraphImporter)

        return NetworkxASM(graph_id=graph.graph_id,
                           importer=graph.importer,
                           logger=graph.log)
