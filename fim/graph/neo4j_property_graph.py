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
Neo4j-specific implementation of property graph abstraction
"""
from typing import Dict, Any, Tuple

import logging
import os
import tempfile
import uuid
import time
import json
import networkx as nx
from neo4j import GraphDatabase

from .abc_property_graph import ABCPropertyGraph, PropertyGraphImportException, \
    PropertyGraphQueryException

# to deal with intermittent APOC problems on MAC
APOC_RETRY_COUNT = 10

class Neo4jPropertyGraph(ABCPropertyGraph):
    """
    Neo4j-specific implementation of property graph abstraction
    """

    def __init__(self, *, url: str, user: str, pswd: str, import_host_dir: str, import_dir: str):
        """ URL of Neo4j instance, credentials and directory
        from where Neo4j can import graphs"""
        self.url = url
        self.user = user
        self.pswd = pswd
        self.import_host_dir = import_host_dir
        self.import_dir = import_dir
        self.driver = GraphDatabase.driver(self.url, auth=(user, pswd))

        self.log = logging.getLogger(__name__)

    def _prep_graph(self, graph: str, graph_id: str = None) -> Tuple[str, str, str]:
        """
        Import a workflow graphml, assigning it a new unique graph ID
        return the name of the file where graph is saved with updated GraphID
        and the assigned graphID
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

        # add graph id to every node
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

    def _import_graph(self, graphml_file: str, graph_id: str = None) -> None:
        """
        import graph into neo4j giving every node a label GraphNode
        :param graphml_file:
        :param graph_id:
        :return:
        """

        try:
            with self.driver.session() as session:
                session.run(
                    'call apoc.import.graphml( $fileName, {batchSize: 10000, '
                    'readLabels: true, storeNodeIds: true, '
                    'defaultRelationshipType: "isPrerequisiteFor" } ) ',
                    fileName=graphml_file)
                # force label on all imported nodes
                self.log.debug(f"Adding Node label to graph {graph_id}")
                query_string = "match (n {GraphID: $graphId }) set n:GraphNode"
                session.run(query_string, graphId=graph_id)
        except Exception as e:
            msg = "Neo4j APOC import error %s", str(e)
            raise PropertyGraphImportException(graph_id=None, msg=msg)

    def import_graph_from_string(self, *, graph_string: str, graph_id: str = None) -> str:
        """
        import graph into Neo4j from a string, assigning it a unique id
        :param graph_string: 
        :param graph_id: 
        :return: 
        """
        assert graph_string is not None

        self.log.debug('Importing graph with id %s', graph_id)
        try:
            assigned_id, host_file_name, mapped_file_name = self._prep_graph(graph_string, graph_id)
        except Exception as e:
            msg = "NetworkX graph error %s", str(e)
            raise PropertyGraphImportException(graph_id=graph_id, msg=msg)

        if graph_id is not None:
            assert assigned_id == graph_id

        retry = APOC_RETRY_COUNT
        while retry > 0:
            try:
                # something in APOC prevents loading sometimes on some platforms
                self.log.debug("Trying to load the file %s", mapped_file_name)
                self._import_graph(mapped_file_name, assigned_id)
                retry = -1
            except PropertyGraphImportException:
                self.log.warning("Transient error, unable to load, deleting and reimporting graph %s",
                                 assigned_id)
                retry = retry - 1
                self.delete_graph(graph_id=assigned_id)
                # sleep and try again
                time.sleep(1.0)

        # remove the file
        os.unlink(host_file_name)

        if retry == 0:
            raise PropertyGraphImportException(graph_id=graph_id,
                                               msg='Unable to load graph after multiple attempts')

        return assigned_id

    def import_graph_from_file(self, *, graph_file: str, graph_id: str = None) -> str:
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

    def _validate_graph(self, graph_id: str, rules_file: str) -> None:
        """ validate the graph imported in Neo4j according to a set of given Cypher rules"""
        f = open(rules_file)
        rules_dict = json.load(f)
        f.close()

        for r in rules_dict:
            with self.driver.session() as session:
                # print('Applying rule ', r['msg'])
                v = session.run(r['rule'], graphId=graph_id).single().value()
                # print("Rule {}, value {}".format(r['msg'], v))
                if v is False:
                    raise PropertyGraphImportException(graph_id=graph_id, msg=r['msg'])

        return True

    def validate_graph(self, *, graph_id: str) -> None:
        """
        validate a graph from a built-in set of rules
        :param graph_id:
        :return:
        """
        assert graph_id is not None
        self.log.info('Validating graph %s', graph_id)
        return self._validate_graph(graph_id, os.path.dirname(__file__) + '/rules.json')

    def delete_graph(self, *, graph_id: str) -> None:
        """
        Delete a graph from Neo4j
        :param graph_id:
        :return:
        """
        assert graph_id is not None
        self.log.debug('Deleting graph %s', graph_id)
        with self.driver.session() as session:
            session.run('match (n:GraphNode {GraphID: $graphId })detach delete n', graphId=graph_id)

    def get_node_properties(self, *, graph_id: str, node_id: str) -> Dict[str, Any]:
        """
        get properties of a node as a dictionary
        :param graph_id:
        :param node_id:
        :return:
        """
        assert graph_id is not None
        assert node_id is not None
        query = "MATCH (n:GraphNode {GraphID: $graphId, ID: $nodeId}) RETURN properties(n)"
        with self.driver.session() as session:
            val = session.run(query, graphId=graph_id, nodeId=node_id).single()
            if val is None:
                raise PropertyGraphQueryException(graph_id=graph_id, node_id=node_id, msg="Unable to find node")
            return val.data()['properties(n)']

    def get_link_properties(self, *, graph_id: str, node_a: str, node_b: str, kind: str) -> Dict[str, Any]:
        """
        get properties of a link between nodes
        :param graph_id:
        :param node_a:
        :param node_b:
        :param kind:
        :return:
        """
        assert graph_id is not None
        assert node_a is not None
        assert node_b is not None
        assert kind is not None
        query = f"MATCH (a:GraphNode {{GraphId:$graphId, ID:$nodeA}}) -[r:{kind}]- " \
            f"(b:GraphNode {{GraphId:$graphId, ID:$nodeB}}) RETURN properties(r)"
        with self.driver.session() as session:
            val = session.run(query, graphId=graph_id, nodeA=node_a, nodeB=node_b).single()
            if val is None:
                raise PropertyGraphQueryException(graph_id=graph_id, node_id=node_a, msg="Unable to find link")
            return val.data()['properties(r)']

    def update_node_property(self, *, graph_id: str, node_id: str, prop_name: str, prop_val: Any) -> None:
        """
        update a single property of a node in a graph overwriting the previous value
        :param graph_id:
        :param node_id:
        :param prop_name:
        :param prop_val:
        :return:
        """
        assert graph_id is not None
        assert node_id is not None
        assert prop_name is not None
        query = f"MATCH (s:GraphNode {{GraphID: $graphId, ID: $nodeId}}) " \
            f"SET s+={{ {prop_name}: $propVal}} RETURN properties(s)"
        with self.driver.session() as session:
            val = session.run(query, graphId=graph_id, nodeId=node_id, propVal=prop_val)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=graph_id, node_id=node_id, msg="Unable to set property")

    def update_node_properties(self, *, graph_id: str, node_id: str, props: Dict[str, Any]) -> None:
        """
        update multiple properties on a node (value types in dictionary must be convertible to string)
        :param graph_id:
        :param node_id:
        :param props:
        :return:
        """
        assert graph_id is not None
        assert node_id is not None
        assert props is not None

        all_props = ""
        for k, v in props.items():
            all_props += f'{k}: "{v}", '
        if len(all_props) > 2:
            all_props = all_props[:-2]

        query = f"MATCH (s:GraphNode {{GraphID: $graphId, ID: $nodeId}}) " \
            f"SET s+= {{ {all_props} }} RETURN properties(s)"
        with self.driver.session() as session:
            val = session.run(query, graphId=graph_id, nodeId=node_id)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=graph_id, node_id=node_id,
                                                  msg="Unable to set properties")

    def update_link_property(self, *, graph_id: str, node_a: str, node_b: str, kind: str, prop_name: str,
                             prop_val: Any) -> None:
        """
        update a single property of a link
        :param graph_id:
        :param node_a:
        :param node_b:
        :param kind:
        :param prop_name:
        :param prop_val:
        :return:
        """
        assert graph_id is not None
        assert node_a is not None
        assert node_b is not None
        assert kind is not None
        assert prop_name is not None
        query = f"MATCH (a:GraphNode {{GraphID: $graphId, ID: $nodeA}}) -[r:{kind}]- " \
            f"(b:GraphNode {{GraphID: $graphId, ID:$nodeB}}) SET s+={{ {prop_name}: $propVal}} " \
            f"RETURN properties(r)"
        with self.driver.session() as session:
            val = session.run(query, graphId=graph_id, nodeA=node_a, nodeB=node_b, propVal=prop_val)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=graph_id, node_id=node_a,
                                                  msg="Unable to set property on a link")

    def update_link_properties(self, *, graph_id: str, node_a: str, node_b: str, kind: str,
                               props: Dict[str, Any]) -> None:
        """
        update multiple properties of a link
        :param graph_id:
        :param node_a:
        :param node_b:
        :param kind:
        :param props:
        :return:
        """
        assert graph_id is not None
        assert node_a is not None
        assert node_b is not None
        assert kind is not None
        assert props is not None

        all_props = ""
        for k, v in props.items():
            all_props += f'{k}: "{v}", '
        if len(all_props) > 2:
            all_props = all_props[:-2]

        query = "MATCH (a:GraphNode {{GraphID: $graphId, ID: $nodeA}}) -[r:{kind}]- " \
            f"(b:GraphNode {{GraphID: $graphId, ID:$nodeB}}) SET s+= {{ {all_props} }} RETURN properties(s)"
        with self.driver.session() as session:
            val = session.run(query, graphId=graph_id, nodeA=node_a, nodeB=node_b)
            if val is None or len(val.value()) == 0:
                raise PropertyGraphQueryException(graph_id=graph_id, node_id=node_a,
                                                  node_b=node_b, kind=kind,
                                                  msg="Unable to set properties on a link")
