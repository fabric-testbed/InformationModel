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

from typing import Any, List, Tuple

import uuid

from .model_element import ModelElement, ElementType

from ..slivers.interface_info import InterfaceType, InterfaceSliver
from ..graph.abc_property_graph import ABCPropertyGraph


class Interface(ModelElement):

    def __init__(self, *, name: str, node_id: str = None, topo: Any,
                 etype: ElementType = ElementType.EXISTING,
                 parent_node_id: str = None,
                 itype: InterfaceType = None, **kwargs):
        """
        Don't call this method yourself, call node.add_interface()
        node_id will be generated if not provided for experiment topologies

        :param name:
        :param node_id:
        :param topo:
        :param etype: is this supposed to exist or new should be created
        :param parent_node_id: parent network service or parent interface
        :param itype: node type if it is new
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
            if itype is None:
                raise RuntimeError("When creating interfaces you must specify InterfaceType")
            super().__init__(name=name, node_id=node_id, topo=topo)
            sliver = InterfaceSliver()
            sliver.node_id = self.node_id
            sliver.set_name(self.name)
            sliver.set_type(itype)
            sliver.set_properties(**kwargs)

            self.topo.graph_model.add_interface_sliver(parent_node_id=parent_node_id, interface=sliver)
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            if not self.topo.graph_model.check_node_name(node_id=node_id, name=name,
                                                         label=ABCPropertyGraph.CLASS_ConnectionPoint):
                raise RuntimeError(f"Interface with this id and name {name} doesn't exist")

    def add_child_interface(self):
        raise RuntimeError("Not implemented")

    def get_property(self, pname: str) -> Any:
        """
        Retrieve a interface property
        :param pname:
        :return:
        """
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        if_sliver = self.topo.graph_model.interface_sliver_from_graph_properties_dict(node_properties)
        return if_sliver.get_property(pname)

    def set_property(self, pname: str, pval: Any):
        """
        Set a interface property
        :param pname:
        :param pval:
        :return:
        """
        if_sliver = InterfaceSliver()
        if_sliver.set_property(prop_name=pname, prop_val=pval)
        # write into the graph
        prop_dict = self.topo.graph_model.interface_sliver_to_graph_properties_dict(if_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    def set_properties(self, **kwargs):
        """
        Set multiple properties of the interface
        :param kwargs:
        :return:
        """
        if_sliver = InterfaceSliver()
        if_sliver.set_properties(**kwargs)
        # write into the graph
        prop_dict = self.topo.graph_model.interface_sliver_to_graph_properties_dict(if_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    @staticmethod
    def list_properties() -> Tuple[str]:
        return InterfaceSliver.list_properties()

    def get_peer(self):
        """
        Find a 'peer' interface connected across a Link. Returns Interface object.
        :return: peer Interface object or None
        """
        peer_id = self.topo.graph_model.find_peer_connection_point(node_id=self.node_id)
        if peer_id is None:
            return None
        clazzes, node_props = self.topo.graph_model.get_node_properties(node_id=peer_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        assert ABCPropertyGraph.CLASS_ConnectionPoint in clazzes
        return Interface(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=peer_id,
                         topo=self.topo)

    def __repr__(self):
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        if_sliver = self.topo.graph_model.interface_sliver_from_graph_properties_dict(node_properties)
        return if_sliver.__repr__()

    def __str__(self):
        return self.__repr__()
