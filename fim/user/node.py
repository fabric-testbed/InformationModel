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

from .model_element import ModelElement, ElementType
from .component import Component, ComponentType
from .switch_fabric import SwitchFabric
from .interface import Interface

from ..graph.abc_property_graph import ABCPropertyGraph

from ..slivers.network_node import NodeSliver
from ..slivers.attached_components import ComponentSliver
from ..slivers.network_node import NodeType
from ..slivers.switch_fabric import SFLayer


class Node(ModelElement):
    """
    A basic node of the topology
    """

    def __init__(self, *, name: str, node_id: str = None, topo: Any, etype: ElementType = ElementType.EXISTING,
                 ntype: NodeType = None, site: str = None, **kwargs):
        """
        Don't call this method yourself, call topology.add_node()
        node_id will be generated if not provided.

        :param name:
        :param node_id:
        :param topo:
        :param etype: is this supposed to exist or new should be created
        :param ntype: node type if it is new
        :param site: node site
        :param kwargs: any additional properties
        """
        assert name is not None
        assert topo is not None

        if etype == ElementType.NEW:
            # cant use isinstance as it would create circular import dependencies
            # node id myst be specified for new nodes in substrate topologies
            if str(topo.__class__) == "<class 'fim.user.topology.SubstrateTopology'>" and \
                    node_id is None:
                raise RuntimeError("When adding new nodes to substrate topology nodes you must specify static Node ID")
            if node_id is None:
                node_id = str(uuid.uuid4())
            super().__init__(name=name, node_id=node_id, topo=topo)
            if ntype is None:
                raise RuntimeError("When creating nodes you must specify NodeType")
            if site is None:
                raise RuntimeError("When creating nodes you must specify site")

            self.node_id = node_id
            sliver = NodeSliver()
            sliver.set_node_id(self.node_id)
            sliver.set_resource_name(self.name)
            sliver.set_resource_type(ntype)
            sliver.set_site(site)
            # set anything that has a setter
            for k, v in kwargs.items():
                try:
                    # we can set anything the sliver model has a setter for
                    sliver.__getattribute__('set_' + k)(v)
                except AttributeError:
                    raise RuntimeError(f'Unable to set property {k} on the node - no such property available')

            self.topo.graph_model.add_network_node_sliver(sliver=sliver)
        else:
            if node_id is None:
                node_id = str(uuid.uuid4())
            super().__init__(name=name, node_id=node_id, topo=topo)
            # check that this node exists
            existing_node_id = self.topo.graph_model.find_node_by_name(node_name=name,
                                                                       label=str(ABCPropertyGraph.CLASS_NetworkNode))
            if node_id is not None and existing_node_id != node_id:
                raise RuntimeError("Existing node id does not match provided. "
                                   "In general you shouldn't need to specify node id for existing nodes.")
            self.node_id = node_id

    def add_component(self, *, name: str, node_id: str = None, ctype: ComponentType,
                      model: str,  switch_fabric_node_id: str = None, **kwargs) -> Component:
        """
        Add a component of specified type, model and name to this node. When working with substrate
        topologies you must specify the switch_fabric_node_id and provide a list of interface node ids.
        :param name:
        :param node_id:
        :param ctype:
        :param model:
        :param name:
        :param switch_fabric_node_id:
        :param kwargs: additional properties of the component
        :return:
        """
        # add component node and populate properties
        c = Component(name=name, node_id=node_id, topo=self.topo, etype=ElementType.NEW,
                      ctype=ctype, model=model, switch_fabric_node_id=switch_fabric_node_id,
                      parent_node_id=self.node_id, **kwargs)
        return c

    def add_switch_fabric(self, *, name: str, node_id: str = None, layer: SFLayer):
        """
        Add a switch fabric to node (mostly needed in substrate topologies)
        :param name:
        :param node_id:
        :param layer:
        :return:
        """
        sf = SwitchFabric(name=name, node_id=node_id, layer=layer, parent_node_id=self.node_id)
        return sf

    def remove_component(self, name: str) -> None:
        assert name is not None
        self.topo.graph_model.remove_component_with_interfaces_and_links(
            node_id=self.__get_component_by_name(name=name).node_id)

    def __get_component_by_name(self, name: str) -> Component:
        """
        Find component of a node by its name, return Component object
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.topo.graph_model.find_component_by_name(parent_node_id=self.node_id, component_name=name)
        return Component(name=name, node_id=node_id, topo=self.topo)

    def __get_component_by_id(self, node_id: str) -> Component:
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

    def __list_components(self) -> Dict[str, Component]:
        """
        List all Components children of a node in the topology as a dictionary
        organized by component name. Modifying the dictionary will not affect
        the underlying model, but modifying Components in the dictionary will.
        :return:
        """
        node_id_list = self.topo.graph_model.get_all_network_node_components(parent_node_id=self.node_id)
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
        _, node_props = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        ret = ""
        for prop in props_of_interest:
            if node_props.get(prop, None) is not None:
                ret = ret + node_props.get(prop, None) + ' '
        return ret
