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
from lxml import etree
from io import StringIO
import networkx as nx

"""
Utilities package for working with graphs (Neo4j and NetworkX)
"""


class GraphML:

    @staticmethod
    def networkx_to_neo4j(graph_string: str) -> str:
        """
        NetworkX doesn't use Label properties unlike Neo4j. To make
        export from NetworkX work with import from Neo4j we need to
        massage GraphML produced by NetworkX by copying the value of
        edge Class property (used in NetworkX) to edge Label (used in Neo4j).
        """
        # copy label attributes from Class property
        ns = {'g': 'http://graphml.graphdrawing.org/xmlns'}
        tree = etree.fromstring(bytes(graph_string, 'utf-8'))
        # find key ids for Class properties for edges and nodes (in GraphML they are separate)
        edge_class = node_class = None
        for c in tree.findall('./g:key[@attr.name="Class"]', ns):
            if c.get('for') == 'edge':
                edge_class = c.attrib['id']
            if c.get('for') == 'node':
                node_class = c.attrib['id']

        for e in tree.findall('./g:graph/g:edge', ns):
            data = e.find(f"g:data[@key='{edge_class}']", ns)
            if not e.attrib.get('label'):
                e.set('label', data.text)
        for n in tree.findall('./g:graph/g:node', ns):
            data = n.find(f"g:data[@key='{node_class}']", ns)
            if not n.attrib.get('labels'):
                # to make NetworkX and Neo4j exports as similar as possible
                # add 'GraphNode' label to all nodes too (neo4j does it)
                n.set('labels', ':GraphNode:' + data.text)
        return etree.tostring(tree, method='xml').decode('utf-8')

    @staticmethod
    def nx_write_graphml(graph: nx.Graph, file_name: str):
        """
        Replacement for nx.write_graphml that writes in a way that is compatible
        with Neo4j GraphML
        """
        graph_string = '\n'.join(nx.generate_graphml(graph))
        graph_string = GraphML.networkx_to_neo4j(graph_string)
        with open(file_name, 'w') as f:
            f.write(graph_string)
            f.flush()
