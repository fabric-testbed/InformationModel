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
Abstract definition of ADM (Aggregate Delegation Model) functionality
"""
import json

from collections import defaultdict

from abc import ABCMeta, abstractmethod
from ..abc_property_graph import ABCPropertyGraph, PropertyGraphQueryException
from ...slivers.delegations import Delegations, Pools, DelegationType


class ABCADMPropertyGraph(ABCPropertyGraph):
    """
    Interface for an ADM Mixin on top of a property graph
    """

    @abstractmethod
    def __init__(self, *, graph_id: str, importer, logger=None):
        super().__init__(graph_id=graph_id, importer=importer, logger=logger)

    def rewrite_delegations(self, *, real_adm_id: str = None) -> None:
        """
        Rewrite label and capacity delegations on all nodes to be dictionaries
        referenced by ADM graph id. Note that external code should
        not interact with delegations on ADM graphs.
        Sometimes ADMs are cloned into temporary graphs so the method provides
        a way to pass original ADM id as an option.
        :param real_adm_id:
        :return:
        """
        for node_id in self.list_all_node_ids():
            _, node_props = self.get_node_properties(node_id=node_id)
            props_modified = False
            for delegation_prop_name in [self.PROP_LABEL_DELEGATIONS, self.PROP_CAPACITY_DELEGATIONS]:
                if delegation_prop_name in node_props.keys():
                    if node_props.get(delegation_prop_name, None) is None or \
                            node_props[delegation_prop_name] == self.NEO4j_NONE:
                        continue
                    props_modified = True
                    # turn delegation into Python object
                    delegations = Delegations.from_json(json_str=node_props[delegation_prop_name],
                                                        atype=DelegationType.LABEL if
                                                        delegation_prop_name == self.PROP_LABEL_DELEGATIONS else
                                                        DelegationType.CAPACITY)
                    if len(delegations.get_delegation_ids()) != 1:
                        raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                                          msg=f'This node contains delegation structure with more'
                                                              f'than one entry {delegations}')
                    # replace the one delegation id that should be present here with a graph id
                    # CAUTION: We directly manipulate the delegations object innards here for efficiency
                    del_id = list(delegations.get_delegation_ids())[0]
                    delegation = delegations.get_by_delegation_id(del_id)
                    if real_adm_id is None:
                        delegation.delegation_id = self.graph_id
                    else:
                        delegation.delegation_id = real_adm_id
                    delegations.delegations[delegation.delegation_id] = delegations.delegations.pop(del_id)
                    node_props[delegation_prop_name] = delegations.to_json()
            if props_modified:
                # write back
                self.update_node_properties(node_id=node_id, props=node_props)
