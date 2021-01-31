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

from typing import List, Set, Any
from abc import ABCMeta

import json
import networkx as nx
import networkx_query as nxq

from .abc_property_graph import PropertyGraphQueryException, PropertyGraphImportException, ABCPropertyGraph


class NetworkXMixin(metaclass=ABCMeta):
    """
    A mixin class offering useful functionality to NetworkX-based implementations
    """

    NETWORKX_LABEL = 'Class'

    def _find_node(self, *, node_id: str, graph_id: str = None) -> int:
        """
        Find a node matching this node ID or raise a Query Exception,
        returning an internal integer ID
        :param node_id:
        :return:
        """
        assert node_id is not None
        # this is a bit hacky - works for other graphs, not just us
        if graph_id is None:
            use_graph_id = self.graph_id
        else:
            use_graph_id = graph_id

        query_match = list(nxq.search_nodes(self.storage.get_graph(use_graph_id),
                                            {'and': [
                                                {'eq': [ABCPropertyGraph.NODE_ID, node_id]},
                                                {'eq': [ABCPropertyGraph.GRAPH_ID, use_graph_id]}
                                                ]}
                                            ))
        if len(query_match) == 0:
            raise PropertyGraphQueryException(graph_id=use_graph_id,
                                              node_id=node_id, msg="Unable to find node")
        if len(query_match) > 1:
            raise PropertyGraphQueryException(graph_id=use_graph_id,
                                              node_id=node_id, msg="Multiple matches found")
        return query_match[0]

    def _find_all_nodes(self) -> List[int]:
        """
        Find all nodes in this graph returning the list of their internal int IDs
        :return:
        """
        query_match = list(nxq.search_nodes(self.storage.get_graph(self.graph_id),
                                            {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]}))
        if len(query_match) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg="Unable to find graph nodes")
        return query_match

    @staticmethod
    def _get_node_ids_for_list(graph: nx.Graph, nodelist: List) -> List[str] or None:
        """
        Take a list of internal int IDs and return a list of node ids for it for this graph
        :param graph:
        :param nodelist:
        :return:
        """
        assert nodelist is not None
        ret = list()
        for n in nodelist:
            # get node_ids of the path nodes
            ret.append(graph.nodes[n][ABCPropertyGraph.NODE_ID])
        return ret

    @staticmethod
    def _drop_edges_not_of_type(graph: nx.Graph, rel: str) -> None:
        """
        Take a graph and remove all edges that aren't of type/Class rel
        :param graph:
        :param rel:
        :return:
        """
        for e in graph.edges(data=True):
            # e is a tuple (source, target, property dict)
            if e[2].get(NetworkXMixin.NETWORKX_LABEL, None) != rel:
                # delete this edge
                graph.remove_edge(e[0], e[1])

    @staticmethod
    def _get_first_neighbors_via(graph: nx.Graph, real_node: int, rel: str) -> List[int]:
        """
        Get a set of integer internal IDs of nodes that are neighbors of this node
        and are connected via a specified relationship type/Class
        :param graph:
        :param node:
        :param rel:
        :return:
        """
        first_neighbors = set(graph.neighbors(real_node))
        # remove first neighbors connected via relationship type/Class that isn't rel
        neighbor_drop_list = list()
        for n in first_neighbors:
            if graph.edges[(real_node, n)].get(NetworkXMixin.NETWORKX_LABEL, None) != rel:
                neighbor_drop_list.append(n)

        return list(first_neighbors.difference(neighbor_drop_list))

    @staticmethod
    def _filter_nodes_by_label(graph: nx.Graph, nodeset: Set[int], node_label: str) -> List[int]:
        """
        Return a new list with only members that have the matching label
        :param graph:
        :param nodeset:
        :param node_label:
        :return:
        """
        droplist = list()
        for n in nodeset:
            if graph.nodes[n].get(NetworkXMixin.NETWORKX_LABEL, None) != node_label:
                droplist.append(n)
        return list(set(nodeset).difference(droplist))

    @staticmethod
    def _collect_nodeids(graph: nx.Graph) -> Set[str]:
        """
        Collect node ids from a NetworkX graph object as a set
        :param graph:
        :return:
        """
        assert isinstance(graph, nx.Graph)
        nodeids = set()
        for n in list(graph.nodes):
            nodeids.add(graph.nodes[n][ABCPropertyGraph.NODE_ID])
        return nodeids