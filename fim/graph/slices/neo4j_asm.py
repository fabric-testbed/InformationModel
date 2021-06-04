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

from fim.graph.abc_property_graph import PropertyGraphQueryException
from fim.graph.neo4j_property_graph import Neo4jPropertyGraph, Neo4jGraphImporter
from fim.graph.slices.abc_asm import ABCASMPropertyGraph


class Neo4jASM(ABCASMPropertyGraph, Neo4jPropertyGraph):

    def __init__(self, *, graph_id=str, importer, logger=None):
        super().__init__(graph_id=graph_id, importer=importer, logger=logger)

    def check_node_name(self, *, node_id: str, label: str, name: str) -> bool:
        assert node_id is not None
        assert label is not None
        assert name is not None

        query = f"MATCH (n:{label} {{GraphID: $graphId, NodeID: $nodeId, Name: $name}}) " \
                f"RETURN collect(n.NodeID) as nodeids"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, nodeId=node_id, name=name).single()
            if val is None or len(val.data()) == 0:
                return False
            return len(val.data()['nodeids']) > 0

    def find_node_by_name(self, *, node_name: str, label: str) -> str:

        assert node_name is not None
        assert label is not None
        query = f"MATCH(n:{label} {{GraphID: $graphId, Name: $name }}) RETURN collect(n.NodeID) as nodeids"
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id, name=node_name).single()
            if val is None or len(val.data()) == 0:
                raise PropertyGraphQueryException(graph_id=self.graph_id,
                                                  node_id=None,
                                                  msg=f"Unable to find node with name {node_name} class {label}")
            if len(val.data()['nodeids']) > 1:
                    raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                                      msg=f"Graph contains multiple nodes "
                                                          f"with name {node_name} class {label}")
            return val.data()['nodeids'][0]


class Neo4jASMFactory:
    """
    Help convert graphs between formats so long as they are rooted in Neo4jPropertyGraph
    """
    @staticmethod
    def create(graph: Neo4jPropertyGraph) -> Neo4jASM:
        assert graph is not None
        assert isinstance(graph.importer, Neo4jGraphImporter)

        return Neo4jASM(graph_id=graph.graph_id,
                        importer=graph.importer,
                        logger=graph.log)
