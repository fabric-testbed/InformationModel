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
Implementation of ARM (Aggregate Resource Model) functionality
"""
from ..neo4j_property_graph import Neo4jPropertyGraph, Neo4jGraphImporter
from .abc_arm import ABCARMPropertyGraph


class Neo4jARMGraph(ABCARMPropertyGraph, Neo4jPropertyGraph):
    """
    Implementation of ARM management
    """

    def __init__(self, *, graph: Neo4jPropertyGraph, logger=None):
        """
        Initialize Neo4j ARM - supply an implementation of a graph
        :param graph:
        """
        super().__init__(graph=graph, logger=logger)


class Neo4jARMFactory:
    """
    Help convert graphs between formats so long as they are rooted in Neo4jPropertyGraph
    """
    @staticmethod
    def create(graph: Neo4jPropertyGraph) -> Neo4jARMGraph:
        assert graph is not None
        assert isinstance(graph.importer, Neo4jGraphImporter)

        return Neo4jARMGraph(graph=graph,
                             logger=graph.log)