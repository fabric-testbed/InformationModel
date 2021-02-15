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

from typing import Any, Dict

import uuid

from .model_element import ModelElement
from .interface import Interface
from ..slivers.attached_components import ComponentSliver, ComponentType


class Component(ModelElement):
    """
    A component, like a GPU, a NIC, an FPGA or an NVMe drive
    """

    def __init__(self, *, name: str, node_id: str = None, parent: Any, topo: Any):

        if node_id is None:
            node_id = str(uuid.uuid4())
        super().__init__(name=name, node_id=node_id, parent=parent, topo=topo)

    def set_component_properties(self, *, name: str, node_id: str, ctype: ComponentType, model: str, **kwargs):

        self.sliver = ComponentSliver()
        self.sliver.set_resource_type(ctype)
        self.sliver.set_resource_name(name)
        self.sliver.set_resource_model(model)
        self.sliver.set_graph_node_id(node_id)
        for k, v in kwargs.items():
            try:
                # we can set anything the sliver model has a setter for
                if self.sliver.__getattribute__('set_' + k) is not None:
                    self.sliver.__getattribute__('set_' + k)(v)
            except AttributeError:
                raise RuntimeError('Unable to set attribute ' + k + ' on the component - no such attribute available')

    def get_component_sliver(self) -> ComponentSliver:
        return self.sliver

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
        _, node_props = self.topo.slice_model.get_node_properties(node_id=self.node_id)
        ret = ""
        for prop in props_of_interest:
            if node_props.get(prop, None) is not None:
                ret = ret + node_props.get(prop, None) + ' '
        return ret
