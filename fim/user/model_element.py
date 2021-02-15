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

from typing import Any
from abc import ABC, ABCMeta


class ModelElement(ABC):
    """
    Abstract element of a model
    """
    def __init__(self, *, name: str, node_id: str, parent: Any or None=None, topo: Any):
        """
        An element of topology relates to the topology object
        :param name:
        :param node_id:
        :param parent: Node or Component or None
        :param topo: Topology
        """
        assert name is not None
        assert node_id is not None
        assert topo is not None
        self.name = name
        self.parent = parent
        self.topo = topo
        self.node_id = node_id
        self.sliver = None

    def set_parent(self, parent: Any):
        """
        Set parent of this element (typically None for Node, Node for Component and
        Component or Interface for Interface)
        :param parent:
        :return:
        """
        self.parent = parent

    def rename(self, new_name: str):
        """
        Rename the model element in the model graph
        :param new_name:
        :return:
        """
        assert new_name is not None
        self.name = new_name
        self.topo.slice_model.update_node_property(node_id=self.node_id,
                                                   prop_name='Name',
                                                   prop_val=new_name)
