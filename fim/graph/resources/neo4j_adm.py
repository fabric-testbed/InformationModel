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
Neo4j implementation of ADM (Aggregate Delegation Model) functionality.
"""

import uuid

from ..neo4j_property_graph import Neo4jPropertyGraph, Neo4jGraphImporter
from .abc_adm import ABCADMPropertyGraph


class Neo4jADMGraph(ABCADMPropertyGraph, Neo4jPropertyGraph):

    def __init__(self, *, graph_id: str = None, importer: Neo4jGraphImporter, logger=None):
        """
        Initialize CBM either from existing ID or generate new graph id
        :param graph_id:
        :param importer:
        """
        if graph_id is None:
            graph_id = str(uuid.uuid4())

        super().__init__(graph_id=graph_id, importer=importer, logger=logger)


class Neo4jADMFactory:
    """
    Help convert graphs between formats so long as they are rooted in Neo4jPropertyGraph
    """
    @staticmethod
    def create(graph: Neo4jPropertyGraph) -> Neo4jADMGraph:
        assert graph is not None
        assert isinstance(graph.importer, Neo4jGraphImporter)

        return Neo4jADMGraph(graph_id=graph.graph_id,
                             importer=graph.importer,
                             logger=graph.log)
