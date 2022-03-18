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
import logging
from typing import Tuple, Any, List, Set

import uuid

from fim.view_only_dict import ViewOnlyDict

from .model_element import ModelElement, ElementType, TopologyException

from fim.graph.abc_property_graph import ABCPropertyGraph
from fim.user.interface import Interface, InterfaceType
from fim.user.link import Link, LinkType
from fim.slivers.network_service import NetworkServiceSliver, ServiceType, NSLayer, ERO, PathInfo, MirrorDirection
from fim.slivers.gateway import Gateway


class NetworkService(ModelElement):
    """
    A network service object in a topology that can pass packets between interfaces.
    Unlike a link, network service owns its interfaces. Typical topology fragment is
    component - network service - interface - link - interface - network service
    In addition to public methods the following calls
    return various dictionaries or lists:
    service.interface_list - a list of interfaces attached to this service
    """
    def __init__(self, *, name: str, node_id: str = None, topo: Any,
                 etype: ElementType = ElementType.EXISTING,
                 parent_node_id: str = None,
                 interfaces: List[Interface] = None,
                 nstype: ServiceType = None, technology: str = None,
                 **kwargs):
        """
        Don't call this method yourself, call topology.add_network_service()
        node_id will be generated if not provided for experiment topologies

        :param name:
        :param node_id:
        :param topo:
        :param etype: is this supposed to exist or new should be created
        :param parent_node_id: node_id of the parent Node if any (for new components)
        :param interfaces: list of interface objects to connect
        :param nstype: service type if new
        :param technology: service technology
        :param kwargs: any additional properties
        """
        assert name is not None
        assert topo is not None

        site = None
        if etype == ElementType.NEW:
            # node id myst be specified for new nodes in substrate topologies
            if node_id is None:
                node_id = str(uuid.uuid4())
            super().__init__(name=name, node_id=node_id, topo=topo)
            if nstype is None:
                raise TopologyException("When creating new services you must specify ServiceType")
            # cant use isinstance as it would create circular import dependencies
            # We do more careful checks for ExperimentTopologies, but for substrate we let things loose
            if str(self.topo.__class__) == "<class 'fim.user.topology.ExperimentTopology'>" and interfaces:
                sites = self.__validate_nstype_constraints(nstype, interfaces)

                # if a single-site service
                if len(sites) == 1:
                    site = sites.pop()

            sliver = NetworkServiceSliver()
            sliver.node_id = self.node_id
            sliver.set_name(self.name)
            sliver.set_type(nstype)
            sliver.set_site(site)
            # set based on service type
            sliver.set_layer(NetworkServiceSliver.ServiceConstraints[nstype].layer)
            sliver.set_technology(technology)
            sliver.set_properties(**kwargs)
            self.topo.graph_model.add_network_service_sliver(parent_node_id=parent_node_id, network_service=sliver)
            self._interfaces = list()
            if interfaces is not None and len(interfaces) > 0:
                for i in interfaces:
                    # run through guardrails, then connect
                    self.__service_guardrails(sliver, i)
                    self.__connect_interface(interface=i)
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            # check that this node exists
            existing_node_id = self.topo.\
                graph_model.find_node_by_name(node_name=name,
                                              label=ABCPropertyGraph.CLASS_NetworkService)
            if existing_node_id != node_id:
                raise TopologyException(f'Service name {name} node id does not match the expected node id.')
            # collect a list of interface nodes it attaches to
            interface_list = self.topo.graph_model.get_all_ns_or_link_connection_points(link_id=self.node_id)
            name_id_tuples = list()
            # need to look up their names - a bit inefficient, need to think about this /ib
            for iff in interface_list:
                _, props = self.topo.graph_model.get_node_properties(node_id=iff)
                name_id_tuples.append((props[ABCPropertyGraph.PROP_NAME], iff))
            self._interfaces = [Interface(node_id=tup[1], topo=topo, name=tup[0]) for tup in name_id_tuples]

    @property
    def type(self):
        return self.get_property('type') if self.__dict__.get('topo', None) is not None else None

    @property
    def site(self):
        return self.get_property('site') if self.__dict__.get('topo', None) is not None else None

    @site.setter
    def site(self, value: str):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('site', value)

    @property
    def technology(self):
        return self.get_property('technology') if self.__dict__.get('topo', None) is not None else None

    @property
    def layer(self):
        return self.get_property('layer') if self.__dict__.get('topo', None) is not None else None

    @property
    def controller_url(self):
        return self.get_property('controller_url') if self.__dict__.get('topo', None) is not None else None

    @controller_url.setter
    def controller_url(self, value: str):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('controller_url', value)

    @property
    def ero(self):
        return self.get_property('ero') if self.__dict__.get('topo', None) is not None else None

    @ero.setter
    def ero(self, value: ERO):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('ero', value)

    @property
    def path_info(self):
        return self.get_property('path_info') if self.__dict__.get('topo', None) is not None else None

    @path_info.setter
    def path_info(self, value: PathInfo):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('path_info', value)

    @property
    def gateway(self):
        return self.get_property('gateway') if self.__dict__.get('topo', None) is not None else None

    @gateway.setter
    def gateway(self, gateway: Gateway):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('gateway', gateway)

    def get_sliver(self) -> NetworkServiceSliver:
        """
        Get a deep sliver representation of this node from graph
        :return:
        """
        return self.topo.graph_model.build_deep_ns_sliver(node_id=self.node_id)

    def __validate_nstype_constraints(self, nstype, interfaces) -> Set[str]:
        """
        Validate service constraints as encoded for each services (number of interfaces, instances, sites).
        Note that interfaces is a list of interfaces belonging to nodes!
        :param nstype:
        :param interfaces:
        :return: a list of sites the service covers
        """

        # check the number of instances of this service
        if NetworkServiceSliver.ServiceConstraints[nstype].num_instances != NetworkServiceSliver.NO_LIMIT:
            services = self.topo.graph_model.get_all_nodes_by_class_and_type(label=ABCPropertyGraph.CLASS_NetworkService,
                                                                             ntype=str(nstype))
            if len(services) + 1 > NetworkServiceSliver.ServiceConstraints[self.type].num_instances:
                raise TopologyException(f"Service type {nstype} cannot have {len(services) + 1} instances. "
                                        f"Limit: {NetworkServiceSliver.ServiceConstraints[nstype].num_instances}")
        # check the number of interfaces
        if NetworkServiceSliver.ServiceConstraints[nstype].num_interfaces != NetworkServiceSliver.NO_LIMIT:
            if len(interfaces) > NetworkServiceSliver.ServiceConstraints[nstype].num_interfaces:
                raise TopologyException(f"Service of type {nstype} cannot have {len(interfaces)} interfaces. "
                                        f"Limit: {NetworkServiceSliver.ServiceConstraints[nstype].num_interfaces}")
        sites = set()
        # check the number of sites spanned by this service
        if NetworkServiceSliver.ServiceConstraints[nstype].num_sites != NetworkServiceSliver.NO_LIMIT:
            # trace ownership of each interface and count the sites involved
            for interface in interfaces:
                owner = self.topo.get_owner_node(interface)
                if owner is None:
                    print(f'Interface {interface=} has no owner')
                sites.add(owner.site)

            if len(sites) > NetworkServiceSliver.ServiceConstraints[nstype].num_sites:
                raise TopologyException(f"Service of type {nstype} cannot span {len(sites)} sites. "
                                        f"Limit: {NetworkServiceSliver.ServiceConstraints[nstype].num_sites}.")
        return sites

    def validate_constraints(self, interfaces):
        """
        Validate service constraints - number of sites, interfaces, instances, properties
        """

        nstype = self.type
        self.__validate_nstype_constraints(nstype, interfaces)

        # check properties
        req_props = NetworkServiceSliver.ServiceConstraints[nstype].required_properties
        forb_props = NetworkServiceSliver.ServiceConstraints[nstype].forbidden_properties
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        ns_sliver = self.topo.graph_model.network_service_sliver_from_graph_properties_dict(node_properties)
        for rp in req_props:
            if not ns_sliver.get_property(rp):
                raise TopologyException(f"Service of type {nstype} must have property {rp} set")
        for fp in forb_props:
            if ns_sliver.get_property(fp):
                raise TopologyException(f"Service of type {nstype} must NOT have property {fp} set")

        # check interface types that are required to attach
        rit = NetworkServiceSliver.ServiceConstraints[nstype].required_interface_types
        if len(rit) > 0:
            for i in interfaces:
                if not i.type in rit:
                    raise TopologyException(f"Service of type {nstype} must use one of the following interface types:"
                                            f"{rit} instead of {i.type}")

    @staticmethod
    def __service_guardrails(sliver: NetworkServiceSliver, interface: Interface):
        """
        Checks if this interface can be added to this service for various reasons related to e.g.
        service implementation constraints (that can be temporary and change from release to release).
        :param sliver:
        :param interface:
        :return:
        """
        # - L2P2P service does not work for shared ports
        # - L2S2S needs to warn that it may not work if the VMs with shared ports land on the same worker
        if sliver.get_type() == ServiceType.L2PTP and \
            interface.type == InterfaceType.SharedPort:
            raise TopologyException(f"Unable to connect interface {interface.name} to service {sliver.get_name()}: "
                                    f"L2P2P service currently doesn't support shared interfaces")

    def __connect_interface(self, *, interface: Interface):
        """
        Connect a (compute or switch) node interface to network service by transparently
        creating a peer service interface and a link between them
        :param interface
        :return:
        """
        assert interface is not None
        assert isinstance(interface, Interface)

        # we can only connect interfaces connected to (compute or switch) nodes,
        parent = self.topo.get_owner_node(interface)
        if parent is None:
            raise TopologyException(f'Interface {interface} is not owned by a node, as expected.')
        # we can only connect interfaces that aren't already connected
        peer_ids = self.topo.graph_model.find_peer_connection_points(node_id=interface.node_id)
        if peer_ids is not None:
            raise TopologyException(f'Interface {interface} is already connected to another service.')
        # create a peer interface, create a link between them
        peer_if = Interface(name='-'.join([parent.name, interface.name]),
                            parent_node_id=self.node_id,
                            etype=ElementType.NEW, topo=self.topo, itype=InterfaceType.ServicePort)
        # link type is determined by the type of interface = L2Path for shared, Patch for Dedicated
        if interface.type == InterfaceType.SharedPort:
            ltype = LinkType.L2Path
        else:
            ltype = LinkType.Patch

        peer_link = Link(name=peer_if.name + '-link', topo=self.topo, etype=ElementType.NEW,
                         interfaces=[interface, peer_if], ltype=ltype)
        self._interfaces.append(peer_if)

    def disconnect_interface(self, *, interface: Interface) -> None:
        """
        Disconnect a node interface from the network service.
        Transparently remove peer service interface and link between them.
        :param interface:
        :return:
        """
        assert interface is not None

        peers = interface.get_peers()
        if peers is None or len(peers) == 0:
            return

        if len(peers) > 1:
            raise TopologyException(f'List of ServicePort peers for interface {interface} is more than one')

        self.topo.graph_model.remove_cp_and_links(node_id=peers[0].node_id)
        # remove from interface list as well
        self._interfaces = list(filter((lambda x: x.node_id != peers[0].node_id), self._interfaces))

    def add_interface(self, *, name: str, node_id: str = None, itype: InterfaceType = InterfaceType.TrunkPort,
                      **kwargs):
        """
        Add an interface to network service
        :param name:
        :param node_id:
        :param itype: interface type e.g. TrunkPort, AccessPort or VINT
        :param kwargs: additional parameters
        :return:
        """
        assert name is not None

        # check uniqueness
        if name in self.__list_interfaces().keys():
            raise TopologyException('Interface names must be unique within a switch fabric')
        iff = Interface(name=name, node_id=node_id, parent_node_id=self.node_id,
                        etype=ElementType.NEW, topo=self.topo, itype=itype,
                        **kwargs)
        return iff

    def remove_interface(self, *, name: str) -> None:
        """
        Remove an ServicePort interface from the network service.
        :param name:
        :return:
        """
        assert name is not None
        # cant use isinstance as it would create circular import dependencies
        if str(self.topo.__class__) == "<class 'fim.user.topology.ExperimentTopology'>":
            raise TopologyException("Cannot remove interface from NetworkService in Experiment topology")
        node_id = self.topo.graph_model.find_connection_point_by_name(parent_node_id=self.node_id,
                                                                      iname=name)
        self.topo.graph_model.remove_cp_and_links(node_id=node_id)

    def get_property(self, pname: str) -> Any:
        """
        Retrieve a service property
        :param pname:
        :return:
        """
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        ns_sliver = self.topo.graph_model.network_service_sliver_from_graph_properties_dict(node_properties)
        return ns_sliver.get_property(pname)

    def set_property(self, pname: str, pval: Any):
        """
        Set a service property or unset of pval is None
        :param pname:
        :param pval:
        :return:
        """
        if pval is None:
            self.unset_property(pname)
            return
        service_sliver = NetworkServiceSliver()
        service_sliver.set_property(prop_name=pname, prop_val=pval)
        # write into the graph
        prop_dict = self.topo.graph_model.network_service_sliver_to_graph_properties_dict(service_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    def set_properties(self, **kwargs):
        """
        Set multiple properties of the service
        :param kwargs:
        :return:
        """
        service_sliver = NetworkServiceSliver()
        service_sliver.set_properties(**kwargs)
        # write into the graph
        prop_dict = self.topo.graph_model.network_service_sliver_to_graph_properties_dict(service_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    @staticmethod
    def list_properties() -> Tuple[str]:
        return NetworkServiceSliver.list_properties()

    def __get_interface_by_id(self, node_id: str) -> Interface:
        """
        Get an interface of network service by its node_id, return Interface object
        :param node_id:
        :return:
        """
        assert node_id is not None
        _, node_props = self.topo.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        return Interface(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id,
                         topo=self.topo)

    def __get_interface_by_name(self, name: str) -> Interface:
        """
        Get an interface of network service by its name
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.topo.graph_model.find_connection_point_by_name(parent_node_id=self.node_id,
                                                                      iname=name)
        return Interface(name=name, node_id=node_id, topo=self.topo)

    def __list_interfaces(self) -> ViewOnlyDict:
        """
        List all interfaces of the network service as a dictionary
        :return:
        """
        node_id_list = self.topo.graph_model.get_all_ns_or_link_connection_points(link_id=self.node_id)
        ret = dict()
        for nid in node_id_list:
            c = self.__get_interface_by_id(nid)
            ret[c.name] = c
        return ViewOnlyDict(ret)

    def __list_of_interfaces(self) -> Tuple[Interface]:
        """
        Return a list of all interfaces of network service
        :return:
        """
        return tuple(self._interfaces)

    @property
    def interface_list(self):
        return self.__list_of_interfaces()

    @property
    def interfaces(self):
        return self.__list_interfaces()

    def __repr__(self):
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        service_sliver = self.topo.graph_model.network_service_sliver_from_graph_properties_dict(node_properties)
        interface_names = [iff.name for iff in self._interfaces]
        return service_sliver.__repr__() + str(interface_names)

    def __str__(self):
        return self.__repr__()


class PortMirrorService(NetworkService):
    """
    PortMirroring service is special because interfaces in it aren't equal.
    There is the mirrored interface and there is a mirrored-to interface.
    Also it is not typically defined as part of ARMs, CBMs or (A)BQMs.
    """

    def __init__(self, *, name: str, node_id: str = None, topo: Any,
                 etype: ElementType = ElementType.EXISTING,
                 parent_node_id: str = None, direction: MirrorDirection = MirrorDirection.Both,
                 from_interface_name: str = None, to_interface: Interface = None,
                 **kwargs):
        if etype == ElementType.NEW:
            assert to_interface
            assert from_interface_name

            # only the 'to_interface' is actually connected to the service
            # the 'from_interface' is connected to something else
            # to_interface has to be a full-rate interface

            # make sure that to_interface is a DedicatedPort
            if to_interface.type != InterfaceType.DedicatedPort:
                raise TopologyException(f'Adding PortMirrorService {name} failed - only dedicated '
                                        f'ports belonging to SmartNICs can be attached.')
            super().__init__(name=name, node_id=node_id, topo=topo, etype=etype,
                             parent_node_id=parent_node_id, interfaces=[to_interface],
                             nstype=ServiceType.PortMirror, technology=None,
                             mirror_port=from_interface_name, mirror_direction=direction,
                             **kwargs)
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            # check that this node exists
            existing_node_id = self.topo.\
                graph_model.find_node_by_name(node_name=name,
                                              label=ABCPropertyGraph.CLASS_NetworkService)
            if existing_node_id != node_id:
                raise TopologyException(f'Service name {name} node id does not match the expected node id.')
            # collect a list of interface nodes it attaches to
            interface_list = self.topo.graph_model.get_all_ns_or_link_connection_points(link_id=self.node_id)
            name_id_tuples = list()
            # need to look up their names - a bit inefficient, need to think about this /ib
            for iff in interface_list:
                _, props = self.topo.graph_model.get_node_properties(node_id=iff)
                name_id_tuples.append((props[ABCPropertyGraph.PROP_NAME], iff))
            self._interfaces = [Interface(node_id=tup[1], topo=topo, name=tup[0]) for tup in name_id_tuples]

    @property
    def mirror_port(self):
        return self.get_property('mirror_port') if self.__dict__.get('topo', None) is not None else None

    @property
    def mirror_direction(self):
        return self.get_property('mirror_direction') if self.__dict__.get('topo', None) is not None else None
