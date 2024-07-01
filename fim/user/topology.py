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
from typing import List, Tuple, Any, Set, Tuple
import enum

import uuid
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict

from fim.view_only_dict import ViewOnlyDict

from .model_element import ModelElement, TopologyException
from ..slivers.network_node import NodeType
from ..slivers.network_link import LinkType
from ..slivers.network_service import NSLayer, ServiceType, MirrorDirection, NetworkServiceSliver
from ..graph.slices.abc_asm import ABCASMPropertyGraph
from ..graph.slices.networkx_asm import NetworkxASM
from ..graph.slices.neo4j_asm import Neo4jASM
from ..graph.abc_property_graph import ABCPropertyGraph, GraphFormat
from ..graph.resources.networkx_arm import NetworkXARMGraph
from ..graph.networkx_property_graph import NetworkXGraphImporter
from ..graph.networkx_property_graph_disjoint import NetworkXGraphImporterDisjoint
from ..graph.resources.neo4j_arm import Neo4jARMGraph
from ..slivers.delegations import Delegation, Delegations, Pools, DelegationType, DelegationFormat
from fim.graph.resources.networkx_abqm import NetworkXAggregateBQM, NetworkXABQMFactory
from fim.slivers.capacities_labels import FreeCapacity, Labels, Capacities
from fim.slivers.interface_info import InterfaceType
from fim.slivers.topology_diff import TopologyDiff, TopologyDiffTuple, TopologyDiffModifiedTuple, WhatsModifiedFlag

from .model_element import ElementType
from .node import Node
from .component import Component
from .composite_node import CompositeNode
from .network_service import NetworkService, PortMirrorService
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
    Default constructor and load functions create NetworkX-based ASM graphs. Pass
    in Neo4jImporter to create a Neo4j-based Topology.
    """
    def __init__(self, graph_file: str = None, graph_string: str = None, logger=None, importer=None):

        if not importer:
            self.graph_model = NetworkxASM(graph_id=str(uuid.uuid4()),
                                           importer=NetworkXGraphImporter(logger=logger),
                                           logger=logger)
        else:
            if isinstance(importer, NetworkXGraphImporter) or \
                    isinstance(importer, NetworkXGraphImporterDisjoint):
                self.graph_model = NetworkxASM(graph_id=str(uuid.uuid4()),
                                               importer=importer,
                                               logger=logger)
            else:
                self.graph_model = Neo4jASM(graph_id=str(uuid.uuid4()),
                                            importer=importer,
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
        if isinstance(e, Node) or isinstance(e, Link):
            # nodes or links don't have parents
            return None

        # interfaces have NSs as parents
        if isinstance(e, Interface):
            if e.type == InterfaceType.SubInterface:
                node_name, node_id = self.graph_model.get_parent(node_id=e.node_id,
                                                                 rel=ABCPropertyGraph.REL_CONNECTS,
                                                                 parent=ABCPropertyGraph.CLASS_ConnectionPoint)
                if node_id is None:
                    raise TopologyException(f'Interface {e} has no parent')
                return Interface(name=node_name, node_id=node_id, topo=self)

            node_name, node_id = self.graph_model.get_parent(node_id=e.node_id,
                                                             rel=ABCPropertyGraph.REL_CONNECTS,
                                                             parent=ABCPropertyGraph.CLASS_NetworkService)
            if node_id is None:
                raise TopologyException(f'Interface {e} has no parent')
            return NetworkService(name=node_name, node_id=node_id, topo=self)

        # components have nodes as parents
        if isinstance(e, Component):
            node_name, node_id = self.graph_model.get_parent(node_id=e.node_id,
                                                             rel=ABCPropertyGraph.REL_HAS,
                                                             parent=ABCPropertyGraph.CLASS_NetworkNode)
            if node_id is None:
                raise TopologyException(f'Component {e} has no parent')
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

            node_name, node_id = self.graph_model.get_parent(node_id=e.node_id,
                                                             rel=ABCPropertyGraph.REL_HAS,
                                                             parent=ABCPropertyGraph.CLASS_CompositeNode)
            if node_id is not None:
                return CompositeNode(name=node_name, node_id=node_id, topo=self)

            return None

        raise TopologyException(f'Unable to determine parent of element {e}')

    def get_owner_node(self, e: ModelElement) -> ModelElement or None:
        """
        Get an owner Node element for Component, NetworkService or Interface. For Link and Node
        return None
        :param e:
        :return:
        """
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
        return TopologyException(f'Unable to determine owner node of element {e}')

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
        # make sure name is unique within the topology
        if name in self._list_nodes().keys():
            raise TopologyException('Node names must be unique within topology.')
        # add node to graph
        n = Node(name=name, node_id=node_id, topo=self, site=site,
                 etype=ElementType.NEW, ntype=ntype, **kwargs)
        return n

    def remove_node(self, name: str):
        """
        Remove node and all its components, its interfaces and interfaces of components.
        Remove a matching ServicePort if connected to a NetworkService.
        :param name:
        :return:
        """
        if name not in self.nodes.keys():
            raise TopologyException(f'Node {name} is not in this topology.')
        for i in self.nodes[name].interface_list:
            # disconnect if connected to a network service
            peers = i.get_peers(itype=InterfaceType.ServicePort)
            if peers:
                if len(peers) == 1:
                    # disconnect from its parent service
                    self.get_parent_element(peers[0]).disconnect_interface(i)
                else:
                    raise TopologyException(f'Interface {i.name} has more than one peer, this is a model error.')

        self.graph_model.remove_network_node_with_components_nss_cps_and_links(
            node_id=self._get_node_by_name(name=name).node_id)

    def add_facility(self, *, name: str, node_id: str = None, site: str,
                     nstype: ServiceType = ServiceType.VLAN,
                     nslabels: Labels or None = None,
                     interfaces: List[Tuple[Any]] or None = None,
                     **kwargs) -> Node:
        """
        Add a facility node with VLAN service and FacilityPort interface as a single construct.
        Works for aggregate topologies and experiment topologies the same way.
        Link and interface node_ids are derived from node_id if it is provided.
        :param name: name of facility (must match the advertisement)
        :param node_id : optional node id of the facility node (all other node ids are derived if provided)
        :param site: site of the facility (must match the advertisement)
        :param nstype: alternative type of network service in Facility (defaults to VLAN)
        :param nslabels: additional labels for facility network service (defaults to None)
        :param interfaces: definitions of interfaces - list of tuples each including (name, labels, capacities) for
        each interface a facility will have. If a facility only has one interface it is OK to use **kwargs.
        :kwargs: parameters for the interface of the facility (bandwidth, mtu, LAN tags etc)
        """
        # should work with deep sliver reconstruction
        facn = self.add_node(name=name, node_id=node_id, site=site, ntype=NodeType.Facility)
        facs = facn.add_network_service(name=name + '-ns', node_id=node_id + '-ns' if node_id else None,
                                        nstype=nstype, labels=nslabels)
        if not interfaces:
            # if no interfaces are defined, use implicit definition and kwargs
            # this is how the code was defined originally
            faci = facs.add_interface(name=name + '-int', node_id=node_id + '-int' if node_id else None,
                                      itype=InterfaceType.FacilityPort, **kwargs)
        else:
            # if interfaces are defined, assume a list of tuples (name, labels, capacities) are present
            # this was added to support multiple interfaces per facility
            for iname, ilabels, icapacities in interfaces:
                iindex = 0
                faci = facs.add_interface(name=iname, node_id=node_id + f'-int{iindex}' if node_id else None,
                                          itype=InterfaceType.FacilityPort, labels=ilabels, capacities=icapacities)
                iindex += 1

        return facn

    def remove_facility(self, *, name: str):
        """
        Remove a facility and associated network service and interface, disconnecting it from a
        service as appropriate. Same as removing a node.
        """
        fac = self._get_node_by_name(name)
        if fac.type != NodeType.Facility:
            raise TopologyException(f'{name} is not a Facility node, cannot remove.')
        self.remove_node(name)

    def add_switch(self, *, name: str, node_id: str = None, site: str,
                   nstype: ServiceType = ServiceType.P4, nslabels: Labels or None = None,
                   nports: int = 8, portlabels: Labels or None = None,
                   portcapacities: Capacities or None = None,
                   **kwargs) -> Node:
        """
        Add a switch (P4 type by default) with some number of ports (8 by default)
        all given names and label local_names 'p1'-'p8'.
        :param name:
        :param node_id:
        :param site:
        :param nstype: network service type (defaults to P4)
        :param nslabels: additional labels for switch network service
        :param nports: number of ports (defaults to 8)
        :param portlabels: labels to be added to each port (otherwise overridden with default)
        :param portcapacities: capacities to be added to each port (otherwise overridden with default)
        :param kwargs: pass additional parameters to add node (e.g. model)
        """
        switch = self.add_node(name=name, node_id=node_id, site=site, ntype=NodeType.Switch)
        switch_ns = switch.add_network_service(name=name + '-ns',
                                               node_id=node_id + '-ns' if node_id else None,
                                               nstype=nstype, labels=nslabels)
        # name them 'p1'-'p8'
        for i in range(1, nports + 1):
            labels = Labels(local_name=f'p{i}')
            # 100G port
            capacities = Capacities(bw=100)
            switch_i = switch_ns.add_interface(name=f'p{i}', node_id=node_id + f'-int{i}' if node_id else None,
                                               itype=InterfaceType.DedicatedPort,
                                               labels=portlabels if portlabels else labels,
                                               capacities=portcapacities if portcapacities else capacities)
        return switch

    def remove_switch(self, *, name: str):
        """
        Remove a switch and associated network service and interfaces, disconnecting it from a
        service as appropriate. Same as removing a node.
        """
        fac = self._get_node_by_name(name)
        if fac.type != NodeType.Switch:
            raise TopologyException(f'{name} is not a Switch node, cannot remove.')
        self.remove_node(name)

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
        # make sure name is unique within the topology
        if name in self._list_links().keys():
            raise TopologyException('Link names must be unique within topology.')
        link = Link(name=name, node_id=node_id, ltype=ltype, interfaces=interfaces,
                    etype=ElementType.NEW, topo=self, technology=technology, **kwargs)
        return link

    def remove_link(self, name: str):
        """
        Remove a link between interfaces
        :param name:
        :return:
        """
        self.graph_model.remove_network_link(node_id=self._get_link_by_name(name=name).node_id)

    def add_network_service(self, *, name: str, node_id: str = None, nstype: ServiceType,
                            interfaces: List[Interface] = None, technology: str = None, **kwargs) -> NetworkService:
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
                            etype=ElementType.NEW, interfaces=interfaces, technology=technology, **kwargs)
        return ns

    def remove_network_service(self, name: str):
        """
        Remove a network service and associated service interfaces
        :param name:
        :return:
        """
        self.graph_model.remove_ns_with_cps_and_links(node_id=self._get_ns_by_name(name=name).node_id)

    def _get_node_by_name(self, name: str) -> Node:
        """
        Find node by its name, return Node object
        :param name:
        :return:
        """
        node_id = self.graph_model.find_node_by_name(node_name=name,
                                                     label=ABCPropertyGraph.CLASS_NetworkNode)
        return Node(name=name, node_id=node_id, topo=self)

    def _get_link_by_name(self, name: str) -> Link:
        """
        Find link by its name, return Link object
        :param name:
        :return:
        """
        node_id = self.graph_model.find_node_by_name(node_name=name,
                                                     label=ABCPropertyGraph.CLASS_Link)
        return Link(name=name, node_id=node_id, topo=self)

    def _get_ns_by_name(self, name: str) -> NetworkService:
        """
        Find a network service by its name, return NetworkService object
        :param name:
        :return:
        """
        node_id = self.graph_model.find_node_by_name(node_name=name,
                                                     label=ABCPropertyGraph.CLASS_NetworkService)
        return NetworkService(name=name, node_id=node_id, topo=self)

    def _get_node_by_id(self, node_id: str) -> Node:
        """
        Get node by its node_id, return Node object
        :param node_id:
        :return:
        """
        _, node_props = self.graph_model.get_node_properties(node_id=node_id)
        return Node(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, topo=self)

    def _get_link_by_id(self, node_id: str) -> Link:
        """
        Get link by its node_id, return Link object
        :param node_id:
        :return:
        """
        _, node_props = self.graph_model.get_node_properties(node_id=node_id)
        return Link(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, topo=self)

    def _get_ns_by_id(self, node_id: str) -> NetworkService:
        """
        Get network service by its node id, return NetworkService object
        :param node_id:
        :return:
        """
        _, node_props = self.graph_model.get_node_properties(node_id=node_id)
        ns = NetworkService(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, topo=self)
        if ns.type == ServiceType.PortMirror:
            return PortMirrorService(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, topo=self)
        return ns

    def _list_nodes(self) -> ViewOnlyDict:
        """
        List all NetworkNodes in the topology as a dictionary
        organized by node name. Modifying the dictionary will not affect
        the underlying model, but modifying Nodes in the dictionary will.
        :return:
        """
        node_id_list = self.graph_model.get_all_network_nodes()
        ret = dict()
        for nid in node_id_list:
            n = self._get_node_by_id(nid)
            # exclude Facility nodes
            if n.type != NodeType.Facility:
                ret[n.name] = n
        return ViewOnlyDict(ret)

    def _list_network_services(self) -> ViewOnlyDict:
        """
        List all NetworkServices in the topology as a dictionary organized by name.
        Modifying the dictionary will not affect the underlying model, but modifying
        NetworkServices in the dictionary will.
        :return:
        """
        node_id_list = self.graph_model.get_all_network_service_nodes()
        ret = dict()
        for nid in node_id_list:
            n = self._get_ns_by_id(nid)
            ret[n.name] = n
        return ViewOnlyDict(ret)

    def _list_links(self) -> ViewOnlyDict:
        """
        List all Links in the topology as a dictionary organized by Link name.
        :return:
        """
        link_id_list = self.graph_model.get_all_network_links()
        ret = dict()
        for nid in link_id_list:
            n = self._get_link_by_id(nid)
            ret[n.name] = n
        return ViewOnlyDict(ret)

    def _list_of_interfaces(self) -> Tuple[Any]:
        """
        List all interfaces of the topology as a list.
        :return:
        """
        ret = list()
        for n in self.nodes.values():
            ret.extend(n.interface_list)
        return tuple(ret)

    @property
    def nodes(self):
        return self._list_nodes()

    @property
    def links(self):
        return self._list_links()

    @property
    def network_services(self):
        return self._list_network_services()

    @property
    def interface_list(self):
        return self._list_of_interfaces()

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

    def load(self, *, file_name: str = None, graph_string: str = None, new_graph_id: str = None):
        """
        Load the topology from file or string. It is possible to overwrite the graph id if
        loading from string (but not from file).
        :param file_name:
        :param graph_string:
        :param new_graph_id:
        :return:
        """
        if file_name is None and graph_string is None:
            raise TopologyException('Either file_name or graph_string parameters must be specified.')
        if file_name is not None:
            nx_pgraph = self.graph_model.importer.import_graph_from_file_direct(graph_file=file_name)
        else:
            if not new_graph_id:
                nx_pgraph = self.graph_model.importer.import_graph_from_string_direct(graph_string=graph_string)
            else:
                nx_pgraph = self.graph_model.importer.import_graph_from_string(graph_string=graph_string,
                                                                               graph_id=new_graph_id)
        if isinstance(self.graph_model.importer, NetworkXGraphImporter):
            self.graph_model = NetworkxASM(graph_id=nx_pgraph.graph_id,
                                           importer=nx_pgraph.importer,
                                           logger=nx_pgraph.log)
        else:
            self.graph_model = Neo4jASM(graph_id=nx_pgraph.graph_id,
                                        importer=nx_pgraph.importer,
                                        logger=nx_pgraph.log)

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
            lines.append(n.name + "[" + str(n.type) + ", " +
                         str(n.site) + "]:  " +
                         self.__print_caplabs__(n.capacities))
            for i in n.direct_interfaces.values():
                lines.append("\t\t" + i.name + ": " + str(i.type) + " " +
                             self.__print_caplabs__(i.capacities) + " " +
                             self.__print_caplabs__(i.labels))
            for c in n.components.values():
                lines.append("\t" + c.name + ": " + " " + str(c.type) + " " +
                             c.model)
                for i in c.interface_list:
                    lines.append("\t\t" + i.name + ": " + str(i.type) + " " +
                                 self.__print_caplabs__(i.capacities))
        lines.append("Links:")
        for l in self.links.values():
            interface_names = [iff.name for iff in l.interface_list]
            lines.append("\t" + l.name + "[" + str(l.type) + "]: " +
                         str(interface_names))
        lines.append("Network Services:")
        for ns in self.network_services.values():
            interface_names = [iff.name for iff in ns.interface_list]
            lines.append("\t" + ns.name + "[" + str(ns.type) + "]:" +
                         str(interface_names))

        return "\n".join(lines)

    @property
    def facilities(self) -> ViewOnlyDict or None:
        """
        Return facilities connected in this topology. Facilities should NOT be composite nodes in the ad.
        :return:
        """
        fac_ids = self.graph_model.get_all_nodes_by_class_and_type(label=ABCPropertyGraph.CLASS_NetworkNode,
                                                                   ntype=str(NodeType.Facility))
        if fac_ids is None:
            return None
        ret = dict()
        for nid in fac_ids:
            n = self._get_node_by_id(nid)
            ret[n.name] = n
        return ViewOnlyDict(ret)

    def validate(self):
        """
        Validate an experiment or a substrate topology. Throw an exception if rules
        are violated.
        :return:
        """
        # check nodes
        for n in self.nodes.values():
            n.validate_constraints()

        check_num_instances = set()
        # check network services, interfaces, sites
        for s in self.network_services.values():
            # check if the service type is one that requires num_instance per site validation
            if NetworkServiceSliver.ServiceConstraints[s.type].num_instances != NetworkServiceSliver.NO_LIMIT:
                # add this type into validation set for later
                check_num_instances.add(s.type)
            # perform other interface-based validations
            service_interfaces = s.interface_list
            node_interfaces = list()
            # some services like OVS have node ports, others like Bridge, STS, PTP
            # have ServicePorts which peer with node ports. Validation code needs
            # owning nodes for each interface so we search for proper interfaces
            for si in service_interfaces:
                if si.type == InterfaceType.ServicePort:
                    # there should only ever be one peer for a service port
                    peers = si.get_peers()
                    if peers is None or len(peers) != 1:
                        raise TopologyException(f'Interface {si} of Network Service {s} has unexpected '
                                                f'number of peer interfaces')
                    node_interfaces.append(si.get_peers()[0])
                else:
                    node_interfaces.append(si)
            s.validate_constraints(node_interfaces)

        # some constraints are for the entire model, like num_instances per site for NetworkServices
        for nstype in check_num_instances:
            # get services of this type in the model
            services_of_type = set()
            for s in self.network_services.values():
                if s.type == nstype:
                    services_of_type.add(s)
            # number of services of this type per site
            services_per_site = defaultdict(int)
            for s in services_of_type:
                if s.site:
                    services_per_site[s.site] += 1
                else:
                    for interface in s.interfaces:
                        owner = self.get_owner_node(interface)
                        if owner:
                            services_per_site[owner.site] += 1

            # raise exception if needed
            for site, count in services_per_site.items():
                if count > NetworkServiceSliver.ServiceConstraints[nstype].num_instances:
                    raise TopologyException(f"Services of type {nstype} cannot have more than "
                                            f"{NetworkServiceSliver.ServiceConstraints[nstype].num_instances} instances "
                                            f"in each site (site {site} violates that and has {count})")


class ExperimentTopology(Topology):
    """
    Define an user topology model, inheriting behavior from Topology class.
    In addition to publicly visible methods the following calls can be made:
    topology.nodes - a read-only dictionary of nodes in the topology
    topology.links - a read-only dictionary of links in the topology
    topology.interface_list - a read-only list of all interfaces of all nodes
    If you want to operate on top of a Neo4j graph, use the cast() method.
    """
    def __init__(self, graph_file: str = None, graph_string: str = None, logger=None, importer=None):
        super().__init__(graph_file=graph_file, graph_string=graph_string, logger=logger, importer=importer)

    def cast(self, *, asm_graph: ABCASMPropertyGraph):
        """
        'Cast' an existing instance of ASM graph into a topology. This can create Neo4j or NetworkX-based
        topology classes
        :param asm_graph:
        :return:
        """
        assert isinstance(asm_graph, ABCASMPropertyGraph)
        self.graph_model = asm_graph

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

            all_node_like = list(self.nodes.values())
            all_node_like.extend(self.facilities.values())
            # link interfaces of NSs and NSs to nodes
            for ns in self.network_services.values():
                for nint in ns.interface_list:
                    peer_int_ids = self.graph_model.find_peer_connection_points(node_id=nint.node_id)
                    if peer_int_ids is None:
                        continue
                    for peer_int_id in peer_int_ids:
                        _, peer_props = self.graph_model.get_node_properties(node_id=peer_int_id)
                        peer_int = Interface(node_id=peer_int_id, name=peer_props[ABCPropertyGraph.PROP_NAME],
                                             topo=self)
                        peer_int_parent = self.get_parent_element(peer_int)
                        if peer_int_parent is None:
                            continue

                        # Parent for a sub interface is Interface, get the parent again to get NetworkService
                        if peer_int.type == InterfaceType.SubInterface:
                            peer_int_parent = self.get_parent_element(peer_int_parent)

                            if peer_int_parent is None:
                                continue

                        derived_graph.add_edge(ns.name, peer_int_parent.name)
                for n in all_node_like:
                    if self.get_owner_node(ns) == n:
                        derived_graph.add_edge(ns.name, n.name)

            pos = layout(derived_graph)
            nx.draw_networkx(derived_graph, pos=pos)
            if not interactive:
                plt.show()
            if file_name is not None:
                plt.savefig(file_name)
        else:
            raise TopologyException("This level of detail not yet implemented")

    def add_port_mirror_service(self, *, name: str, node_id: str = None,
                                from_interface_name: str, to_interface: Interface, from_interface_vlan: str = None,
                                direction: MirrorDirection = MirrorDirection.Both,
                                **kwargs) -> PortMirrorService:
        """
        Add a network service to a topology. Interfaces can be specified upfront or added/removed later
        :param name:
        :param node_id:
        :param from_interface_name: name of the interface to mirror
        :param from_interface_vlan: vlan of the interface to mirror
        :param to_interface: node interface to mirror to
        :param direction:
        :param kwargs:
        :return:
        """
        ns = PortMirrorService(name=name, node_id=node_id, topo=self,
                               etype=ElementType.NEW, direction=direction,
                               from_interface_name=from_interface_name,
                               from_interface_vlan=from_interface_vlan,
                               to_interface=to_interface, **kwargs)
        return ns

    @staticmethod
    def _generate_set_of_diff_elements(elems, topo: Topology, elemClass):

        return {elemClass(name=x[ABCPropertyGraph.PROP_NAME],
                          node_id=x[ABCPropertyGraph.NODE_ID], topo=topo)
                for x in elems}

    @staticmethod
    def _is_parented_component(comp: Component, nodes: Set[Node]):
        """
        Is this component parented to any of the nodes?
        """
        if not nodes:
            return False
        parent_node = comp.topo.get_parent_element(comp)
        # so we can get early exit
        for n in nodes:
            if n.node_id == parent_node.node_id:
                return True
        return False

    @staticmethod
    def _is_parented_interface(intf: Interface, nss: Set[NetworkService]):
        """
        Is this Interface parented to the Network Service
        """
        if not nss:
            return False
        parent_ns = intf.topo.get_parent_element(intf)
        # so we can get early exit
        for ns in nss:
            if ns.node_id == parent_ns.node_id:
                return True
        return False

    @staticmethod
    def _is_parented_ns(ns: NetworkService, parents: Set[Node or Component]):
        """
        Is this Network Service parented to a node or component
        """
        if not parents:
            return False
        parent_node = ns.topo.get_parent_element(ns)
        if parent_node:
            # so we get early exit
            for n in parents:
                if n.node_id == parent_node.node_id:
                    return True
        return False

    @staticmethod
    def _exclude_parented_elements(nodes: Set[Node], nss: Set[NetworkService],
                                   components: Set[Component], interfaces: Set[Interface]):
        """
        for lists of graph nodes (AnotB or BnotA) exclude parented components,
        network services and interfaces
        - components listed as part of nodes should be excluded
        - nss listed as part of added nodes should be excluded
        - interfaces listed as part of added or excluded network services should also be excluded
        """

        excluded_components = {c for c in components if ExperimentTopology._is_parented_component(c, nodes)}
        excluded_nss = {ns for ns in nss if ExperimentTopology._is_parented_ns(ns, nodes.union(excluded_components))}
        excluded_interfaces = {i for i in interfaces if ExperimentTopology._is_parented_interface(i, nss.union(excluded_nss))}
        return nodes, nss - excluded_nss, components - excluded_components, interfaces - excluded_interfaces

    def _generate_list_of_modified_elements(self, other_topo: Topology, label: str, elemClass) -> List[Tuple[Any, WhatsModifiedFlag]]:
        """
        Generate list of tuples <element, WhatsModifiedFlag> for NetworkNodes, NetworkServices, Components and Interfaces.
        Note that elements are in reference to self topology.
        """
        ret = list()
        flags_dict = dict()
        # looks at Labels, Capacities and UserData
        graph_nodes, graph_nodes1 = self.graph_model.get_graph_property_diff(other_topo.graph_model, label)
        # sanity check
        assert len(graph_nodes) == len(graph_nodes1)
        # now need to generate flags and to avoid extra querying we compare property values returned by the query
        for n in zip(graph_nodes, graph_nodes1):
            # compare Labels, Capacities and UserData properties. This coupling to the query code which also
            # checks these properties is a bit unpleasant but avoids extra querying
            flags = WhatsModifiedFlag.NONE
            if n[0].get(ABCPropertyGraph.PROP_LABELS) != n[1].get(ABCPropertyGraph.PROP_LABELS):
                flags |= WhatsModifiedFlag.LABELS
            if n[0].get(ABCPropertyGraph.PROP_CAPACITIES) != n[1].get(ABCPropertyGraph.PROP_CAPACITIES):
                flags |= WhatsModifiedFlag.CAPACITIES
            if n[0].get(ABCPropertyGraph.PROP_USER_DATA) != n[1].get(ABCPropertyGraph.PROP_USER_DATA):
                flags |= WhatsModifiedFlag.USER_DATA
            # append a tuple <element, flags> to the list, notice that element is created in reference
            # to self topology, which is the original
            elem = elemClass(name=n[0][ABCPropertyGraph.PROP_NAME], node_id=n[0][ABCPropertyGraph.NODE_ID], topo=self)
            ret.append((elem, flags))

        return ret

    def diff(self, t) -> TopologyDiff:
        """
        Do a diff of two topologies assuming they are both in Neo4j (will not work with NetworkX backend)
        """
        nodes_diff = self.graph_model.get_graph_diff(t.graph_model, ABCPropertyGraph.CLASS_NetworkNode)
        ns_diff = self.graph_model.get_graph_diff(t.graph_model, ABCPropertyGraph.CLASS_NetworkService)
        component_diff = self.graph_model.get_graph_diff(t.graph_model, ABCPropertyGraph.CLASS_Component)
        interface_diff = self.graph_model.get_graph_diff(t.graph_model, ABCPropertyGraph.CLASS_ConnectionPoint)

        # convert to appropriate types to make easier to operate on
        # FIXME: Facility?
        nodes_removed = self._generate_set_of_diff_elements(nodes_diff[0], self, Node)
        nodes_added = self._generate_set_of_diff_elements(nodes_diff[1], t, Node)

        # FIXME: MirrorService?
        nss_removed = self._generate_set_of_diff_elements(ns_diff[0], self, NetworkService)
        nss_added = self._generate_set_of_diff_elements(ns_diff[1], t, NetworkService)

        components_removed = self._generate_set_of_diff_elements(component_diff[0], self, Component)
        components_added = self._generate_set_of_diff_elements(component_diff[1], t, Component)

        interfaces_removed = self._generate_set_of_diff_elements(interface_diff[0], self, Interface)
        interfaces_added = self._generate_set_of_diff_elements(interface_diff[1], t, Interface)

        nodes_added, nss_added, components_added, interfaces_added = \
            ExperimentTopology._exclude_parented_elements(nodes_added, nss_added,
                                                          components_added, interfaces_added)

        nodes_removed, nss_removed, components_removed, interfaces_removed = \
            ExperimentTopology._exclude_parented_elements(nodes_removed, nss_removed,
                                                          components_removed, interfaces_removed)

        # check for modified properties
        modified_nodes = self._generate_list_of_modified_elements(t,
                                                                  ABCPropertyGraph.CLASS_NetworkNode,
                                                                  Node)
        modified_nss = self._generate_list_of_modified_elements(t,
                                                                ABCPropertyGraph.CLASS_NetworkService,
                                                                NetworkService)
        modified_components = self._generate_list_of_modified_elements(t,
                                                                       ABCPropertyGraph.CLASS_Component,
                                                                       Component)
        modified_interfaces = self._generate_list_of_modified_elements(t,
                                                                       ABCPropertyGraph.CLASS_ConnectionPoint,
                                                                       Interface)

        return TopologyDiff(added=TopologyDiffTuple(nodes=nodes_added,
                                                    components=components_added,
                                                    services=nss_added,
                                                    interfaces=interfaces_added),
                            removed=TopologyDiffTuple(nodes=nodes_removed,
                                                      components=components_removed,
                                                      services=nss_removed,
                                                      interfaces=interfaces_removed),
                            modified=TopologyDiffModifiedTuple(
                                nodes=modified_nodes,
                                components=modified_components,
                                services=modified_nss,
                                interfaces=modified_interfaces
                            ))

    def _prune_node(self, node: Node):
        """
        Prune this node, its components, network services and interfaces as well as peer network
        service interface.
        """
        #self.graph_model.remove_network_node_with_components_nss_cps_and_links(node_id=node.node_id)
        self.remove_node(name=node.name)

    def _prune_ns(self, ns: NetworkService):
        """
        Prune this network service and its interfaces
        """
        self.graph_model.remove_ns_with_cps_and_links(node_id=ns.node_id)

    def _prune_components(self, c: Component, parent: Node):
        """
        Prune this component, its network services and interfaces as well as peer
        network service interfaces
        """
        #self.graph_model.remove_component_with_nss_cps_and_links(node_id=c.node_id)
        parent.remove_component(c.name)

    def _prune_interface(self, i: Interface):
        """
        Prune this interface
        """
        self.graph_model.remove_cp_and_links(node_id=i.node_id)

    def prune(self, reservation_state):
        """
        Prune the topology of any elements with reservation_info.reservation_state matching
        the provided.
        """
        #
        # for all nodes, network services, components and interfaces collect them
        #
        nodes = set()
        components = set()
        nss = set()
        seennss = set()
        interfaces = set()
        for n in self.nodes.values():
            nsl = n.get_sliver()
            if nsl.get_reservation_info() and \
                    nsl.get_reservation_info().reservation_state == reservation_state:
                nodes.add(n)
            for c in n.components.values():
                csl = c.get_sliver()
                if csl.get_reservation_info() and \
                        csl.get_reservation_info().reservation_state == reservation_state:
                    components.add((c, n))
                for ns in c.network_services.values():
                    seennss.add(ns)
                    nsl = ns.get_sliver()
                    if nsl.get_reservation_info() and \
                            nsl.get_reservation_info().reservation_state == reservation_state:
                        nss.add(ns)
                    for i in ns.interface_list:
                        isl = i.get_sliver()
                        if isl.get_reservation_info() and \
                                isl.get_reservation_info().reservation_state == reservation_state:
                            interfaces.add(i)

        # top level network services only, we visited others already
        for ns in self.network_services.values():
            if ns not in seennss:
                nsl = ns.get_sliver()
                if nsl.get_reservation_info() and \
                        nsl.get_reservation_info().reservation_state == reservation_state:
                    nss.add(ns)
                for i in ns.interface_list:
                    isl = i.get_sliver()
                    if isl.get_reservation_info() and \
                            isl.get_reservation_info().reservation_state == reservation_state:
                        interfaces.add(i)

        # all deletes are supposed to be idempotent
        for n in nodes:
            self._prune_node(n)

        # need parents too
        for c, n in components:
            self._prune_components(c, n)

        for ns in nss:
            self._prune_ns(ns)

        for i in interfaces:
            self._prune_interface(i)


class SubstrateTopology(Topology):
    """
    Define an substrate topology model, inheriting behavior from Topology class.
    In addition to publicly visible methods the following calls can be made:
    topology.nodes - a read-only dictionary of nodes in the topology
    topology.links - a read-only dictionary of links in the topology
    topology.interface_list - a read-only list of all interfaces of all nodes
    """

    def __init__(self, graph_file: str = None, graph_string: str = None, logger=None, importer=None):
        super().__init__(graph_file=graph_file, graph_string=graph_string, logger=logger, importer=importer)

    def as_arm(self):
        """
        Return model as ARM graph built on top of internal model. Model is not cloned or copied,
        rather recast into ARM, so any changes to the model propagate back to the topology.
        :return:
        """
        if isinstance(self.graph_model, NetworkxASM):
            return NetworkXARMGraph(graph=self.graph_model,
                                    logger=self.graph_model.log)
        else:
            return Neo4jARMGraph(graph=self.graph_model,
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
                    for i in c.interface_list:
                        delegations = self.__copy_to_delegations(e=i, atype=t,
                                                                 delegation_id=delegation_id)
                        if delegations is not None:
                            delegations_dicts[t][i.node_id] = delegations
                # network services (for eg switches and facilities)
                for sf in n.network_services.values():
                    delegations = self.__copy_to_delegations(e=sf, atype=t,
                                                             delegation_id=delegation_id)
                    if delegations is not None:
                        delegations_dicts[t][sf.node_id] = delegations
                    for i in sf.interface_list:
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
    topology.sites - a read-only dictionary of sites in the topology
    topology.nodes - a read-only dictionary of nodes
    topology.links - a read-only dictionary of links in the topology
    topology.facilities - a read-only dictionary of facilities
    """

    def __init__(self, graph_file: str = None, graph_string: str = None, logger=None):

        self.graph_model = NetworkXAggregateBQM(graph_id=str(uuid.uuid4()),
                                                importer=NetworkXGraphImporter(logger=logger),
                                                logger=logger)
        if graph_file is not None or graph_string is not None:
            self.load(file_name=graph_file, graph_string=graph_string)

    def add_node(self, *, name: str, node_id: str = None, site: str, ntype: NodeType = NodeType.VM,
                 **kwargs) -> Node:
        raise TopologyException('Cannot add node to advertisement')

    def add_link(self, *, name: str, node_id: str = None, ltype: LinkType = None,
                 interfaces: List[Interface], layer: NSLayer = None, technology: str = None,
                 **kwargs) -> Link:
        raise TopologyException('Cannot add link to advertisement')

    def load(self, *, file_name: str = None, graph_string: str = None):
        """
        Load the BQM (query model) topology from file or string
        :param file_name:
        :param graph_string:
        :return:
        """
        if file_name is None and graph_string is None:
            raise TopologyException('Either file_name or graph_string must be specified.')
        if file_name is not None:
            nx_pgraph = self.graph_model.importer.import_graph_from_file_direct(graph_file=file_name)
        else:
            nx_pgraph = self.graph_model.importer.import_graph_from_string_direct(graph_string=graph_string)
        self.graph_model = NetworkXABQMFactory.create(nx_pgraph)

    def _get_node_by_id(self, node_id: str) -> Node:
        """
        Get node by its node_id, return Node or CompositeNode object
        :param node_id:
        :return:
        """
        claz, node_props = self.graph_model.get_node_properties(node_id=node_id)
        if claz[0] == ABCPropertyGraph.CLASS_CompositeNode:
            return CompositeNode(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, topo=self)
        elif claz[0] == ABCPropertyGraph.CLASS_NetworkNode:
            return Node(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, topo=self)

    def _get_link_by_id(self, node_id: str) -> Link:
        """
        Get link by its node_id, return Link object
        :param node_id:
        :return:
        """
        _, node_props = self.graph_model.get_node_properties(node_id=node_id)
        return Link(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, topo=self)

    def __list_sites(self) -> ViewOnlyDict:
        """
        List site information
        :return:
        """
        node_id_list = self.graph_model.get_all_composite_nodes()
        ret = dict()
        for nid in node_id_list:
            n = self._get_node_by_id(nid)
            ret[n.name] = n
        return ViewOnlyDict(ret)

    def _list_links(self) -> ViewOnlyDict:
        link_id_list = self.graph_model.get_all_network_links()
        ret = dict()
        for nid in link_id_list:
            n = self._get_link_by_id(nid)
            ret[n.name] = n
        return ViewOnlyDict(ret)

    @property
    def sites(self):
        return self.__list_sites()

    @property
    def nodes(self):
        """
        Same as sites property
        :return:
        """
        return self.__list_sites()

    @property
    def links(self):
        return self._list_links()

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

            derived_graph = nx.Graph()
            for n in network_sites:
                _, props = self.graph_model.get_node_properties(node_id=n)
                derived_graph.add_node(props[ABCPropertyGraph.PROP_NAME])

            # build two-element lists of which nodes should be connected by edges
            # indexed by link name
            graph_edges = defaultdict(list)
            all_node_like = list(self.sites.values())
            all_node_like.extend(self.facilities.values())
            for n in all_node_like:
                for nint in n.interface_list:
                    for l in self.links.values():
                        # this works because of custom ModelElement.__eq__()
                        if nint in l.interface_list:
                            graph_edges[l.name].append(n.name)

            edge_labels = dict()
            for k, v in graph_edges.items():
                if len(v) >= 2:
                    derived_graph.add_edge(v[0], v[1])
                    # edge_labels[(v[0], v[1])] = k
                    edge_labels[(v[0], v[1])] = ""
                else:
                    print(f'WARNING: unable to find a peer interface for {v[0]}, proceeding')

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
        if self.sites:
            for n in self.sites.values():
                tot_cap = n.capacities
                alloc_cap = n.capacity_allocations
                if tot_cap is not None:
                    ncp = FreeCapacity(total=tot_cap, allocated=alloc_cap)
                    lines.append(n.name + " [Site] : " + str(ncp))
                else:
                    lines.append(n.name + " [Site]")
                lines.append("\tComponents:")
                for c in n.components.values():
                    ccp = FreeCapacity(total=c.capacities,
                                       allocated=c.capacity_allocations)
                    lines.append("\t\t" + c.name + ": " + " " + str(c.get_property("type")) + " " +
                                 c.model + " " + str(ccp))
                lines.append("\tSite Interfaces:")
                for i in n.interface_list:
                    if i.capacities is not None:
                        icp = FreeCapacity(total=i.capacities,
                                           allocated=i.capacity_allocations)
                        lines.append("\t\t" + i.name + ": " + str(i.get_property("type")) + " " +
                                    str(icp))
        if self.facilities:
            for fp in self.facilities.values():
                lines.append(fp.name + " [Facility]")
                lines.append("\tFacility Interfaces:")
                for i in fp.interface_list:
                    if i.capacities is not None:
                        icp = FreeCapacity(total=i.capacities,
                                           allocated=i.capacity_allocations)
                        lines.append("\t\t" + i.name + ": " + str(i.get_property("type")) + " " +
                                    str(icp) + " " + self.__print_caplabs__(i.labels))

        if self.links:
            lines.append("Links:")
            for l in self.links.values():
                interface_names = [iff.name for iff in l.interface_list]
                lines.append("\t" + l.name + "[" + str(l.type) + "]: " +
                             str(interface_names))

        return "\n".join(lines)
