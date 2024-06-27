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
from collections import defaultdict

import uuid

import fim.user.topology
from fim.view_only_dict import ViewOnlyDict

from .model_element import ModelElement, ElementType, TopologyException

from fim.graph.abc_property_graph import ABCPropertyGraph
from fim.user.interface import Interface, InterfaceType
from fim.user.link import Link, LinkType
from fim.slivers.network_service import NetworkServiceSliver, ServiceType, NSLayer, ERO, PathInfo, MirrorDirection
from fim.slivers.gateway import Gateway
from fim.slivers.capacities_labels import Labels


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
                 check_existing: bool = False,
                 site: str = None,
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
        :param check_existing: check if Network Service exists in the graph
        :param kwargs: any additional properties
        """
        assert name is not None
        assert topo is not None

        if etype == ElementType.NEW:
            # node id myst be specified for new nodes in substrate topologies
            if node_id is None:
                node_id = str(uuid.uuid4())
            super().__init__(name=name, node_id=node_id, topo=topo)
            if nstype is None:
                raise TopologyException("When creating new services you must specify ServiceType")

            sliver = NetworkServiceSliver()
            sliver.node_id = self.node_id
            sliver.set_name(self.name)
            sliver.set_type(nstype)
            # set based on service type
            sliver.set_layer(NetworkServiceSliver.ServiceConstraints[nstype].layer)
            sliver.set_technology(technology)
            sliver.set_properties(**kwargs)
            sliver.set_site(site)
            self.topo.graph_model.add_network_service_sliver(parent_node_id=parent_node_id, network_service=sliver)
            self._interfaces = list()

            if interfaces is not None and len(interfaces) > 0:
                connected_interfaces = list()
                for i in interfaces:
                    # run through guardrails, then connect
                    try:
                        self.__service_guardrails(sliver, i)
                        self.connect_interface(interface=i)
                        connected_interfaces.append(i)
                    except TopologyException as e:
                        # disconnect previously connected interfaces
                        for ii in connected_interfaces:
                            self.disconnect_interface(ii)
                        # remove sliver from the graph
                        self.topo.graph_model.remove_ns_with_cps_and_links(node_id=self.node_id)
                        # re-throw the exception
                        raise TopologyException(str(e))
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            if check_existing:
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

    @property
    def mirror_port(self):
        return self.get_property('mirror_port') if self.__dict__.get('topo', None) is not None else None

    @mirror_port.setter
    def mirror_port(self, value):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('mirror_port', value)

    @property
    def mirror_vlan(self):
        return self.get_property('mirror_vlan') if self.__dict__.get('topo', None) is not None else None

    @mirror_vlan.setter
    def mirror_vlan(self, value):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('mirror_vlan', value)

    @property
    def mirror_direction(self):
        return self.get_property('mirror_direction') if self.__dict__.get('topo', None) is not None else None

    @mirror_direction.setter
    def mirror_direction(self, value):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('mirror_direction', value)

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

    def __validate_nstype_constraints(self, nstype, interfaces):
        """
        Validate service constraints as encoded for each services (number of interfaces, instances, sites).
        Note that interfaces is a list of interfaces belonging to nodes!
        :param nstype:
        :param interfaces:
        """

        # check the number of interfaces only for experiment topologies
        # in e.g. advertisements network services with no interfaces hang off dataplane switches
        if isinstance(self.topo, fim.user.topology.ExperimentTopology):
            if NetworkServiceSliver.ServiceConstraints[nstype].min_interfaces != NetworkServiceSliver.NO_LIMIT:
                if len(interfaces) < NetworkServiceSliver.ServiceConstraints[nstype].min_interfaces:
                    raise TopologyException(f"Service {self.name} of type {nstype} cannot have {len(interfaces)} interfaces. "
                                            f"Limit at least: {NetworkServiceSliver.ServiceConstraints[nstype].min_interfaces}")
            if NetworkServiceSliver.ServiceConstraints[nstype].num_interfaces != NetworkServiceSliver.NO_LIMIT:
                if len(interfaces) > NetworkServiceSliver.ServiceConstraints[nstype].num_interfaces:
                    raise TopologyException(f"Service {self.name} of type {nstype} cannot have {len(interfaces)} interfaces. "
                                            f"Limit at most: {NetworkServiceSliver.ServiceConstraints[nstype].num_interfaces}")
        sites = set()
        # check the number of sites spanned by this service
        if NetworkServiceSliver.ServiceConstraints[nstype].num_sites != NetworkServiceSliver.NO_LIMIT:
            # trace ownership of each interface and count the sites involved
            for interface in interfaces:
                owner = self.topo.get_owner_node(interface)
                if owner is None:
                    print(f'In validating service {self.name} interface {interface=} has no owner')
                sites.add(owner.site)

            if len(sites) > NetworkServiceSliver.ServiceConstraints[nstype].num_sites:
                raise TopologyException(f"Service {self.name} of type {nstype} cannot span {len(sites)} sites. "
                                        f"Limit: {NetworkServiceSliver.ServiceConstraints[nstype].num_sites}.")

        if len(sites) == 0:
            # disconnected service, probably a modify-result, pass
            pass
        elif len(sites) == 1:
            # set the site property if possible
            old_site = self.site
            if not self.site:
                self.site = sites.pop()

            if old_site and old_site != self.site:
                raise TopologyException(f"For service {self.name} originally specified site {old_site} does not"
                                        f"match the site {self.site} inferred from connected interfaces.")
        else:
            if self.site:
                raise TopologyException(f"Service {self.name} of type {self.type} is multi-site, "
                                        f"but site {self.site} was specified in constructor")

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
        if sliver.get_type() == ServiceType.L2PTP and \
            interface.type == InterfaceType.SharedPort:
            raise TopologyException(f"Unable to connect interface {interface.name} to service {sliver.get_name()}: "
                                    f"L2P2P service currently doesn't support shared interfaces")

    def connect_interface(self, interface: Interface):
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
        # FIXME: copy labels from the interface into peer_labels (only needed in L3VPN, but why not?)
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

    def disconnect_interface(self, interface: Interface) -> None:
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
            raise TopologyException(f'Interface {interface} has more than one peer: {peers}, '
                                    f'this is a model error, unable to proceed.')

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
        all_names = [n.name for n in self._interfaces]
        if name in all_names:
            raise TopologyException(f'Interface {name} is not unique within a network service')
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

    def peer(self, ns, **kwargs) -> None:
        """
        Supported in ASMs. Peer this network service to another. A few constraints are enforced like services being
        of the same type. Both services will have ServicePort interfaces facing each other over a link.
        :param ns: opposite network service
        :param kwargs: typically labels and capacities to put on the interface facing the other service
        """
        assert(isinstance(ns, NetworkService))
        self_iface = self.add_interface(name=self.name + '-' + ns.name, itype=InterfaceType.ServicePort, **kwargs)
        other_iface = ns.add_interface(name=ns.name + '-' + self.name, itype=InterfaceType.ServicePort)
        # link them together with L2Path
        peer_link = Link(name=self_iface.name + '-link', topo=self.topo, etype=ElementType.NEW,
                         interfaces=[self_iface, other_iface], ltype=LinkType.L2Path)
        # update interface lists
        self._interfaces.append(self_iface)
        ns._interfaces.append(other_iface)

    def unpeer(self, ns) -> None:
        """
        Supported primarily in ASMs.
        Do the opposite of peer() - remove the ServicePort interfaces connecting these two services and the
        link between them
        """
        assert(isinstance(ns, NetworkService))
        # see if they peer
        sp = self.topo.graph_model.get_nodes_on_shortest_path(node_a=self.node_id, node_z=ns.node_id)
        if len(sp) == 0:
            raise TopologyException(f"Network services {self.name} and {ns.name} do not peer!")
        # remove ConnectionPoints and link between them
        self.topo.graph_model.remove_cp_and_links(node_id=sp[1])
        ns.topo.graph_model.remove_cp_and_links(node_id=sp[-2])
        # update interface lists
        self._interfaces = list(filter((lambda x: x.node_id != sp[1]), self._interfaces))
        ns._interfaces = list(filter((lambda x: x.node_id != sp[-2]), self._interfaces))

    def copy_to_peer_labels(self) -> None:
        """
        This generally is only needed for a few service types like L3VPN and only on ASMs.
        This call copies Labels property from ConnectionPoints/Interfaces that
        are peers of ServicePorts of this service to PeerLabels property of ServicePorts.
        Generally expected to be executed by Orchestrator on ASMs.
        """
        # for each service interface, locate its peer, copy Labels to PeerLabels
        for srv_if in self.interface_list:
            peer_ifs = srv_if.get_peers()
            if not peer_ifs:
                continue
            # generally the first one is all we need
            srv_if.peer_labels = peer_ifs[0].labels

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
        ret = dict()
        for intf in self._interfaces:
            ret[intf.name] = intf
        return ViewOnlyDict(ret)

    def __list_of_interfaces(self) -> Tuple[Interface]:
        """
        Return a list of names of interfaces of network service
        :return:
        """
        return tuple(self._interfaces)

    @property
    def interface_list(self):
        """
        List of names of service interfaces
        """
        return self.__list_of_interfaces()

    @property
    def interfaces(self):
        """
        Dictionary name->Interface for all interfaces
        """
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
                 from_interface_name: str = None, from_interface_vlan: str = None, to_interface: Interface = None,
                 check_existing: bool = False,
                 **kwargs):
        if etype == ElementType.NEW:
            assert to_interface
            assert from_interface_name

            # only the 'to_interface' is actually connected to the service
            # the 'from_interface' is connected to something else
            # to_interface has to be a full-rate interface

            super().__init__(name=name, node_id=node_id, topo=topo, etype=etype,
                             parent_node_id=parent_node_id, interfaces=[to_interface],
                             nstype=ServiceType.PortMirror, technology=None,
                             mirror_port=from_interface_name, mirror_vlan=from_interface_vlan,
                             mirror_direction=direction,
                             **kwargs)
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            if check_existing:
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
    def mirror_vlan(self):
        return self.get_property('mirror_vlan') if self.__dict__.get('topo', None) is not None else None

    @property
    def mirror_direction(self):
        return self.get_property('mirror_direction') if self.__dict__.get('topo', None) is not None else None
