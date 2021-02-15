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
Abstract definition of ARM (Aggregate Resource Model) functionality
"""

from abc import ABCMeta, abstractmethod
from typing import List

from ..abc_property_graph import ABCPropertyGraph
from fim.slivers.delegations import DelegationType


class ABCARMMixin(metaclass=ABCMeta):
    """
    Interface for an ARM Mixin on top of a property graph
    """
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'generate_adms') and
                callable(subclass.generate_adms) or NotImplemented)

    @abstractmethod
    def generate_adms(self) -> List[ABCPropertyGraph]:
        """
        Partition an already loaded ARM model into multiple ADMs, return the GUIDs
        of the ADM partitions
        :return:
        """

    @abstractmethod
    def get_delegations(self, *, node_id: str, delegation_type: DelegationType) -> List:
        """
        Get Label or Capacity delegation from an ARM as a Python object. They are represented
        as lists of dictionaries, with fields like ipv4, vlan or vlan-pool. May also include fields
        to denote specific delegations.
        :param node_id:
        :param delegation_type:
        :return:
        """