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
from typing import Any
import uuid

from .model_element import ModelElement, ElementType
from ..slivers.switch_fabric import SwitchFabricSliver, SFType, SFLayer
from ..graph.abc_property_graph import ABCPropertyGraph


class SwitchFabric(ModelElement):
    """
    SwitchFabric class
    """
    def __init__(self, *, name: str, node_id: str = None, topo: Any, etype: ElementType = ElementType.EXISTING,
                 layer: SFLayer = None, parent_node_id: str = None):
        """
        Create a new switch fabric. Don't call this yourself, call Node.add_switch_fabric().
        NodeID is mandatory in substrate models.
        :param name:
        :param node_id:
        :param topo:
        :param layer: layer of the switch fabric
        :param parent_node_id: id of parent node for new nodes
        :param etype:
        """
        assert name is not None
        assert topo is not None
        # cant use isinstance as it would create circular import dependencies
        super().__init__(name=name, node_id=node_id, topo=topo)
        if etype == ElementType.NEW:
            if parent_node_id is None:
                raise RuntimeError("For new switch fabrics parent node id must be specified")
            if str(topo.__class__) == "<class 'fim.user.topology.SubstrateTopology'>" and node_id is None:
                raise RuntimeError("When adding switch fabrics to substrate topology nodes "
                                   "you must specify static Node ID")
            if node_id is None:
                node_id = str(uuid.uuid4())
            sfsliver = SwitchFabricSliver()
            sfsliver.set_node_id(node_id)
            sfsliver.set_resource_name(name)
            sfsliver.set_resource_type(SFType.SwitchFabric)
            sfsliver.set_layer(layer)
            self.topo.graph_model.add_switch_fabric(parent_node_id=parent_node_id, switch_fabric=sfsliver)
        else:
            # check that this node exists
            existing_node_id = self.topo.graph_model.find_node_by_name(node_name=name,
                                                                       label=str(ABCPropertyGraph.CLASS_SwitchFabric))
            if node_id is not None and existing_node_id != node_id:
                raise RuntimeError("Existing node id does not match provided. "
                                   "In general you shouldn't need to specify node id for existing nodes.")
            self.node_id = node_id

    def add_interface(self):
        pass