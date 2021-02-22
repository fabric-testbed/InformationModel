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

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import enum

import uuid
import networkx as nx
import matplotlib.pyplot as plt

from ..slivers.network_node import NodeType, NodeSliver
from ..slivers.network_link import LinkType, NetworkLinkSliver
from ..slivers.switch_fabric import SFLayer
from ..graph.slices.networkx_asm import NetworkxASM
from ..graph.networkx_property_graph import NetworkXGraphImporter
from ..graph.abc_property_graph import ABCPropertyGraph

from .model_element import ElementType
from .node import Node
from .interface import Interface
from .link import Link


class TopologyDetail(enum.Enum):
    """
    Describe the level of detail for drawing a topology.
    """
    Derived = enum.auto()
    WithComponents = enum.auto()
    InfoModel = enum.auto()


class Topology(ABC):
    """
    Define and manipulate a topology over its life cycle
    """
    def __init__(self, logger=None):
        self.graph_model = NetworkxASM(graph_id=str(uuid.uuid4()),
                                       importer=NetworkXGraphImporter(logger=logger),
                                       logger=logger)

    def add_node(self, *, name: str, node_id: str = None, site: str, ntype: NodeType = NodeType.VM,
                 **kwargs) -> Node:
        """
        Add a network node into the substrate topology. Be sure to hardcode node_id - it should
        be consistent from revision to revision of the topology for the same objects.
        kwargs serve to add parameters to the node
        cpu_cores
        ram_size
        disk_size
        image_type
        image_ref
        :param name:
        :param node_id:
        :param site:
        :param ntype:
        :return:
        """
        assert name is not None
        assert site is not None
        # add node to graph
        n = Node(name=name, node_id=node_id, topo=self, site=site,
                 etype=ElementType.NEW, ntype=ntype, **kwargs)
        return n

    def remove_node(self, name: str):
        """
        Remove node and all its components, its interfaces and interfaces of components
        :param name:
        :return:
        """
        assert name is not None
        self.graph_model.remove_network_node_with_components_sfs_cps_and_links(
            node_id=self.__get_node_by_name(name=name).node_id)

    def add_link(self, *, name: str, node_id: str = None, ltype: LinkType = None,
                 interfaces: List[Interface], layer: SFLayer = None, technology: str = None,
                 **kwargs) -> Link:
        """
        Add link between listed interfaces with specified parameters
        :param name:
        :param node_id:
        :param ltype:
        :param interfaces:
        :param layer:
        :param technology:
        :param kwargs:
        :return:
        """
        # add link to graph
        link = Link(name=name, node_id=node_id, ltype=ltype, interfaces=interfaces, **kwargs,
                    etype=ElementType.NEW, topo=self, layer=layer, technology=technology)
        return link

    def remove_link(self, name: str):
        """
        Remove a link between interfaces
        :param name:
        :return:
        """
        assert name is not None
        self.graph_model.remove_network_link(node_id=self.__get_link_by_name(name=name).node_id)

    def __get_node_by_name(self, name: str) -> Node:
        """
        Find node by its name, return Node object
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.graph_model.find_node_by_name(node_name=name,
                                                     label=ABCPropertyGraph.CLASS_NetworkNode)
        return Node(name=name, node_id=node_id, topo=self)

    def __get_link_by_name(self, name: str) -> Link:
        """
        Find link by its name, return Link object
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.graph_model.find_node_by_name(node_name=name,
                                                     label=ABCPropertyGraph.CLASS_Link)
        return Link(name=name, node_id=node_id, topo=self)

    def __get_node_by_id(self, node_id: str) -> Node:
        """
        Get node by its node_id, return Node object
        :param node_id:
        :return:
        """
        assert node_id is not None
        _, node_props = self.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        return Node(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, topo=self)

    def __get_link_by_id(self, node_id: str) -> Link:
        """
        Get link by its node_id, return Link object
        :param node_id:
        :return:
        """
        assert node_id is not None
        _, node_props = self.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        return Link(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, topo=self)

    def __list_nodes(self) -> Dict[str, Node]:
        """
        List all NetworkNodes in the topology as a dictionary
        organized by node name. Modifying the dictionary will not affect
        the underlying model, but modifying Nodes in the dictionary will.
        :return:
        """
        node_id_list = self.graph_model.get_all_network_nodes()
        # Could consider using frozendict or other immutable idioms
        ret = dict()
        for nid in node_id_list:
            n = self.__get_node_by_id(nid)
            ret[n.name] = n
        return ret

    def __list_links(self) -> Dict[str, Link]:
        """
        List all Links in the topology as a dictionary organized by Link name.
        :return:
        """
        link_id_list = self.graph_model.get_all_network_links()
        ret = dict()
        for nid in link_id_list:
            n = self.__get_link_by_id(nid)
            ret[n.name] = n
        return ret

    def __list_interfaces(self) -> Dict[str, Interface]:
        """
        List all interfaces of the topology as a dictionary
        :return:
        """
        ret = dict()
        for n in self.nodes.values():
            ret.update(n.interfaces)
        return ret

    def __getattr__(self, item):
        """
        Special handling for attributes like 'nodes' and 'links' -
        which query into the model. They return dicts and list
        containers. Modifying containers does not affect the underlying
        graph mode, but modifying elements of lists or values of dicts does.
        :param item:
        :return:
        """
        if item == 'nodes':
            return self.__list_nodes()
        if item == 'links':
            return self.__list_links()
        if item == 'interfaces':
            return self.__list_interfaces()

    def serialize(self, file_name=None) -> Any:
        """
        Serialize to string or to file, depending on whether file_name
        is provided.
        :param file_name:
        :return string containing GraphML if file_name is None:
        """
        graph_string = self.graph_model.serialize_graph()
        if file_name is None:
            return graph_string
        else:
            with open(file_name, 'w') as f:
                f.write(graph_string)
        return None

    def draw(self, *, file_name: str = None, interactive: bool = False,
             topo_detail: TopologyDetail = TopologyDetail.Derived,
             layout=nx.spring_layout):
        """
        Use pyplot to draw the derived topology
        :param file_name: save figure to a file (drawing type is determined by extension, e.g. .png)
        :param interactive: use interactive pyplot mode (defaults to False)
        :param topo_detail: level of detail to use in drawing, defaults to OnlyNodes
        :param layout: use one of available layout algorithms in NetworkX (defaults to spring_layout)
        :return:
        """
        # clear the drawing
        if not interactive:
            plt.ioff()
        else:
            plt.ion()
        plt.clf()
        if topo_detail == TopologyDetail.InfoModel:
            # create dictionaries of names for nodes and labels for edges
            g = self.graph_model.storage.extract_graph(self.graph_model.graph_id)
            if g is None:
                return
            node_labels = dict()
            for l in g.nodes:
                node_labels[l] = g.nodes[l][ABCPropertyGraph.PROP_NAME] + \
                                 '[' + g.nodes[l][ABCPropertyGraph.PROP_TYPE] + ']'
            edge_labels = dict()
            for e in g.edges:
                edge_labels[e] = g.edges[e][ABCPropertyGraph.PROP_CLASS]
            # run the layout
            pos = layout(g)
            # draw
            nx.draw_networkx(g, labels=node_labels, pos=pos)
            nx.draw_networkx_edge_labels(g, edge_labels=edge_labels, pos=pos)
            if not interactive:
                plt.show()
            if file_name is not None:
                plt.savefig(file_name)
        elif topo_detail == TopologyDetail.Derived:
            # collect all network nodes and links, draw edges between them
            network_nodes = self.graph_model.get_all_network_nodes()
            links = self.graph_model.get_all_network_links()

            derived_graph = nx.Graph()
            for n in network_nodes:
                _, props = self.graph_model.get_node_properties(node_id=n)
                derived_graph.add_node(props[ABCPropertyGraph.PROP_NAME])
            for l in links:
                _, props = self.graph_model.get_node_properties(node_id=l)
                derived_graph.add_node(props[ABCPropertyGraph.PROP_NAME])

            for n in self.nodes.values():
                node_ints = n.interfaces.values()
                for nint in node_ints:
                    for l in self.links.values():
                        # this works because of custom ModelElement.__eq__()
                        if nint in l.interfaces:
                            derived_graph.add_edge(n.name, l.name)

            pos = layout(derived_graph)
            nx.draw_networkx(derived_graph, pos=pos)
            if not interactive:
                plt.show()
            if file_name is not None:
                plt.savefig(file_name)
        else:
            raise RuntimeError("This level of detail not yet implemented")


class ExperimentTopology(Topology):
    """
    Define an user topology model
    """
    def __init__(self, logger=None):
        super().__init__(logger)


class SubstrateTopology(Topology):
    """
    Define an substrate topology model.
    """
    def __init__(self, logger=None):
        super().__init__(logger)

