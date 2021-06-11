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

from abc import ABC
from typing import List, Dict, Tuple, Any
import enum

import uuid
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

from fim.view_only_dict import ViewOnlyDict

from .model_element import ModelElement
from ..slivers.network_node import NodeType
from ..slivers.network_link import LinkType
from ..slivers.network_service import NSLayer, ServiceType
from ..graph.slices.abc_asm import ABCASMPropertyGraph
from ..graph.slices.networkx_asm import NetworkxASM
from ..graph.abc_property_graph import ABCPropertyGraph, GraphFormat
from ..graph.resources.networkx_arm import NetworkXARMGraph, NetworkXGraphImporter
from ..slivers.delegations import Delegation, Delegations, Pools, DelegationType, DelegationFormat
from fim.graph.resources.networkx_abqm import NetworkXAggregateBQM, NetworkXABQMFactory
from fim.slivers.capacities_labels import Capacities, CapacityTuple

from .model_element import ElementType
from .node import Node
from .component import Component
from .composite_node import CompositeNode
from .network_service import NetworkService
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
    Base class to define and manipulate a topology over its life cycle.
    Default constructor and load functions create NetworkX-based ASM graphs.
    """
    def __init__(self, graph_file: str = None, graph_string: str = None, logger=None):

        self.graph_model = NetworkxASM(graph_id=str(uuid.uuid4()),
                                       importer=NetworkXGraphImporter(logger=logger),
                                       logger=logger)
        if graph_file is not None or graph_string is not None:
            self.load(file_name=graph_file, graph_string=graph_string)

    def get_parent_element(self, e: ModelElement) -> ModelElement or None:
        """
        Instantiate a ModelElement parent of this element or return None
        for Links, Nodes and sometimes NetworkServices
        :param e:
        :return:
        """
        assert e is not None
        if isinstance(e, Node) or isinstance(e, Link):
            # nodes or links don't have parents
            return None
        # components have nodes as parents
        if isinstance(e, Component):
            node_name, node_id = self.graph_model.get_parent(node_id=e.node_id,
                                                             rel=ABCPropertyGraph.REL_HAS,
                                                             parent=ABCPropertyGraph.CLASS_NetworkNode)
            if node_id is None:
                raise RuntimeError(f'Component {e} has no parent')
            return Node(name=node_name, node_id=node_id, topo=self)
        # NSs may have nodes or components as parents or be by themselves
        if isinstance(e, NetworkService):
            node_name, node_id = self.graph_model.get_parent(node_id=e.node_id,
                                                             rel=ABCPropertyGraph.REL_HAS,
                                                             parent=ABCPropertyGraph.CLASS_Component)
            if node_id is not None:
                return Component(name=node_name, node_id=node_id, topo=self)

            node_name, node_id = self.graph_model.get_parent(node_id=e.node_id,
                                                             rel=ABCPropertyGraph.REL_HAS,
                                                             parent=ABCPropertyGraph.CLASS_NetworkNode)
            if node_id is not None:
                return Node(name=node_name, node_id=node_id, topo=self)
            else:
                return None
        # interfaces have NSs as parents
        if isinstance(e, Interface):
            node_name, node_id = self.graph_model.get_parent(node_id=e.node_id,
                                                             rel=ABCPropertyGraph.REL_CONNECTS,
                                                             parent=ABCPropertyGraph.CLASS_NetworkService)
            if node_id is None:
                raise RuntimeError(f'Interface {e} has no parent')
            return NetworkService(name=node_name, node_id=node_id, topo=self)
        raise RuntimeError(f'Unable to determine parent of element {e}')

    def get_owner_node(self, e: ModelElement) -> ModelElement or None:
        """
        Get an owner Node element for Component, NetworkService or Interface. For Link and Node
        return None
        :param e:
        :return:
        """
        assert e is not None
        if isinstance(e, Node) or isinstance(e, Link):
            # nodes or links don't have parents
            return None
        if isinstance(e, Component):
            return self.get_parent_element(e)
        if isinstance(e, NetworkService):
            # either it is directly owned by a switch or via a component or by itself
            pe = self.get_parent_element(e)
            if pe is None:
                return None
            if isinstance(pe, Node):
                return pe
            else:
                return self.get_parent_element(pe)
        if isinstance(e, Interface):
            # figure out the owner of the parent network service
            ns = self.get_parent_element(e)
            if ns is not None:
                return self.get_owner_node(ns)
        return RuntimeError(f'Unable to determine owner node of element {e}')

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
        self.graph_model.remove_network_node_with_components_nss_cps_and_links(
            node_id=self.__get_node_by_name(name=name).node_id)

    def add_link(self, *, name: str, node_id: str = None, ltype: LinkType,
                 interfaces: List[Interface], technology: str = None,
                 **kwargs) -> Link:
        """
        Add link between listed interfaces with specified parameters (for experiment
        topologies you want add_network_service instead)
        :param name:
        :param node_id:
        :param ltype:
        :param interfaces:
        :param technology:
        :param kwargs:
        :return:
        """
        # add link to graph
        link = Link(name=name, node_id=node_id, ltype=ltype, interfaces=interfaces,
                    etype=ElementType.NEW, topo=self, technology=technology, **kwargs)
        return link

    def remove_link(self, name: str):
        """
        Remove a link between interfaces
        :param name:
        :return:
        """
        assert name is not None
        self.graph_model.remove_network_link(node_id=self.__get_link_by_name(name=name).node_id)

    def add_network_service(self, *, name: str, node_id: str = None, nstype: ServiceType,
                            interfaces: List[Interface], technology: str = None, **kwargs) -> NetworkService:
        """
        Add a network service to a topology. Interfaces can be specified upfront or added/removed later
        :param name:
        :param node_id:
        :param nstype:
        :param interfaces:
        :param technology:
        :param kwargs:
        :return:
        """
        ns = NetworkService(name=name, node_id=node_id, topo=self, nstype=nstype,
                            etype=ElementType.NEW, interfaces=interfaces, technology=technology)
        return ns

    def remove_network_service(self, name: str):
        """
        Remove a network service and associated service interfaces
        :param name:
        :return:
        """
        assert name is not None
        self.graph_model.remove_ns_with_cps_and_links(node_id=self.__get_ns_by_name(name=name).node_id)

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

    def __get_ns_by_name(self, name: str) -> NetworkService:
        """
        Find a network service by its name, return NetworkService object
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.graph_model.find_node_by_name(node_name=name,
                                                     label=ABCPropertyGraph.CLASS_NetworkService)
        return NetworkService(name=name, node_id=node_id, topo=self)

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

    def __get_ns_by_id(self, node_id: str) -> NetworkService:
        """
        Get network service by its node id, return NetworkService object
        :param node_id:
        :return:
        """
        assert node_id is not None
        _, node_props = self.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        return NetworkService(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, topo=self)

    def __list_nodes(self) -> ViewOnlyDict:
        """
        List all NetworkNodes in the topology as a dictionary
        organized by node name. Modifying the dictionary will not affect
        the underlying model, but modifying Nodes in the dictionary will.
        :return:
        """
        node_id_list = self.graph_model.get_all_network_nodes()
        ret = dict()
        for nid in node_id_list:
            n = self.__get_node_by_id(nid)
            ret[n.name] = n
        return ViewOnlyDict(ret)

    def __list_network_services(self) -> ViewOnlyDict:
        """
        List all NetworkServices in the topology as a dictionary organized by name.
        Modifying the dictionary will not affect the underlying model, but modifying
        NetworkServices in the dictionary will.
        :return:
        """
        node_id_list = self.graph_model.get_all_network_service_nodes()
        ret = dict()
        for nid in node_id_list:
            n = self.__get_ns_by_id(nid)
            ret[n.name] = n
        return ViewOnlyDict(ret)

    def __list_links(self) -> ViewOnlyDict:
        """
        List all Links in the topology as a dictionary organized by Link name.
        :return:
        """
        link_id_list = self.graph_model.get_all_network_links()
        ret = dict()
        for nid in link_id_list:
            n = self.__get_link_by_id(nid)
            ret[n.name] = n
        return ViewOnlyDict(ret)

    def __list_of_interfaces(self) -> Tuple[Any]:
        """
        List all interfaces of the topology as a dictionary
        :return:
        """
        ret = list()
        for n in self.nodes.values():
            ret.extend(n.interfaces.values())
        return tuple(ret)

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
        if item == 'network_services':
            return self.__list_network_services()
        if item == 'interface_list':
            return self.__list_of_interfaces()
        raise RuntimeError(f'Attribute {item} not available')

    def serialize(self, file_name: str = None, fmt: GraphFormat = GraphFormat.GRAPHML) -> str or None:
        """
        Serialize to string or to file, depending on whether file_name
        is provided.
        :param file_name:
        :param fmt: one of GraphFormat possible values
        :return string containing GraphML if file_name is None:
        """
        graph_string = self.graph_model.serialize_graph(format=fmt)
        if file_name is None:
            return graph_string
        else:
            with open(file_name, 'w') as f:
                f.write(graph_string)
        return None

    def load(self, *, file_name: str = None, graph_string: str = None):
        """
        Load the topology from file or string
        :param file_name:
        :param graph_string:
        :return:
        """
        if file_name is None and graph_string is None:
            raise RuntimeError('Either file_name or graph_string parameters must be specified.')
        if file_name is not None:
            nx_pgraph = self.graph_model.importer.import_graph_from_file_direct(graph_file=file_name)
        else:
            nx_pgraph = self.graph_model.importer.import_graph_from_string_direct(graph_string=graph_string)
        self.graph_model = NetworkxASM(graph_id=nx_pgraph.graph_id,
                                       importer=nx_pgraph.importer,
                                       logger=nx_pgraph.log)

    def draw(self, *, file_name: str = None, interactive: bool = False,
             topo_detail: TopologyDetail = TopologyDetail.Derived,
             layout=nx.spring_layout):
        """
        Use pyplot to draw the topology of specified level of detail.
        :param file_name: save figure to a file (drawing type is determined by extension, e.g. .png)
        :param interactive: use interactive pyplot mode (defaults to False)
        :param topo_detail: level of detail to use in drawing, defaults to Derived
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
            service_nodes = self.graph_model.get_all_network_service_nodes()
            links = self.graph_model.get_all_network_links()

            derived_graph = nx.Graph()
            for n in network_nodes:
                _, props = self.graph_model.get_node_properties(node_id=n)
                derived_graph.add_node(props[ABCPropertyGraph.PROP_NAME])
            for ns in service_nodes:
                _, props = self.graph_model.get_node_properties(node_id=ns)
                derived_graph.add_node(props[ABCPropertyGraph.PROP_NAME])

            # link interfaces of NSs and NSs to nodes
            for ns in self.network_services.values():
                for nint in ns.interfaces.values():
                    peer_int_id = self.graph_model.find_peer_connection_point(node_id=nint.node_id)
                    if peer_int_id is None:
                        continue
                    _, peer_props = self.graph_model.get_node_properties(node_id=peer_int_id)
                    peer_int = Interface(node_id=peer_int_id, name=peer_props[ABCPropertyGraph.PROP_NAME],
                                         topo=self)
                    peer_int_parent = self.get_parent_element(peer_int)
                    if peer_int_parent is None:
                        continue
                    derived_graph.add_edge(ns.name, peer_int_parent.name)
                for n in self.nodes.values():
                    if self.get_owner_node(ns) == n:
                        derived_graph.add_edge(ns.name, n.name)

            pos = layout(derived_graph)
            nx.draw_networkx(derived_graph, pos=pos)
            if not interactive:
                plt.show()
            if file_name is not None:
                plt.savefig(file_name)
        else:
            raise RuntimeError("This level of detail not yet implemented")

    @staticmethod
    def __print_caplabs__(caps) -> str:
        if caps is None:
            return '{ }'
        else:
            return str(caps)

    def __str__(self):
        """
        Print topology in tabulated form - network nodes, their components, interfaces, then print links
        and their interfaces
        :return:
        """
        lines = list()
        for n in self.nodes.values():
            lines.append(n.name + "[" + str(n.get_property("type")) + "]:  " +
                         self.__print_caplabs__(n.get_property("capacities")))
            for i in n.direct_interfaces.values():
                lines.append("\t\t" + i.name + ": " + str(i.get_property("type")) + " " +
                             self.__print_caplabs__(i.get_property("capacities")) + " " +
                             self.__print_caplabs__(i.get_property("labels")))
            for c in n.components.values():
                lines.append("\t" + c.name + ": " + " " + str(c.get_property("type")) + " " +
                             c.get_property("model"))
                for i in c.interfaces.values():
                    lines.append("\t\t" + i.name + ": " + str(i.get_property("type")) + " " +
                                 self.__print_caplabs__(i.get_property("capacities")))
        lines.append("Links:")
        for l in self.links.values():
            interface_names = [iff.name for iff in l.interface_list]
            lines.append("\t" + l.name + "[" + str(l.get_property("type")) + "]: " +
                         str(interface_names))

        return "\n".join(lines)


class ExperimentTopology(Topology):
    """
    Define an user topology model, inheriting behavior from Topology class.
    In addition to publicly visible methods the following calls can be made:
    topology.nodes - a read-only dictionary of nodes in the topology
    topology.links - a read-only dictionary of links in the topology
    topology.interface_list - a read-only list of all interfaces of all nodes
    If you want to operate on top of a Neo4j graph, use the cast() method.
    """
    def __init__(self, graph_file: str = None, graph_string: str = None, logger=None):
        super().__init__(graph_file=graph_file, graph_string=graph_string, logger=logger)

    def cast(self, *, asm_graph: ABCASMPropertyGraph):
        """
        'Cast' an existing instance of ASM graph into a topology. This can create Neo4j or NetworkX-based
        topology classes
        :param asm_graph:
        :return:
        """
        assert asm_graph is not None
        assert isinstance(asm_graph, ABCASMPropertyGraph)
        self.graph_model = asm_graph


class SubstrateTopology(Topology):
    """
    Define an substrate topology model, inheriting behavior from Topology class.
    In addition to publicly visible methods the following calls can be made:
    topology.nodes - a read-only dictionary of nodes in the topology
    topology.links - a read-only dictionary of links in the topology
    topology.interface_list - a read-only list of all interfaces of all nodes
    """

    def __init__(self, graph_file: str = None, graph_string: str = None, logger=None):
        super().__init__(graph_file=graph_file, graph_string=graph_string, logger=logger)

    def as_arm(self):
        """
        Return model as ARM graph built on top of internal model. Model is not cloned or copied,
        rather recast into ARM, so any changes to the model propagate back to the topology.
        :return:
        """
        return NetworkXARMGraph(graph=self.graph_model,
                                logger=self.graph_model.log)

    @staticmethod
    def __copy_to_delegations(e: ModelElement, atype: DelegationType,
                              delegation_id: str) -> Delegations or None:
        """
        From a model element (node, component, network service, interface), copy
        capacities or labels to a Delegations and return Delegations or none if
        no capacities or labels specified. Return None if element is a stitch node.
        :param e:
        :return:
        """
        assert e is not None
        assert delegation_id is not None
        if e.get_property("stitch_node"):
            return None
        if atype == DelegationType.CAPACITY:
            caps_or_labels = e.get_property(pname='capacities')
        else:
            caps_or_labels = e.get_property(pname='labels')
        if caps_or_labels is not None:
            d = Delegation(atype=atype, delegation_id=delegation_id, aformat=DelegationFormat.SinglePool)
            d.set_details(caps_or_labels)
            # encapsulate in Delegations - this is a single delegation case, no others will be added
            ret = Delegations(atype=atype)
            ret.add_delegations(d)
            return ret
        return None

    def single_delegation(self, *, delegation_id: str, label_pools: Pools, capacity_pools: Pools):
        """
        For simple cases when there is one delegation that delegates everything. Be sure to have
        capacities and labels specified on individual elements where needed - they get copied
        into delegations. Pools must be specified externally. There is no way to specify on
        the same node a single element delegation and a pool definition or reference.
        :param delegation_id:
        :param label_pools:
        :param capacity_pools:
        :return:
        """
        assert label_pools.pool_type == DelegationType.LABEL
        assert capacity_pools.pool_type == DelegationType.CAPACITY

        delegations_dicts = {DelegationType.CAPACITY: dict(),
                             DelegationType.LABEL: dict()}
        pool_dict = {DelegationType.CAPACITY: capacity_pools,
                     DelegationType.LABEL: label_pools}
        for t in DelegationType:
            for n in self.nodes.values():
                # delegate every NetworkNode and its component by copying their capacities and labels
                # if present. Each delegations object is intended for one node.
                delegations = self.__copy_to_delegations(e=n, atype=t,
                                                         delegation_id=delegation_id)
                if delegations is not None:
                    delegations_dicts[t][n.node_id] = delegations
                # components
                for c in n.components.values():
                    delegations = self.__copy_to_delegations(e=c, atype=t,
                                                             delegation_id=delegation_id)
                    if delegations is not None:
                        delegations_dicts[t][c.node_id] = delegations
                    for i in c.interfaces.values():
                        delegations = self.__copy_to_delegations(e=i, atype=t,
                                                                 delegation_id=delegation_id)
                        if delegations is not None:
                            delegations_dicts[t][i.node_id] = delegations
                # network services (for eg switches)
                for sf in n.network_services.values():
                    delegations = self.__copy_to_delegations(e=sf, atype=t,
                                                             delegation_id=delegation_id)
                    if delegations is not None:
                        delegations_dicts[t][sf.node_id] = delegations
                    for i in sf.interfaces.values():
                        delegations = self.__copy_to_delegations(e=i, atype=t,
                                                                 delegation_id=delegation_id)
                        if delegations is not None:
                            delegations_dicts[t][i.node_id] = delegations

            self.as_arm().annotate_delegations_and_pools(dels=delegations_dicts[t],
                                                         pools=pool_dict[t])


class AdvertizedTopology(Topology):
    """
    Topology object to operate on BQM (Query) models returned from e.g.
    listResources etc.
    In addition to publicly visible methods the following calls can be made:
    topology.sites - a read-only dictionary of nodes in the topology
    topology.links - a read-only dictionary of links in the topology
    """

    def __init__(self, graph_file: str = None, graph_string: str = None, logger=None):

        self.graph_model = NetworkXAggregateBQM(graph_id=str(uuid.uuid4()),
                                                importer=NetworkXGraphImporter(logger=logger),
                                                logger=logger)
        if graph_file is not None or graph_string is not None:
            self.load(file_name=graph_file, graph_string=graph_string)

    def add_node(self, *, name: str, node_id: str = None, site: str, ntype: NodeType = NodeType.VM,
                 **kwargs) -> Node:
        raise RuntimeError('Cannot add node to advertisement')

    def add_link(self, *, name: str, node_id: str = None, ltype: LinkType = None,
                 interfaces: List[Interface], layer: NSLayer = None, technology: str = None,
                 **kwargs) -> Link:
        raise RuntimeError('Cannot add link to advertisement')

    def load(self, *, file_name: str = None, graph_string: str = None):
        """
        Load the BQM (query model) topology from file or string
        :param file_name:
        :param graph_string:
        :return:
        """
        if file_name is None and graph_string is None:
            raise RuntimeError('Either file_name or graph_string must be specified.')
        if file_name is not None:
            nx_pgraph = self.graph_model.importer.import_graph_from_file_direct(graph_file=file_name)
        else:
            nx_pgraph = self.graph_model.importer.import_graph_from_string_direct(graph_string=graph_string)
        self.graph_model = NetworkXABQMFactory.create(nx_pgraph)

    def __get_node_by_id(self, node_id: str) -> Node:
        """
        Get node by its node_id, return Node object
        :param node_id:
        :return:
        """
        assert node_id is not None
        _, node_props = self.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        return CompositeNode(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, topo=self)

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

    def __list_sites(self) -> ViewOnlyDict:
        """
        List site information
        :return:
        """
        node_id_list = self.graph_model.get_all_composite_nodes()
        ret = dict()
        for nid in node_id_list:
            n = self.__get_node_by_id(nid)
            ret[n.name] = n
        return ViewOnlyDict(ret)

    def __list_links(self) -> ViewOnlyDict:
        link_id_list = self.graph_model.get_all_network_links()
        ret = dict()
        for nid in link_id_list:
            n = self.__get_link_by_id(nid)
            ret[n.name] = n
        return ViewOnlyDict(ret)

    def __getattr__(self, item):
        if item == 'sites':
            return self.__list_sites()
        if item == 'links':
            return self.__list_links()
        raise RuntimeError(f'Attribute {item} not available')

    def draw(self, *, file_name: str = None, interactive: bool = False,
             topo_detail: TopologyDetail = TopologyDetail.Derived,
             layout=nx.spring_layout):
        """
        Use pyplot to draw the topology of the advertisement.
        :param file_name: save figure to a file (drawing type is determined by extension, e.g. .png)
        :param interactive: use interactive pyplot mode (defaults to False)
        :param topo_detail: level of topology detail (defaults to Derived)
        :param layout: use one of available layout algorithms in NetworkX (defaults to spring_layout)
        :return:
        """
        # clear the drawing
        if not interactive:
            plt.ioff()
        else:
            plt.ion()
        plt.clf()

        if topo_detail == TopologyDetail.Derived:
            # unlike derived for slices, here we don't even draw
            # links as objects because they are all point-to-point

            # collect all network nodes and links, draw edges between them
            network_sites = self.graph_model.get_all_composite_nodes()
            links = self.graph_model.get_all_network_links()

            derived_graph = nx.Graph()
            for n in network_sites:
                _, props = self.graph_model.get_node_properties(node_id=n)
                derived_graph.add_node(props[ABCPropertyGraph.PROP_NAME])

            # build two-element lists of which nodes should be connected by edges
            # indexed by link name
            graph_edges = defaultdict(list)
            for n in self.sites.values():
                node_ints = n.interfaces.values()
                for nint in node_ints:
                    for l in self.links.values():
                        # this works because of custom ModelElement.__eq__()
                        if nint in l.interface_list:
                            graph_edges[l.name].append(n.name)
                            #derived_graph.add_edge(n.name, l.name)

            edge_labels = dict()
            for k, v in graph_edges.items():
                derived_graph.add_edge(v[0], v[1])
                edge_labels[(v[0], v[1])] = k

            pos = layout(derived_graph)
            nx.draw_networkx(derived_graph, pos=pos)
            nx.draw_networkx_edge_labels(derived_graph, edge_labels=edge_labels, pos=pos)

            if not interactive:
                plt.show()
            if file_name is not None:
                plt.savefig(file_name)
        elif topo_detail == TopologyDetail.InfoModel:
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

    def __str__(self):
        """
        Print topology in tabulated form - network nodes, their components, interfaces, then print links
        and their interfaces
        :return:
        """
        lines = list()
        for n in self.sites.values():
            ncp = CapacityTuple(total=n.get_property("capacities"),
                                allocated=n.get_property("capacity_allocations"))
            lines.append(n.name + ": " + str(ncp))
            lines.append("\tComponents:")
            for c in n.components.values():
                ccp = CapacityTuple(total=c.get_property("capacities"),
                                    allocated=c.get_property("capacity_allocations"))
                lines.append("\t\t" + c.name + ": " + " " + str(c.get_property("type")) + " " +
                             c.get_property("model") + " " + str(ccp))
            lines.append("\tSite Interfaces:")
            for i in n.interfaces.values():
                icp = CapacityTuple(total=i.get_property("capacities"),
                                    allocated=i.get_property("capacity_allocations"))
                lines.append("\t\t" + i.name + ": " + str(i.get_property("type")) + " " +
                             str(icp))
        lines.append("Links:")
        for l in self.links.values():
            interface_names = [iff.name for iff in l.interface_list]
            lines.append("\t" + l.name + "[" + str(l.get_property("type")) + "]: " +
                         str(interface_names))
        return "\n".join(lines)
