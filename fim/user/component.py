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

from typing import Any, Dict, List

import uuid

from ..graph.abc_property_graph import ABCPropertyGraph
from .model_element import ModelElement, ElementType
from .interface import Interface
from .switch_fabric import SwitchFabric, SFLayer
from ..slivers.attached_components import ComponentSliver, ComponentType
from ..slivers.component_catalog import ComponentCatalog


class Component(ModelElement):
    """
    A component, like a GPU, a NIC, an FPGA or an NVMe drive
    """

    def __init__(self, *, name: str, node_id: str = None, topo: Any,
                 etype: ElementType = ElementType.EXISTING, model: str = None,
                 ctype: ComponentType = None, parent_node_id: str = None,
                 switch_fabric_node_id: str = None, interface_node_ids: List[str] = None,
                 **kwargs):
        """
        Don't call this yourself, use Node.add_component(). Instantiates components based on
        catalog resource file.
        :param name:
        :param node_id:
        :param topo:
        :param etype: is this supposed to be new or existing
        :param model: must be specified if a new component
        :param ctype: component type
        :param parent_node_id: node_id of the parent Node (for new components)
        :param switch_fabric_node_id: node id of switch fabric if one needs to be added (for substrate models only)
        :param interface_node_ids: a list of node ids for expected interfaces (for substrate models only)
        """

        assert name is not None
        assert topo is not None
        # cant use isinstance as it would create circular import dependencies
        if str(topo.__class__) == "<class 'fim.user.topology.SubstrateTopology'>" and node_id is None:
            raise RuntimeError("When adding components to substrate topology nodes you must specify static Node ID")
        if etype == ElementType.NEW and model is None:
            raise RuntimeError("When creating a new component, model must be specified")
        if node_id is None:
            node_id = str(uuid.uuid4())
        super().__init__(name=name, node_id=node_id, topo=topo)
        if etype == ElementType.NEW:
            if parent_node_id is None:
                raise RuntimeError("Parent node id must be specified for new components")
            if model is None or ctype is None:
                raise RuntimeError("Model and component type must be specified for new components")
            if str(topo.__class__) == "<class 'fim.user.topology.SubstrateTopology'>" and \
                    (ctype == ComponentType.SharedNIC or ctype == ComponentType.SmartNIC) and \
                    (switch_fabric_node_id is None or interface_node_ids is None):
                raise RuntimeError('For substrate topologies and components with network interfaces '
                                   'static switch_fabric node id and interface node ids must be specified')
            cata = ComponentCatalog()
            comp_sliver = cata.generate_component(name=name, model=model, ctype=ctype,
                                                  switch_fabric_node_id=switch_fabric_node_id,
                                                  interface_node_ids=interface_node_ids)
            comp_sliver.set_node_id(node_id)



            self.topo.graph_model.add_component_sliver(parent_node_id=parent_node_id, component=comp_sliver)
        else:
            # check that this node exists
            existing_node_id = self.topo.graph_model.find_node_by_name(node_name=name,
                                                                       label=str(ABCPropertyGraph.CLASS_Component))
            if node_id is not None and existing_node_id != node_id:
                raise RuntimeError("Existing node id does not match provided. "
                                   "In general you shouldn't need to specify node id for existing nodes.")
            self.node_id = node_id

    def __list_interfaces(self) -> Dict[str, Interface]:
        """
        List all interfaces of the topology as a dictionary
        :return:
        """
        raise RuntimeError("Not yet implemented")

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

    def __repr__(self):
        """
        Print concise information about the node
        :return:
        """
        # reach into the graph properties, pull out a few
        props_of_interest = ['Site', 'Type', 'Model', 'NodeID']
        _, node_props = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        ret = ""
        for prop in props_of_interest:
            if node_props.get(prop, None) is not None:
                ret = ret + node_props.get(prop, None) + ' '
        return ret
