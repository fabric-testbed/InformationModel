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
Abstract definition of CBM (Combined Broker Model) functionality.
"""
from abc import ABCMeta, abstractmethod
from typing import List

import uuid

from ..abc_property_graph import ABCPropertyGraph, ABCPropertyGraphConstants
from fim.slivers.delegations import DelegationType


class ABCCBMPropertyGraph(ABCPropertyGraph):
    """
    Abstract definition of CBM
    """
    @abstractmethod
    def merge_adm(self, *, adm: ABCPropertyGraph) -> None:
        """
        Add an ADM to the CBM model
        :param adm:
        :return:
        """

    @abstractmethod
    def unmerge_adm(self, *, graph_id: str) -> None:
        """
        Unmerge an ADM with this graph id from CBM
        :param graph_id:
        :return:
        """

    def snapshot(self) -> str:
        """
        Take a snapshot of CBM and return its graph ID
        :return:
        """
        new_graph_id = str(uuid.uuid4())
        self.clone_graph(new_graph_id=new_graph_id)

        return new_graph_id

    def rollback(self, *, graph_id: str) -> None:
        """
        Roll back CBM to a specified snapshot,
        deleting the snapshot. Note that no checks are done
        that the offered graph_id belongs to a CBM snapshot.
        :param graph_id: if None, use previous snapshot
        :return:
        """
        assert graph_id is not None
        # delete self
        self.delete_graph()
        # clone other graph into self
        cbm_temp = self.importer.cast_graph(graph_id=graph_id)
        # renumber cbm temp to be the original graph id
        cbm_temp.update_nodes_property(prop_name=ABCPropertyGraphConstants.GRAPH_ID,
                                       prop_val=self.graph_id)

    @abstractmethod
    def get_bqm(self, **kwargs) -> ABCPropertyGraph:
        """
        Return a BQM (Broker Query Model) graph filtered depending on parameters
        :param kwargs:
        :return:
        """

    @abstractmethod
    def get_delegations(self, *, node_id: str, adm_id: str, delegation_type: DelegationType) -> List:
        """
        Retrieve Label or Capacity delegations attribuited to a particular ADM as a python object.
        Individual delegations are lists of dictionaries with possible pool designators.
        :param node_id:
        :param adm_id:
        :param delegation_type:
        :return:
        """

