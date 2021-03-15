#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2021 FABRIC Testbed
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
from typing import Any, List, Dict, Tuple
import uuid

from fim.view_only_dict import ViewOnlyDict
from .model_element import ModelElement, ElementType
from .interface import Interface
from ..slivers.switch_fabric import SwitchFabricSliver, SFType, SFLayer
from ..slivers.interface_info import InterfaceType
from ..graph.abc_property_graph import ABCPropertyGraph


class SwitchFabric(ModelElement):
    """
    SwitchFabric class
    """
    def __init__(self, *, name: str, node_id: str = None, topo: Any,
                 etype: ElementType = ElementType.EXISTING,
                 layer: SFLayer = SFLayer.L2, parent_node_id: str = None):
        """
        Create a new switch fabric. Don't call this yourself, call Node.add_switch_fabric().
        NodeID is mandatory in substrate models.
        :param name:
        :param node_id:
        :param topo:
        :param layer: layer of the switch fabric (defaults to L2)
        :param parent_node_id: id of parent node for new nodes
        :param etype:
        """
        assert name is not None
        assert topo is not None

        if etype == ElementType.NEW:
            # cant use isinstance as it would create circular import dependencies
            if str(topo.__class__) == "<class 'fim.user.topology.SubstrateTopology'>" and node_id is None:
                raise RuntimeError(
                    "When adding switch fabrics to substrate topology nodes you must specify static Node ID")
            if node_id is None:
                node_id = str(uuid.uuid4())
            if parent_node_id is None:
                raise RuntimeError("For new switch fabrics parent node id must be specified")
            if str(topo.__class__) == "<class 'fim.user.topology.SubstrateTopology'>" and node_id is None:
                raise RuntimeError("When adding switch fabrics to substrate topology nodes "
                                   "you must specify static Node ID")
            super().__init__(name=name, node_id=node_id, topo=topo)
            sfsliver = SwitchFabricSliver()
            sfsliver.node_id = node_id
            sfsliver.set_name(name)
            sfsliver.set_type(SFType.SwitchFabric)
            sfsliver.set_layer(layer)
            self.topo.graph_model.add_switch_fabric_sliver(parent_node_id=parent_node_id, switch_fabric=sfsliver)
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            if not self.topo.graph_model.check_node_name(node_id=node_id, name=name,
                                                         label=ABCPropertyGraph.CLASS_SwitchFabric):
                raise RuntimeError(f"SwitchFabric with this id and name {name} doesn't exist")

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
        # check uniqueness
        if name in self.__list_interfaces().keys():
            raise RuntimeError('Interface names must be unique within a switch fabric')
        iff = Interface(name=name, node_id=node_id, parent_node_id=self.node_id,
                        etype=ElementType.NEW, topo=self.topo, itype=itype,
                        **kwargs)
        return iff

    def remove_interface(self, *, name: str) -> None:
        """
        Remove an interface from the switch fabric, disconnect from links. Remove links
        if they have nothing else connecting to them.
        :param name:
        :return:
        """
        assert name is not None

        node_id = self.topo.graph_model.find_connection_point_by_name(parent_node_id=self.node_id,
                                                                      iname=name)
        self.topo.graph_model.remove_cp_and_links(node_id=node_id)

    def get_property(self, pname: str) -> Any:
        """
        Retrieve a switch fabric property
        :param pname:
        :return:
        """
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        sf_sliver = self.topo.graph_model.switch_fabric_sliver_from_graph_properties_dict(node_properties)
        return sf_sliver.get_property(pname)

    def set_property(self, pname: str, pval: Any):
        """
        Set a switch fabric property
        :param pname:
        :param pval:
        :return:
        """
        sf_sliver = SwitchFabricSliver()
        sf_sliver.set_property(prop_name=pname, prop_val=pval)
        # write into the graph
        prop_dict = self.topo.graph_model.switch_fabric_sliver_to_graph_properties_dict(sf_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    def set_properties(self, **kwargs):
        """
        Set multiple properties of the switch fabtic
        :param kwargs:
        :return:
        """
        sf_sliver = SwitchFabricSliver()
        sf_sliver.set_properties(**kwargs)
        # write into the graph
        prop_dict = self.topo.graph_model.switch_fabric_sliver_to_graph_properties_dict(sf_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    @staticmethod
    def list_properties() -> Tuple[str]:
        return SwitchFabricSliver.list_properties()

    def __get_interface_by_id(self, node_id: str) -> Interface:
        """
        Get an interface of switch fabric by its node_id, return Interface object
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
        Get an interface of switch fabric by its name
        :param name:
        :return:
        """
        assert name is not None
        node_id = self.topo.graph_model.find_connection_point_by_name(parent_node_id=self.node_id,
                                                                      iname=name)
        return Interface(name=name, node_id=node_id, topo=self.topo)

    def __list_interfaces(self) -> ViewOnlyDict:
        """
        List all interfaces of the switch fabric as a dictionary
        :return:
        """
        node_id_list = self.topo.graph_model.get_all_sf_connection_points(parent_node_id=self.node_id)
        # Could consider using frozendict or other immutable idioms
        ret = dict()
        for nid in node_id_list:
            c = self.__get_interface_by_id(nid)
            ret[c.name] = c
        return ViewOnlyDict(ret)

    def __list_of_interfaces(self) -> Tuple[Interface]:
        """
        Return a list of all interfaces of switch fabric
        :return:
        """
        node_id_list = self.topo.graph_model.get_all_sf_connection_points(parent_node_id=self.node_id)
        ret = list()
        for nid in node_id_list:
            c = self.__get_interface_by_id(nid)
            ret.append(c)
        return tuple(ret)

    def __getattr__(self, item):
        """
        Special handling for attributes like 'components' and 'interfaces' -
        which query into the model. They return dicts and list
        containers. Modifying containers does not affect the underlying
        graph mode, but modifying elements of lists or values of dicts does.
        :param item:
        :return:
        """
        if item == 'interfaces':
            return self.__list_interfaces()
        if item == 'interface_list':
            return self.__list_of_interfaces()
        raise RuntimeError(f'Attribute {item} not available')

    def __repr__(self):
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        sf_sliver = self.topo.graph_model.switch_fabric_sliver_from_graph_properties_dict(node_properties)
        return sf_sliver.__repr__()

    def __str__(self):
        return self.__repr__()

