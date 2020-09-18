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
Implementation of ARM (Aggregate Resource Model) functionality
"""
from typing import List, Dict, Any
from recordclass import recordclass
import json
import itertools
import logging
import uuid

from ..neo4j_property_graph import Neo4jPropertyGraph
from ..abc_property_graph import ABCPropertyGraph, PropertyGraphQueryException, PropertyGraphImportException
from .abc_arm import ABCARMMixin
from ..typed_tuples import Label, Capacity, LabelException, LabelOrCapacityException, CapacityException

from ..delegations import DelegationType, Pools, Delegations, Delegation


class Neo4jARMGraph(Neo4jPropertyGraph, ABCARMMixin):
    """
    Implementation of ARM management
    """
    POOL_TYPE_TO_CLASS = {DelegationType.LABEL: (ABCPropertyGraph.PROP_LABEL_DELEGATIONS,
                                                 ABCPropertyGraph.FIELD_LABEL_POOL, Label),
                          DelegationType.CAPACITY: (ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS,
                                                    ABCPropertyGraph.FIELD_CAPACITY_POOL, Capacity)}

    DEFAULT_DELEGATION = "default"

    def __init__(self, *, graph: Neo4jPropertyGraph):
        """
        Initialize ARM - supply an implementation of a graph and a graph id
        :param graph_id:
        :param graph:
        """
        super().__init__(graph_id=graph.graph_id, importer=graph.importer)
        self.label_pools = Pools(atype=DelegationType.LABEL)
        self.capacity_pools = Pools(atype=DelegationType.CAPACITY)
        self.label_delegations = Delegations(atype=DelegationType.LABEL)
        self.capacity_delegations = Delegations(atype=DelegationType.CAPACITY)
        self.pools = {DelegationType.LABEL: self.label_pools,
                      DelegationType.CAPACITY: self.capacity_pools}
        self.delegations = {DelegationType.LABEL: self.label_delegations,
                            DelegationType.CAPACITY: self.capacity_delegations}
        self.log = logging.getLogger(__name__)
        self.node_ids = None
        self.node_props = dict()

    def _find_pool_definition(self, *, delegation: Dict, pool_type: DelegationType) -> (str, str):
        """
        Inspect a single delegation to find pool definition and delegation fields, return as a Tuple
        <pool_id, delegation_id>. When delegation is not specified, delegation_id is set to "default".
        :param delegation: single dictionary of a delegation
        :param delegation_prop_name: name of a property for pool definition (label_pool or capacity_pool)
        :return:
        """
        _, pool_field, pool_cls = self.POOL_TYPE_TO_CLASS[pool_type]
        self.log.debug(f"Looking for pool definition in {delegation} of type {pool_type.name}")
        if pool_field in delegation.keys():
            # parse the delegation pool
            pool = pool_cls(atype=pool_field, aval=delegation[pool_field])
            if self.FIELD_DELEGATION in delegation.keys():
                delegation_id = delegation[self.FIELD_DELEGATION]
            else:
                delegation_id = self.DEFAULT_DELEGATION
            return pool.get_val(), delegation_id
        else:
            return None, None

    def _find_pool_mentions(self, *, delegation: Dict, pool_type: DelegationType) -> List[str]:
        """
        Inspect a single delegation to find pool mentions and return a list of all mentioned pool_ids
        or empty list
        :param delegation: single dictionary of a delegation
        :param pool_type:
        :return:
        """
        _, pool_field, pool_cls = self.POOL_TYPE_TO_CLASS[pool_type]
        self.log.debug(f"Looking for pool mention in {delegation} of type {pool_type.name}")
        if Neo4jPropertyGraph.FIELD_POOL in delegation.keys():
            # return the list
            mention = delegation[Neo4jPropertyGraph.FIELD_POOL]
            if isinstance(mention, list):
                return mention
            else:
                return [mention]
        else:
            return []

    def _process_delegation_no_pools(self, *, delegation: Dict, dele_type: DelegationType, node_id: str) -> Delegation:
        """
        process a delegation with no pools, get a delegation wid from delegation dictionary or
        assign 'default' and return a fully formed Delegation object
        :param delegation:
        :param dele_type:
        :return: delegation id
        """
        # extract the delegation id
        if self.FIELD_DELEGATION in delegation.keys():
            delegation_id = delegation[self.FIELD_DELEGATION]
        else:
            delegation_id = self.DEFAULT_DELEGATION
        delegation_obj = Delegation(atype=dele_type, defined_on=node_id, delegation_id=delegation_id)
        delegation_obj.set_details(dele_dict=delegation)
        return delegation_obj

    def _process_single_delegation(self, *, delegation: Dict, dele_type: DelegationType, node_id: str):
        """
        Process a single delegation dictionary for pool definitions, pool mentions or individual delegations.
        Update pools and delegations fields of this object
        :param delegation:
        :param dele_type:
        :param node_id
        :return:
        """
        # check for pool definitions
        pool_id, del_id = self._find_pool_definition(delegation=delegation,
                                                     pool_type=dele_type)
        self.log.debug(f"Single: Decoded pool {pool_id}, delegation {del_id}")
        with_pool = False

        if pool_id is not None:
            # if the pool is not defined, create a new one, if it is defined augment the definition
            pool = self.pools[dele_type].get_pool_by_id(pool_id=pool_id)
            pool.set_delegation_id(delegation_id=del_id)
            pool.set_defined_on(node_id=node_id)
            pool.set_pool_details(pool_dict=delegation)
            with_pool = True

        # check for pool mentions
        pool_mentions = self._find_pool_mentions(delegation=delegation, pool_type=dele_type)
        for pool_id in pool_mentions:
            # if this pool already defined, add node id to list for which it is defined
            pool = self.pools[dele_type].get_pool_by_id(pool_id=pool_id)
            pool.add_defined_for(node_ids=node_id)
            with_pool = True

        # check for plain delegation (without a pool)
        if not with_pool:
            delegation_obj = self._process_delegation_no_pools(delegation=delegation,
                                                               dele_type=dele_type,
                                                               node_id=node_id)
            self.delegations[dele_type].add_delegation(delegation=delegation_obj)

    def _find_delegations_in_properties(self, *, props: Dict, pool_type: DelegationType, node_id: str) -> None:
        """
        Check if a delegation property of a node ( label or capacity) contains a
        pool (label or capacity) declaration, return a list of (pool_id, delegation_id, JSON delegation)
        tuples or empty list. Also process single delegations not included in pool definitions
        :param props: all properties of a node
        :param pool_type
        :param node_id
        :return:
        """
        if pool_type not in self.POOL_TYPE_TO_CLASS.keys():
            raise LabelOrCapacityException(f"Invalid pool type {pool_type}")

        delegation_prop_name, _, _ = self.POOL_TYPE_TO_CLASS[pool_type]
        self.log.debug(f"Checking properties {props} for {delegation_prop_name} pool definitions")
        if delegation_prop_name in props.keys():
            # get the list of delegations as a JSON string
            # note that Neo4j returns string 'None' if property is not filled, but present
            if props[delegation_prop_name] == self.NEO4j_NONE:
                return

            self.log.debug(f"Decoding {delegation_prop_name} delegations {props[delegation_prop_name]} on node {node_id}")
            delegations = json.loads(props[delegation_prop_name])

            if not isinstance(delegations, list):
                if not isinstance(delegations, dict):
                    raise LabelOrCapacityException(f"Delegation {delegations} must be a list "
                                                   "of dictionaries or a dictionary")
                # just a single dictionary
                self._process_single_delegation(delegation=delegations,
                                                dele_type=pool_type, node_id=node_id)
            else:
                # a list of dictionaries
                for delegation in delegations:
                    self._process_single_delegation(delegation=delegation,
                                                    dele_type=pool_type, node_id=node_id)

    def _catalog_delegations(self) -> None:
        """
        Locate all nodes with delegations in them, taking into account pools.
        :param graph_id:
        :return:
        """

        # collect information about pools
        for node_id in self.node_ids:
            _, props = self.get_node_properties(node_id=node_id)
            self.node_props[node_id] = props
            self.log.debug(f"Processing node {node_id} for {self.PROP_LABEL_DELEGATIONS} "
                           f"and {self.PROP_CAPACITY_DELEGATIONS}")
            # if a node doesn't have delegations we skip it
            if self.PROP_LABEL_DELEGATIONS not in props.keys() and \
                    self.PROP_CAPACITY_DELEGATIONS not in props.keys():
                continue
            # look for label and capacity pool definitions and mentions
            self._find_delegations_in_properties(props=props,
                                                 pool_type=DelegationType.LABEL, node_id=node_id)

            self._find_delegations_in_properties(props=props,
                                                 pool_type=DelegationType.CAPACITY, node_id=node_id)
            # also look for delegations without pools

        # build indices on pools so we can find them from a delegation id
        print("POOLS")
        for pool_type, pools in self.pools.items():
            # remember to biuld the index of the pools by delegation id
            pools.build_index_by_delegation_id()
            print(pool_type, pools)

        print("DELEGATIONS")
        for del_type, delegations in self.delegations.items():
            print(del_type, delegations)

    def generate_adms(self) -> List[ABCPropertyGraph]:
        """
        Generate delegation models from the current ARM graph and return
        the list of tuples <delegation, graph_id> for generated ADMs
        :return:
        """
        self.node_ids = self.list_all_node_ids()
        if len(self.node_ids) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              node_id=None, msg="Unable to list nodes of ARM graph")
        # collect information on delegated pools and individual delegations
        self._catalog_delegations()

        # number of distinct delegation keys across label and capacity pools and plain delegations
        # is the number of ADMs we will generate
        unique_delegation_ids = self.label_pools.\
            get_delegation_ids().union(self.capacity_pools.get_delegation_ids(),
                                       self.label_delegations.get_delegation_ids(),
                                       self.capacity_delegations.get_delegation_ids())

        # graph id, definite nodes to keep
        DelegationInfo = recordclass('DelegationInfo', ['graph_id',
                                                        'graph',
                                                        'keep_nodes',
                                                        'remove_nodes'])

        # generate unique graph ids and empty node sets for delegation graphs
        # remember these tuples and the fields are not mutable
        delegations_info = {del_id: DelegationInfo(graph_id=str(uuid.uuid4()),
                                                   graph=None,
                                                   keep_nodes=set(),
                                                   remove_nodes=set())
                            for del_id in unique_delegation_ids}

        node_ids_to_delegations = {node_id: list() for node_id in self.node_ids }
        for del_id in unique_delegation_ids:
            # build up lists of node ids that definitely belong to each delegation
            # as a union of all .for_ fields on pools and on all delegations
            delegations_info[del_id].keep_nodes.update(
                self.label_pools.get_node_ids(delegation_id=del_id),
                self.capacity_pools.get_node_ids(delegation_id=del_id),
                self.label_delegations.get_node_ids(delegation_id=del_id),
                self.capacity_delegations.get_node_ids(delegation_id=del_id)
            )
            # also build a dictionary from node_id to a list of delegation ids
            for node_id in delegations_info[del_id].keep_nodes:
                node_ids_to_delegations[node_id].append(del_id)
            # clone the original ARM graph into ADM graphs for each new graph ID
            delegations_info[del_id].graph = self.clone_graph(new_graph_id=delegations_info[del_id].graph_id)

        # print(f"DELEGATIONS TO GRAPH IDS {delegations_info}")
        # print(f"NODES TO DELEGATIONS {node_ids_to_delegations}")

        # in addition to 'definite' keep nodes, we should also keep nodes that lie
        # on shortest paths between them (due to hierarchical structure of resources)
        for del_id in unique_delegation_ids:
            temp_node_set = set()
            for node_a, node_z in itertools.combinations(delegations_info[del_id].keep_nodes, 2):
                temp_node_set.update(self.get_nodes_on_shortest_path(node_a=node_a, node_z=node_z))
            delegations_info[del_id].keep_nodes.update(temp_node_set)

        print(f"Full keep nodes for del1: {delegations_info['del1'].keep_nodes}")

        all_nodes_set = set(self.node_ids)
        all_nodes_set.difference_update(delegations_info["del1"].keep_nodes)

        print(f"Full delete nodes for del1: {all_nodes_set}")

        return [x.graph for x in delegations_info.values()]

