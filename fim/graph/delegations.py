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
Label and capacity delegations and pools. Each delegation knows which node it is
defined on, each pool knows which node defined it and which nodes it
applies to and can be set/queried for that information.
"""

from enum import Enum
from typing import List, Dict, Set
import json

from .neo4j_property_graph import Neo4jPropertyGraph


class DelegationType(Enum):
    CAPACITY = 1
    LABEL = 2


class Delegation:
    """Label and capacity delegation. Only on individual resources.
    Pools are used to define delegations across multiple resources.
    """
    def __init__(self, atype: DelegationType, defined_on: str, delegation_id: str):
        """
        Define a delegation of resources on a given node
        :param atype:
        :param defined_on:
        :param delegation_id:
        """
        assert atype is not None
        assert defined_on is not None
        assert delegation_id is not None
        self.type = atype
        self.on_ = defined_on
        self.delegation_id = delegation_id
        self.delegation_details = None

    def set_details(self, *, dele_dict: Dict) -> None:
        """
        set details of the delegation dictionary, removing the delegation
        identifier field from dictionary
        :param dele_dict:
        :return:
        """
        assert dele_dict is not None
        # pop the delegation field
        dele_dict.pop(Neo4jPropertyGraph.FIELD_DELEGATION, None)
        self.delegation_details = dele_dict

    def get_details(self) -> Dict:
        """
        get delegation details as a dictionary (minus the delegation id)
        :return:
        """
        return self.delegation_details

    def __repr__(self) -> str:
        return f"{self.type} delegation delegated to {self.delegation_id}: " \
               f"{self.on_} with {self.delegation_details} "


class Delegations:
    """
    Multiple delegations references by delegation id
    """
    def __init__(self, atype: DelegationType):
        self.type = atype
        self.delegations = {}

    def add_delegation(self, *, delegation: Delegation) -> None:
        """
        Append a well-formed delegation to the list of delegations matching
        this id
        :param delegation:
        :return:
        """
        assert delegation.delegation_id is not None
        if self.delegations.get(delegation.delegation_id, None) is None:
            self.delegations[delegation.delegation_id] = []

        self.delegations[delegation.delegation_id].append(delegation)

    def get_by_delegation_id(self, *, delegation_id: str) -> List[Delegation]:
        """
        retrieve a list of delegations by their id or None
        :param delegation_id:
        :return:
        """
        assert delegation_id is not None
        return self.delegations.get(delegation_id, None)

    def get_delegation_ids(self) -> Set:
        """
        get a set of all delegation ids
        :return:
        """
        return set(self.delegations.keys())

    def get_node_ids(self, *, delegation_id: str) -> Set:
        """
        return a set of nodes ids for a given delegation id
        :param delegation_id:
        :return:
        """
        assert delegation_id is not None
        ret = set()
        if delegation_id not in self.delegations.keys():
            return ret
        for delegation in self.delegations[delegation_id]:
            ret.add(delegation.on_)
        return ret

    def __repr__(self):
        return f"{self.delegations}"


class Pool:
    """
    Label and capacity pools. Each pool knows which node defined it and which nodes it
    applies to and can be set/queried for that information.
    """
    def __init__(self, *, atype: DelegationType, pool_id: str, delegation_id: str = None,
                 defined_on: str = None, defined_for: List[str] = None):
        """
        Define a label or capacity pool and optionally specify where it is defined and for which nodes
        and what resources fall into it
        :param atype:
        :param pool_id:
        :param defined_on:
        :param defined_for:
        :param delegation_id:
        """
        assert atype is not None
        assert pool_id is not None
        self.type = atype
        self.on_ = defined_on
        self.delegation_id = delegation_id
        if defined_for is None:
            self.for_ = []
        else:
            self.for_ = defined_for
        self.pool_id = pool_id
        self.pool_details = None

    def set_defined_on(self, *, node_id: str) -> None:
        """
        Set ID of node on which this pool is defined
        :param node_id:
        :return:
        """
        assert node_id is not None
        self.on_ = node_id

    def set_defined_for(self, *, node_id_list: List[str]) -> None:
        """
        set/replace the pool's defined_for list of nodes
        :param node_id_list:
        :return:
        """
        assert node_id_list is not None
        assert len(node_id_list) != 0

        self.for_ = node_id_list

    def add_defined_for(self, *, node_ids) -> None:
        """
        Add to the list of nodes for which the pool is defined for.
        Individual items or lists
        :param node_ids:
        :return:
        """
        assert node_ids is not None
        if isinstance(node_ids, str):
            self.for_.append(node_ids)
        elif isinstance(node_ids, list):
            self.for_.extend(node_ids)

    def set_pool_details(self, *, pool_dict: Dict) ->None:
        """
        set details of the pool dictionary, removing delegation
        identifier field from dictionary
        :param pool_dict:
        :return:
        """
        assert pool_dict is not None
        pool_dict.pop(Neo4jPropertyGraph.FIELD_DELEGATION, None)
        self.pool_details = pool_dict

    def get_pool_details(self) -> Dict:
        """
        Return pool label or capacity details as a dictionary.
        :return:
        """
        return self.pool_details

    def set_delegation_id(self, *, delegation_id: str) -> None:
        assert delegation_id is not None
        self.delegation_id = delegation_id

    def add_defined_for(self, *, node_ids) -> None:
        """
        add a single element or a list
        :param node_ids: single node id or list
        :return:
        """
        assert node_ids is not None
        if isinstance(node_ids, list):
            self.for_.extend(node_ids)
        elif isinstance(node_ids, str):
            self.for_.append(node_ids)

    def is_defined_on(self, *, node_id: str) -> bool:
        """
        Is this pool defined on this node?
        :param node_id:
        :return:
        """
        return node_id == self.on_

    def is_defined_for(self, *, node_id: str) -> bool:
        """
        Is this pool defined for this node?
        :param node_id:
        :return:
        """
        return node_id in self.for_

    def get_defined_on(self) -> str:
        return self.on_

    def get_defined_for(self) -> List[str]:
        return self.for_

    def get_pool_id(self) -> str:
        return self.pool_id

    def get_pool_type(self) -> DelegationType:
        return self.type

    def get_delegation_id(self) -> str:
        return self.delegation_id

    def validate_pool(self):
        """
        Validate a pool to make sure delegation id is present, on, for and details are defined
        :return:
        """
        if self.delegation_id is None:
            raise PoolException(f"Pool {self.pool_id} does not have a delegation ID")
        if self.get_defined_on() is None:
            raise PoolException(f"Pool {self.pool_id} is not defined on any node")
        if self.get_defined_for() is None or len(self.get_defined_for()) == 0:
            raise PoolException(f"Pool {self.pool_id} is not mentioned on any nodes")
        if self.get_defined_on() not in self.get_defined_for():
            raise PoolException(f"Pool {self.pool_id} is not mentioned on the node where it is defined")
        if self.get_pool_details() is None:
            raise PoolException(f"Pool {self.pool_id} does not have any resource details")

    def __repr__(self) -> str:
        return f"{self.type} pool {self.pool_id} delegated to {self.delegation_id}: " \
               f"{self.on_}=> {self.for_} with {self.pool_details} "


class Pools:
    """
    Map between node ids, pools and delegations
    """
    def __init__(self, atype: DelegationType):
        self.pool_by_id = {}
        self.pools_by_delegation = None
        self.pool_type = atype

    def get_type(self) -> DelegationType:
        return self.pool_type

    def get_pool_by_id(self, *, pool_id: str, strict: bool = False) -> Pool:
        """
        Return a pool for this id. If strict is false (default) and pool doesn't exist,
        create a new pool of type matching this pools type.
        :param pool_id:
        :param strict
        :return:
        """
        assert pool_id is not None
        if strict:
            return self.pool_by_id.get(pool_id, None)
        else:
            p = self.pool_by_id.get(pool_id, None)
            if p is None:
                p = Pool(atype=self.pool_type, pool_id=pool_id)
                self.add_pool(pool=p)
            return p

    def build_index_by_delegation_id(self) -> None:
        """
        Validate all pools then index them by delegation ids, raise PoolException if any of them
        don't have the delegation id defined. Validate that all fields are filled in.
        :return:
        """
        self.pools_by_delegation = {}
        for pool in self.pool_by_id.values():
            pool.validate_pool()
            if self.pools_by_delegation.get(pool.get_delegation_id(), None) is None:
                self.pools_by_delegation[pool.get_delegation_id()] = []
            self.pools_by_delegation[pool.get_delegation_id()].append(pool)

    def get_pools_by_delegation_id(self, *, delegation_id: str) -> List[Pool]:
        """
        return a list of Pool(s) for a delegation. raises PoolException if the index based on
        delegation ids have not been built yet
        :param delegation_id:
        :return:
        """
        assert delegation_id is not None
        if self.pools_by_delegation is None:
            raise PoolException("Pools are node indexed by delegation, please run build_index_by_delegation_id()")
        return self.pools_by_delegation.get(delegation_id, None)

    def add_pool(self, *, pool: Pool) -> None:
        """
        add a pool to the index
        :param pool:
        :return:
        """
        assert pool is not None
        assert pool.get_pool_id() is not None
        self.pool_by_id[pool.get_pool_id()] = pool

    def get_delegation_ids(self) -> Set:
        """
        return a set of all delegation ids
        :return:
        """
        if self.pools_by_delegation is None:
            raise PoolException("Pools are not indexed by delegation, unable to get set of delegation ids")
        return set(self.pools_by_delegation.keys())

    def get_node_ids(self, *, delegation_id: str) -> Set:
        """
        Get a set of nodes for a given delegation across all pools
        :param delegation_id:
        :return:
        """
        assert delegation_id is not None
        if self.pools_by_delegation is None:
            raise PoolException("Pools are not indexed by delegation, unable to get node ids by delegation id")
        ret = set()
        if delegation_id not in self.pools_by_delegation.keys():
            return ret
        for pool in self.pools_by_delegation[delegation_id]:
            ret.update(pool.get_defined_for())
        return ret

    def validate_pools(self):
        """
        Make sure all pools have a defined on and for nodes.
        :return:
        """
        for _, pool in self.pool_by_id.items():
            pool.validate_pool()

    def __repr__(self):
        return f"{self.pool_by_id}"


class PoolException(Exception):
    """
    Exception with a pool
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Pool exception: {msg}")


class DelegationException(Exception):
    """
    Exception with a pool
    """
    def __init__(self, msg: str):
        assert msg is not None
        super().__init__(f"Delegation exception: {msg}")