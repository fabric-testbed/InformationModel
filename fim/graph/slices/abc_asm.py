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
Abstract definition of ASM (Abstract Slice Model) functionality
"""

from typing import List, Any, Dict
from abc import ABCMeta, abstractmethod

from fim.slivers.network_node import NodeSliver
from fim.slivers.attached_components import ComponentSliver
from fim.slivers.switch_fabric import SwitchFabricSliver
from fim.slivers.interface_info import InterfaceSliver
from fim.slivers.capacities_labels import Capacities, Labels
from fim.slivers.network_link import NetworkLinkSliver
from fim.graph.abc_property_graph import ABCPropertyGraph


class ABCASMMixin(metaclass=ABCMeta):
    """
    Interface for an ASM Mixin on top of a property graph
    """
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'get_all_network_nodes') and
                callable(subclass.get_all_network_nodes) or NotImplemented)

    @abstractmethod
    def check_node_unique(self, *, label: str, name: str):
        """
        Check no other node of this class/label and name exists
        :param label:
        :param name:
        :return:
        """

    @abstractmethod
    def get_all_network_nodes(self) -> List[str]:
        """
        Get a list of nodes IDs in a slice model
        :return:
        """

    @abstractmethod
    def get_all_network_links(self) -> List[str]:
        """
        Get a list of link node ids in a slice model
        :return:
        """

    @abstractmethod
    def get_all_network_node_components(self, parent_node_id: str) -> List[str]:
        """
        Get a list of node ids of components that are connected to a parent node
        :param parent_node_id:
        :return:
        """

    @abstractmethod
    def get_all_node_or_component_connection_points(self, parent_node_id: str) -> List[str]:
        """
        Get a list of interfaces attached to switch fabrics
        :param parent_node_id:
        :return:
        """

    @abstractmethod
    def get_all_network_node_or_component_sfs(self, parent_node_id: str) -> List[str]:
        """
        Get a list of node or component switch fabrics
        :param parent_node_id:
        :return:
        """

    @abstractmethod
    def get_all_sf_connection_points(self, parent_node_id: str) -> List[str]:
        """
        Get a list of interfaces as children of a switch fabric
        :param parent_node_id:
        :return:
        """

    @abstractmethod
    def get_all_link_interfaces(self, link_id: str) -> List[str]:
        """
        Get a list of interface node ids attached to this link
        :param link_id:
        :return:
        """

    @abstractmethod
    def find_node_by_name(self, node_name: str, label: str) -> str:
        """
        Get node id of node based on its name and class/label. Throw
        exception if multiple matches found.
        :param node_name:
        :param label: node label or class of the node
        :return:
        """

    @abstractmethod
    def remove_network_node_with_components_sfs_cps_and_links(self, node_id: str):
        """
        Remove a network node and all of its components from the graph
        :param node_id:
        :return:
        """

    @abstractmethod
    def remove_component_with_sfs_cps_and_links(self, node_id: str):
        """
        Remove a component with subtending switch fabrics, connection points and links
        :param node_id:
        :return:
        """

    @abstractmethod
    def remove_sf_with_cps_and_links(self, node_id: str):
        """
        Remove a SwitchFabric with subtending connection points and links
        :param node_id:
        :return:
        """

    @abstractmethod
    def remove_cp_and_links(self, node_id: str):
        """
        Remove connection point with subtending parent connection points and links
        :param node_id:
        :return:
        """

    @abstractmethod
    def add_network_node_sliver(self, *, sliver: NodeSliver):
        """
        Use node sliver to add node, components and interfaces to the graph
        :param sliver:
        :return:
        """

    @abstractmethod
    def add_network_link_sliver(self, *, lsliver: NetworkLinkSliver, interfaces: List[str]):
        """
        Add a link sliver node connecting the specified interface nodes (listed by node_id)
        :param lsliver:
        :param interfaces:
        :return:
        """

    @abstractmethod
    def add_component_sliver(self, *, parent_node_id: str, component: ComponentSliver):
        """
        Add Component (PCI device) to a node with node_id
        :param parent_node_id:
        :param component:
        :return:
        """

    @abstractmethod
    def add_switch_fabric_sliver(self, *, parent_node_id: str, switch_fabric: SwitchFabricSliver):
        """
        Add switch fabric to component or node
        :param parent_node_id:
        :param switch_fabric:
        :return:
        """

    @abstractmethod
    def add_interface_sliver(self, *, parent_node_id: str, interface: InterfaceSliver):
        """
        Add switching fabric (if needed) and an interface of the component
        :param parent_node_id:
        :param interface:
        :return:
        """

    @abstractmethod
    def find_component_by_name(self, *, parent_node_id: str, component_name: str) -> str:
        """
        Find a component by name as a child of a node
        :param parent_node_id:
        :param component_name:
        :return:
        """

    @abstractmethod
    def find_sf_by_name(self, *, parent_node_id: str, sfname: str) -> str:
        """
        Find a switch fabric by name as a child of a node or component
        :param parent_node_id:
        :param sfname:
        :return:
        """

    @abstractmethod
    def find_connection_point_by_name(self, *, parent_node_id: str, iname: str) -> str:
        """
        Find an interface by name as a child of switch fabric
        :param parent_node_id:
        :param iname:
        :return:
        """

    @staticmethod
    def node_sliver_from_graph_properties_dict(d: Dict[str, str]) -> NodeSliver:
        n = NodeSliver()
        if d.get(ABCPropertyGraph.PROP_IMAGE_REF, None) is None:
            image_ref = None
            image_type = None
        else:
            image_ref, image_type = d[ABCPropertyGraph.PROP_IMAGE_REF].split(',')
        n.set_properties(resource_name=d.get(ABCPropertyGraph.PROP_NAME, None),
                         resource_type=n.type_from_str(d.get(ABCPropertyGraph.PROP_TYPE, None)),
                         capacities=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITIES, None)),
                         labels=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABELS, None)),
                         site=d.get(ABCPropertyGraph.PROP_SITE, None),
                         image_ref=image_ref,
                         image_type=image_type,
                         management_ip=d.get(ABCPropertyGraph.PROP_MGMT_IP, None),
                         allocation_constraints=d.get(ABCPropertyGraph.PROP_ALLOCATION_CONSTRAINTS, None),
                         service_endpoint=d.get(ABCPropertyGraph.PROP_SERVICE_ENDPOINT, None),
                         details=d.get(ABCPropertyGraph.PROP_DETAILS, None)
                         )
        return n

    @staticmethod
    def link_sliver_from_graph_properties_dict(d: Dict[str, str]) -> NetworkLinkSliver:
        n = NetworkLinkSliver()
        n.set_properties(resource_name=d.get(ABCPropertyGraph.PROP_NAME, None),
                         resource_type=n.type_from_str(d.get(ABCPropertyGraph.PROP_TYPE, None)),
                         capacities=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITIES, None)),
                         labels=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABELS, None)),
                         layer=n.layer_from_str(d.get(ABCPropertyGraph.PROP_LAYER, None)),
                         technology=d.get(ABCPropertyGraph.PROP_TECHNOLOGY, None),
                         details=d.get(ABCPropertyGraph.PROP_DETAILS, None)
                         )
        return n

    @staticmethod
    def component_sliver_from_graph_properties_dict(d: Dict[str, str]) -> ComponentSliver:
        """
        Create component sliver from node graph properties
        :param d:
        :return:
        """
        cs = ComponentSliver()
        cs.set_properties(name=d.get(ABCPropertyGraph.PROP_NAME, None),
                          resource_type=cs.type_from_str(d.get(ABCPropertyGraph.PROP_TYPE, None)),
                          capacities=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITIES, None)),
                          labels=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABELS, None)),
                          details=d.get(ABCPropertyGraph.PROP_DETAILS, None)
                          )
        return cs

    @staticmethod
    def switch_fabric_sliver_from_graph_properties_dict(d: Dict[str, str]) -> SwitchFabricSliver:
        """
        SwitchFabric sliver from node graph properties
        :param d:
        :return:
        """
        sf = SwitchFabricSliver()
        sf.set_properties(name=d.get(ABCPropertyGraph.PROP_NAME, None),
                          resource_type=sf.type_from_str(d.get(ABCPropertyGraph.PROP_TYPE, None)),
                          capacities=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITIES, None)),
                          labels=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABELS, None)),
                          layer=sf.layer_from_str(d.get(ABCPropertyGraph.PROP_LAYER, None)),
                          details=d.get(ABCPropertyGraph.PROP_DETAILS, None)
                          )
        return sf

    @staticmethod
    def interface_sliver_from_graph_properties_dict(d: Dict[str, str]) -> InterfaceSliver:
        """
        Interface sliver from node graph properties
        :param d:
        :return:
        """
        isl = InterfaceSliver()
        isl.set_properties(name=d.get(ABCPropertyGraph.PROP_NAME, None),
                           resource_type=isl.type_from_str(d.get(ABCPropertyGraph.PROP_TYPE, None)),
                           capacities=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITIES, None)),
                           labels=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABELS, None)),
                           details=d.get(ABCPropertyGraph.PROP_DETAILS, None)
                           )
        return isl

    @staticmethod
    def node_sliver_to_graph_properties_dict(sliver: NodeSliver) -> Dict[str, str]:
        """
        This method knows how to map sliver fields to graph properties
        :param self:
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict[ABCPropertyGraph.PROP_NAME] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict[ABCPropertyGraph.PROP_TYPE] = str(sliver.resource_type)
        if sliver.capacities is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITIES] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict[ABCPropertyGraph.PROP_LABELS] = sliver.labels.to_json()
        if sliver.site is not None:
            prop_dict[ABCPropertyGraph.PROP_SITE] = sliver.site
        if sliver.image_ref is not None and sliver.image_type is not None:
            prop_dict[ABCPropertyGraph.PROP_IMAGE_REF] = sliver.image_ref + ',' + str(sliver.image_type)
        if sliver.management_ip is not None:
            prop_dict[ABCPropertyGraph.PROP_MGMT_IP] = str(sliver.management_ip)
        if sliver.allocation_constraints is not None:
            prop_dict[ABCPropertyGraph.PROP_ALLOCATION_CONSTRAINTS] = sliver.allocation_constraints
        if sliver.service_endpoint is not None:
            prop_dict[ABCPropertyGraph.PROP_SERVICE_ENDPOINT] = str(sliver.service_endpoint)
        if sliver.details is not None:
            prop_dict[ABCPropertyGraph.PROP_DETAILS] = sliver.details
        return prop_dict

    @staticmethod
    def link_sliver_to_graph_properties_dict(sliver: NetworkLinkSliver) -> Dict[str, str]:
        """
        This method knows how to map sliver fields to graph properties
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict[ABCPropertyGraph.PROP_NAME] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict[ABCPropertyGraph.PROP_TYPE] = str(sliver.resource_type)
        if sliver.capacities is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITIES] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict[ABCPropertyGraph.PROP_LABELS] = sliver.labels.to_json()
        if sliver.layer is not None:
            prop_dict[ABCPropertyGraph.PROP_LAYER] = str(sliver.layer)
        if sliver.technology is not None:
            prop_dict[ABCPropertyGraph.PROP_TECHNOLOGY] = str(sliver.technology)
        if sliver.details is not None:
            prop_dict[ABCPropertyGraph.PROP_DETAILS] = sliver.details

        return prop_dict

    @staticmethod
    def component_sliver_to_graph_properties_dict(sliver: ComponentSliver) -> Dict[str, str]:
        """
        This method knows how to map component sliver fields to graph properties
        :param self:
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict[ABCPropertyGraph.PROP_NAME] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict[ABCPropertyGraph.PROP_TYPE] = str(sliver.resource_type)
        if sliver.capacities is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITIES] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict[ABCPropertyGraph.PROP_LABELS] = sliver.labels.to_json()
        if sliver.details is not None:
            prop_dict[ABCPropertyGraph.PROP_DETAILS] = sliver.details

        return prop_dict

    @staticmethod
    def switch_fabric_sliver_to_graph_properties_dict(sliver: SwitchFabricSliver) -> Dict[str, str]:
        """
        This method knows how to map switch fabric sliver fields to graph properties
        :param self:
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict[ABCPropertyGraph.PROP_NAME] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict[ABCPropertyGraph.PROP_TYPE] = str(sliver.resource_type)
        if sliver.capacities is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITIES] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict[ABCPropertyGraph.PROP_LABELS] = sliver.labels.to_json()
        if sliver.layer is not None:
            prop_dict[ABCPropertyGraph.PROP_LAYER] = str(sliver.layer)
        if sliver.details is not None:
            prop_dict[ABCPropertyGraph.PROP_DETAILS] = sliver.details

        return prop_dict

    @staticmethod
    def interface_sliver_to_graph_properties_dict(sliver: InterfaceSliver) -> Dict[str, str]:
        """
        This method knows how to map interface sliver fields to graph properties
        :param self:
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict[ABCPropertyGraph.PROP_NAME] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict[ABCPropertyGraph.PROP_TYPE] = str(sliver.resource_type)
        if sliver.capacities is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITIES] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict[ABCPropertyGraph.PROP_LABELS] = sliver.labels.to_json()
        if sliver.details is not None:
            prop_dict[ABCPropertyGraph.PROP_DETAILS] = sliver.details

        return prop_dict
