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
from typing import Dict
from abc import abstractmethod
from typing import List
from recordclass import recordclass
import json
import uuid

from ..abc_property_graph import ABCPropertyGraph, PropertyGraphQueryException
from fim.slivers.delegations import Delegation, DelegationType, Pool, ARMPools, ARMDelegations
from ..typed_tuples import Label, Capacity, LabelOrCapacityException


class ABCARMPropertyGraph(ABCPropertyGraph):
    """
    Interface for an ARM Mixin on top of a property graph
    """
    POOL_TYPE_TO_CLASS = {DelegationType.LABEL: (ABCPropertyGraph.PROP_LABEL_DELEGATIONS,
                                                 ABCPropertyGraph.FIELD_LABEL_POOL, Label),
                          DelegationType.CAPACITY: (ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS,
                                                    ABCPropertyGraph.FIELD_CAPACITY_POOL, Capacity)}

    DEFAULT_DELEGATION = "default"
    LabelsAndProperties = recordclass('LabelsAndProperties', ['labels', 'properties'])
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
        self.label_pools = ARMPools(atype=DelegationType.LABEL)
        self.capacity_pools = ARMPools(atype=DelegationType.CAPACITY)
        self.label_delegations = ARMDelegations(atype=DelegationType.LABEL)
        self.capacity_delegations = ARMDelegations(atype=DelegationType.CAPACITY)
        self.pools = {DelegationType.LABEL: self.label_pools,
                      DelegationType.CAPACITY: self.capacity_pools}
        self.delegations = {DelegationType.LABEL: self.label_delegations,
                            DelegationType.CAPACITY: self.capacity_delegations}
        self.nodes = dict()
        self.node_ids = None

    def _find_pool_definition(self, *, delegation: Dict, pool_type: DelegationType) -> (str, str):
        """
        Inspect a single delegation to find pool definition and delegation fields, return as a Tuple
        <pool_id, delegation_id>. When delegation is not specified, delegation_id is set to "default".
        :param delegation: single dictionary of a delegation
        :param pool_type: type of a pool (label or capacity)
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
        return None, None

    def _find_pool_mentions(self, *, delegation: Dict, pool_type: DelegationType) -> List[str]:
        """
        Inspect a single delegation to find pool mentions and return a list of all mentioned pool_ids
        or empty list
        :param delegation: single dictionary of a delegation
        :param pool_type:
        :return:
        """
        self.log.debug(f"Looking for pool mention in {delegation} of type {pool_type.name}")
        if ABCARMPropertyGraph.FIELD_POOL in delegation.keys():
            # return the list
            mention = delegation[ABCARMPropertyGraph.FIELD_POOL]
            if isinstance(mention, list):
                return mention
            return [mention]
        return []

    def _process_delegation_no_pools(self, *, delegation: Dict, dele_type: DelegationType, node_id: str) -> Delegation:
        """
        process a delegation with no pools, get a delegation id from delegation dictionary or
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
            if props.get(delegation_prop_name, None) is None or \
                    props[delegation_prop_name] == self.NEO4j_NONE:
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
        :return:
        """

        # collect information about pools
        for node_id in self.node_ids:
            self.nodes[node_id].labels, self.nodes[node_id].properties = self.get_node_properties(node_id=node_id)
            self.log.debug(f"Processing node {node_id} for {self.PROP_LABEL_DELEGATIONS} "
                           f"and {self.PROP_CAPACITY_DELEGATIONS}")
            # if a node doesn't have delegations we skip it
            if self.PROP_LABEL_DELEGATIONS not in self.nodes[node_id].properties.keys() and \
                    self.PROP_CAPACITY_DELEGATIONS not in self.nodes[node_id].properties.keys():
                continue
            # look for label and capacity pool definitions and mentions
            self._find_delegations_in_properties(props=self.nodes[node_id].properties,
                                                 pool_type=DelegationType.LABEL, node_id=node_id)

            self._find_delegations_in_properties(props=self.nodes[node_id].properties,
                                                 pool_type=DelegationType.CAPACITY, node_id=node_id)
            # also look for delegations without pools

        # build indices on pools so we can find them from a delegation id
        for _, pools in self.pools.items():
            pools.build_index_by_delegation_id()

    def _update_delegation_properties(self, *, del_id: str, del_type: DelegationType,
                                      graph: ABCPropertyGraph,
                                      node_ids: List[str]):
        """
        Update capacity or label delegations on graph nodes based on previously collection
        delegations information. Use the information about kept nodes to speed things up.
        :param del_id:
        :param del_type:
        :param graph:
        :param node_ids:
        :return:
        """
        assert node_ids is not None
        assert graph is not None
        assert del_id is not None

        delegation_prop_name, _, _ = self.POOL_TYPE_TO_CLASS[del_type]
        collected_delegations = self.delegations[del_type]
        delegations_list = collected_delegations.get_by_delegation_id(delegation_id=del_id)
        collected_pools = self.pools[del_type]
        pools_list = collected_pools.get_pools_by_delegation_id(delegation_id=del_id)

        # first fill in a temporary dict with delegation info, then write it into properties
        new_delegations = dict()
        # collect pool mentions separately, then merge
        new_pool_mentions = dict()
        # walk through all node_ids and check delegations and pools
        for node_id in node_ids:
            # each entry matches a node id and is a list of dictionaries
            new_delegations[node_id] = list()

            if delegations_list is not None:
                # find if there is a delegation on this node
                for delegation in delegations_list:
                    if delegation.on_ == node_id:
                        new_delegations[node_id].append(delegation.get_details())

            if pools_list is not None:
                for pool in pools_list:
                    if pool.on_ == node_id:
                        # find if there was a pool definition on this node
                        new_delegations[node_id].append(pool.get_pool_details())
                        # pool definition includes a pool mention
                        if new_pool_mentions.get(node_id, None) is None:
                            new_pool_mentions[node_id] = list()
                        new_pool_mentions[node_id].append(pool.pool_id)
                    elif node_id in pool.for_:
                        # find if there was a pool mention on this node
                        # add it to 'pool' (if exists, create otherwise)
                        if new_pool_mentions.get(node_id, None) is None:
                            new_pool_mentions[node_id] = list()
                        new_pool_mentions[node_id].append(pool.pool_id)

        # merge pool mentions
        for node_id, pool in new_pool_mentions.items():
            new_delegations[node_id].append({ABCARMPropertyGraph.FIELD_POOL: pool})

        # write appropriate property name into the node on appropriate graph
        for node_id in node_ids:
            node_delegation_info = new_delegations.get(node_id, None)
            if node_delegation_info is not None and len(node_delegation_info) != 0:
                node_delegation_str = json.dumps(node_delegation_info)
                graph.update_node_property(node_id=node_id,
                                           prop_name=delegation_prop_name,
                                           prop_val=node_delegation_str)

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
        # build a dictionary to hold node labels and properties
        self.nodes = {k: self.LabelsAndProperties(None, None) for k in self.node_ids}

        # collect information on delegated pools and individual delegations
        self._catalog_delegations()

        # number of distinct delegation keys across label and capacity pools and plain delegations
        # is the number of ADMs we will generate
        unique_delegation_ids = self.label_pools.\
            get_delegation_ids().union(self.capacity_pools.get_delegation_ids(),
                                       self.label_delegations.get_delegation_ids(),
                                       self.capacity_delegations.get_delegation_ids())

        # generate unique graph ids and empty node sets for delegation graphs
        # remember these tuples and the fields are not mutable
        delegations_info = {del_id: self.DelegationInfo(graph_id=str(uuid.uuid4()),
                                                        graph=None,
                                                        keep_nodes=set(),
                                                        remove_nodes=set())
                            for del_id in unique_delegation_ids}

        node_ids_to_delegations = {node_id: list() for node_id in self.node_ids}
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

        # in addition to definite keep nodes, we should also keep nodes that
        # a) lie on shortest paths between two connection points we are keeping (to include the links)
        # b) switch fabrics that connect to connection points
        # c) network nodes that have switch fabrics
        # Determine nodes to delete by doing a difference between all nodes and keep nodes
        # Remove nodes
        # Annotate keep nodes with proper delegation information

        for del_id in unique_delegation_ids:
            # get a list of connection points we are keeping
            keep_cps = set()
            for node_id in delegations_info[del_id].keep_nodes:
                if 'ConnectionPoint' in self.nodes[node_id].labels:
                    keep_cps.add(node_id)

            # trace from connection points over links to other connection points
            # remember connection points
            new_cps = set()
            for cp in keep_cps:
                cp_neighbors = self.get_first_and_second_neighbor(node_id=cp,
                                                                  rel1="connects",
                                                                  node1_label="Link",
                                                                  rel2="connects",
                                                                  node2_label="ConnectionPoint")
                for pair in cp_neighbors:
                    # pair is a 2-element list
                    delegations_info[del_id].keep_nodes.update(pair)
                    new_cps.add(pair[1])

            keep_cps.update(new_cps)
            # from all keep cps (original and added), find switch fabrics and components or
            # network nodes
            for cp in keep_cps:
                cp_neighbors = self.get_first_and_second_neighbor(node_id=cp,
                                                                  rel1="connects",
                                                                  node1_label="SwitchFabric",
                                                                  rel2="has",
                                                                  node2_label="NetworkNode")
                for pair in cp_neighbors:
                    delegations_info[del_id].keep_nodes.update(pair)

                cp_neighbors = self.get_first_and_second_neighbor(node_id=cp,
                                                                  rel1="connects",
                                                                  node1_label="SwitchFabric",
                                                                  rel2="has",
                                                                  node2_label="Component")
                for pair in cp_neighbors:
                    delegations_info[del_id].keep_nodes.update(pair)

            delegations_info[del_id].remove_nodes = set(self.node_ids)
            delegations_info[del_id].remove_nodes.difference_update(delegations_info[del_id].keep_nodes)
            for node_id in delegations_info[del_id].remove_nodes:
                delegations_info[del_id].graph.delete_node(node_id=node_id)

            # go through capacity delegations under this delegation id, replace annotations on kept nodes
            # of approprate graph
            self._update_delegation_properties(del_id=del_id,
                                               del_type=DelegationType.LABEL,
                                               graph=delegations_info[del_id].graph,
                                               node_ids=delegations_info[del_id].keep_nodes)
            self._update_delegation_properties(del_id=del_id,
                                               del_type=DelegationType.CAPACITY,
                                               graph=delegations_info[del_id].graph,
                                               node_ids=delegations_info[del_id].keep_nodes)

        return {k: delegations_info[k].graph for k in unique_delegation_ids}

    def get_delegations(self, *, node_id: str, delegation_type: DelegationType) -> List:
        """
        Get Label or Capacity delegations of a given node. They are represented
        as lists of dictionaries. Dictionaries may include delegation and pool
        designators. Returns None if delegation property is not defined.
        :param node_id:
        :param delegation_type:
        :return:
        """
        assert node_id is not None
        prop_field_name, _, _ = self.POOL_TYPE_TO_CLASS[delegation_type]
        return self.get_node_json_property_as_object(node_id=node_id, prop_name=prop_field_name)