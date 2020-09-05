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
Implementation for Neo4j of ARM (Aggregate Resource Model) functionality
"""
from typing import List, Dict, Any
import json

from .abc_arm import ABCARMMixin
from ..neo4j_property_graph import Neo4jPropertyGraph
from ..abc_property_graph import PropertyGraphQueryException, PropertyGraphImportException
from ..typed_tuples import Label, Capacity, LabelException, LabelOrCapacityException, CapacityException

from ..pools import PoolType, Pool, Pools


class Neo4jARM(Neo4jPropertyGraph, ABCARMMixin):
    """
    Implementation of Neo4j ARM management
    """
    POOL_TYPE_TO_CLASS = {PoolType.LABEL:
                              (Neo4jPropertyGraph.PROP_LABEL_DELEGATIONS,
                               Neo4jPropertyGraph.FIELD_LABEL_POOL, Label),
                          PoolType.CAPACITY:
                              (Neo4jPropertyGraph.PROP_CAPACITY_DELEGATIONS,
                               Neo4jPropertyGraph.FIELD_CAPACITY_POOL, Capacity)}

    DEFAULT_DELEGATION = "default"

    def __init__(self, *, url: str, user: str, pswd: str, import_host_dir: str, import_dir: str):
        super().__init__(url=url, user=user, pswd=pswd, import_host_dir=import_host_dir, import_dir=import_dir)
        self.label_pools = Pools(atype=PoolType.LABEL)
        self.capacity_pools = Pools(atype=PoolType.CAPACITY)
        self.pools = {PoolType.LABEL: self.label_pools,
                      PoolType.CAPACITY: self.capacity_pools}

    def _find_pool_definition(self, *, delegation: Dict, pool_type: PoolType) -> (str, str):
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

    def _find_pool_mentions(self, *, delegation: Dict, pool_type: PoolType) -> List[str]:
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

    def _process_single_delegation(self, *, delegation: Dict, pool_type: PoolType, node_id: str):
        """
        Process a single delegation dictionary for pool definitions and pool mentions
        :param delegation:
        :param pool_type:
        :param node_id
        :return:
        """
        # check for pool definitions
        pool_id, del_id = self._find_pool_definition(delegation=delegation,
                                                     pool_type=pool_type)
        self.log.debug(f"Single: Decoded pool {pool_id}, delegation {del_id}")
        if pool_id is not None:
            # if the pool is not defined, create a new one, if it is defined augment the definition
            pool = self.pools[pool_type].get_pool_by_id(pool_id=pool_id)
            pool.set_delegation_id(delegation_id=del_id)
            pool.set_defined_on(node_id=node_id)
            pool.set_pool_details(pool_dict=delegation)

        # check for pool mentions
        pool_mentions = self._find_pool_mentions(delegation=delegation, pool_type=pool_type)
        for pool_id in pool_mentions:
            # if this pool already defined, add node id to list for which it is defined
            pool = self.pools[pool_type].get_pool_by_id(pool_id=pool_id)
            pool.add_defined_for(node_ids=node_id)

    def _find_pools(self, *, props: Dict, pool_type: PoolType, node_id: str) -> None:
        """
        Check if a delegation property of a node ( label or capacity) contains a
        pool (label or capacity) declaration, return a list of (pool_id, delegation_id, JSON delegation)
        tuples or empty list
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

            self.log.debug(f"Decoding {delegation_prop_name} delegations {props[delegation_prop_name]}")
            delegations = json.loads(props[delegation_prop_name])

            if not isinstance(delegations, list):
                if not isinstance(delegations, dict):
                    raise LabelOrCapacityException(f"Delegation {delegations} must be a list "
                                                   "of dictionaries or a dictionary")
                # just a single dictionary
                self._process_single_delegation(delegation=delegations,
                                                pool_type=pool_type, node_id=node_id)
            else:
                # a list of dictionaries
                for delegation in delegations:
                    self._process_single_delegation(delegation=delegation,
                                                    pool_type=pool_type, node_id=node_id)

    def _locate_delegations(self, *, graph_id: str) -> Dict[str, Any]:
        """
        Locate all nodes with delegations in them, taking into account pools.
        :param graph_id:
        :return:
        """
        assert graph_id is not None
        nodes = self.list_all_node_ids(graph_id=graph_id)
        if len(nodes) == 0:
            raise PropertyGraphQueryException(graph_id=graph_id, node_id=None, msg="Unable to list nodes of graph")

        # first pass over nodes: build a dictionary of pools to delegations
        # as well as cache all node properties for now
        pools_to_delegations = dict()
        nodes_props = dict()
        for node_id in nodes:
            props = self.get_node_properties(graph_id=graph_id, node_id=node_id)
            nodes_props[node_id] = props
            self.log.debug(f"Processing node {node_id} for {self.PROP_LABEL_DELEGATIONS} "
                           f"and {self.PROP_CAPACITY_DELEGATIONS}")
            # if a node doesn't have delegations we skip it
            if self.PROP_LABEL_DELEGATIONS not in props.keys() and \
                    self.PROP_CAPACITY_DELEGATIONS not in props.keys():
                continue
            # look for label and capacity pool definitions
            self._find_pools(props=props,
                             pool_type=PoolType.LABEL, node_id=node_id)

            self._find_pools(props=props,
                             pool_type=PoolType.CAPACITY, node_id=node_id)

            # look for pool mentions on all nodes' delegations

        print(f"Label pools {self.label_pools}")
        print(f"Capacity pools {self.capacity_pools}")

    def generate_adms(self) -> List[str]:
        """
        Generate delegation models from the current ARM graph and return the list of tuples <delegation, graph_id> for
        ADMs stored in Neo4j
        :return:
        """