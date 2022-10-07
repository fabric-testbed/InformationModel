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
NetworkX-specific implementation of property graph abstraction
"""
import logging
import threading

import networkx as nx
import networkx_query as nxq
from collections import defaultdict
from threading import Lock

from .abc_property_graph import ABCPropertyGraph, PropertyGraphImportException, PropertyGraphQueryException
from .networkx_property_graph import NetworkXPropertyGraph, NetworkXGraphImporter


def constant_factory(val):
    return lambda: val


class NetworkXPropertyGraphDisjoint(NetworkXPropertyGraph):
    """
    This class implements most of ABCPropertyGraph functionality.
    It stores each graph as a separate object and as a result is more
    efficient, however cannot implement merge_nodes properly - a RuntimeError
    will be raised if the method is called.
    For a fully semantics-compliant implementation please see
    NetworkXPropertyGraph.
    """

    def __init__(self, *, graph_id: str, importer, logger=None):
        # don't call immediate predecessor
        super().__init__(graph_id=graph_id, importer=importer)
        assert isinstance(importer, NetworkXGraphImporterDisjoint)

    def merge_nodes(self, node_id: str, other_graph, merge_properties=None):
        """
        Not implementable in NetworkX with graphs stored separately -
        has assumptions about a common store for all graphs.
        Would require to store all graphs in a single NetworkX graph.
        """
        raise RuntimeError("Not implementable with this backend.")

    def graph_exists(self) -> bool:
        """
        Does the graph with this ID exist?
        :return:
        """
        graph_nodes = list(nxq.search_nodes(self.storage.get_graph(self.graph_id),
                                            {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]}))
        if graph_nodes is not None and len(graph_nodes) > 0:
            return True
        return False


class NetworkXGraphStorageDisjoint:
    """
    Shell for singleton storing all graphs in-memory. Graphs
    are stored as separate NetworkX objects.
    """

    class __NetworkXGraphStorage:
        """
        Singleton in-memory storage for graphs stored separately by id
        """

        def __init__(self, logger=None):
            self.graphs = defaultdict(nx.Graph)
            # start ids with 1 in each graph
            self.graph_node_ids = defaultdict(constant_factory(1))
            self.log = logger
            self.lock = threading.Lock()

        def add_graph(self, graph_id: str, graph: nx.Graph) -> None:
            # check this graph_id isn't already present
            self.lock.acquire()
            try:
                if graph_id in self.graphs.keys():
                    # graph already present, warn and exit
                    if self.log is not None:
                        self.log.warn('Attempting to insert a graph with the same GraphID, skipping')
                    self.lock.release()
                    return
                # relabel incoming graph nodes to integers, then add
                temp_graph = nx.convert_node_labels_to_integers(graph, 1)
                # set/overwrite GraphID property on all nodes
                for n in list(temp_graph.nodes()):
                    if not temp_graph.nodes[n].get(ABCPropertyGraph.NODE_ID, None):
                        raise PropertyGraphImportException(graph_id=graph_id,
                                                           msg="Some nodes are missing NodeID property, unable to import")
                    temp_graph.nodes[n][ABCPropertyGraph.GRAPH_ID] = graph_id
                # this is needed in case passed in graph is actually a DiGraph
                # which graphs produced by yEd tend to be
                self.graphs[graph_id] = nx.Graph()
                self.graphs[graph_id].add_nodes_from(temp_graph.nodes(data=True))
                self.graphs[graph_id].add_edges_from(temp_graph.edges(data=True))
                self.graph_node_ids[graph_id] = len(self.graphs[graph_id].nodes()) + 1
            except Exception as e:
                raise e
            finally:
                self.lock.release()

        def add_graph_direct(self, graph_id: str, graph: nx.Graph) -> None:

            self.lock.acquire()
            try:
                # check this graph_id isn't already present
                if graph_id in self.graphs.keys():
                    self.graphs[graph_id].clear()
                # relabel incoming graph nodes to integers, then merge
                temp_graph = nx.convert_node_labels_to_integers(graph, 1)
                self.graphs[graph_id] = temp_graph
                self.graph_node_ids[graph_id] = len(self.graphs[graph_id].nodes()) + 1
            except Exception as e:
                raise e
            finally:
                self.lock.release()

        def del_graph(self, graph_id: str) -> None:
            self.lock.acquire()
            try:
                if len(self.graphs[graph_id].nodes) > 0:
                    self.graphs[graph_id].clear()
            except Exception as e:
                raise e
            finally:
                self.lock.release()

        def extract_graph(self, graph_id: str) -> nx.Graph or None:
            self.lock.acquire()
            graph = self.graphs[graph_id]
            self.lock.release()
            return graph.copy()

        def get_graph(self, graph_id) -> nx.Graph:
            # return the store for this graph
            self.lock.acquire()
            ret = self.graphs[graph_id]
            self.lock.release()
            return ret

        def del_all_graphs(self) -> None:
            self.lock.acquire()
            self.graphs.clear()
            self.lock.release()

        def add_blank_node_to_graph(self, graph_id, **attrs) -> int:
            # add a new node into a graph, return internal
            # int id of the added node
            self.lock.acquire()
            try:
                new_id = self.graph_node_ids[graph_id]
                self.graph_node_ids[graph_id] += 1
                self.graphs[graph_id].add_node(new_id, GraphID=graph_id, **attrs)
            except Exception as e:
                raise e
            finally:
                self.lock.release()
            return new_id

    storage_instance = None

    def __init__(self, logger=None):
        if not NetworkXGraphStorageDisjoint.storage_instance:
            NetworkXGraphStorageDisjoint.storage_instance = NetworkXGraphStorageDisjoint.__NetworkXGraphStorage(logger)

    def __getattr__(self, name):
        return getattr(self.storage_instance, name)


class NetworkXGraphImporterDisjoint(NetworkXGraphImporter):
    """
    Importer for NetworkX graphs. Stores graphs separately a dictionary
    based on GUID strings.
    """

    def __init__(self, *, logger=None):
        """
        Initialize the importer setting up storage and logger
        :param logger:
        """
        self.storage = NetworkXGraphStorageDisjoint(logger=logger)
        self.graph_class = NetworkXPropertyGraphDisjoint
        if logger is None:
            self.log = logging.getLogger(__name__)
        else:
            self.log = logger

