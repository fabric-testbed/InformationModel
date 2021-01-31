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
from typing import Dict, Any, Tuple, List, Set

import logging
import uuid
import time
import json
import tempfile
import networkx as nx
import networkx_query as nxq

from .abc_property_graph import ABCPropertyGraph, PropertyGraphImportException, \
    PropertyGraphQueryException, ABCGraphImporter


class NetworkXPropertyGraph(ABCPropertyGraph):

    NETWORKX_LABEL = 'Class'

    def __init__(self, *, graph_id: str):
        self.graph_id = graph_id
        self.graphs = NetworkXGraphStorage()

    def validate_graph(self) -> None:
        """
        NetworkX offers limited opportunities for query/validation
        :return:
        """
        self._validate_all_json_properties()

    def delete_graph(self) -> None:
        self.graphs.del_graph(self.graph_id)

    def get_node_properties(self, *, node_id: str) -> (List[str], Dict[str, Any]):
        """
        get a tuple of labels (list) and properties (dict) of a node. Note that individual
        properties are strings (could be JSON encoded objects). Note that 'Class' property
        contains the equivalent of a label in Neo4j. It is not returned among the regular
        properties.
        :param node_id:
        :return: (list, dict)
        """
        assert node_id is not None
        query_match = list(nxq.search_nodes(self.graphs[self.graph_id],
                                            {'eq': ['NodeID', node_id]}))
        if len(query_match) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              node_id=node_id, msg="Unable to find node")
        node_props = self.graphs[self.graph_id].nodes[query_match[0]].copy()
        label = node_props.pop(self.NETWORKX_LABEL)
        return [label], node_props

    def get_node_json_property_as_object(self, *, node_id: str, prop_name: str) -> Any:
        assert node_id is not None
        assert prop_name is not None
        # very similar to Neo4j, but doesn't compare to NEO4j_NONE
        _, node_props = self.get_node_properties(node_id=node_id)
        prop_str = node_props.get(prop_name, None)
        if prop_str is None:
            return None
        try:
            prop_val = json.loads(prop_str)
            return prop_val
        except json.decoder.JSONDecodeError:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              node_id=node_id,
                                              msg=f"Unable to decode property {prop_str} as JSON.")

    def get_link_properties(self, *, node_a: str, node_b: str) -> (str, Dict[str, Any]):
        """
        get link type and properties of a link between two nodes as a tuple (no multigraphs)
        :param node_a:
        :param node_b:
        :return: (type, Dict)
        """
        assert node_a is not None
        assert node_b is not None
        # need to test for a->b and b->a
        edge_props = None
        try:
            # FIXME: incorrect - node_a are NODE_IDs , not node labels
            edge_props = self.graphs[self.graph_id].edges[(node_a, node_b)].copy()
        except KeyError:
            # try reverse edge
            try:
                # FIXME: incorrect - node_a are NODE_IDs , not node labels
                edge_props = self.graphs[self.graph_id].edges[(node_b, node_a)].copy()
            except KeyError:
                # no edge exists
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Link doesn't exist")
        if edge_props is None:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Error finding link")
        etype = edge_props.pop(self.NETWORKX_LABEL)

        return etype, edge_props

    def update_node_property(self, *, node_id: str, prop_name: str, prop_val: Any) -> None:
        """
        update a single property of a node in a graph overwriting the previous value
        :param node_id:
        :param prop_name:
        :param prop_val:
        :return:
        """
        assert node_id is not None
        assert prop_name is not None
        assert prop_val is not None
        query_match = list(nxq.search_nodes(self.graphs[self.graph_id],
                                            {'eq': ['NodeID', node_id]}))
        if len(query_match) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              node_id=node_id, msg="Unable to find node")
        node_props = self.graphs[self.graph_id].nodes[query_match[0]]
        node_props[prop_name] = prop_val

    def update_nodes_property(self, *, prop_name: str, prop_val: Any) -> None:
        """
        update a selected property on all nodes of the graph
        :param prop_name:
        :param prop_val:
        :return:
        """
        assert prop_name is not None
        assert prop_val is not None
        for n in list(self.graphs[self.graph_id].nodes):
            self.graphs[self.graph_id].nodes[n][prop_name] = prop_val

    def update_node_properties(self, *, node_id: str, props: Dict[str, Any]) -> None:
        """
        update multiple properties on a node (value types in dictionary must be convertible to string)
        :param node_id:
        :param props:
        :return:
        """
        assert node_id is not None
        assert props is not None
        query_match = list(nxq.search_nodes(self.graphs[self.graph_id],
                                            {'eq': ['NodeID', node_id]}))
        if len(query_match) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              node_id=node_id, msg="Unable to find node")
        node_props = self.graphs[self.graph_id].nodes[query_match[0]]
        node_props.update(props)

    def update_link_property(self, *, node_a: str, node_b: str, kind: str, prop_name: str, prop_val: Any) -> None:
        """
        update a single property of a link, overriding existing property or inserting a new one
        :param node_a:
        :param node_b:
        :param kind:
        :param prop_name:
        :param prop_val:
        :return:
        """
        assert node_a is not None
        assert node_b is not None
        assert kind is not None
        assert prop_name is not None
        assert prop_val is not None

        edge_props = None
        try:
            edge_props = self.graphs[self.graph_id].edges[(node_a, node_b)]
        except KeyError:
            # try reverse edge
            try:
                edge_props = self.graphs[self.graph_id].edges[(node_b, node_a)]
            except KeyError:
                # no edge exists
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Link doesn't exist")
        if edge_props is None:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Error finding link")
        etype = edge_props.pop(self.NETWORKX_LABEL)
        if etype != kind:
            return
        edge_props[prop_name] = prop_val

    def update_link_properties(self, *, node_a: str, node_b: str, kind: str, props: Dict[str, Any]) -> None:
        """
        update multiple properties of a link overriding existing ones if necessary
        :param node_a:
        :param node_b:
        :param kind:
        :param props:
        :return:
        """
        assert node_a is not None
        assert node_b is not None
        assert kind is not None
        assert props is not None
        edge_props = None
        try:
            edge_props = self.graphs[self.graph_id].edges[(node_a, node_b)]
        except KeyError:
            # try reverse edge
            try:
                edge_props = self.graphs[self.graph_id].edges[(node_b, node_a)]
            except KeyError:
                # no edge exists
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Link doesn't exist")
        if edge_props is None:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Error finding link")
        etype = edge_props.pop(self.NETWORKX_LABEL)
        if etype != kind:
            return
        edge_props.update(props)

    def list_all_node_ids(self) -> List[str]:
        """
        List all NodeID properties of nodes in a graph
        :return:
        """
        nodeids = list()
        for n in list(self.graphs[self.graph_id].nodes):
            nodeids.append(self.graphs[self.graph_id][n]['NodeID'])
        return nodeids

    def serialize_graph(self) -> str:
        """
        Serialize a given graph into GraphML string
        :return:
        """
        graph_string = '\n'.join(nx.generate_graphml(self.graphs[self.graph_id]))
        return graph_string

    def clone_graph(self, *, new_graph_id: str):
        """
        Clone a graph to a new graph_id (only a shallow copy in NetworkX)
        :param new_graph_id:
        :return:
        """
        assert new_graph_id is not None
        new_graph = self.graphs[self.graph_id].copy()
        self.graphs[new_graph_id] = new_graph

    def graph_exists(self) -> bool:
        """
        Does the graph with this ID exist?
        :return:
        """
        return self.graph_id in self.graphs.keys()

    def get_nodes_on_shortest_path(self, *, node_a: str, node_z: str, rel: str = None) -> List:
        pass

    def get_first_neighbor(self, *, node_id: str, rel: str, node_label: str) -> List:
        pass

    def get_first_and_second_neighbor(self, *, node_id: str, rel1: str, node1_label: str, rel2: str,
                                      node2_label: str) -> List:
        pass

    def delete_node(self, *, node_id: str):
        """
        Delete node from a graph (incident edges automatically deleted)
        :param node_id:
        :return:
        """
        assert node_id is not None
        query_match = list(nxq.search_nodes(self.graphs[self.graph_id],
                                            {'eq': ['NodeID', node_id]}))
        if len(query_match) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              node_id=node_id, msg="Unable to find node")
        self.graphs[self.graph_id].remove_node(query_match[0])

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
            nodeids.add(graph.nodes[n]['NodeID'])
        return nodeids

    def find_matching_nodes(self, *, graph) -> Set:
        """
        Return a set of node ids that match between the two graphs
        :param graph: ID of the other graph
        :return:
        """
        assert graph is not None
        # collect NodeID properties from self and other graph as set,
        # return an intersection
        self_ids = self._collect_nodeids(self.graphs[self.graph_id])
        other_ids = self._collect_nodeids(self.graphs[graph])
        return self_ids.intersection(other_ids)

    def merge_nodes(self, node_id: str, graph, merge_properties=None):
        """
        Not implementable in NetworkX with graphs stored separately -
        has assumptions about a common store for all graphs.
        Would require to store all graphs in a single NetworkX graph.
        """
        raise RuntimeError("Not implemented")


class NetworkXGraphStorage:
    """
    Shell for singleton storing all graphs in-memory
    """

    class __NetworkXGraphStorage:
        """
        Singleton in-memory storage for graphs
        """

        def __init__(self):
            self.graphs = dict()

        def add_graph(self, graph_id: str, graph):
            self.graphs[graph_id] = graph

        def get_graph(self, graph_id):
            return self.graphs.get(graph_id, None)

        def del_graph(self, graph_id):
            self.graphs.pop(graph_id, None)

        def del_all_graphs(self):
            self.graphs.clear()

        def __getitem__(self, item):
            return self.graphs[item]

    storage_instance = None

    def __init__(self):
        if not NetworkXGraphStorage.storage_instance:
            NetworkXGraphStorage.storage_instance = NetworkXGraphStorage.__NetworkXGraphStorage()

    def __getattr__(self, name):
        return getattr(self.storage_instance, name)


class NetworkXGraphImporter(ABCGraphImporter):
    """
    Importer for NetworkX graphs. Stores graphs in a dictionary basedon GUID strings.
    """

    def __init__(self, *, logger=None):
        """
        Initialize the importer setting up storage and logger
        :param logger:
        """
        self.graphs = NetworkXGraphStorage()
        if logger is None:
            self.log = logging.getLogger(__name__)
        else:
            self.log = logger

    @staticmethod
    def _relabel_nodes_to_nodeids(graph: nx.Graph, copy: bool) -> nx.Graph:
        """
        Relabel node names to their node ids. If copy set to True, produce a
        copy, otherwise do it in place
        :param graph:
        :param copy:
        :return:
        """
        name_map = dict()
        for n in list(graph.nodes):
            name_map[n] = graph.nodes[n]['NodeID']

        # not every node has a NodeID property
        if len(graph.nodes) != len(name_map):
            raise PropertyGraphImportException(graph_id=None, msg="Some nodes are missing NodeID property")

        return nx.relabel_nodes(graph, name_map, copy)

    def import_graph_from_string(self, *, graph_string: str, graph_id: str = None) -> ABCPropertyGraph:
        """
        Load graph serialized as a GraphML string. Assign graph id property to nodes.
        :param graph_string:
        :param graph_id:
        :return:
        """
        assert graph_string is not None

        if graph_id is None:
            graph_id = str(uuid.uuid4())

        with tempfile.NamedTemporaryFile(suffix="-graphml", mode='w') as f1:
            f1.write(graph_string)
            # read using networkx
            self.graphs[graph_id] = nx.read_graphml()

        # ovewrite graph id on every node
        for n in list(self.graphs[graph_id].nodes):
            self.graphs[graph_id].nodes[n]['GraphID'] = graph_id

        return NetworkXPropertyGraph(graph_id=graph_id)

    def import_graph_from_string_direct(self, *, graph_string: str) -> ABCPropertyGraph:
        """
        Load graph serialized as a GraphML string with no checks or manipulations. It is
        assumed the GraphML already contains graph ids and node ids.
        :param graph_string:
        :return:
        """
        assert graph_string is not None

        with tempfile.NamedTemporaryFile(suffix="-graphml", mode='w') as f1:
            f1.write(graph_string)
            # get graph id (kinda inefficient, because reads graph in, then discards)
            graph_id = self.get_graph_id(graph_file=f1.name)
            # read using networkx
            self.graphs[graph_id] = nx.read_graphml(f1.name)

        return NetworkXPropertyGraph(graph_id=graph_id) if graph_id is not None else None

    def import_graph_from_file_direct(self, *, graph_file: str) -> ABCPropertyGraph:
        """
        Import a graph from file without any manipulations
        :param graph_file: name of the file
        :return:
        """
        assert graph_file is not None
        # get graph id
        graph_id = self.get_graph_id(graph_file=graph_file)
        self.graphs[graph_id] = nx.read_graphml(graph_file)
        return NetworkXPropertyGraph(graph_id=graph_id) if graph_id is not None else None

    def delete_graph(self, *, graph_id: str) -> None:
        """
        Delete a single graph with this id
        :param graph_id:
        :return:
        """
        assert graph_id is not None
        # return None to avoid KeyError
        self.graphs.del_graph(graph_id)

    def delete_all_graphs(self) -> None:
        """
        Remove all graphs from the by-GUID in-memory dictionary
        :return:
        """
        self.graphs.del_all_graphs()
