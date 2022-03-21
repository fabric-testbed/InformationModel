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

from typing import Dict, Any, List, Tuple

import uuid

from fim.view_only_dict import ViewOnlyDict
from .model_element import ModelElement, ElementType, TopologyException
from .component import Component, ComponentType
from .network_service import NetworkService
from .interface import Interface

from ..graph.abc_property_graph import ABCPropertyGraph, PropertyGraphQueryException

from ..slivers.network_node import NodeSliver
from ..slivers.network_node import NodeType
from ..slivers.network_service import ServiceType, NetworkServiceInfo
from ..slivers.component_catalog import ComponentModelType
from ..slivers.capacities_labels import CapacityHints, Location, ReservationInfo


class Node(ModelElement):
    """
    A basic node of any topology. In addition to public methods the following calls
    return various dictionaries or lists:
    node.components - returns a dictionary of components by name
    node.interfaces - returns a dictionary of interfaces by name
    node.interface_list - returns a list of interfaces
    node.direct_interfaces - returns a dictionary of direct interfaces, i.e. those
    not attached to components (mostly relevant to switches, not servers
    or VMs)
    network_services - returns a dictionary of network_services (mostly relevant
    to switches, not servers or VMs)
    """

    def __init__(self, *, name: str, node_id: str = None, topo: Any, etype: ElementType = ElementType.EXISTING,
                 ntype: NodeType = None, site: str = None, ns_info: NetworkServiceInfo = None, **kwargs):
        """
        Don't call this method yourself, call topology.add_node()
        node_id will be generated if not provided for experiment topologies

        :param name:
        :param node_id:
        :param topo:
        :param etype: is this supposed to exist or new should be created
        :param ntype: node type if it is new
        :param site: node site
        :param ns_info: NetworkServiceInfo structure
        :param kwargs: any additional properties
        """
        assert name is not None
        assert topo is not None

        if etype == ElementType.NEW:
            # cant use isinstance as it would create circular import dependencies
            # node id myst be specified for new nodes in substrate topologies
            if str(topo.__class__) == "<class 'fim.user.topology.SubstrateTopology'>" and \
                    node_id is None:
                raise TopologyException("When adding new nodes to substrate topology nodes you must specify static Node ID")
            if node_id is None:
                node_id = str(uuid.uuid4())
            super().__init__(name=name, node_id=node_id, topo=topo)
            if ntype is None:
                raise TopologyException("When creating nodes you must specify NodeType")
            if site is None:
                raise TopologyException("When creating nodes you must specify site")

            sliver = NodeSliver()
            sliver.node_id = self.node_id
            sliver.set_name(self.name)
            sliver.set_type(ntype)
            sliver.set_site(site)
            sliver.network_service_info = ns_info
            sliver.set_properties(**kwargs)
            self.topo.graph_model.add_network_node_sliver(sliver=sliver)
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            # check that this node exists
            existing_node_id = self.topo.graph_model.find_node_by_name(node_name=name,
                                                                       label=str(ABCPropertyGraph.CLASS_NetworkNode))
            if existing_node_id != node_id:
                raise TopologyException(f'Node name {name} is not unique within the topology')

    @property
    def site(self):
        return self.get_property('site') if self.__dict__.get('topo', None) is not None else None

    @site.setter
    def site(self, value: str):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('site', value)

    @property
    def type(self):
        return self.get_property('type') if self.__dict__.get('topo', None) is not None else None

    @property
    def image_type(self):
        return self.get_property('image_type') if self.__dict__.get('topo', None) is not None else None

    @image_type.setter
    def image_type(self, value: str):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('image_type', value)

    @property
    def image_ref(self):
        return self.get_property('image_ref') if self.__dict__.get('topo', None) is not None else None

    @image_ref.setter
    def image_ref(self, value: str):
        if self.__dict__.get('topo', None) is not None:
            imtype = self.get_property('image_type')
            # image ref and type have fate-sharing - neither can be null to be written into a graph
            self.set_properties(image_ref=value, image_type=imtype)

    @property
    def management_ip(self):
        # no user-facing setter for this one
        return self.get_property('management_ip') if self.__dict__.get('topo', None) is not None else None

    @property
    def capacity_hints(self):
        return self.get_property('capacity_hints') if self.__dict__.get('topo', None) is not None else None

    @capacity_hints.setter
    def capacity_hints(self, value: CapacityHints):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('capacity_hints', value)

    @property
    def reservation_info(self):
        return self.get_property('reservation_info') if self.__dict__.get('topo', None) is not None else None

    @reservation_info.setter
    def reservation_info(self, value: ReservationInfo):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('reservation_info', value)

    @property
    def location(self):
        return self.get_property('location') if self.__dict__.get('topo', None) is not None else None

    @location.setter
    def location(self, value: Location):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('location', value)

    @property
    def components(self):
        return self.__list_components()

    @property
    def interfaces(self):
        return self.__list_interfaces()

    @property
    def interface_list(self):
        return self.__list_of_interfaces()

    @property
    def direct_interfaces(self):
        return self.__list_direct_interfaces()

    @property
    def network_services(self):
        return self.__list_network_services()

    def validate_constraints(self):
        """
        Validate node constraints - properties
        """

        nstype = self.type

        # check properties
        req_props = NodeSliver.NodeConstraints[nstype].required_properties
        forb_props = NodeSliver.NodeConstraints[nstype].forbidden_properties
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        node_sliver = self.topo.graph_model.node_sliver_from_graph_properties_dict(node_properties)
        for rp in req_props:
            if not node_sliver.get_property(rp):
                raise TopologyException(f"Node of type {nstype} must have property {rp} set")
        for fp in forb_props:
            if node_sliver.get_property(fp):
                raise TopologyException(f"Node of type {nstype} must NOT have property {fp} set")

    def get_sliver(self) -> NodeSliver:
        """
        Get a deep sliver representation of this node from graph
        :return:
        """
        return self.topo.graph_model.build_deep_node_sliver(node_id=self.node_id)

    def get_property(self, pname: str) -> Any:
        """
        Retrieve a node property
        :param pname:
        :return:
        """
        assert pname is not None
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        node_sliver = self.topo.graph_model.node_sliver_from_graph_properties_dict(node_properties)
        return node_sliver.get_property(pname)

    def set_property(self, pname: str, pval: Any):
        """
        Set a node property or unset if pval is None
        :param pname:
        :param pval:
        :return:
        """
        if pval is None:
            self.unset_property(pname)
            return
        node_sliver = NodeSliver()
        node_sliver.set_property(prop_name=pname, prop_val=pval)
        # write into the graph
        prop_dict = self.topo.graph_model.node_sliver_to_graph_properties_dict(node_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    def set_properties(self, **kwargs):
        """
        Set multiple properties of the node
        :param kwargs:
        :return:
        """
        node_sliver = NodeSliver()
        node_sliver.set_properties(**kwargs)
        # write into the graph
        prop_dict = self.topo.graph_model.node_sliver_to_graph_properties_dict(node_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    @staticmethod
    def list_properties() -> Tuple[str]:
        return tuple(NodeSliver.list_properties())

    def add_component(self, *, name: str, node_id: str = None, ctype: ComponentType = None,
                      model: str = None, model_type: ComponentModelType = None,
                      network_service_node_id: str=None, interface_node_ids=None,
                      interface_labels=None, **kwargs) -> Component:
        """
        Add a component of specified type, model and name to this node. When working with substrate
        topologies you must specify the network_service_node_id and provide a list of interface node ids.
        :param name:
        :param node_id:
        :param ctype: ComponentType
        :param model: Model string (exact match)
        :param  model_type: ComponentModelType (combines ComponentType and Model)
        :param network_service_node_id: network service identifier for substrate models
        :param interface_node_ids: interface identifiers for substrate models
        :param interface_labels: list of labels for interfaces in substrate models
        :param kwargs: additional properties of the component
        :return:
        """
        assert name is not None
        # make sure name is unique within the node
        if name in self.__list_components().keys():
            raise TopologyException('Component names must be unique within node.')
        # add component node and populate properties
        c = Component(name=name, node_id=node_id, topo=self.topo, etype=ElementType.NEW,
                      ctype=ctype, model=model, comp_model=model_type,
                      network_service_node_id=network_service_node_id,
                      interface_node_ids=interface_node_ids, interface_labels=interface_labels,
                      parent_node_id=self.node_id, **kwargs)
        return c

    def add_storage(self, *, name: str, node_id: str = None, **kwargs) -> Component:
        """
        Add storage as a component (only in ASMs). Note that storage shows up as a component
        on the list of node components. Typically you want to specify labels=Labels(local_name='volume name')
        as part of keyargs so an existing volume can get attached.
        :param name:
        :param node_id:
        :param kwargs: additional properties of the component
        :return:
        """
        assert name is not None
        if str(self.topo.__class__) != "<class 'fim.user.topology.ExperimentTopology'>":
            raise TopologyException('Storage can be added as a component only in ExperimentTopologies')
        # make sure name is unique within the node
        if name in self.__list_components().keys():
            raise TopologyException('Component names must be unique within node.')
        # add component node and populate properties
        c = Component(name=name, node_id=node_id, topo=self.topo, etype=ElementType.NEW,
                      ctype=ComponentType.Storage, model=NodeType.NAS.name,
                      parent_node_id=self.node_id, **kwargs)
        return c

    def add_network_service(self, *, name: str, node_id: str = None, nstype: ServiceType, **kwargs) -> NetworkService:
        """
        Add a network service to node ( needed in substrate topologies)
        :param name:
        :param node_id:
        :param layer:
        :param kwargs:
        :return:
        """
        assert name is not None
        # make sure name is unique within the node
        if name in self.__list_network_services().keys():
            raise TopologyException('NetworkService names must be unique within node.')
        ns = NetworkService(name=name, node_id=node_id, parent_node_id=self.node_id, topo=self.topo,
                            etype=ElementType.NEW, nstype=nstype, **kwargs)
        return ns

    def remove_component(self, name: str) -> None:
        """
        Remove a component from the node (and network services and their interfaces)
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.topo.graph_model.find_component_by_name(parent_node_id=self.node_id,
                                                               component_name=name)
        self.topo.graph_model.remove_component_with_nss_cps_and_links(node_id=node_id)

    def remove_network_service(self, name: str) -> None:
        """
        Remove a network service from the node (and all its interfaces)
        :param name:
        :return:
        """
        assert name is not None

        node_id = self.topo.graph_model.find_ns_by_name(parent_node_id=self.node_id,
                                                        nsname=name)
        self.topo.graph_model.remove_ns_with_cps_and_links(node_id=node_id)

    def remove_storage(self, name: str) -> None:
        """
        Removes attached storage component
        """
        self.remove_component(name)

    def __get_component_by_name(self, name: str) -> Component:
        """
        Find component of a node by its name, return Component object
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.topo.graph_model.find_component_by_name(parent_node_id=self.node_id,
                                                               component_name=name)
        return Component(name=name, node_id=node_id, topo=self.topo)

    def _get_component_by_id(self, node_id: str) -> Component:
        """
        Get component of a node by its node_id, return Component object
        :param node_id:
        :return:
        """
        assert node_id is not None
        _, node_props = self.topo.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        return Component(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id,
                         topo=self.topo)

    def __get_ns_by_name(self, name: str) -> NetworkService:
        """
        Find NetworkService of a node by its name, return NetworkService object
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.topo.graph_model.find_ns_by_name(parent_node_id=self.node_id, component_name=name)
        return NetworkService(name=name, node_id=node_id, topo=self.topo)

    def __get_ns_by_id(self, node_id: str) -> NetworkService:
        """
        Get a network service of a node by its node_id, return NetworkService object
        :param node_id:
        :return:
        """
        assert node_id is not None
        _, node_props = self.topo.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        return NetworkService(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id,
                              topo=self.topo)

    def __get_interface_by_id(self, node_id: str) -> Interface:
        """
        Get an interface of a node by its node_id, return Interface object
        :param node_id:
        :return:
        """
        assert node_id is not None
        clazzes, node_props = self.topo.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        assert ABCPropertyGraph.CLASS_ConnectionPoint in clazzes
        return Interface(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id,
                         topo=self.topo)

    def __list_components(self) -> ViewOnlyDict:
        """
        List all Components children of a node in the topology as a dictionary
        organized by component name. Modifying the dictionary will not affect
        the underlying model, but modifying Components in the dictionary will.
        :return:
        """
        node_id_list = self.topo.graph_model.get_all_network_node_components(parent_node_id=self.node_id)
        ret = dict()
        for nid in node_id_list:
            c = self._get_component_by_id(nid)
            ret[c.name] = c
        return ViewOnlyDict(ret)

    def __list_network_services(self) -> ViewOnlyDict:
        """
        List all network service children of a node as a dictionary organized
        by network service name. Modifying the dictionary will not affect
        the underlying model, but modifying NetworkServices in the dictionary will.
        :return:
        """
        node_id_list = self.topo.graph_model.get_all_network_node_or_component_nss(parent_node_id=self.node_id)
        ret = dict()
        for nid in node_id_list:
            c = self.__get_ns_by_id(nid)
            ret[c.name] = c
        return ViewOnlyDict(ret)

    def __list_direct_interfaces(self) -> ViewOnlyDict:
        """
        List all directly-attached interfaces of the node as a dictionary
        :return:
        """
        # immediately-attached interfaces
        node_if_list = self.topo.graph_model.get_all_node_or_component_connection_points(parent_node_id=self.node_id)
        ret = dict()
        for nid in node_if_list:
            i = self.__get_interface_by_id(nid)
            ret[i.name] = i
        return ViewOnlyDict(ret)

    def __list_interfaces(self) -> ViewOnlyDict:
        """
        List all interfaces of node and its components
        :return:
        """
        # immediately-attached interfaces
        # FIXME: note that because there could be a collision on interface name, this
        # may produce invalid results sometimes. Better to use list_of_interfaces
        node_if_list = self.topo.graph_model.get_all_node_or_component_connection_points(parent_node_id=self.node_id)
        direct_interfaces = dict()
        for nid in node_if_list:
            i = self.__get_interface_by_id(nid)
            direct_interfaces[i.name] = i
        cdict = self.__list_components()
        for k, v in cdict.items():
            comp_interfaces = v.interfaces
            direct_interfaces.update(comp_interfaces)
        return ViewOnlyDict(direct_interfaces)

    def __list_of_interfaces(self) -> Tuple[Interface]:
        """
        List all interfaces of node and its components
        :return:
        """
        node_if_list = self.topo.graph_model.get_all_node_or_component_connection_points(parent_node_id=self.node_id)
        direct_interfaces = list()
        for nid in node_if_list:
            i = self.__get_interface_by_id(nid)
            direct_interfaces.append(i)
        cdict = self.__list_components()
        for k, v in cdict.items():
            direct_interfaces.extend(v.interface_list)
        return tuple(direct_interfaces)

    def get_component(self, name: str):
        """
        Get a component by this name
        :param name:
        :return:
        """
        return self.__get_component_by_name(name)

    def __repr__(self):
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        node_sliver = self.topo.graph_model.node_sliver_from_graph_properties_dict(node_properties)
        return node_sliver.__repr__()

    def __str__(self):
        return self.__repr__()


