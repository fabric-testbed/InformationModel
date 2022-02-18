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
Neo4j-specific implementation of property graph abstraction
"""
from typing import Dict, Any, Tuple, List, Set

import logging
import shutil
import os
import tempfile
import uuid
import time
import json
import networkx as nx
from neo4j import GraphDatabase

from .abc_property_graph import ABCPropertyGraph, PropertyGraphImportException, \
    PropertyGraphQueryException, ABCGraphImporter, GraphFormat

# to deal with intermittent APOC problems on MAC
APOC_RETRY_COUNT = 10


class Neo4jPropertyGraph(ABCPropertyGraph):
    """
    Neo4j-specific implementation of property graph abstraction
    """

    def __init__(self, *, graph_id: str, importer, logger=None):
        """
        Initialize a property graph object. Logger is optional.
        :param graph_id:
        :param importer:
        :param logger:
        """
        super().__init__(graph_id=graph_id, importer=importer, logger=logger)
        assert isinstance(importer, Neo4jGraphImporter)
        self.driver = importer.driver

    def _validate_graph(self, rules_file: str) -> None:
        """ validate the graph imported in Neo4j according to a set of given Cypher rules"""
        f = open(rules_file)
        rules_dict = json.load(f)
        f.close()

        for r in rules_dict:
            with self.driver.session() as session:
                #print('Applying rule ', r['msg'])
                single = session.run(r['rule'], graphId=self.graph_id).single()
                if single is None:
                    return
                v = single.value()
                # print("Rule {}, value {}".format(r['msg'], v))
                if v is False:
                    raise PropertyGraphImportException(graph_id=self.graph_id, msg=r['msg'])

    def validate_graph(self) -> None:
        """
        validate a graph from a built-in set of rules
        :return:
        """
        self.log.info(f'Applying validation rules to graph {self.graph_id}')
        self._validate_graph(os.path.join(os.path.dirname(__file__), 'data', 'graph_validation_rules.json'))
        self.log.info(f'Checking JSON properties of graph {self.graph_id}')
        self._validate_all_json_properties()

    def delete_graph(self) -> None:
        """
        Delete a graph from Neo4j
        :return:
        """
        self.log.debug(f'Deleting graph {self.graph_id}')
        with self.driver.session() as session:
            session.run('match (n:GraphNode {GraphID: $graphId })detach delete n', graphId=self.graph_id)

    def get_all_nodes_by_class(self, *, label: str) -> List[str]:
        assert label is not None
        query = f"MATCH (n:{label} {{GraphID: $graphId}}) RETURN collect(n.NodeID) as nodeids"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id).single()
            if val is None:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=None, msg="Unable to find network links")
            return val.data()['nodeids']

    def get_all_nodes_by_class_and_type(self, *, label: str, ntype: str) -> List[str]:
        assert label is not None
        assert ntype is not None
        query = f"MATCH(n:{label} {{GraphID: $graphId, Type: $ntype}}) RETURN collect(n.NodeID) as nodeids"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, ntype=ntype).single()
            if val is None:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=None, msg="Unable to find network links")
            return val.data()['nodeids']

    def list_all_node_ids(self) -> List[str]:
        """
        List all NodeID properties of nodes in a graph
        :return:
        """
        query = "MATCH (n:GraphNode {GraphID: $graphId}) RETURN collect(n.NodeID) as nodeids"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id).single()
            if val is None:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=None, msg="Unable to list graph nodes")
            return val.data()['nodeids']

    def get_node_properties(self, *, node_id: str) -> (List[str], Dict[str, Any]):
        """
        get a tuple of labels (list) and properties (dict) of a node. Note that individual
        properties are strings (could be JSON encoded objects).
        :param node_id:
        :return: (list, dict)
        """
        assert node_id is not None
        query = "MATCH (n:GraphNode {GraphID: $graphId, NodeID: $nodeId}) RETURN labels(n), properties(n)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeId=node_id).single()
            if val is None:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=node_id, msg="Unable to find node")
            labels = val.data()['labels(n)']
            labels.remove('GraphNode')
            return labels, val.data()['properties(n)']

    def get_node_json_property_as_object(self, *, node_id: str, prop_name: str) -> Any:
        """
        Return node property as a python object (applies to JSON encoded properties), will
        fail on other property values.
        :param node_id:
        :param prop_name:
        :return:
        """
        assert node_id is not None
        assert prop_name is not None
        _, node_props = self.get_node_properties(node_id=node_id)
        prop_str = node_props.get(prop_name, None)
        if prop_str is None or prop_str == self.NEO4j_NONE:
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
        query = f"MATCH (a:GraphNode {{GraphID:$graphId, NodeID:$nodeA}}) -[r]- " \
            f"(b:GraphNode {{GraphID:$graphId, NodeID:$nodeB}}) RETURN type(r), properties(r)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeA=node_a, nodeB=node_b).single()
            if val is None:
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Link doesn't exist")
            return val.data()['type(r)'], val.data()['properties(r)']

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
        query = f"MATCH (s:GraphNode {{GraphID: $graphId, NodeID: $nodeId}}) " \
            f"SET s+={{ {prop_name}: $propVal}} RETURN properties(s)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeId=node_id, propVal=prop_val)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=node_id, msg=f"Unable to set property {prop_name}")

    def unset_node_property(self, *, node_id: str, prop_name: str) -> None:
        assert node_id is not None
        assert prop_name is not None

        if prop_name in ABCPropertyGraph.NO_UNSET_PROPERTIES:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg=f"Not allowed to unset property {prop_name}")
        query = f"MATCH (n:GraphNode {{GraphID: $graphId, NodeID: $nodeId}}) " \
                f"REMOVE n.{prop_name} RETURN n.NodeID"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeId=node_id)
            if val is None or len(val.value()) == 0:
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
        query = f"MATCH (s:GraphNode {{GraphID: $graphId}}) " \
                f"SET s+={{ {prop_name}: $propVal}} RETURN properties(s)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, propVal=prop_val)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                                  msg=f"Unable to set property {prop_name} on graph nodes")

    def update_node_properties(self, *, node_id: str, props: Dict[str, Any]) -> None:
        """
        update multiple properties on a node (value types in dictionary must be convertible to string)
        :param node_id:
        :param props:
        :return:
        """
        assert node_id is not None
        assert props is not None

        all_props = ""
        for k, v in props.items():
            all_props += f"{k}: '{v}', "
        if len(all_props) > 2:
            all_props = all_props[:-2]

        query = f"MATCH (s:GraphNode {{GraphID: $graphId, NodeID: $nodeId}}) " \
            f"SET s+= {{ {all_props} }} RETURN properties(s)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeId=node_id)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=node_id,
                                                  msg="Unable to set multiple properties")

    def update_link_property(self, *, node_a: str, node_b: str, kind: str, prop_name: str,
                             prop_val: Any) -> None:
        """
        update a single property of a link
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
        query = f"MATCH (a:GraphNode {{GraphID: $graphId, NodeID: $nodeA}}) -[r:{kind}]- " \
            f"(b:GraphNode {{GraphID: $graphId, NodeID:$nodeB}}) SET r+={{ {prop_name}: $propVal}} " \
            f"RETURN properties(r)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeA=node_a, nodeB=node_b, propVal=prop_val)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a,
                                                  msg=f"Unable to set property {prop_name} on a link")

    def unset_link_property(self, *, node_a: str, node_b: str, kind: str, prop_name: str) -> None:
        assert node_a is not None
        assert node_b is not None
        assert kind is not None
        assert prop_name is not None

        query = f"MATCH (a:GraphNode {{GraphID: $graphId, NodeID: $nodeA}}) -[r:{kind}]- " \
                f"(b:GraphNode {{GraphID: $graphId, NodeID:$nodeB}}) REMOVE r.{prop_name} RETURN r"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeA=node_a, nodeB=node_b)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a,
                                                  msg=f"Unable to set property {prop_name} on a link")

    def update_link_properties(self, *, node_a: str, node_b: str, kind: str,
                               props: Dict[str, Any]) -> None:
        """
        update multiple properties of a link
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

        all_props = ""
        for k, v in props.items():
            all_props += f'{k}: "{v}", '
        if len(all_props) > 2:
            all_props = all_props[:-2]

        query = "MATCH (a:GraphNode {{GraphID: $graphId, NodeID: $nodeA}}) -[r:{kind}]- " \
            f"(b:GraphNode {{GraphID: $graphId, NodeID:$nodeB}}) SET r+= {{ {all_props} }} RETURN properties(s)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeA=node_a, nodeB=node_b)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a,
                                                  node_b=node_b, kind=kind,
                                                  msg="Unable to set properties on a link")

    def serialize_graph(self, format: GraphFormat = GraphFormat.GRAPHML) -> str:
        """
        Serialize a given graph into GraphML string or return None if graph not found
        :return:
        """
        if format != GraphFormat.GRAPHML:
            PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                        msg=f"Unsupported export graph format {format.name}")
        inner_query = f'match(n:GraphNode {{GraphID: "{self.graph_id}"}}) optional match(n) -[r]- (m) return n, r, m'
        # run inner query to check the graph has anything in it
        with self.driver.session() as session:
            val = session.run(inner_query)
            if val.peek() is None:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=None, msg="No such graph in the database")

        query = f"with '{inner_query}' as query " \
                "CALL apoc.export.graphml.query(query, null, {stream: true, useTypes: true}) " \
                "YIELD file, source, format, nodes, relationships, properties, time, " \
                "rows, batchSize, batches, done, data " \
                "RETURN file, source, format, nodes, relationships, properties, time, " \
                "rows, batchSize, batches, done, data"

        with self.driver.session() as session:
            val = session.run(query).single()
            graph_string = val.get('data')

        if graph_string == self.NEO4j_NONE:
            return None

        # CAUTION: horrible kludge - APOC exports without indicating 'labels' is a key,
        # even though it is used, and then NetworkX refuses to import. Direct imports to
        # Neo4j work though. So we add a line to XML to declare 'labels' a key. Sigh /ib 09/12/2020
        graph_lines = graph_string.splitlines()
        graph_lines.insert(3, '<key id="labels" for="node" attr.name="labels" attr.type="string"/>\n')
        graph_string = "".join(graph_lines)
        return graph_string

    def graph_exists(self) -> bool:
        """
        Does the graph with this ID exist?
        :return:
        """
        inner_query = f'match(n:GraphNode {{GraphID: "{self.graph_id}"}}) -[r]- (m) return n, r, m'
        # run  query to check the graph has anything in it
        with self.driver.session() as session:
            val = session.run(inner_query)
            if val.peek() is None:
                return False
        return True

    def get_nodes_on_shortest_path(self, *, node_a: str, node_z: str, rel: str = None) -> List:
        """
        Get a list of node ids that lie on a shortest path between two nodes. Return empty
        list if no path can be found.
        :param node_a:
        :param node_z:
        :param rel:
        :return:
        """
        assert node_a is not None
        assert node_z is not None

        if rel is None:
            query = "match (a:GraphNode {GraphID: $graphId, NodeID: $nodeA}) with a match " \
                    "(z:GraphNode {GraphID: $graphId, NodeID: $nodeZ}), " \
                    "p=shortestPath((a) -[*1..]- (z)) with nodes(p) as pathnodes " \
                    "unwind pathnodes as pathnode return collect(pathnode.NodeID) as nodeids"
        else:
            query = f"match (a:GraphNode {{GraphID: $graphId, NodeID: $nodeA}}) with a match " \
                    f"(z:GraphNode {{GraphID: $graphId, NodeID: $nodeZ}}), " \
                    f"p=shortestPath((a) -[:{rel}*1..]- (z)) with nodes(p) as pathnodes " \
                    f"unwind pathnodes as pathnode return collect(pathnode.NodeID) as nodeids"

        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeA=node_a, nodeZ=node_z).single()
            if val is None:
                return list()
            return val.data()['nodeids']

    def get_first_neighbor(self, *, node_id: str, rel: str, node_label: str) -> List[str]:
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
        query = f"match (a:GraphNode {{GraphID: $graphId, NodeID: $nodeA}}) -[:{rel}]- " \
                f"(b:{node_label} {{ GraphID: $graphId}}) return b.NodeID"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeA=node_id).value()
            if val is None:
                return list()
            return val

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
        assert node_id is not None
        assert rel1 is not None
        assert node1_label is not None
        assert rel2 is not None
        assert node2_label is not None

        query = f"match (a:GraphNode {{GraphID: $graphId, NodeID: $nodeA}}) -[:{rel1}]- "\
                f"(b:{node1_label} {{GraphID: $graphId}}) -[:{rel2}]- "\
                f"(c:{node2_label} {{GraphID: $graphId}}) WHERE $nodeA <> c.NodeID return b.NodeID, c.NodeID"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeA=node_id).values()
            if val is None:
                return list()
            return val

    def delete_node(self, *, node_id: str):
        """
        Delete node from a graph (incident edges automatically deleted)
        :param node_id:
        :return:
        """
        query = "match (n:GraphNode {GraphID: $graphId, NodeID: $nodeId}) " \
                "call apoc.nodes.delete(n, 10) yield value return *"
        with self.driver.session() as session:
            session.run(query, graphId=self.graph_id, nodeId=node_id).single()

    def node_exists(self, *, node_id: str, label: str):
        """
        Check if this node exists
        :param node_id:
        :param label:
        :return:
        """
        assert node_id is not None
        assert label is not None
        query = f"MATCH (n:{label} {{GraphID: $graphId, NodeID: $nodeId}} RETURN collect(n.NodeID) as nodeids"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeId=node_id).single()
            if val is None or len(val.data()) == 0 or len(val.data()['nodeids']) == 0:
                return False
            return True

    def add_node(self, *, node_id: str, label: str, props: Dict[str, Any] = None) -> None:

        assert node_id is not None
        assert label is not None

        all_props = f"Class: '{label}', GraphID: '{self.graph_id}', NodeID: '{node_id}', "
        if props is not None:
            for k, v in props.items():
                all_props += f"{k}: '{v}', "
        all_props = all_props[:-2]
        labels = f"'GraphNode', '{label}'"
        query = f"CALL apoc.create.node([ {labels} ], {{ {all_props} }});"
        with self.driver.session() as session:
            session.run(query)

    def add_link(self, *, node_a: str, rel: str, node_b: str, props: Dict[str, Any] = None) -> None:

        assert node_a is not None
        assert rel is not None
        assert node_b is not None

        all_props = ""
        if props is not None:
            for k, v in props.items():
                all_props += f"{k}: '{v}', "
        all_props = all_props[:-2]
        query = f"MATCH (a:GraphNode {{GraphID: $graphId, NodeID: $nodeA}}) " \
                f"MATCH (b:GraphNode {{GraphID: $graphId, NodeID: $nodeB}}) " \
                f"CALL apoc.create.relationship(a, \"{rel}\", {{ {all_props} }}, b)" \
                f"YIELD rel RETURN rel"
        with self.driver.session() as session:
            session.run(query, graphId=self.graph_id, nodeA=node_a, nodeB=node_b)

    def find_matching_nodes(self, *, other_graph) -> Set:
        """
        Return a set of node ids that match between the two graphs
        :param other_graph:
        :return:
        """
        assert other_graph is not None
        assert isinstance(other_graph, ABCPropertyGraph)
        assert other_graph.graph_exists()

        query = "match(n:GraphNode {GraphID: $graphId}) with n match " \
                "(m:GraphNode {GraphID: $graphId1}) where m.NodeID=n.NodeID " \
                "return collect(n.NodeID) as common_ids"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, graphId1=other_graph.graph_id).single()
        if val is None:
            return set()
        return set(val.data()['common_ids'])

    def merge_nodes(self, node_id: str, other_graph, merge_properties: Dict = None):
        """
        Merge two nodes of the same id belonging to two graphs. Optionally
        specify merging behavior for individual properties. Common relationships are merged.
        Information on formatting merge properties:
        https://neo4j.com/labs/apoc/4.1/graph-updates/graph-refactoring/merge-nodes/
        Example merge properties in Python:
        {
            "name":'discard', # keep property of the caller
            "age":'overwrite', # keep property of the other graph
            "kids":'combine', # make a Neo4j list of properties
            "`addr.*`": 'overwrite',
            "`.*`": 'discard'
        }
        :param node_id:
        :param other_graph:
        :param merge_properties:
        :return:
        """
        assert node_id is not None
        assert other_graph is not None
        assert other_graph.graph_exists()
        if merge_properties is not None:
            # convert properties to Neo4j format
            l = list()
            for k, v in merge_properties.items():
                l.append(str(k) + ":'" + str(v) + "'")
            merge_properties_as_string = "{" + ",".join(l) + "}"
            query = f"match (n:GraphNode {{GraphID: $graphId, NodeID: $nodeId}}), " \
                    f"(m:GraphNode {{GraphID: $graphId1, NodeID: $nodeId}}) " \
                    f"with head(collect([n, m])) as nodes " \
                    f"call apoc.refactor.mergeNodes(nodes, {{properties: {merge_properties_as_string}, " \
                    f"mergeRels: true}}) yield node return node"
        else:
            query = "match (n:GraphNode {GraphID: $graphId, NodeID: $nodeId}), " \
                    "(m:GraphNode {GraphID: $graphId1, NodeID: $nodeId}) " \
                    "with head(collect([n, m])) as nodes " \
                    "call apoc.refactor.mergeNodes(nodes, {properties: 'discard', mergeRels: true}) " \
                    "yield node return node"
        with self.driver.session() as session:
            session.run(query, graphId=self.graph_id,
                        graphId1=other_graph.graph_id,
                        nodeId=node_id).single()

    def get_stitch_nodes(self) -> List[str]:
        query = f"MATCH (n:GraphNode {{GraphID: $graphId, StitchNode: 'true'}}) RETURN collect(n.NodeID) as nodeids"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id).single()
            if val is None:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=None, msg="Unable to find stitch nodes")
            return val.data()['nodeids']

    def check_node_unique(self, *, label: str, name: str) -> bool:
        assert label is not None
        assert name is not None

        query = f"MATCH (n:{label} {{GraphID: $graphId, Name: $name}}) RETURN collect(n.NodeID) as nodeids"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, name=name).single()
            if val is None or len(val.data()) == 0 or len(val.data()['nodeids']) == 0:
                return True
            return False


class Neo4jGraphImporter(ABCGraphImporter):

    index_initialized = False

    def __init__(self, *, url: str, user: str, pswd: str, import_host_dir: str, import_dir: str, logger=None):
        """
        URL of Neo4j instance, credentials and directory
        from where Neo4j can import graphs.
        :param url:
        :param user:
        :param pswd:
        :param import_host_dir: as seen outside Neo4j docker.
        :param import_dir: as seen by neo4j, set to None if neo4j not in Docker
        :param logger:
        """
        self.url = url
        self.user = user
        self.pswd = pswd
        self.import_host_dir = import_host_dir
        self.import_dir = import_dir
        try:
            self.driver = GraphDatabase.driver(self.url, auth=(user, pswd))
        except Exception as e:
            msg = f"Unable to connect to Neo4j: {str(e)}"
            raise PropertyGraphImportException(graph_id=None, msg=msg)
        if logger is None:
            self.log = logging.getLogger(__name__)
        else:
            self.log = logger
        self._add_indexes()

    def _add_indexes(self):
        """
        Add required indexes in idempotent manner
        :return:
        """
        if Neo4jGraphImporter.index_initialized:
            return
        Neo4jGraphImporter.index_initialized = True
        index_file = os.path.join(os.path.dirname(__file__), 'data', 'neo4j_indexes.json')
        f = open(index_file)
        index_dict = json.load(f)
        f.close()
        self.log.info('Adding Neo4j indexes')
        for index_name, index_cmd in index_dict.items():
            with self.driver.session() as session:
                try:
                    session.run(index_cmd)
                except:
                    # ignore exceptions
                    pass

    def _prep_graph(self, graph: str, graph_id: str = None) -> Tuple[str, str, str]:
        """
        Import a graphml graph, assigning it a new unique graph ID to GraphID property
        (overwrite if there already). return the name of the file where graph is saved
        with updated GraphID and the assigned graphID
        :param graph:
        :param graph_id:
        :return:
        """
        if graph_id is None:
            graph_id = str(uuid.uuid4())

        # save to file
        with tempfile.NamedTemporaryFile(suffix="-graphml", mode='w') as f1:
            f1.write(graph)
            f1.flush()
            # read using networkx
            g = nx.read_graphml(f1.name)

        # ovewrite graph id on every node and check that NodeID is present
        for n in list(g.nodes):
            if not g.nodes[n].get('NodeID', None):
                raise PropertyGraphImportException(graph_id=graph_id,
                                                   msg="Some nodes are missing NodeID property, unable to import")
            g.nodes[n][ABCPropertyGraph.GRAPH_ID] = graph_id

        # save back to GraphML
        # where to save is determined by whether importDir is set
        dest_dir = self.import_host_dir
        if dest_dir is None:
            dest_dir = tempfile.gettempdir()

        uniq_name = str(uuid.uuid4())
        host_file_name = os.path.join(dest_dir, uniq_name)
        mapped_file_name = os.path.join(self.import_dir, uniq_name)

        nx.write_graphml(g, host_file_name)

        return graph_id, host_file_name, mapped_file_name

    def _import_graph(self, graphml_file: str, graph_id: str) -> None:
        """
        import graph into neo4j giving every node a label GraphNode
        and converting Class property into a label
        :param graphml_file:
        :param graph_id:
        :return:
        """

        assert graphml_file is not None
        assert graph_id is not None
        # delete this graph if it exists
        self.delete_graph(graph_id=graph_id)
        try:
            with self.driver.session() as session:
                self.log.debug(f"Loading graph {graph_id} into Neo4j")
                session.run(
                    'call apoc.import.graphml( $fileName, {batchSize: 10000, '
                    'readLabels: true, storeNodeIds: true } ) ',
                    fileName=graphml_file).single()
                # force one common label on all imported nodes
                self.log.debug(f"Adding GraphNode label to graph {graph_id}")
                query_string = "MATCH (n {GraphID: $graphId }) SET n:GraphNode"
                session.run(query_string, graphId=graph_id)
                # convert class property into a label as well
                self.log.debug(f"Converting Class property into Neo4j label for all nodes")
                query_string = "MATCH (n {GraphID: $graphId }) " \
                               "CALL apoc.create.addLabels([ id(n) ], [ n.Class ]) YIELD node RETURN node"
                session.run(query_string, graphId=graph_id)
                # push class labels into class property on relationships
                self.log.debug(f"Pushing label into Class property on all relationships")
                query_string = "MATCH (n {GraphID: $graphId }) - [r] - (n1 {GraphID: $graphId }) " \
                               "CALL apoc.create.setRelProperty(r, 'Class', TYPE(r)) yield rel return rel"
                session.run(query_string, graphId=graph_id)
        except Exception as e:
            msg = f"Neo4j APOC import error {str(e)}"
            raise PropertyGraphImportException(graph_id=graph_id, msg=msg)

    def import_graph_from_string(self, *, graph_string: str, graph_id: str = None) -> Neo4jPropertyGraph:
        """
        import graph into Neo4j from a string, assigning it a unique id
        :param graph_string:
        :param graph_id:
        :return:
        """
        assert graph_string is not None

        self.log.debug(f'Importing graph with id {graph_id}')
        try:
            assigned_id, host_file_name, mapped_file_name = self._prep_graph(graph_string, graph_id)
        except Exception as e:
            msg = f"NetworkX graph error {str(e)}"
            raise PropertyGraphImportException(graph_id=graph_id, msg=msg)

        if graph_id is not None:
            assert assigned_id == graph_id

        retry = APOC_RETRY_COUNT
        while retry > 0:
            try:
                # something in APOC prevents loading sometimes on some platforms
                self.log.debug(f"Trying to load the file {mapped_file_name}")
                self._import_graph(mapped_file_name, assigned_id)
                retry = -1
            except PropertyGraphImportException:
                self.log.warning(f"Transient error, unable to load, deleting and reimporting graph {assigned_id}")
                retry = retry - 1
                self.delete_graph(graph_id=assigned_id)
                # sleep and try again
                time.sleep(1.0)

        # remove the file
        self.log.debug(f"Unlinking temporary file {host_file_name}")
        os.unlink(host_file_name)

        if retry == 0:
            raise PropertyGraphImportException(graph_id=assigned_id,
                                               msg='Unable to load graph after multiple attempts')

        return Neo4jPropertyGraph(graph_id=assigned_id, importer=self, logger=self.log)

    def import_graph_from_string_direct(self, *, graph_string: str) -> ABCPropertyGraph:
        """
        import a graph from string without any manipulations
        :param graph_string:
        :return:
        """
        # save string to temp file
        dest_dir = self.import_host_dir
        assert dest_dir is not None
        uniq_name = str(uuid.uuid4())
        # need both host file name and what is seen from inside Docker
        host_file_name = os.path.join(dest_dir, uniq_name)
        mapped_file_name = os.path.join(self.import_dir, uniq_name)

        with open(host_file_name, 'w') as f:
            f.write(graph_string)

        # get graph id
        graph_id = self.get_graph_id(graph_file=host_file_name)

        self._import_graph(mapped_file_name, graph_id)

        # unlink temp file
        self.log.debug(f"Unlinking temporary file {host_file_name}")
        os.unlink(host_file_name)

        return Neo4jPropertyGraph(graph_id=graph_id, importer=self, logger=self.log)

    def import_graph_from_file_direct(self, *, graph_file: str) -> ABCPropertyGraph:
        """
        import a graph from file without any manipulations
        :param graph_file:
        :return:
        """
        assert graph_file is not None

        # copy file
        dest_dir = self.import_host_dir
        assert dest_dir is not None
        uniq_name = str(uuid.uuid4())
        # need both host file name and what is seen from inside Docker
        host_file_name = os.path.join(dest_dir, uniq_name)
        mapped_file_name = os.path.join(self.import_dir, uniq_name)

        shutil.copyfile(graph_file, host_file_name)

        # get graph id
        graph_id = self.get_graph_id(graph_file=host_file_name)

        # load file
        self._import_graph(mapped_file_name, graph_id)

        # unlink copied file
        self.log.debug(f"Unlinking copied file {host_file_name}")
        os.unlink(host_file_name)

        return Neo4jPropertyGraph(graph_id=graph_id, importer=self, logger=self.log)

    def delete_all_graphs(self) -> None:
        """
        Delete all graphs from the database
        :return:
        """
        self.log.debug('Deleting all graphs from the database')
        with self.driver.session() as session:
            session.run('match (n) detach delete n')

    def delete_graph(self, *, graph_id: str) -> None:
        """
        Delete a graph from Neo4j
        :return:
        """
        self.log.debug(f'Deleting graph {graph_id}')
        with self.driver.session() as session:
            session.run('match (n:GraphNode {GraphID: $graphId })detach delete n', graphId=graph_id)

    def cast_graph(self, *, graph_id: str) -> ABCPropertyGraph:

        assert graph_id is not None
        neo4jg = Neo4jPropertyGraph(graph_id=graph_id, importer=self, logger=self.log)
        assert neo4jg.graph_exists()
        return neo4jg
