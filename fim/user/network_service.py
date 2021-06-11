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
from typing import Tuple, Any, List

import uuid

from fim.view_only_dict import ViewOnlyDict

from .model_element import ModelElement, ElementType

from fim.graph.abc_property_graph import ABCPropertyGraph
from fim.user.interface import Interface, InterfaceType
from fim.user.link import Link, LinkType
from fim.slivers.network_service import NetworkServiceSliver, ServiceType


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
                raise RuntimeError("When creating new services you must specify ServiceType")
            # cant use isinstance as it would create circular import dependencies
            # We do more careful checks for ExperimentTopologies, but for substrate we let things loose
            if str(self.topo.__class__) == "<class 'fim.user.topology.ExperimentTopology'>":
                if interfaces is None or len(interfaces) == 0 or (not isinstance(interfaces, tuple) and
                                                                  not isinstance(interfaces, list)):
                    raise RuntimeError("When creating new services in ExperimentTopology you "
                                       "must specify the list of interfaces to connect.")
                # check the number of instances of this service
                if NetworkServiceSliver.ServiceConstraints[nstype].num_instances != NetworkServiceSliver.NO_LIMIT:
                    services = topo.graph_model.get_all_nodes_by_class_and_type(label=ABCPropertyGraph.CLASS_NetworkService,
                                                                                ntype=str(nstype))
                    if len(services) + 1 > NetworkServiceSliver.ServiceConstraints[nstype].num_instances:
                        raise RuntimeError(f"Service type {nstype} cannot have {len(services) + 1} instances. "
                                           f"Limit: {NetworkServiceSliver.ServiceConstraints[nstype].num_instances}")
                # check the number of interfaces
                if NetworkServiceSliver.ServiceConstraints[nstype].num_interfaces != NetworkServiceSliver.NO_LIMIT:
                    if len(interfaces) > NetworkServiceSliver.ServiceConstraints[nstype].num_interfaces:
                        raise RuntimeError(f"Service of type {nstype} cannot have {len(interfaces)} interfaces. "
                                           f"Limit: {NetworkServiceSliver.ServiceConstraints[nstype].num_interfaces}")
                # check the number of sites spanned by this service
                if NetworkServiceSliver.ServiceConstraints[nstype].num_sites != NetworkServiceSliver.NO_LIMIT:
                    # trace ownership of each interface and count the sites involved
                    sites = set()
                    for interface in interfaces:
                        owner = topo.get_owner_node(interface)
                        sites.add(owner.get_property('site'))
                    if len(sites) > NetworkServiceSliver.ServiceConstraints[nstype].num_sites:
                        raise RuntimeError(f"Service of type {nstype} cannot span {len(sites)} sites. "
                                           f"Limit: {NetworkServiceSliver.ServiceConstraints[nstype].num_sites}.")
                    # set site property for  services that only are in one site
                    if NetworkServiceSliver.ServiceConstraints[nstype].num_sites == 1:
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
                    self.connect_interface(interface=i)
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            # check that this node exists
            existing_node_id = self.topo.\
                graph_model.find_node_by_name(node_name=name,
                                              label=ABCPropertyGraph.CLASS_NetworkService)
            if existing_node_id != node_id:
                raise RuntimeError(f'Service name {name} node id does not match the expected node id.')
            # collect a list of interface nodes it attaches to
            interface_list = self.topo.graph_model.get_all_ns_or_link_connection_points(link_id=self.node_id)
            name_id_tuples = list()
            # need to look up their names - a bit inefficient, need to think about this /ib
            for iff in interface_list:
                _, props = self.topo.graph_model.get_node_properties(node_id=iff)
                name_id_tuples.append((props[ABCPropertyGraph.PROP_NAME], iff))
            self._interfaces = [Interface(node_id=tup[1], topo=topo, name=tup[0]) for tup in name_id_tuples]

    def connect_interface(self, *, interface: Interface):
        """
        Connect a (compute or switch) node interface to network service by transparently
        creating a peer service interface and a link between them
        :param interface
        :return:
        """
        assert interface is not None
        assert isinstance(interface, Interface)

        # we can only connect interfaces connected to (compute or switch) nodes
        if self.topo.get_owner_node(interface) is None:
            raise RuntimeError(f'Interface {interface} is not owned by a node, as expected.')
        # we can only connect interfaces that aren't already connected
        peer_id = self.topo.graph_model.find_peer_connection_point(node_id=interface.node_id)
        if peer_id is not None:
            raise RuntimeError(f'Interface {interface} is already connected to another service.')
        # create a peer interface, create a link between them
        peer_if = Interface(name=self.name + '-' + interface.name, parent_node_id=self.node_id,
                            etype=ElementType.NEW, topo=self.topo, itype=InterfaceType.ServicePort)
        # link type is determined by the type of interface = L2Path for shared, Patch for Dedicated
        if interface.get_property('type') == InterfaceType.SharedPort:
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

        # find parent network service
        owner = self.topo.get_parent_element(interface)
        # find id of the interface node
        interface_node_id = self.topo.graph_model.find_connection_point_by_name(parent_node_id=owner.node_id,
                                                                                iname=interface.name)
        node_id = self.topo.graph_model.find_peer_connection_point(node_id=interface_node_id)
        if node_id is None:
            return

        self.topo.graph_model.remove_cp_and_links(node_id=node_id)
        # remove from interfaces list as well
        to_remove = None
        for i in self._interfaces:
            if i.node_id == node_id:
                to_remove = i
        if to_remove is not None:
            self._interfaces.remove(to_remove)

    def add_interface(self, *, name: str, node_id: str = None, itype: InterfaceType = InterfaceType.TrunkPort,
                      **kwargs):
        """
        Add an interface to node (mostly needed in substrate topologies)
        :param name:
        :param node_id:
        :param itype: interface type e.g. TrunkPort, AccessPort or VINT
        :param kwargs: additional parameters
        :return:
        """
        assert name is not None
        # cant use isinstance as it would create circular import dependencies
        if str(self.topo.__class__) == "<class 'fim.user.topology.ExperimentTopology'>":
            raise RuntimeError("Do not need to add interface to NetworkService in Experiment topology")

        # check uniqueness
        if name in self.__list_interfaces().keys():
            raise RuntimeError('Interface names must be unique within a switch fabric')
        iff = Interface(name=name, node_id=node_id, parent_node_id=self.node_id,
                        etype=ElementType.NEW, topo=self.topo, itype=itype,
                        **kwargs)
        return iff

    def remove_interface(self, *, name: str) -> None:
        """
        Remove an interface from the switch fabric, disconnect from links (in substrate topologies). Remove links
        if they have nothing else connecting to them.
        :param name:
        :return:
        """
        assert name is not None
        # cant use isinstance as it would create circular import dependencies
        if str(self.topo.__class__) == "<class 'fim.user.topology.ExperimentTopology'>":
            raise RuntimeError("Cannot remove interface from NetworkService in Experiment topology")
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
        if_sliver = self.topo.graph_model.network_service_sliver_from_graph_properties_dict(node_properties)
        return if_sliver.get_property(pname)

    def set_property(self, pname: str, pval: Any):
        """
        Set a service property
        :param pname:
        :param pval:
        :return:
        """
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

    def __getattr__(self, item):
        """
        Special handling for attributes like 'nodes' and 'links' -
        which query into the model. They return dicts and list
        containers. Modifying containers does not affect the underlying
        graph mode, but modifying elements of lists or values of dicts does.
        :param item:
        :return:
        """

        if item == 'interface_list':
            return self.__list_of_interfaces()
        if item == 'interfaces':
            return self.__list_interfaces()

        raise RuntimeError(f'Attribute {item} not available')

    def __repr__(self):
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        service_sliver = self.topo.graph_model.network_service_sliver_from_graph_properties_dict(node_properties)
        interface_names = [iff.name for iff in self._interfaces]
        return service_sliver.__repr__() + str(interface_names)

    def __str__(self):
        return self.__repr__()