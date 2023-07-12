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
from typing import List, Dict, Tuple

import uuid

from ..abc_property_graph import ABCPropertyGraph, ABCPropertyGraphConstants
from fim.slivers.delegations import DelegationType
from fim.slivers.attached_components import AttachedComponentsInfo


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

    @abstractmethod
    def get_matching_nodes_with_components(self, *, label: str, props: Dict,
                                           comps: AttachedComponentsInfo = None) -> List[str]:
        """
        Return a list of Node IDs of network nodes of this class with these properties
        that have at least as many components of types and models as specified in comps.
        Models or types of comps can be omitted, in which case only a match based on the
        the one that is not omitted. Comps can be None in which case only a match
        on properties is performed.
        :param comps:
        :return:
        """

    @abstractmethod
    def get_intersite_links(self) -> List[Tuple]:
        """
        Get a list of unique intersite links, and return a list of tuples
        (Source NodeID, Link NodeID, Sink NodeID, Source Site, Sink Site,
        Source CP NodeID, Sink CP NodeID).
        :return:
        """

    @abstractmethod
    def get_sites(self) -> List[str]:
        """
        Return a lexicographically sorted list of site names in CBM topology
        """

    @abstractmethod
    def get_disconnected_sites(self) -> List[str]:
        """
        Return a lexicographically sorted list of site names that are disconnected in the CBM topology
        """

    @abstractmethod
    def get_connected_sites(self) -> List[str]:
        """
        Return a lexicographically sorted list of site names that are connected in the CBM topology
        """

    @abstractmethod
    def get_facility_ports(self) -> List[str]:
        """
        Return a lexicographically sorted list of names of facility ports in the CBM topology
        """