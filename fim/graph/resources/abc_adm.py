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

from abc import ABCMeta, abstractmethod
from ..abc_property_graph import ABCPropertyGraph
from ...slivers.delegations import ARMDelegations, ARMPools, DelegationType


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
                    delegation = json.loads(node_props[delegation_prop_name])
                    new_delegation = dict()
                    if real_adm_id is None:
                        new_delegation[self.graph_id] = delegation
                    else:
                        new_delegation[real_adm_id] = delegation
                    new_delegation_json = json.dumps(new_delegation)
                    node_props[delegation_prop_name] = new_delegation_json
            if props_modified:
                # write back
                self.update_node_properties(node_id=node_id, props=node_props)

    def annotate_delegations_and_pools(self, *, dels: ARMDelegations, pools: ARMPools):
        """
        Take delegations and pools and write them into the graph as appropriate.
        This assumes that pools.build_index_by_delegation_id() has been run.
        Pools and delegations are assumed to be of the same type (Capacity or Label).
        :param dels:
        :param pools:
        :return:
        """
        assert dels is not None
        assert pools is not None
        assert pools.pool_type == dels.type

        delegations_and_pools_per_node = dict()

        # delegations are organized in lists by delegation id, each delegation
        # is a label or capacity specification with delegation id
        # need to break them up by node to attach to appropriate nodes
        for k, v in dels.delegations.items():
            # each entry is a list
            for d in v:
                # multiple (capacity or label) delegations can be defined on the same node
                node_delegations = delegations_and_pools_per_node.get(d.on_, list())
                full_details = d.get_full_details()
                if full_details is not None:
                    node_delegations.append(full_details)
                    delegations_and_pools_per_node[d.on_] = node_delegations

        # pools are more complicated than delegations.
        # A pool definition includes capacities or labels,
        # a delegation id and a pool id. Pool mentions must be present on all nodes
        # included in the pool (including the node where pool is defined).

        # we need a place to put pool mentions for now
        pool_mentions_per_node = dict()

        if pools.pools_by_delegation is not None:
            for k, pool_list in pools.pools_by_delegation.items():
                # each entry is a list
                for pool in pool_list:
                    node_delegations = delegations_and_pools_per_node.get(pool.on_, list())
                    full_details = pool.get_full_pool_details()
                    if full_details is not None:
                        node_delegations.append(full_details)
                        delegations_and_pools_per_node[pool.on_] = node_delegations
                        node_mentions = set()
                        node_mentions.update(pool.get_defined_for())
                        node_mentions.add(pool.on_)
                        # add self on_ and for_ mentions into pool_mentions_per_node
                        for for_node in node_mentions:
                            node_pool_list = pool_mentions_per_node.get(for_node, list())
                            node_pool_list.append(pool.pool_id)
                            pool_mentions_per_node[for_node] = node_pool_list

        # update graph from delegations_and_pools and pool_mentions per node
        # get the combined set of affected node ids
        affected_nodes = set()
        affected_nodes.update(delegations_and_pools_per_node.keys())
        affected_nodes.update(pool_mentions_per_node.keys())

        for node in affected_nodes:
            node_delegations = list()
            if delegations_and_pools_per_node.get(node, None) is not None:
                node_delegations.extend(delegations_and_pools_per_node[node])
            if pool_mentions_per_node.get(node, None) is not None:
                for pool_id in pool_mentions_per_node[node]:
                    node_delegations.append({ABCPropertyGraph.FIELD_POOL: pool_id})

            if dels.type == DelegationType.CAPACITY:
                self.update_node_property(node_id=node, prop_name=ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS,
                                          prop_val=json.dumps(node_delegations))
            else:
                self.update_node_property(node_id=node, prop_name=ABCPropertyGraph.PROP_LABEL_DELEGATIONS,
                                          prop_val=json.dumps(node_delegations))
