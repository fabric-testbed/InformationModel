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
# Author: Komal Thareja (kthare10@renci.org)
"""
Base class for all sliver types
"""
from abc import ABC, abstractmethod

from fim.slivers.capacities_labels import Capacities, Labels


class BaseElement(ABC):
    """Base class for all sliver types"""

    @abstractmethod
    def __init__(self):
        self.resource_type = None
        self.resource_name = None
        self.resource_model = None
        self.capacities = None
        self.labels = None
        self.node_id = None
        self.details = None
        self.verbose = False

    def set_resource_type(self, resource_type):
        """setter"""
        self.resource_type = resource_type

    def set_node_id(self, graph_node_id: str):
        """setter"""
        self.node_id = graph_node_id

    def set_resource_name(self, resource_name: str):
        self.resource_name = resource_name

    def set_resource_model(self, resource_model: str):
        self.resource_model = resource_model

    def set_model(self, resource_model: str):
        self.resource_model = resource_model

    def set_capacities(self, cap: Capacities) -> None:
        self.capacities = cap

    def set_labels(self, lab: Labels) -> None:
        self.labels = lab

    def set_details(self, desc: str) -> None:
        self.details = desc

    def print_verbose(self, f: bool) -> None:
        """
        Set verbosity for printing details of the sliver
        :param f:
        :return:
        """
        self.verbose = f

    def __repr__(self):
        # FIXME print the __dict__
        return 'ResourceType: ' + str(self.resource_type) + \
               '\nNodeID: ' + str(self.node_id)


class BaseElementWithDelegation(BaseElement):
    """
    Intended to be used in advertisements
    """
    def __init__(self):
        super().__init__()
        self.capacity_delegations = None
        self.label_delegations = None

    def set_capacity_delegations(self, cap_del) -> None:
        self.capacity_delegations = cap_del

    def set_label_delegations(self, lab_del) -> None:
        self.label_delegations = lab_del
