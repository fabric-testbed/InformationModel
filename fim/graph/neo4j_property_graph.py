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
from typing import Dict, Any, Tuple, List

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
    PropertyGraphQueryException, ABCGraphImporter

# to deal with intermittent APOC problems on MAC
APOC_RETRY_COUNT = 10


class Neo4jPropertyGraph(ABCPropertyGraph):
    """
    Neo4j-specific implementation of property graph abstraction
    """

    NEO4j_NONE = "None"

    def __init__(self, *, graph_id: str, importer):
        super().__init__(graph_id=graph_id)
        self.importer = importer
        assert isinstance(importer, Neo4jGraphImporter)
        self.driver = importer.driver
        self.log = logging.getLogger(__name__)

    def _validate_json_property(self, node_id: str, prop_name: str, strict: bool = False) -> str:
        """
        Validate that JSON in a particular node in a particular property is valid or throw
        a JSONDecodeError exception. Strict set to true causes exception if property is not found.
        Default strict is set to False. If property is not a valid JSON it's value is returned.
        :param node_id:
        :param prop_name:
        :param strict
        :return:
        """
        assert node_id is not None
        assert prop_name is not None
        _, props = self.get_node_properties(node_id=node_id)
        if prop_name not in props.keys():
            if strict:
                # if property is not there, raise exception
                raise PropertyGraphImportException(graph_id=self.graph_id, node_id=node_id,
                                                   msg=f"Unable to find property {prop_name} on a node")
            else:
                # if property is not there, just return
                return None
        # try loading it as JSON. Exception may be thrown
        if props[prop_name] is not None and props[prop_name] != "None":
            try:
                json.loads(props[prop_name])
            except json.decoder.JSONDecodeError:
                return props[prop_name]
        else:
            return None

    def _validate_all_json_properties(self) -> None:
        """
        Validate all expected JSON properties of all nodes in a given graph or raise an exception
        :return:
        """
        nodes = self.list_all_node_ids()
        if len(nodes) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              node_id=None, msg="Unable to list nodes of graph")
        for node in nodes:
            for prop in self.JSON_PROPERTY_NAMES:
                prop_val = self._validate_json_property(node_id=node, prop_name=prop)
                if prop_val is not None:
                    raise PropertyGraphImportException(graph_id=self.graph_id, node_id=node,
                                                       msg=f"Unable to parse JSON property {prop} with value {prop_val}")

    def _validate_graph(self, rules_file: str) -> None:
        """ validate the graph imported in Neo4j according to a set of given Cypher rules"""
        f = open(rules_file)
        rules_dict = json.load(f)
        f.close()

        for r in rules_dict:
            with self.driver.session() as session:
                # print('Applying rule ', r['msg'])
                v = session.run(r['rule'], graphId=self.graph_id).single().value()
                # print("Rule {}, value {}".format(r['msg'], v))
                if v is False:
                    raise PropertyGraphImportException(graph_id=self.graph_id, msg=r['msg'])

    def validate_graph(self) -> None:
        """
        validate a graph from a built-in set of rules
        :return:
        """
        self.log.info(f'Applying validation rules to graph {self.graph_id}')
        self._validate_graph(os.path.dirname(__file__) + '/data/graph_validation_rules.json')
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

    def list_all_node_ids(self) -> List[str]:
        """
        List all NodeID properties of nodes in a graph
        :return:
        """
        query = "MATCH (n {GraphID: $graphId}) RETURN collect(n.NodeID) as nodeids"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id).single()
            if val is None:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=None, msg="Unable to list graph nodes")
            return val.data()['nodeids']


    def get_node_properties(self, *, node_id: str) -> (List[str],Dict[str, Any]):
        """
        get properties of a node as a dictionary
        :param node_id:
        :return:
        """
        assert node_id is not None
        query = "MATCH (n:GraphNode {GraphID: $graphId, NodeID: $nodeId}) RETURN labels(n), properties(n)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeId=node_id).single()
            if val is None:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=node_id, msg="Unable to find node")
            return val.data()['labels(n)'], val.data()['properties(n)']

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
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a, msg="Unable to find link")
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
        query = f"MATCH (s:GraphNode {{GraphID: $graphId, NodeID: $nodeId}}) " \
            f"SET s+={{ {prop_name}: $propVal}} RETURN properties(s)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeId=node_id, propVal=prop_val)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=node_id, msg="Unable to set property")

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
            all_props += f'{k}: "{v}", '
        if len(all_props) > 2:
            all_props = all_props[:-2]

        query = f"MATCH (s:GraphNode {{GraphID: $graphId, NodeID: $nodeId}}) " \
            f"SET s+= {{ {all_props} }} RETURN properties(s)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeId=node_id)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=node_id,
                                                  msg="Unable to set properties")

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
        query = f"MATCH (a:GraphNode {{GraphID: $graphId, NodeID: $nodeA}}) -[r:{kind}]- " \
            f"(b:GraphNode {{GraphID: $graphId, NodeID:$nodeB}}) SET s+={{ {prop_name}: $propVal}} " \
            f"RETURN properties(r)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeA=node_a, nodeB=node_b, propVal=prop_val)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a,
                                                  msg="Unable to set property on a link")

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
            f"(b:GraphNode {{GraphID: $graphId, NodeID:$nodeB}}) SET s+= {{ {all_props} }} RETURN properties(s)"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeA=node_a, nodeB=node_b)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_a,
                                                  node_b=node_b, kind=kind,
                                                  msg="Unable to set properties on a link")

    def serialize_graph(self) -> str:
        """
        Serialize a given graph into GraphML string
        :return:
        """
        inner_query = f'match(n {{GraphID: "{self.graph_id}"}}) -[r]- (m) return n, r, m'
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

        # FIXME: horrible kludge - APOC exports without indicating 'labels' is a key,
        # even though it is used, and then NetworkX refuses to import. Direct imports to
        # Neo4j work though. So we add a line to XML to declare 'labels' a key. Sigh /ib 09/12/2020
        graph_lines = graph_string.splitlines()
        graph_lines.insert(3, '<key id="labels" for="node" attr.name="labels" attr.type="string"/>\n')
        graph_string = "".join(graph_lines)
        return graph_string

    def clone_graph(self, *, new_graph_id: str) -> ABCPropertyGraph:
        """
        Clone a graph by serializing to string and then reimporting with a new ID.
        APOC procedures do not work well for this.
        Does not check for presence of this graph id in the database
        :param new_graph_id:
        :return:
        """
        assert new_graph_id is not None
        graph_string = self.serialize_graph()
        if graph_string == self.NEO4j_NONE:
            raise PropertyGraphQueryException(msg=f"Unable to find graph with id {self.graph_id} for cloning")
        return self.importer.import_graph_from_string(graph_string=graph_string, graph_id=new_graph_id)

    def graph_exists(self) -> bool:
        """
        Does the graph with this ID exist?
        :return:
        """
        inner_query = f'match(n {{GraphID: "{self.graph_id}"}}) -[r]- (m) return n, r, m'
        # run inner query to check the graph has anything in it
        with self.driver.session() as session:
            val = session.run(inner_query)
            if val.peek() is None:
                return False
        return True

    def get_nodes_on_shortest_path(self, *, node_a: str, node_z: str) -> List:
        """
        Get a list of node ids that lie on a shortest path between two nodes. Return empty
        list if no path can be found.
        :param node_a:
        :param node_z:
        :return:
        """
        query = "match (a:GraphNode {GraphID: $graphId, NodeID: $nodeA}) with a match " \
                "(z:GraphNode {GraphID: $graphId, NodeID: $nodeZ}), " \
                "p=shortestPath((a) -[*1..]- (z)) with nodes(p) as pathnodes " \
                "unwind pathnodes as pathnode return collect(pathnode.NodeID) as nodeids"

        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeA=node_a, nodeZ=node_z).single()
            if val is None:
                return list()
            return val.data()['nodeids']


class Neo4jGraphImporter(ABCGraphImporter):

    def __init__(self, *, url: str, user: str, pswd: str, import_host_dir: str, import_dir: str):
        """ URL of Neo4j instance, credentials and directory
        from where Neo4j can import graphs"""
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
        self.log = logging.getLogger(__name__)

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
            # read using networkx
            g = nx.read_graphml(f1.name)

        # ovewrite graph id on every node
        for n in list(g.nodes):
            g.nodes[n]['GraphID'] = graph_id

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
        :param graphml_file:
        :param graph_id:
        :return:
        """

        assert graphml_file is not None
        assert graph_id is not None
        try:
            with self.driver.session() as session:
                self.log.debug(f"Loading graph {graph_id} into Neo4j")
                val = session.run(
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
        except Exception as e:
            msg = f"Neo4j APOC import error {str(e)}"
            raise PropertyGraphImportException(graph_id=graph_id, msg=msg)

    def enumerate_graph_nodes(self, *, graph_file: str, new_graph_file: str, node_id_prop: str = 'NodeID') -> None:
        """
        Read in a graph and add a NodeId property to every node assigning a unique GUID.
        Save into a new file
        :param graph_file: original graph file name
        :param new_graph_file: new file name
        :param node_id_prop: alternative property name for node id (default NodeId)
        :return:
        """
        assert graph_file is not None
        assert new_graph_file is not None

        # read using networkx
        g = nx.read_graphml(graph_file)
        # add node id to every node
        for n in list(g.nodes):
            g.nodes[n][node_id_prop] = str(uuid.uuid4())
        # save to a new file
        nx.write_graphml(g, new_graph_file)

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

        return Neo4jPropertyGraph(graph_id=assigned_id, importer=self)

    def import_graph_from_string_direct(self, *, graph_string: str) -> None:
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

        # load file
        try:
            with self.driver.session() as session:
                val = session.run(
                    'call apoc.import.graphml( $fileName, {batchSize: 10000, '
                    'readLabels: true, storeNodeIds: true } ) ',
                    fileName=mapped_file_name).single()
        except Exception as e:
            msg = f"Neo4j APOC import error {str(e)}"
            raise PropertyGraphImportException(graph_id=None, msg=msg)

        # unlink temp file
        self.log.debug(f"Unlinking temporary file {host_file_name}")
        os.unlink(host_file_name)

    def import_graph_from_file(self, *, graph_file: str, graph_id: str = None) -> Neo4jPropertyGraph:
        """
        read graph from a file assigning it a given id or generating a new one
        :param graph_file:
        :param graph_id:
        :return:
        """
        assert graph_file is not None
        with open(graph_file, 'r') as f:
            graph_string = f.read()

        return self.import_graph_from_string(graph_string=graph_string, graph_id=graph_id)

    def import_graph_from_file_direct(self, *, graph_file: str) -> str:
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

        # load file
        try:
            with self.driver.session() as session:
                val = session.run(
                    'call apoc.import.graphml( $fileName, {batchSize: 10000, '
                    'readLabels: true, storeNodeIds: true } ) ',
                    fileName=mapped_file_name).single()
        except Exception as e:
            msg = f"Neo4j APOC import error {str(e)}"
            raise PropertyGraphImportException(graph_id=None, msg=msg)

        # unlink copied file
        self.log.debug(f"Unlinking copied file {host_file_name}")
        os.unlink(host_file_name)

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