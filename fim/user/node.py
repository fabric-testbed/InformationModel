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
from .model_element import ModelElement, ElementType
from .component import Component, ComponentType
from .switch_fabric import SwitchFabric
from .interface import Interface

from ..graph.abc_property_graph import ABCPropertyGraph, PropertyGraphQueryException

from ..slivers.network_node import NodeSliver
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
        node_id will be generated if not provided for experiment topologies

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

            sliver = NodeSliver()
            sliver.node_id = self.node_id
            sliver.set_name(self.name)
            sliver.set_type(ntype)
            sliver.set_site(site)
            sliver.set_properties(**kwargs)

            self.topo.graph_model.add_network_node_sliver(sliver=sliver)
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            # check that this node exists
            existing_node_id = self.topo.graph_model.find_node_by_name(node_name=name,
                                                                       label=str(ABCPropertyGraph.CLASS_NetworkNode))
            if existing_node_id != node_id:
                raise RuntimeError(f'Node name {name} is not unique within the topology')

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
        Set a node property
        :param pname:
        :param pval:
        :return:
        """
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

    def add_component(self, *, name: str, node_id: str = None, ctype: ComponentType,
                      model: str,  switch_fabric_node_id: str = None, interface_node_ids=None,
                      **kwargs) -> Component:
        """
        Add a component of specified type, model and name to this node. When working with substrate
        topologies you must specify the switch_fabric_node_id and provide a list of interface node ids.
        :param name:
        :param node_id:
        :param ctype:
        :param model:
        :param name:
        :param switch_fabric_node_id:
        :param interface_node_ids:
        :param kwargs: additional properties of the component
        :return:
        """
        assert name is not None
        # make sure name is unique within the node
        if name in self.__list_components().keys():
            raise RuntimeError('Component names must be unique within node.')
        # add component node and populate properties
        c = Component(name=name, node_id=node_id, topo=self.topo, etype=ElementType.NEW,
                      ctype=ctype, model=model, switch_fabric_node_id=switch_fabric_node_id,
                      interface_node_ids=interface_node_ids, parent_node_id=self.node_id, **kwargs)
        return c

    def add_switch_fabric(self, *, name: str, node_id: str = None, layer: SFLayer):
        """
        Add a switch fabric to node (mostly needed in substrate topologies)
        :param name:
        :param node_id:
        :param layer:
        :return:
        """
        assert name is not None
        # make sure name is unique within the node
        if name in self.__list_switch_fabrics().keys():
            raise RuntimeError('SwitchFabric names must be unique within node.')
        sf = SwitchFabric(name=name, node_id=node_id, layer=layer, parent_node_id=self.node_id,
                          etype=ElementType.NEW, topo=self.topo)
        return sf

    def remove_component(self, name: str) -> None:
        """
        Remove a component from the node (and switch fabrics and their interfaces)
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.topo.graph_model.find_component_by_name(parent_node_id=self.node_id,
                                                               component_name=name)
        self.topo.graph_model.remove_component_with_sfs_cps_and_links(node_id=node_id)

    def remove_switch_fabric(self, name: str) -> None:
        """
        Remove a switch fabric from the node (and all its interfaces)
        :param name:
        :return:
        """
        assert name is not None

        node_id = self.topo.graph_model.find_sf_by_name(parent_node_id=self.node_id,
                                                        sfname=name)
        self.topo.graph_model.remove_sf_with_cps_and_links(node_id=node_id)

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

    def __get_sf_by_name(self, name: str) -> SwitchFabric:
        """
        Find SwitchFabric of a node by its name, return SwitchFabric object
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.topo.graph_model.find_sf_by_name(parent_node_id=self.node_id, component_name=name)
        return SwitchFabric(name=name, node_id=node_id, topo=self.topo)

    def __get_sf_by_id(self, node_id: str) -> SwitchFabric:
        """
        Get a switch fabric of a node by its node_id, return SwitchFabric object
        :param node_id:
        :return:
        """
        assert node_id is not None
        _, node_props = self.topo.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        return SwitchFabric(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id,
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

    def __list_switch_fabrics(self) -> ViewOnlyDict:
        """
        List all switch fabric children of a node as a dictionary organized
        by switch fabric name. Modifying the dictionary will not affect
        the underlying model, but modifying Components in the dictionary will.
        :return:
        """
        node_id_list = self.topo.graph_model.get_all_network_node_or_component_sfs(parent_node_id=self.node_id)
        ret = dict()
        for nid in node_id_list:
            c = self.__get_sf_by_id(nid)
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

    def __list_of_interfaces(self) -> Tuple[Any]:
        """
        List all interfaces of node and its components
        :return:
        """
        return tuple(self.__list_interfaces().values())

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
        if item == 'interface_list':
            return self.__list_of_interfaces()
        if item == 'direct_interfaces':
            return self.__list_direct_interfaces()
        if item == 'switch_fabrics':
            return self.__list_switch_fabrics()
        raise RuntimeError(f'Attribute {item} not available')

    def __repr__(self):
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        node_sliver = self.topo.graph_model.node_sliver_from_graph_properties_dict(node_properties)
        return node_sliver.__repr__()

    def __str__(self):
        return self.__repr__()


