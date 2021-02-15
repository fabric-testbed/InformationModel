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

from typing import Dict, Any

import uuid

from .model_element import ModelElement
from .component import Component, ComponentType
from .interface import Interface

from ..graph.abc_property_graph import ABCPropertyGraph

from ..slivers.network_node import NodeSliver
from ..slivers.network_node import NodeType


class Node(ModelElement):
    """
    A basic node of the topology
    """

    def __init__(self, *, name: str, node_id: str = None, topo: Any):
        """
        Don't call this method yourself, call topology.add_node()
        node_id will be generated if not provded.

        :param name:
        :param node_id:
        :param topo:
        """
        if node_id is None:
            node_id = str(uuid.uuid4())
        super().__init__(name=name, node_id=node_id, topo=topo)

    def set_node_properties(self, *, name: str, node_id: str, ntype: NodeType, site: str, **kwargs):
        """
        Set properties of a new node.
        kwargs let you set the various parameters of the node
        cpu_cores
        ram_size
        disk_size
        image_type
        image_ref
        :param name:
        :param node_id:
        :param ntype:
        :param site:
        :param topo:
        :param kwargs:
        :return:
        """
        self.sliver = NodeSliver()
        self.sliver.set_site(site)
        self.sliver.set_resource_name(name)
        self.sliver.set_resource_type(ntype)
        self.sliver.set_graph_node_id(node_id)
        for k, v in kwargs.items():
            try:
                # we can set anything the sliver model has a setter for
                if self.sliver.__getattribute__('set_' + k) is not None:
                    self.sliver.__getattribute__('set_' + k)(v)
            except AttributeError:
                raise RuntimeError('Unable to set attribute ' + k + ' on the node - no such attribute available')

    def get_sliver(self):
        return self.sliver

    def add_component(self, *, ctype: ComponentType, model: str, name: str, **kwargs) -> Component:
        """
        Add a component of specified type, model and name to this node
        :param ctype:
        :param model:
        :param name:
        :param kwargs: additional properties of the component
        :return:
        """
        # check graph doesn't contain component with this name on this node
        # add component node and populate properties
        c = Component(name=name, parent=self, topo=self.topo)
        c.set_component_properties(name=name, node_id=c.node_id, ctype=ctype, model=model, **kwargs)
        self.topo.slice_model.add_network_node_component_sliver(parent_node_id=self.node_id,
                                                                component=c.get_component_sliver())
        return c

    def remove_component(self, name: str) -> None:
        assert name is not None
        self.topo.slice_model.remove_component_with_interfaces_and_links(
            node_id=self.__get_component_by_name(name=name).node_id)

    def __get_component_by_name(self, name: str) -> Component:
        """
        Find component of a node by its name, return Component object
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.topo.slice_model.find_component_by_name(parent_node_id=self.node_id, component_name=name)
        return Component(name=name, node_id=node_id, parent=self, topo=self.topo)

    def __get_component_by_id(self, node_id: str) -> Component:
        """
        Get component of a node by its node_id, return Component object
        :param node_id:
        :return:
        """
        assert node_id is not None
        _, node_props = self.topo.slice_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        return Component(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id, parent=self, topo=self.topo)

    def __list_components(self) -> Dict[str, Component]:
        """
        List all Components children of a node in the topology as a dictionary
        organized by component name. Modifying the dictionary will not affect
        the underlying model, but modifying Components in the dictionary will.
        :return:
        """
        node_id_list = self.topo.slice_model.get_all_network_node_components(parent_node_id=self.node_id)
        # Could consider using frozendict or other immutable idioms
        ret = dict()
        for nid in node_id_list:
            c = self.__get_component_by_id(nid)
            ret[c.name] = c
        return ret

    def __list_interfaces(self) -> Dict[str, Interface]:
        """
        List all interfaces of the node as a dictionary
        :return:
        """
        raise RuntimeError("Not yet implemented")

    def get_component(self, name: str):
        """
        Get a component by this name
        :param name:
        :return:
        """
        return self.__get_component_by_name(name)

    def __getattr__(self, item):
        """
        Special handling for attributes like 'components' and 'interfaces' -
        which query into the model. They return dicts and list
        containers. Modifying containers does not affect the underlying
        graph mode, but modifying elements of lists or values of dicts does.
        :param item:
        :return:
        """
        if item == 'components':
            return self.__list_components()
        if item == 'interfaces':
            return self.__list_interfaces()

    def __repr__(self):
        """
        Print concise information about the node
        :return:
        """
        # reach into the graph properties, pull out a few
        props_of_interest = ['Site', 'Type', 'NodeID']
        _, node_props = self.topo.slice_model.get_node_properties(node_id=self.node_id)
        ret = ""
        for prop in props_of_interest:
            if node_props.get(prop, None) is not None:
                ret = ret + node_props.get(prop, None) + ' '
        return ret

