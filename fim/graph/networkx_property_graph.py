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
from typing import Dict, Any, List, Set

import logging
import uuid
import json
import tempfile
import networkx as nx
import networkx_query as nxq

from .abc_property_graph import ABCPropertyGraph, PropertyGraphImportException, \
    PropertyGraphQueryException, ABCGraphImporter, GraphFormat
from .networkx_mixin import NetworkXMixin


class NetworkXPropertyGraph(ABCPropertyGraph, NetworkXMixin):
    """
    This class implements ABCPropertyGraph functionality.
    It stores all graphs in a single store (similar to Neo4j) and relies
    on queries to extract the needed subgraphs. It is less efficient
    than NetworkXPropertyGraphDisjoint, however fully compliant with
    ABCPropertyGraph interface.
    """

    def __init__(self, *, graph_id: str, importer, logger=None):
        """
        :param graph_id:
        :param importer: should be an instance of NetworkXGraphImporter
        :param logger: optional
        """
        super().__init__(graph_id=graph_id, importer=importer, logger=logger)
        assert isinstance(importer, NetworkXGraphImporter)
        self.storage = importer.storage

    def validate_graph(self) -> None:
        """
        NetworkX offers limited opportunities for query/validation
        :return:
        """
        self._validate_all_json_properties()
        # check that all nodes and links have 'Class' property
        for n in self.storage.get_graph(self.graph_id).nodes:
            if self.storage.get_graph(self.graph_id).nodes[n].get(ABCPropertyGraph.PROP_CLASS, None) is None:
                raise PropertyGraphImportException(graph_id=self.graph_id,
                                                   msg="Some nodes are missing 'Class' property")
        for e in self.storage.get_graph(self.graph_id).edges:
            if self.storage.get_graph(self.graph_id).edges[e].get(ABCPropertyGraph.PROP_CLASS, None) is None:
                raise PropertyGraphImportException(graph_id=self.graph_id,
                                                   msg="Some edges are missing 'Class' property")

    def delete_graph(self) -> None:
        self.storage.del_graph(self.graph_id)

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
        try:
            node_props = self.storage.get_graph(self.graph_id).nodes[self._find_node(node_id=node_id)].copy()
        except KeyError:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              node_id=node_id, msg="Unable to find node")
        label = node_props.pop(self.NETWORKX_LABEL)
        return [label], node_props

    def get_node_json_property_as_object(self, *, node_id: str, prop_name: str) -> Any:
        """
        Return property as a JSON object or None if property not set. Query exception
        if property is not interpretable as JSON
        :param node_id:
        :param prop_name:
        :return:
        """
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

        # find nodes matching those IDs and get link properties
        real_node_a = self._find_node(node_id=node_a)
        real_node_b = self._find_node(node_id=node_b)
        try:
            edge_props = self.storage.get_graph(self.graph_id).edges[(real_node_a, real_node_b)].copy()
        except KeyError:
            # no edge exists
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Link doesn't exist")
        try:
            etype = edge_props.pop(self.NETWORKX_LABEL)
            return etype, edge_props
        except KeyError:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a,
                                              msg=f"Unable to find {self.NETWORKX_LABEL} property on link")

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

        if prop_name == self.NETWORKX_LABEL:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg=f"Changing {self.NETWORKX_LABEL} property is not permitted")
        # note that we are not copying node properties, which means the next line modifies
        node_props = self.storage.get_graph(self.graph_id).nodes[self._find_node(node_id=node_id)]
        node_props[prop_name] = prop_val

    def unset_node_property(self, *, node_id: str, prop_name: str) -> None:
        assert node_id is not None
        assert prop_name is not None

        if prop_name == self.NETWORKX_LABEL:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg=f"Unsetting {self.NETWORKX_LABEL} property is not permitted")
        if prop_name in ABCPropertyGraph.NO_UNSET_PROPERTIES:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg=f"Unsetting property {prop_name} is not allowed)")

        # since this is not a copy, after that we modify live graph
        node_props = self.storage.get_graph(self.graph_id).nodes[self._find_node(node_id=node_id)]
        if prop_name in node_props.keys():
            node_props.pop(prop_name)
        else:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg=f"Unable to unset property {prop_name}")

    def update_nodes_property(self, *, prop_name: str, prop_val: Any) -> None:
        """
        update a selected property on all nodes of the graph
        :param prop_name:
        :param prop_val:
        :return:
        """
        assert prop_name is not None
        assert prop_val is not None
        graph_nodes = self._find_all_nodes()

        if prop_name == self.NETWORKX_LABEL:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg=f"Changing {self.NETWORKX_LABEL} property is not permitted")
        for n in graph_nodes:
            self.storage.get_graph(self.graph_id).nodes[n][prop_name] = prop_val

    def update_node_properties(self, *, node_id: str, props: Dict[str, Any]) -> None:
        """
        update multiple properties on a node (value types in dictionary must be convertible to string)
        :param node_id:
        :param props:
        :return:
        """
        assert node_id is not None
        assert props is not None
        if self.NETWORKX_LABEL in props.keys():
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg=f"Changing {self.NETWORKX_LABEL} property is not permitted")
        # gives pointer directly into properties of a node in a graph
        node_props = self.storage.get_graph(self.graph_id).nodes[self._find_node(node_id=node_id)]
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

        if prop_name == self.NETWORKX_LABEL:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg=f"Changing {self.NETWORKX_LABEL} property is not permitted")
        # find nodes matching those IDs and get link properties
        real_node_a = self._find_node(node_id=node_a)
        real_node_b = self._find_node(node_id=node_b)
        try:
            # not a copy
            edge_props = self.storage.get_graph(self.graph_id).edges[(real_node_a, real_node_b)]
        except KeyError:
            # no edge exists
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Link doesn't exist")
        etype = edge_props.get(self.NETWORKX_LABEL, None)
        if etype != kind:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a,
                                              msg="Link of this type doesn't exist")
        edge_props[prop_name] = prop_val

    def unset_link_property(self, *, node_a: str, node_b: str, kind: str, prop_name: str) -> None:
        assert node_a is not None
        assert node_b is not None
        assert kind is not None
        assert prop_name is not None

        if prop_name == self.NETWORKX_LABEL:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg=f"Unsetting {self.NETWORKX_LABEL} property is not permitted")
        # find nodes matching those IDs and get link properties
        real_node_a = self._find_node(node_id=node_a)
        real_node_b = self._find_node(node_id=node_b)
        try:
            # not a copy
            edge_props = self.storage.get_graph(self.graph_id).edges[(real_node_a, real_node_b)]
        except KeyError:
            # no edge exists
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Link doesn't exist")
        etype = edge_props.get(self.NETWORKX_LABEL, None)
        if etype != kind:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a,
                                              msg="Link of this type doesn't exist")
        if prop_name in edge_props.keys():
            edge_props.pop(prop_name)

    def update_link_properties(self, *, node_a: str, node_b: str, kind: str, props: Dict[str, Any]) -> None:
        """
        update multiple properties of a link overriding existing ones if necessary.
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

        if self.NETWORKX_LABEL in props.keys():
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg=f"Changing {self.NETWORKX_LABEL} property is not permitted")

        real_node_a = self._find_node(node_id=node_a)
        real_node_b = self._find_node(node_id=node_b)
        try:
            # not a copy
            edge_props = self.storage.get_graph(self.graph_id).edges[(real_node_a, real_node_b)]
        except KeyError:
            # no edge exists
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Link doesn't exist")
        etype = edge_props.get(self.NETWORKX_LABEL, None)
        if etype != kind:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a,
                                              msg="Link of this type doesn't exist")
        edge_props.update(props)

    def get_all_nodes_by_class(self, *, label: str) -> List[str]:
        assert label is not None
        my_graph = self.storage.get_graph(self.graph_id)
        graph_nodes = list(nxq.search_nodes(my_graph,
                                            {'and': [
                                                {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraph.PROP_CLASS,
                                                        label]}
                                            ]
                                            }))
        ret = list()
        for n in graph_nodes:
            ret.append(my_graph.nodes[n][ABCPropertyGraph.NODE_ID])
        return ret

    def get_all_nodes_by_class_and_type(self, *, label: str, ntype: str) -> List[str]:
        assert label is not None
        assert ntype is not None
        my_graph = self.storage.get_graph(self.graph_id)
        graph_nodes = list(nxq.search_nodes(my_graph,
                                            {'and': [
                                                {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraph.PROP_CLASS, label]},
                                                {'eq': [ABCPropertyGraph.PROP_TYPE, ntype]}
                                            ]
                                            }))
        ret = list()
        for n in graph_nodes:
            ret.append(my_graph.nodes[n][ABCPropertyGraph.NODE_ID])
        return ret

    def list_all_node_ids(self) -> List[str]:
        """
        List all NodeID properties of nodes in a graph
        :return:
        """
        nodeids = list()
        for n in list(self._find_all_nodes()):
            nodeids.append(self.storage.get_graph(self.graph_id).nodes[n][ABCPropertyGraph.NODE_ID])
        return nodeids

    def clone_graph(self, *, new_graph_id: str):
        """
        Clone a graph to a new graph_id (only a shallow copy in NetworkX)
        :param new_graph_id:
        :return:
        """
        assert new_graph_id is not None
        new_graph = self.storage.extract_graph(self.graph_id).copy()
        self.storage.add_graph(new_graph_id, new_graph)
        return NetworkXPropertyGraph(graph_id=new_graph_id, importer=self.importer, logger=self.log)

    def serialize_graph(self, format: GraphFormat = GraphFormat.GRAPHML) -> str:
        """
        Serialize a given graph into GraphML string or return None
        if graph is not found
        :return:
        """
        graph = self.storage.extract_graph(self.graph_id)
        graph_string = None
        if graph is not None:
            if format == GraphFormat.GRAPHML:
                graph_string = '\n'.join(nx.generate_graphml(graph))
            elif format == GraphFormat.JSON_NODELINK:
                json_object = nx.readwrite.node_link_data(graph)
                graph_string = json.dumps(json_object)
            elif format == GraphFormat.CYTOSCAPE:
                json_object = nx.readwrite.cytoscape_data(graph)
                graph_string = json.dumps(json_object)
            else:
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                                  msg=f"Unsupported export graph format {format.name}")
        return graph_string

    def graph_exists(self) -> bool:
        """
        Does the graph with this ID exist?
        :return:
        """
        query_match = list(nxq.search_nodes(self.storage.get_graph(self.graph_id),
                                            {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]}))
        return len(query_match) > 0

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
        # extract a graph
        graph = self.storage.extract_graph(self.graph_id)
        if graph is None:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              msg="Unable to find graph")
        # if relationship specified, drop any edge that is not of type rel from graph copy
        if rel is not None:
            self._drop_edges_not_of_type(graph, rel)
        real_node_a = self._find_node(node_id=node_a)
        real_node_z = self._find_node(node_id=node_z)
        try:
            sp = nx.shortest_path(graph, source=real_node_a, target=real_node_z)
        except nx.exception.NetworkXNoPath:
            return list()
        return self._get_node_ids_for_list(graph, sp)

    def get_first_neighbor(self, *, node_id: str, rel: str, node_label: str) -> List:
        """
        Return a list of ids of nodes of this label related via relationship. List may be empty.
        :param node_id:
        :param rel:
        :param node_label:
        :return:
        """
        assert node_id is not None
        assert rel is not None
        assert node_label is not None

        # extract a graph
        graph = self.storage.extract_graph(self.graph_id)
        if graph is None:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              msg="Unable to find graph")
        real_node = self._find_node(node_id=node_id)
        first_neighbors = set(self._get_first_neighbors_via(graph, real_node, rel))
        # filter out those neighbors that aren't of specified label
        real_first_neighbors = self._filter_nodes_by_label(graph, first_neighbors, node_label)
        # convert internal IDs into real IDs
        return self._get_node_ids_for_list(graph, real_first_neighbors)

    def get_first_and_second_neighbor(self, *, node_id: str, rel1: str, node1_label: str, rel2: str,
                                      node2_label: str) -> List:
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
        assert node_id is not None
        assert rel1 is not None
        assert node1_label is not None
        assert rel2 is not None
        assert node2_label is not None

        # extract a graph
        graph = self.storage.extract_graph(self.graph_id)
        if graph is None:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              msg="Unable to find graph nodes")
        real_node = self._find_node(node_id=node_id)
        first_neighbors = set(graph.neighbors(real_node))
        # remove first neighbors connected via relationship that isn't rel1
        neighbor_drop_list = list()
        for n in first_neighbors:
            if graph.edges[(real_node, n)].get(self.NETWORKX_LABEL, None) != rel1:
                neighbor_drop_list.append(n)

        first_neighbors = first_neighbors.difference(neighbor_drop_list)
        if len(first_neighbors) == 0:
            return list()
        # filter first neighbors by label
        first_neighbors = self._filter_nodes_by_label(graph, first_neighbors, node1_label)

        # make a list of second neighbors as neighbors of neighbors
        second_neighbors_dict = dict()
        for n in first_neighbors:
            second_neighbors = set(graph.neighbors(n))
            neighbor_drop_list = list()
            for k in second_neighbors:
                if graph.edges[(n, k)].get(self.NETWORKX_LABEL, None) != rel2:
                    neighbor_drop_list.append(n)
            second_neighbors = second_neighbors.difference(neighbor_drop_list)
            # filter second neighbors by label
            second_neighbors = self._filter_nodes_by_label(graph, second_neighbors, node2_label)
            if len(second_neighbors) > 0:
                # remove self in case they are there
                if real_node in second_neighbors:
                    second_neighbors.remove(real_node)
                second_neighbors_dict[n] = second_neighbors

        # convert to a list of two-member lists, converting internal IDs to guids
        ret = list()
        for k, v in second_neighbors_dict.items():
            for i in v:
                ret.append(self._get_node_ids_for_list(graph, [k, i]))

        return ret

    def delete_node(self, *, node_id: str):
        """
        Delete node from a graph (incident edges automatically deleted)
        :param node_id:
        :return:
        """
        assert node_id is not None

        self.storage.get_graph(self.graph_id).remove_node(self._find_node(node_id=node_id))

    def node_exists(self, *, node_id: str, label: str) -> bool:
        """
        Check if this node exists
        :param node_id:
        :param label:
        :return:
        """
        assert node_id is not None
        assert label is not None
        graph_nodes = list(nxq.search_nodes(self.storage.get_graph(self.graph_id),
                                            {'and': [
                                                {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraph.NODE_ID, node_id]},
                                                {'eq': [ABCPropertyGraph.PROP_CLASS, label]}
                                            ]}))
        if len(graph_nodes) > 1:
            raise PropertyGraphQueryException(node_id=node_id, graph_id=self.graph_id,
                                              msg="Duplicate node found while checking for node uniqueness")
        return len(graph_nodes) == 1

    def add_node(self, *, node_id: str, label: str, props: Dict[str, Any] = None) -> None:
        """
        Add a node with specified label, classes and initial properties. Properties can be empty,
        but set graph id, node id and label
        :param node_id:
        :param label:
        :param props:
        :return:
        """
        assert node_id is not None
        assert label is not None

        if self.node_exists(node_id=node_id, label=label):
            raise PropertyGraphQueryException(node_id=node_id, graph_id=self.graph_id,
                                              msg="Unable to add node - a node with this ID exists")

        int_id = self.storage.add_blank_node_to_graph(self.graph_id, Class=label,
                                                      NodeID=node_id)
        if props is not None:
            self.storage.get_graph(self.graph_id).nodes[int_id].update(props)

    def add_link(self, *, node_a: str, rel: str, node_b: str, props: Dict[str, Any] = None) -> None:
        """
        Add a link of specified types between two nodes and properties of the link
        :param node_a:
        :param rel:
        :param node_b:
        :param props:
        :return:
        """
        assert node_a is not None
        assert node_b is not None
        assert rel is not None

        real_node_a = self._find_node(node_id=node_a, graph_id=self.graph_id)
        real_node_b = self._find_node(node_id=node_b, graph_id=self.graph_id)
        if props is not None:
            self.storage.get_graph(self.graph_id).add_edge(real_node_a, real_node_b, Class=rel, **props)
        else:
            self.storage.get_graph(self.graph_id).add_edge(real_node_a, real_node_b, Class=rel)

    def find_matching_nodes(self, *, other_graph) -> Set:
        """
        Return a set of node ids that match between the two graphs
        :param other_graph: ID of the other graph
        :return:
        """
        assert other_graph is not None
        # collect NodeID properties from self and other graph as set,
        # return an intersection
        self_ids = set(self.list_all_node_ids())
        other_ids = self._collect_nodeids(self.storage.extract_graph(other_graph.graph_id))
        return self_ids.intersection(other_ids)

    def merge_nodes(self, node_id: str, other_graph, merge_properties=None):
        """
        Merge two nodes of the same id belonging to two graphs. Optionally
        specify merging behavior for individual properties. Common relationships are merged.
        Example merge properties in Python:
        {
            "name":'discard', # keep property of the caller (also if not mentioned in merged_properties)
            "age":'overwrite', # keep property of the other graph
            "kids":'combine', # make a list of properties
        }
        :param node_id:
        :param other_graph: other graph object
        :param merge_properties:
        :return:
        """
        assert node_id is not None
        assert other_graph is not None
        assert other_graph.graph_exists()

        # find out internal IDs of the two nodes in our graph and other graph
        real_node = self._find_node(node_id=node_id)
        real_other_node = self._find_node(node_id=node_id, graph_id=other_graph.graph_id)

        # save properties of both (by copy)
        node_props = self.storage.get_graph(self.graph_id).nodes[real_node].copy()
        other_props = self.storage.get_graph(other_graph.graph_id).nodes[real_other_node].copy()

        # remember that graphid is ignored in get_graph in this implementation, but respected
        # in the disjoint implementation

        # merge the nodes in situ
        nx.contracted_nodes(self.storage.get_graph(self.graph_id), real_node, real_other_node, copy=False)

        # deal with properties
        # remove all properties, including 'contracted' new property
        self.storage.get_graph(self.graph_id).nodes[real_node].clear()

        # construct a new set of properties
        new_props = dict()
        if merge_properties is None:
            new_props = node_props
        else:
            for k, v in node_props.items():
                if k in merge_properties:
                    new_props[k] = node_props[k] if merge_properties[k] == 'discard' else \
                        other_props[k] if merge_properties[k] == 'overwrite' else \
                            [node_props[k], other_props[k]] if merge_properties[k] == 'combine' else None
                else:
                    new_props[k] = node_props[k]
        self.storage.get_graph(self.graph_id).nodes[real_node].update(new_props)

    def get_stitch_nodes(self) -> List[str]:
        my_graph = self.storage.get_graph(self.graph_id)
        graph_nodes = list(nxq.search_nodes(my_graph,
                                            {'and': [
                                                {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraph.PROP_STITCH_NODE, 'true']}
                                            ]
                                            }))
        ret = list()
        for n in graph_nodes:
            ret.append(my_graph.nodes[n][ABCPropertyGraph.NODE_ID])
        return ret

    def check_node_unique(self, *, label: str, name: str):
        """
        Check no other node of this class/label and name exists
        :param label:
        :param name:
        :return:
        """
        graph_nodes = list(nxq.search_nodes(self.storage.get_graph(self.graph_id),
                                            {'and': [
                                                {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraph.PROP_NAME, name]},
                                                {'eq': [ABCPropertyGraph.PROP_CLASS, label]}
                                            ]}))
        return len(graph_nodes) == 0


class NetworkXGraphStorage:
    """
    Shell for singleton storing all graphs in-memory. Graphs
    are stored in a single NetworkX graph object. Care is taken
    when loading new graphs to disambiguate their vertices.
    For the moment the code is not thread-safe.
    """

    class __NetworkXGraphStorage:
        """
        Singleton in-memory storage for graphs
        """

        def __init__(self, logger=None):
            self.graphs = nx.Graph()
            self.start_id = 1
            self.log = logger

        def add_graph(self, graph_id: str, graph: nx.Graph) -> None:
            # check this graph_id isn't already present
            existing_graph_nodes = list(nxq.search_nodes(self.graphs, {'eq': [ABCPropertyGraph.GRAPH_ID, graph_id]}))
            if len(existing_graph_nodes) > 0:
                # graph already present, warn and exit
                if self.log is not None:
                    self.log.warn('Attempting to insert a graph with the same GraphID, skipping')
                return
            # relabel incoming graph nodes to integers, then merge
            temp_graph = nx.convert_node_labels_to_integers(graph, first_label=self.start_id)
            # set/overwrite GraphID property on all nodes
            for n in list(temp_graph.nodes()):
                if not temp_graph.nodes[n].get(ABCPropertyGraph.NODE_ID, None):
                    raise PropertyGraphImportException(graph_id=graph_id,
                                                       msg="Some nodes are missing NodeID property, unable to import")
                temp_graph.nodes[n][ABCPropertyGraph.GRAPH_ID] = graph_id
            self.start_id = self.start_id + len(temp_graph.nodes())
            self.graphs.add_nodes_from(temp_graph.nodes(data=True))
            self.graphs.add_edges_from(temp_graph.edges(data=True))

        def add_graph_direct(self, graph_id: str, graph: nx.Graph) -> None:
            # check this graph_id isn't already present
            existing_graph_nodes = list(nxq.search_nodes(self.graphs, {'eq': [ABCPropertyGraph.GRAPH_ID, graph_id]}))
            if len(existing_graph_nodes) > 0:
                # graph already present, warn and exit
                if self.log is not None:
                    self.log.warn('Attempting to insert a graph with the same GraphID, skipping')
                return
            # relabel incoming graph nodes to integers, then merge
            temp_graph = nx.convert_node_labels_to_integers(graph, first_label=self.start_id)
            self.start_id = self.start_id + len(temp_graph.nodes())
            self.graphs.add_nodes_from(temp_graph.nodes(data=True))
            self.graphs.add_edges_from(temp_graph.edges(data=True))

        def del_graph(self, graph_id: str) -> None:
            # find all nodes of this graph and remove them
            graph_nodes = list(nxq.search_nodes(self.graphs, {'eq': [ABCPropertyGraph.GRAPH_ID, graph_id]}))
            if graph_nodes is not None and len(graph_nodes) > 0:
                self.graphs.remove_nodes_from(graph_nodes)

        def extract_graph(self, graph_id: str) -> nx.Graph or None:
            # extract copy of graph from store or return None
            graph_nodes = list(nxq.search_nodes(self.graphs, {'eq': [ABCPropertyGraph.GRAPH_ID, graph_id]}))
            if len(graph_nodes) == 0:
                return None
            # get adjacency (only gets edges and their properties)
            edge_dict = nx.to_dict_of_dicts(self.graphs, graph_nodes)
            # create new graph from edges
            ret = nx.from_dict_of_dicts(edge_dict)
            for n in graph_nodes:
                # merge node dictionaries
                ret.nodes[n].update(self.graphs.nodes[n])
            return ret

        def get_graph(self, graph_id) -> nx.Graph:
            # return the store for all graphs (graph_id is ignored)
            return self.graphs

        def del_all_graphs(self) -> None:
            self.graphs.clear()

        def add_blank_node_to_graph(self, graph_id, **attrs) -> int:
            # add a new node into a graph, return internal
            # int id of the added node
            self.graphs.add_node(self.start_id, GraphID=graph_id, **attrs)
            self.start_id = self.start_id + 1
            return self.start_id - 1

    storage_instance = None

    def __init__(self, logger=None):
        if not NetworkXGraphStorage.storage_instance:
            NetworkXGraphStorage.storage_instance = NetworkXGraphStorage.__NetworkXGraphStorage(logger=logger)

    def __getattr__(self, name):
        return getattr(self.storage_instance, name)


class NetworkXGraphImporter(ABCGraphImporter):
    """
    Importer for NetworkX graphs. Stores graphs in a single NetworkX
    object. Care is taken to disambiguate nodes when loading graphs.
    """

    def __init__(self, *, logger=None):
        """
        Initialize the importer setting up storage and logger
        :param logger:
        """
        self.storage = NetworkXGraphStorage(logger=logger)
        self.graph_class = NetworkXPropertyGraph
        if logger is None:
            self.log = logging.getLogger(__name__)
        else:
            self.log = logger

    @staticmethod
    def _relabel_nodes_to_nodeids(graph: nx.Graph, copy: bool) -> nx.Graph:
        """
        Relabel node names to their node ids. If copy set to True, produce a
        copy, otherwise do it in place. Note that normally nodes are renamed
        to have integer IDs on import.
        :param graph:
        :param copy:
        :return:
        """
        name_map = dict()
        for n in list(graph.nodes):
            name_map[n] = graph.nodes[n][ABCPropertyGraph.NODE_ID]

        # not every node has a NodeID property
        if len(graph.nodes) != len(name_map):
            raise PropertyGraphImportException(graph_id=None,
                                               msg="Some nodes are missing NodeID property, unable to relabel")

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
            f1.flush()
            # read using networkx
            self.storage.add_graph(graph_id=graph_id, graph=nx.read_graphml(f1.name))

        return self.graph_class(graph_id=graph_id, importer=self, logger=self.log)

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
            f1.flush()
            # get graph id (kinda inefficient, because reads graph in, then discards)
            graph_id = self.get_graph_id(graph_file=f1.name)
            # read using networkx
            self.storage.add_graph_direct(graph_id=graph_id, graph=nx.read_graphml(f1.name))

        return self.graph_class(graph_id=graph_id, importer=self, logger=self.log) if graph_id is not None else None

    def import_graph_from_file_direct(self, *, graph_file: str) -> ABCPropertyGraph:
        """
        Import a graph from file without any manipulations
        :param graph_file: name of the file
        :return:
        """
        assert graph_file is not None
        # get graph id
        graph_id = self.get_graph_id(graph_file=graph_file)
        self.storage.add_graph_direct(graph_id=graph_id, graph=nx.read_graphml(graph_file))
        return self.graph_class(graph_id=graph_id, importer=self, logger=self.log) if graph_id is not None else None

    def delete_graph(self, *, graph_id: str) -> None:
        """
        Delete a single graph with this id
        :param graph_id:
        :return:
        """
        assert graph_id is not None
        self.storage.del_graph(graph_id)

    def delete_all_graphs(self) -> None:
        """
        Remove all graphs from the by-GUID in-memory dictionary
        :return:
        """
        self.storage.del_all_graphs()

    def cast_graph(self, *, graph_id: str) -> ABCPropertyGraph:

        assert graph_id is not None
        neo4jg = NetworkXPropertyGraph(graph_id=graph_id, importer=self, logger=self.log)
        assert neo4jg.graph_exists()
        return neo4jg
