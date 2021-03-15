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

from typing import List, Dict, Tuple
from abc import ABCMeta, abstractmethod

import json

from fim.slivers.network_node import NodeSliver
from fim.slivers.attached_components import ComponentSliver
from fim.slivers.switch_fabric import SwitchFabricSliver
from fim.slivers.interface_info import InterfaceSliver
from fim.slivers.capacities_labels import Capacities, Labels
from fim.slivers.delegations import Delegation
from fim.slivers.network_link import NetworkLinkSliver
from fim.graph.abc_property_graph import ABCPropertyGraph, PropertyGraphQueryException


class ABCASMPropertyGraph(ABCPropertyGraph, metaclass=ABCMeta):
    """
    Interface for ASM
    """

    @abstractmethod
    def __init__(self, *, graph_id=str, importer, logger=None):
        super().__init__(graph_id=graph_id, importer=importer, logger=logger)

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'get_all_network_nodes') and
                callable(subclass.get_all_network_nodes) or NotImplemented)

    @abstractmethod
    def check_node_unique(self, *, label: str, name: str) -> bool:
        """
        Check no other node of this class/label and name exists. Doesn't
        apply universally as e.g. Component names are only unique
        within node, interface names are only unique within SF.
        :param label:
        :param name:
        :return:
        """

    @abstractmethod
    def check_node_name(self, *, node_id: str, label: str, name: str) -> bool:
        """
        Check if a node with this ID of this class/label has this name
        :param node_id:
        :param label:
        :param name:
        :return:
        """

    @abstractmethod
    def find_node_by_name(self, *, node_name: str, label: str) -> str:
        """
        Get node id of node based on its name and class/label. Throw
        exception if multiple matches found.
        :param node_name:
        :param label: node label or class of the node
        :return:
        """

    def get_all_network_nodes(self) -> List[str]:

        return self.get_all_nodes_by_class(label=ABCASMPropertyGraph.CLASS_NetworkNode)

    def get_all_network_links(self) -> List[str]:

        return self.get_all_nodes_by_class(label=ABCASMPropertyGraph.CLASS_Link)

    def set_mapping(self, *, node_id: str, to_graph_id: str, to_node_id: str) -> None:
        """
        Create a mapping from a node to another graph, node
        :param node_id:
        :param to_graph_id:
        :param to_node_id:
        :return:
        """
        assert node_id is not None
        assert to_graph_id is not None
        assert to_node_id is not None

        # save tuple as JSON list of guids
        l = [to_graph_id, to_node_id]
        jsonl = json.dumps(l)
        self.update_node_property(node_id=node_id, prop_name=ABCASMPropertyGraph.PROP_NODE_MAP,
                                  prop_val=jsonl)

    def get_mapping(self, *, node_id: str) -> Tuple[str, str] or None:
        """
        Retrieve a mapping, if exists for this node to another graph, node
        :param node_id:
        :return: graph_id, node_id tuple or None
        """
        assert node_id is not None
        # retrieve tuple as a json 2-member list
        _, props = self.get_node_properties(node_id=node_id)
        jsonl = props.get(ABCASMPropertyGraph.PROP_NODE_MAP, None)
        if jsonl is not None:
            l = json.loads(jsonl)
            assert(len(l) == 2)
            return tuple(l)
        return None

    def find_node_by_name_as_child(self, *, node_name: str, label: str, rel: str, parent_node_id: str) -> str or None:
        """
        Get node id of node based on its name, class label, as child of a parent node via a specified relationship
        or None
        :param node_name: 
        :param label: 
        :param rel: 
        :param parent_node_id: 
        :return: 
        """
        assert node_name is not None
        assert label is not None
        assert rel is not None
        assert parent_node_id is not None

        neighbs = self.get_first_neighbor(node_id=parent_node_id, rel=rel, node_label=label)
        for n in neighbs:
            _, props = self.get_node_properties(node_id=n)
            if props.get(ABCPropertyGraph.PROP_NAME, None) is not None and \
                props[ABCPropertyGraph.PROP_NAME] == node_name:
                return n
        raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                          msg=f"Unable to find node with name {node_name} "
                                              f"class {label} as child of {parent_node_id}")

    def get_all_link_interfaces(self, link_id: str) -> List[str]:
        assert link_id is not None
        # check this is a link
        labels, parent_props = self.get_node_properties(node_id=link_id)
        if ABCPropertyGraph.CLASS_Link not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=link_id,
                                              msg="Node type is not Link")
        return self.get_first_neighbor(node_id=link_id, rel=ABCPropertyGraph.REL_CONNECTS,
                                       node_label=ABCPropertyGraph.CLASS_ConnectionPoint)

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

    def get_all_network_node_or_component_sfs(self, parent_node_id: str) -> List[str]:
        assert parent_node_id is not None
        # check that parent is a NetworkNode or Component
        labels, parent_props = self.get_node_properties(node_id=parent_node_id)
        if ABCPropertyGraph.CLASS_NetworkNode not in labels and \
            ABCPropertyGraph.CLASS_Component not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=parent_node_id,
                                              msg="Parent node type is not NetworkNode or Component")
        return self.get_first_neighbor(node_id=parent_node_id, rel=ABCPropertyGraph.REL_HAS,
                                       node_label=ABCPropertyGraph.CLASS_SwitchFabric)

    def get_all_node_or_component_connection_points(self, parent_node_id: str) -> List[str]:
        """
        Get a list of interfaces attached via switch fabrics
        :param parent_node_id:
        :return:
        """
        assert parent_node_id is not None
        labels, parent_props = self.get_node_properties(node_id=parent_node_id)
        if ABCPropertyGraph.CLASS_NetworkNode not in labels and \
                ABCPropertyGraph.CLASS_Component not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=parent_node_id,
                                              msg="Parent node type is not NetworkNode or Component")
        sfs_ifs = self.get_first_and_second_neighbor(node_id=parent_node_id, rel1=ABCPropertyGraph.REL_HAS,
                                                     node1_label=ABCPropertyGraph.CLASS_SwitchFabric,
                                                     rel2=ABCPropertyGraph.REL_CONNECTS,
                                                     node2_label=ABCPropertyGraph.CLASS_ConnectionPoint)
        ret = list()
        # return only interface IDs, not interested in SwitchFabrics
        for tup in sfs_ifs:
            ret.append(tup[1])
        return ret

    def get_all_sf_connection_points(self, parent_node_id: str) -> List[str]:
        assert parent_node_id is not None
        # check that parent is a SwitchFabric
        labels, parent_props = self.get_node_properties(node_id=parent_node_id)
        if ABCPropertyGraph.CLASS_SwitchFabric not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=parent_node_id,
                                              msg="Parent node type is not SwitchFabric")
        return self.get_first_neighbor(node_id=parent_node_id, rel=ABCPropertyGraph.REL_CONNECTS,
                                       node_label=ABCPropertyGraph.CLASS_ConnectionPoint)

    def find_component_by_name(self, *, parent_node_id: str, component_name: str) -> str:

        component_id_list = self.get_all_network_node_components(parent_node_id=parent_node_id)
        for cid in component_id_list:
            _, cprops = self.get_node_properties(node_id=cid)
            if cprops[ABCPropertyGraph.PROP_NAME] == component_name:
                return cid
        raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                          msg=f"Unable to find component with name {component_name}")

    def find_sf_by_name(self, *, parent_node_id: str, sfname: str) -> str:

        sf_id_list = self.get_all_network_node_or_component_sfs(parent_node_id=parent_node_id)
        for cid in sf_id_list:
            _, cprops = self.get_node_properties(node_id=cid)
            if cprops[ABCPropertyGraph.PROP_NAME] == sfname:
                return cid
        raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                          msg=f"Unable to find SwitchFabric with name {sfname}")

    def find_connection_point_by_name(self, *, parent_node_id: str, iname: str) -> str:

        if_id_list = self.get_all_sf_connection_points(parent_node_id=parent_node_id)
        for cid in if_id_list:
            _, cprops = self.get_node_properties(node_id=cid)
            if cprops[ABCPropertyGraph.PROP_NAME] == iname:
                return cid
        raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                          msg=f"Unable to find ConnectionPoint with name {iname}")

    def remove_network_node_with_components_sfs_cps_and_links(self, node_id: str):
        """
        Remove a network node, all of components and their interfaces, parent interfaces
        and connected links (as appropriate)
        :param node_id:
        :return:
        """
        # the network node itself
        # its components and switch fabrics
        # component switch fabrics
        # switch fabric interfaces (if present)
        # their parent interfaces (if present)
        # the 'Link' objects connected to interfaces if only one or no other interface connects to them

        # check we are a network node
        labels, node_props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_NetworkNode not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg="This node type is not NetworkNode")
        # get a list of components
        components = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                             node_label=ABCPropertyGraph.CLASS_Component)
        for cid in components:
            self.remove_component_with_sfs_cps_and_links(node_id=cid)

        # get a list of switch fabrics, delete the node
        switch_fabrics = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                                 node_label=ABCPropertyGraph.CLASS_SwitchFabric)
        self.delete_node(node_id=node_id)
        for cid in switch_fabrics:
            self.remove_sf_with_cps_and_links(node_id=cid)

    def remove_component_with_sfs_cps_and_links(self, node_id: str):
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
        # get a list of SwitchFabrics, delete the node
        switch_fabrics = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                                 node_label=ABCPropertyGraph.CLASS_SwitchFabric)
        self.delete_node(node_id=node_id)
        for sf in switch_fabrics:
            self.remove_sf_with_cps_and_links(node_id=sf)

    def remove_network_link(self, node_id: str):

        # check we are a link
        labels, node_props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_Link not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg="This node type is not Link")
        # edges to interfaces/connection points will disappear
        self.delete_node(node_id=node_id)

    def remove_sf_with_cps_and_links(self, node_id: str):
        """
        Remove switch fabric with subtending interfaces and links
        :param node_id:
        :return:
        """
        # check we are a switch fabric
        labels, node_props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_SwitchFabric not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg="This node type is not SwitchFabric")
        # get a list of interfaces, delete the switch fabric
        interfaces = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_CONNECTS,
                                             node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
        self.delete_node(node_id=node_id)
        for iif in interfaces:
            self.remove_cp_and_links(node_id=iif)

    def remove_cp_and_links(self, node_id: str):
        """
        Remove ConnectionPoint and links. Parent ConnectionPoints and links are removed
        if they have no other children or other connected connection points.
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
                                            node_label=ABCPropertyGraph.CLASS_Link)
            for link in links:  # should only be one
                connected_interfaces = self.get_first_neighbor(node_id=link,
                                                               rel=ABCPropertyGraph.REL_CONNECTS,
                                                               node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
                if len(connected_interfaces) == 2:  # connected to us and another thing, can delete
                    links_to_delete.add(link)
        # delete nodes in these sets
        for deleted_id in interfaces_to_delete.union(links_to_delete):
            self.delete_node(node_id=deleted_id)

    def add_network_node_sliver(self, *, sliver: NodeSliver):

        assert sliver is not None
        assert sliver.node_id is not None
        assert self.check_node_unique(label=ABCPropertyGraph.CLASS_NetworkNode, name=sliver.resource_name)

        props = self.node_sliver_to_graph_properties_dict(sliver)
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

    def add_network_link_sliver(self, *, lsliver: NetworkLinkSliver, interfaces: List[str]):

        assert lsliver is not None
        assert lsliver.node_id is not None
        assert self.check_node_unique(label=ABCPropertyGraph.CLASS_Link, name=lsliver.resource_name)
        assert interfaces is not None

        props = self.link_sliver_to_graph_properties_dict(lsliver)
        self.add_node(node_id=lsliver.node_id, label=ABCPropertyGraph.CLASS_Link, props=props)
        # add edge links to specified interfaces
        for i in interfaces:
            self.add_link(node_a=lsliver.node_id, rel=ABCPropertyGraph.REL_CONNECTS, node_b=i)

    def add_component_sliver(self, *, parent_node_id: str, component: ComponentSliver):
        """
        Add network node component as a sliver, linking back to parent
        :param parent_node_id:
        :param component:
        :return:
        """
        assert component.node_id is not None
        assert parent_node_id is not None

        props = self.component_sliver_to_graph_properties_dict(component)
        self.add_node(node_id=component.node_id, label=ABCPropertyGraph.CLASS_Component, props=props)
        self.add_link(node_a=parent_node_id, rel=ABCPropertyGraph.REL_HAS, node_b=component.node_id)
        sfi = component.switch_fabric_info
        if sfi is not None:
            for sf in sfi.switch_fabrics.values():
                self.add_switch_fabric_sliver(parent_node_id=component.node_id,
                                              switch_fabric=sf)

    def add_switch_fabric_sliver(self, *, parent_node_id: str, switch_fabric: SwitchFabricSliver):
        """
        Add switch fabric as a sliver to either node or component, linking back to parent.
        :param parent_node_id:
        :param switch_fabric:
        :return:
        """
        assert parent_node_id is not None
        assert switch_fabric.node_id is not None

        props = self.switch_fabric_sliver_to_graph_properties_dict(switch_fabric)
        self.add_node(node_id=switch_fabric.node_id, label=ABCPropertyGraph.CLASS_SwitchFabric, props=props)
        self.add_link(node_a=parent_node_id, rel=ABCPropertyGraph.REL_HAS, node_b=switch_fabric.node_id)
        ii = switch_fabric.interface_info
        if ii is not None:
            for i in ii.interfaces.values():
                self.add_interface_sliver(parent_node_id=switch_fabric.node_id,
                                          interface=i)

    def add_interface_sliver(self, *, parent_node_id: str, interface: InterfaceSliver):
        """
        Add interface to a switch fabric, linking back to parent.
        :param parent_node_id: switch fabric id
        :param interface: interface sliver description
        :return:
        """
        assert interface.node_id is not None
        assert parent_node_id is not None

        props = self.interface_sliver_to_graph_properties_dict(interface)
        self.add_node(node_id=interface.node_id, label=ABCPropertyGraph.CLASS_ConnectionPoint, props=props)
        self.add_link(node_a=parent_node_id, rel=ABCPropertyGraph.REL_CONNECTS, node_b=interface.node_id)
