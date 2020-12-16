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

from fim.slivers.network_node import Node


class ABCASMMixin(metaclass=ABCMeta):
    """
    Interface for an ASM Mixin on top of a property graph
    """
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'add_compute_node') and
                callable(subclass.add_compute_node) or NotImplemented)

    @abstractmethod
    def add_compute_node(self, n: Node):
        """
        Add a compute node to a slice
        :return:
        """

    @abstractmethod
    def get_all_nodes(self) -> List[Node]:
        """
        Get a list of nodes in a slice
        :return:
        """

