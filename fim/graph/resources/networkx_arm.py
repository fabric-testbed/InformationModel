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
NetworkX implementation of ADM (Aggregate Delegation Model) functionality.
"""

import uuid

from ..networkx_property_graph import NetworkXPropertyGraph, NetworkXGraphImporter
from .abc_arm import ABCARMPropertyGraph


class NetworkXARMGraph(ABCARMPropertyGraph, NetworkXPropertyGraph):

    def __init__(self, *, graph: NetworkXPropertyGraph, logger=None):
        """
        Initialize NetworkX ARM - supply an implementation of a graph
        :param graph:
        """
        super().__init__(graph=graph, logger=logger)


class NetworkXARMFactory:
    """
    Help convert graphs between formats so long as they are rooted in NetworkXPropertyGraph
    """
    @staticmethod
    def create(graph: NetworkXPropertyGraph) -> NetworkXARMGraph:
        assert graph is not None
        assert isinstance(graph.importer, NetworkXGraphImporter)

        return NetworkXARMGraph(graph=graph,
                                logger=graph.log)
