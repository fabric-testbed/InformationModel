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
from typing import List, Dict
import uuid
import networkx_query as nxq

from .abc_asm import ABCASMMixin
from ..abc_property_graph import ABCPropertyGraph, PropertyGraphQueryException
from ..networkx_property_graph import NetworkXPropertyGraph, NetworkXGraphImporter
from ...slivers.attached_components import ComponentSliver
from ...slivers.interface_info import InterfaceSliver, InterfaceInfo
from ...slivers.switch_fabric import SwitchFabricSliver
from ...slivers.network_node import NodeSliver as NodeSliver


class NetworkxASM(NetworkXPropertyGraph, ABCASMMixin):
    """
    Class implementing Abstract Slice Model on top of NetworkX
    """

    def __init__(self, *, graph_id: str, importer: NetworkXGraphImporter, logger=None):
        super().__init__(graph_id=graph_id, importer=importer, logger=logger)

    def get_all_network_nodes(self) -> List[str]:
        """
        Return a list of node ids of all graphs of type NetworkNode
        :return:
        """
        my_graph = self.storage.get_graph(self.graph_id)
        graph_nodes = list(nxq.search_nodes(my_graph,
                                            {'and': [
                                                {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraph.PROP_CLASS,
                                                        ABCPropertyGraph.CLASS_NetworkNode]}
                                            ]
                                            }))
        ret = list()
        for n in graph_nodes:
            ret.append(my_graph.nodes[n][ABCPropertyGraph.NODE_ID])
        return ret

    def get_all_network_node_components(self, parent_node_id: str) -> List[str]:
        """
        Return a list of components, children of a prent (presumably network node)
        :param parent_node_id:
        :return:
        """
        assert parent_node_id is not None
        # check that parent is a NetworkNode
        labels, parent_props = self.get_node_properties(node_id=parent_node_id)
        if ABCPropertyGraph.CLASS_NetworkNode not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=parent_node_id,
                                              msg="Parent node type is not NetworkNode")
        return self.get_first_neighbor(node_id=parent_node_id, rel=ABCPropertyGraph.REL_HAS,
                                       node_label=ABCPropertyGraph.CLASS_Component)

    def find_node_by_name(self, node_name: str, label: str) -> str:
        """
        Return a node id of a network node with this name
        :param node_name:
        :param label: label/class of the node
        :return:
        """
        assert node_name is not None
        my_graph = self.storage.get_graph(self.graph_id)
        graph_nodes = list(nxq.search_nodes(my_graph,
                                            {'and': [
                                                {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraph.PROP_NAME, node_name]},
                                                {'eq': [ABCPropertyGraph.PROP_CLASS, label]}
                                            ]}))
        if len(graph_nodes) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg=f"Unable to find node with name {node_name} class {label}")
        if len(graph_nodes) > 1:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg=f"Graph contains multiple nodes with name {node_name} class {label}")

        return my_graph.nodes[graph_nodes[0]][ABCPropertyGraph.NODE_ID]

    def __check_node_unique(self, *, label: str, name: str):
        """
        Check no other node of this class/label and name exists
        :param label:
        :param name:
        :return:
        """
        graph_nodes = list(nxq.search_nodes(self.storage.get_graph(self.graph_id),
                                            {'and': [
                                                {'eq': [ABCPropertyGraph.GRAPH_ID, self.graph_id]},
                                                {'eq': [ABCPropertyGraph.PROP_NAME, name]},
                                                {'eq': [ABCPropertyGraph.PROP_CLASS, label]}
                                            ]}))
        return len(graph_nodes) == 0

    def find_component_by_name(self, *, parent_node_id: str, component_name: str) -> str:

        component_id_list = self.get_all_network_node_components(parent_node_id=parent_node_id)
        for cid in component_id_list:
            _, cprops = self.get_node_properties(node_id=cid)
            if cprops[ABCPropertyGraph.PROP_NAME] == component_name:
                return cid
        raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                          msg=f"Unable to find component with name {component_name}")

    def remove_network_node_with_components_interfaces_and_links(self, node_id: str):
        """
        Remove a network node, all of components and their interfaces, parent interfaces
        and connected links (as appropriate)
        :param node_id:
        :return:
        """
        # the network node itself
        # its components
        # their switch fabrics
        # their interfaces (if present)
        # their parent interfaces (if present)
        # the 'Link' objects connected to interfaces if only one or no other interface connects to them

        # check we are a network node
        labels, node_props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_NetworkNode not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg="This node type is not NetworkNode")
        # get a list of components, delete the node
        components = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                             node_label=ABCPropertyGraph.CLASS_Component)
        self.delete_node(node_id=node_id)
        for cid in components:
            self.remove_component_with_interfaces_and_links(node_id=cid)

    def remove_component_with_interfaces_and_links(self, node_id: str):
        """
        Remove a component of a network node with all attached elements (switch fabrics
        and interfaces). Parent interfaces and links are removed if they have no other
        children or connected interfaces.
        :param node_id: component node id
        :return:
        """
        # check we are a component
        labels, node_props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_Component not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg="This node type is not Component")
        # get a list of SwitchFabrics and their interfaces, delete the node
        sfsints = self.get_first_and_second_neighbor(node_id=node_id,
                                                     rel1=ABCPropertyGraph.REL_HAS,
                                                     node1_label=ABCPropertyGraph.CLASS_SwitchFabric,
                                                     rel2=ABCPropertyGraph.REL_CONNECTS,
                                                     node2_label=ABCPropertyGraph.CLASS_ConnectionPoint)
        switch_fabrics = set()
        interfaces = set()
        for pair in sfsints:
            switch_fabrics.add(pair[0])
            interfaces.add(pair[1])
        # delete component and its switch fabrics
        self.delete_node(node_id=node_id)
        for sf in switch_fabrics:
            self.delete_node(node_id=sf)
        # delete the interfaces
        for interface in interfaces:
            self.remove_interfaces_and_links(node_id=interface)

    def remove_interfaces_and_links(self, node_id: str):
        """
        Remove interfaces of a component. Parent interfaces and links are removed
        if they have no other children or connected interfaces.
        :param node_id: interface node id
        :return:
        """
        # some interfaces may have parent interfaces, which can be deleted if they only have the
        # one child
        interfaces_to_delete = {node_id}
        parents = self.get_first_neighbor(node_id=node_id,
                                          rel=ABCPropertyGraph.REL_CONNECTS,
                                          node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
        for parent in parents:  # really should only be one parent interface
            children = self.get_first_neighbor(node_id=parent,
                                               rel=ABCPropertyGraph.REL_CONNECTS,
                                               node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
            if len(children) == 1:  # if only child, can delete parent
                interfaces_to_delete.add(parent)
        # interfaces themselves and parent interfaces
        # may be connected to links which can be deleted if nothing
        # else connects to them
        links_to_delete = set()
        for interface in interfaces_to_delete:
            links = self.get_first_neighbor(node_id=interface,
                                            rel=ABCPropertyGraph.REL_CONNECTS,
                                            node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
            for link in links:  # should only be one
                connected_interfaces = self.get_first_neighbor(node_id=link,
                                                               rel=ABCPropertyGraph.REL_CONNECTS,
                                                               node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
                if len(connected_interfaces) == 2:  # connected to us and another thing, can delete
                    links_to_delete.add(link)
        # delete nodes in these sets
        for deleted_id in interfaces_to_delete.union(links_to_delete):
            self.delete_node(node_id=deleted_id)

    @staticmethod
    def __node_sliver_to_graph_properties_dict(sliver: NodeSliver) -> Dict[str, str]:
        """
        This method knows how to map sliver fields to graph properties
        :param self:
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict['Name'] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict['Type'] = str(sliver.resource_type)
        if sliver.capacities is not None:
            prop_dict['Capacities'] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict['Labels'] = sliver.labels.to_json()
        if sliver.site is not None:
            prop_dict['Site'] = sliver.site
        if sliver.image_ref is not None and sliver.image_type is not None:
            prop_dict['ImageRef'] = sliver.image_ref + ',' + str(sliver.image_type)
        if sliver.management_ip is not None:
            prop_dict['MgmtIP'] = str(sliver.management_ip)
        if sliver.allocation_constraints is not None:
            prop_dict['AllocationConstraints'] = sliver.allocation_constraints.to_json()
        if sliver.service_endpoint is not None:
            prop_dict['ServiceEndpoint'] = str(sliver.service_endpoint)
        return prop_dict

    def add_network_node_sliver(self, *, sliver: NodeSliver):

        assert sliver.node_id is not None
        assert self.__check_node_unique(label=ABCPropertyGraph.CLASS_NetworkNode, name=sliver.resource_name)

        props = self.__node_sliver_to_graph_properties_dict(sliver)
        self.add_node(node_id=sliver.node_id, label=ABCPropertyGraph.CLASS_NetworkNode, props=props)
        # if components aren't empty, add components, their switch fabrics and interfaces
        aci = sliver.attached_components_info
        if aci is not None:
            for csliver in aci.devices.values():
                self.add_component_sliver(parent_node_id=sliver.node_id,
                                          component=csliver)
        # if switch fabrics arent empty add them with their interfaces
        sfi = sliver.switch_fabric_info
        if sfi is not None:
            for sf in sfi.switch_fabrics.values():
                self.add_switch_fabric_sliver(parent_node_id=sliver.node_id,
                                              switch_fabric=sf)

    @staticmethod
    def __component_sliver_to_graph_properties_dict(sliver: ComponentSliver) -> Dict[str, str]:
        """
        This method knows how to map component sliver fields to graph properties
        :param self:
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict['Name'] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict['Type'] = str(sliver.resource_type)
        if sliver.capacities is not None:
            prop_dict['Capacities'] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict['Labels'] = sliver.labels.to_json()

        return prop_dict

    def add_component_sliver(self, *, parent_node_id: str, component: ComponentSliver):
        """
        Add network node component as a sliver, linking back to parent
        :param parent_node_id:
        :param component:
        :return:
        """
        assert component.node_id is not None
        assert parent_node_id is not None
        assert self.__check_node_unique(label=ABCPropertyGraph.CLASS_Component, name=component.resource_name)
        props = self.__component_sliver_to_graph_properties_dict(component)
        self.add_node(node_id=component.node_id, label=ABCPropertyGraph.CLASS_Component, props=props)
        self.add_link(node_a=parent_node_id, rel=ABCPropertyGraph.REL_HAS, node_b=component.node_id)
        sfi = component.switch_fabric_info
        if sfi is not None:
            for sf in sfi.switch_fabrics.values():
                self.add_switch_fabric_sliver(parent_node_id=component.node_id,
                                              switch_fabric=sf)

    @staticmethod
    def __switch_fabric_sliver_to_graph_properties_dict(sliver: SwitchFabricSliver) -> Dict[str, str]:
        """
        This method knows how to map switch fabric sliver fields to graph properties
        :param self:
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict['Name'] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict['Type'] = str(sliver.resource_type)
        if sliver.capacities is not None:
            prop_dict['Capacities'] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict['Labels'] = sliver.labels.to_json()
        if sliver.layer is not None:
            prop_dict['Layer'] = str(sliver.layer)

        return prop_dict

    def add_switch_fabric_sliver(self, *, parent_node_id: str, switch_fabric: SwitchFabricSliver):
        """
        Add switch fabric as a sliver to either node or component, linking back to parent.
        :param parent_node_id:
        :param switch_fabric:
        :return:
        """
        assert parent_node_id is not None
        assert switch_fabric.node_id is not None
        assert self.__check_node_unique(label=ABCPropertyGraph.CLASS_SwitchFabric,
                                        name=switch_fabric.resource_name)
        props = self.__switch_fabric_sliver_to_graph_properties_dict(switch_fabric)
        self.add_node(node_id=switch_fabric.node_id, label=ABCPropertyGraph.CLASS_SwitchFabric, props=props)
        self.add_link(node_a=parent_node_id, rel=ABCPropertyGraph.REL_HAS, node_b=switch_fabric.node_id)
        ii = switch_fabric.interface_info
        if ii is not None:
            for i in ii.interfaces.values():
                self.add_interface_sliver(parent_node_id=switch_fabric.node_id,
                                          interface=i)

    @staticmethod
    def __interface_sliver_to_graph_properties_dict(sliver: InterfaceSliver) -> Dict[str, str]:
        """
        This method knows how to map interface sliver fields to graph properties
        :param self:
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict['Name'] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict['Type'] = str(sliver.resource_type)
        if sliver.capacities is not None:
            prop_dict['Capacities'] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict['Labels'] = sliver.labels.to_json()

        return prop_dict

    def add_interface_sliver(self, *, parent_node_id: str, interface: InterfaceSliver):
        """
        Add interface to a switch fabric, linking back to parent.
        :param parent_node_id: switch fabric id
        :param interface: interface sliver description
        :return:
        """
        assert interface.node_id is not None
        assert parent_node_id is not None
        assert self.__check_node_unique(label=ABCPropertyGraph.CLASS_ConnectionPoint, name=interface.resource_name)
        props = self.__interface_sliver_to_graph_properties_dict(interface)
        self.add_node(node_id=interface.node_id, label=ABCPropertyGraph.CLASS_ConnectionPoint, props=props)
        self.add_link(node_a=parent_node_id, rel=ABCPropertyGraph.REL_CONNECTS, node_b=interface.node_id)
