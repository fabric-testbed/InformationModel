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
# Author: Ilya Baldin(ibaldin@renci.org)
from typing import List, Dict

import networkx_query as nxq

from fim.graph.abc_property_graph import ABCPropertyGraphConstants, PropertyGraphQueryException
from fim.graph.resources.abc_bqm import ABCBQMPropertyGraph
from fim.graph.networkx_property_graph import NetworkXPropertyGraph, NetworkXGraphImporter


class NetworkXAggregateBQM(ABCBQMPropertyGraph, NetworkXPropertyGraph):
    """
    NetworkX mplementation of a *Aggregate* Broker Query Model (BQM)
    which aggregates site advertisements into  a single Composite Node.
    Intended to work with
    """

    def __init__(self, *, graph_id: str, importer, logger=None):
        super().__init__(graph_id=graph_id, importer=importer, logger=logger)

    def get_all_composite_nodes(self) -> List[str]:
        """
        Get a list of nodes IDs in a BQM model
        :return:
        """
        return self.get_all_nodes_by_class(label=ABCPropertyGraphConstants.CLASS_CompositeNode)

    def get_all_network_links(self) -> List[str]:
        """
        Get a list of link node ids in a BQM model
        :return:
        """
        return self.get_all_nodes_by_class(label=ABCPropertyGraphConstants.CLASS_Link)

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
                                                {'eq': [ABCPropertyGraphConstants.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraphConstants.PROP_NAME, node_name]},
                                                {'eq': [ABCPropertyGraphConstants.PROP_CLASS, label]}
                                            ]}))
        if len(graph_nodes) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg=f"Unable to find node with name {node_name} class {label}")
        if len(graph_nodes) > 1:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg=f"Graph contains multiple nodes with name {node_name} class {label}")

        return my_graph.nodes[graph_nodes[0]][ABCPropertyGraphConstants.NODE_ID]

    def check_node_name(self, *, node_id: str, label: str, name: str) -> bool:
        assert node_id is not None
        assert name is not None
        assert label is not None

        graph_nodes = list(nxq.search_nodes(self.storage.get_graph(self.graph_id),
                                            {'and': [
                                                {'eq': [ABCPropertyGraphConstants.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraphConstants.PROP_NAME, name]},
                                                {'eq': [ABCPropertyGraphConstants.PROP_CLASS, label]},
                                                {'eq': [ABCPropertyGraphConstants.NODE_ID, node_id]}
                                            ]}))
        return len(graph_nodes) > 0


class NetworkXABQMFactory:
    """
    Help convert graphs between formats so long as they are rooted in NetworkXPropertyGraph
    """
    @staticmethod
    def create(graph: NetworkXPropertyGraph) -> NetworkXAggregateBQM:
        assert graph is not None
        assert isinstance(graph.importer, NetworkXGraphImporter)

        return NetworkXAggregateBQM(graph_id=graph.graph_id,
                                    importer=graph.importer,
                                    logger=graph.log)
