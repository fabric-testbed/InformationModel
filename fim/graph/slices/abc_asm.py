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

from typing import List, Any
from abc import ABCMeta, abstractmethod

from fim.slivers.network_node import NodeSliver
from fim.slivers.attached_components import ComponentSliver
from fim.slivers.switch_fabric import SwitchFabricSliver
from fim.slivers.interface_info import InterfaceSliver


class ABCASMMixin(metaclass=ABCMeta):
    """
    Interface for an ASM Mixin on top of a property graph
    """
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'get_all_network_nodes') and
                callable(subclass.get_all_network_nodes) or NotImplemented)

    @abstractmethod
    def get_all_network_nodes(self) -> List[str]:
        """
        Get a list of nodes IDs in a slice model
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
    def find_node_by_name(self, node_name: str, label: str) -> str:
        """
        Get node id of node based on its name and class/label. Throw
        exception if multiple matches found.
        :param node_name:
        :param label: node label or class of the node
        :return:
        """

    @abstractmethod
    def remove_network_node_with_components_interfaces_and_links(self, node_id: str):
        """
        Remove a network node and all of its components from the graph
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
    def add_interface_sliver(self, *, node_id: str, interface: InterfaceSliver):
        """
        Add switching fabric (if needed) and an interface of the component
        :param node_id:
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


