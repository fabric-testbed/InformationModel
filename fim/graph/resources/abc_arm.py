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
from typing import Dict, Tuple, Set,  List
from abc import abstractmethod
from recordclass import recordclass
from collections import defaultdict
import uuid

from ..abc_property_graph import ABCPropertyGraph, PropertyGraphQueryException
from fim.slivers.delegations import DelegationType, Pools, Delegations


class ABCARMPropertyGraph(ABCPropertyGraph):
    """
    Interface for an ARM Mixin on top of a property graph
    """
    DELEGATION_TYPE_TO_PROP = {DelegationType.LABEL: ABCPropertyGraph.PROP_LABEL_DELEGATIONS,
                               DelegationType.CAPACITY: ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS}

    DelegationInfo = recordclass('DelegationInfo', ['graph_id',
                                                    'graph',
                                                    'keep_nodes',
                                                    'remove_nodes'])

    @abstractmethod
    def __init__(self, *, graph: ABCPropertyGraph, logger=None):
        """
        Initialize ARM - supply an implementation of a graph and a graph id
        :param graph:
        :param graph:
        """
        super().__init__(graph_id=graph.graph_id, importer=graph.importer, logger=logger)
        self.node_ids = None

    def catalog_delegations(self) -> Tuple[set[str], Dict[str, Set[str]],
                                           Dict[str, Dict[DelegationType, Delegations]]]:
        """
        Collect all delegations from nodes in the graph.
        Return a set of unique delegation IDs, a dictionary of sets of definite 'keep nodes' by delegation
        and athe dictionary of Delegations organized by node id and delegation type.
        { 'node1': { LABEL: <delegation object>, CAPACITY: <delegation object> } }
        :return:
        """
        unique_delegation_ids = set()
        ret = dict()
        keep_node_sets = defaultdict(set)
        # for efficiency loop over nodes first
        for node in self.node_ids:
            by_type = dict()
            do_add = False
            for atype in [DelegationType.LABEL, DelegationType.CAPACITY]:
                ds = self.get_delegations(node_id=node, delegation_type=atype)
                if ds is None:
                    continue
                unique_delegation_ids.update(ds.get_delegation_ids())
                by_type[atype] = ds
                do_add = True
                for d in ds.get_delegations_as_list():
                    keep_node_sets[d.get_delegation_id()].add(node)
            if do_add:
                ret[node] = by_type
        return unique_delegation_ids, keep_node_sets, ret

    @staticmethod
    def _update_delegations_on_node(*, graph, node_id: str, prop_name: str, prop_val: Delegations or None) -> None:
        """
        Update delegation for labels or capacities (delete if node_val is none)
        :param graph: graph to make changes to
        :param node_id:
        :param prop_name:
        :param prop_val: a delegations object or None
        :return:
        """
        if prop_val is None:
            graph.unset_node_property(node_id=node_id, prop_name=prop_name)
        else:
            graph.update_node_property(node_id=node_id, prop_name=prop_name,
                                       prop_val=prop_val.to_json())

    def generate_adms(self) -> Dict:
        """
        Generate delegation models from the current ARM graph and return
        the dictionary delegation_id: Neo4jPropertyGraph for generated ADMs
        :return:
        """
        self.node_ids = self.list_all_node_ids()
        if len(self.node_ids) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              node_id=None, msg="Unable to list nodes of ARM graph")

        # collect stitch nodes between graphs
        stitch_nodes = self.get_stitch_nodes()

        # catalog delegation IDs across all nodes to determine all unique delegation IDs and the nodes on
        # which delegations are specified.
        unique_delegation_ids, keep_nodes_sets, delegations_by_node = self.catalog_delegations()

        # generate unique graph ids and empty node sets for ADM graphs
        # add stitch nodes as keep nodes to all ADMs
        delegations_info = {del_id: ABCARMPropertyGraph.DelegationInfo(graph_id=str(uuid.uuid4()),
                                                        graph=None,
                                                        keep_nodes=keep_nodes_sets[del_id].union(stitch_nodes),
                                                        remove_nodes=set())
                            for del_id in unique_delegation_ids}

        # At this point we need to write back delegations for specific delegation ID
        # into separate ADM graphs, then determine additional keep nodes and remove
        # unneeded nodes from each.
        for del_id in unique_delegation_ids:
            # clone the original ARM graph into ADM graphs for each new graph ID
            delegations_info[del_id].graph = self.clone_graph(new_graph_id=delegations_info[del_id].graph_id)
            for node in self.node_ids:
                if delegations_by_node.get(node, None) is None:
                    continue
                for atype in [DelegationType.LABEL, DelegationType.CAPACITY]:
                    prop_field_name = self.DELEGATION_TYPE_TO_PROP[atype]
                    ds = None
                    if delegations_by_node[node].get(atype, None) is not None:
                        ds = delegations_by_node[node][atype].return_delegations_for_id(del_id)
                    # rewrite delegations
                    self._update_delegations_on_node(graph=delegations_info[del_id].graph, node_id=node,
                                                     prop_name=prop_field_name, prop_val=ds)

            # in addition to definite keep nodes, we should also keep nodes that
            # a) lie on shortest paths between two connection points we are keeping (to include the links)
            # b) network services that connect to connection points
            # c) network nodes that have network services
            # Determine nodes to delete by doing a difference between all nodes and keep nodes
            # Remove nodes
            # Annotate keep nodes with proper delegation information

            # get a list of connection points we are keeping
            keep_cps = set()
            all_cp_ids = self.get_all_nodes_by_class(label=ABCPropertyGraph.CLASS_ConnectionPoint)
            for node_id in delegations_info[del_id].keep_nodes:
                if node_id in all_cp_ids:
                    keep_cps.add(node_id)

            # trace from connection points over links to other connection points
            # remember connection points
            new_cps = set()
            for cp in keep_cps:
                cp_neighbors = self.get_first_and_second_neighbor(node_id=cp,
                                                                  rel1=ABCPropertyGraph.REL_CONNECTS,
                                                                  node1_label=ABCPropertyGraph.CLASS_Link,
                                                                  rel2=ABCPropertyGraph.REL_CONNECTS,
                                                                  node2_label=ABCPropertyGraph.CLASS_ConnectionPoint)
                for pair in cp_neighbors:
                    # pair is a 2-element list
                    delegations_info[del_id].keep_nodes.update(pair)
                    new_cps.add(pair[1])

            keep_cps.update(new_cps)
            # from all keep cps (original and added), find switch fabrics and components or
            # network nodes
            for cp in keep_cps:
                cp_neighbors = self.get_first_and_second_neighbor(node_id=cp,
                                                                  rel1=ABCPropertyGraph.REL_CONNECTS,
                                                                  node1_label=ABCPropertyGraph.CLASS_NetworkService,
                                                                  rel2=ABCPropertyGraph.REL_HAS,
                                                                  node2_label=ABCPropertyGraph.CLASS_NetworkNode)
                for pair in cp_neighbors:
                    delegations_info[del_id].keep_nodes.update(pair)

                cp_neighbors = self.get_first_and_second_neighbor(node_id=cp,
                                                                  rel1=ABCPropertyGraph.REL_CONNECTS,
                                                                  node1_label=ABCPropertyGraph.CLASS_NetworkService,
                                                                  rel2=ABCPropertyGraph.REL_HAS,
                                                                  node2_label=ABCPropertyGraph.CLASS_Component)
                for pair in cp_neighbors:
                    delegations_info[del_id].keep_nodes.update(pair)

            delegations_info[del_id].remove_nodes = set(self.node_ids)
            delegations_info[del_id].remove_nodes.difference_update(delegations_info[del_id].keep_nodes)
            for node_id in delegations_info[del_id].remove_nodes:
                delegations_info[del_id].graph.delete_node(node_id=node_id)

        return {k: delegations_info[k].graph for k in unique_delegation_ids}

    def get_delegations(self, *, node_id: str, delegation_type: DelegationType) -> Delegations or None:
        """
        Get Label or Capacity delegations of a given node.
        Returns None if delegation property is not defined.
        :param node_id:
        :param delegation_type:
        :return:
        """
        assert node_id is not None
        prop_field_name = self.DELEGATION_TYPE_TO_PROP[delegation_type]
        _, props = self.get_node_properties(node_id=node_id)
        if props.get(prop_field_name, None) is not None and \
                props[prop_field_name] != ABCARMPropertyGraph.NEO4j_NONE:
            return Delegations.from_json(json_str=props[prop_field_name], atype=delegation_type)
        return None

    def annotate_delegations_and_pools(self, *, dels: Dict[str, Delegations], pools: Pools):
        """
        Take delegations by node id and pools of the same type (Capacity or Label) and write them
        into the graph as appropriate. This assumes that pools.build_index_by_delegation_id()
        has been run.
        :param dels:
        :param pools:
        :return:
        """
        assert dels is not None
        assert pools is not None
        # Pools object knows how to transform itself into a dictionary of Delegations
        # objects of appropriate formats (pool definitions and pool references) organized
        # by node id. Delegations object can be directly serialized
        delegations_per_node = pools.generate_delegations_by_node_id()

        # incorporate single element delegations
        for node, ds in dels.items():
            if delegations_per_node.get(node, None) is not None:
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node,
                                                  msg=f"Node {node} already has delegations defined")
            delegations_per_node[node] = ds

        # update graph properties
        for node, v in delegations_per_node.items():
            if pools.get_type() == DelegationType.CAPACITY:
                self.update_node_property(node_id=node, prop_name=ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS,
                                          prop_val=v.to_json())
            else:
                self.update_node_property(node_id=node, prop_name=ABCPropertyGraph.PROP_LABEL_DELEGATIONS,
                                          prop_val=v.to_json())
