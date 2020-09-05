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
Label and capacity pools. Each pool knows which node defined it and which nodes it
applies to and can be set/queried for that information.
"""

from enum import Enum
from typing import List, Dict
import json

from .neo4j_property_graph import Neo4jPropertyGraph

class PoolType(Enum):
    CAPACITY = 1
    LABEL = 2


class Pool:
    """
    Label and capacity pools. Each pool knows which node defined it and which nodes it
    applies to and can be set/queried for that information.
    """
    def __init__(self, *, atype: PoolType, pool_id: str, delegation_id: str = None,
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
        set details of the pool dictionary, removing the pool definition and delegation
        identifier fields from dictionary
        :param pool_dict:
        :return:
        """
        assert pool_dict is not None
        if self.type == PoolType.CAPACITY:
            pool_dict.pop(Neo4jPropertyGraph.FIELD_CAPACITY_POOL, None)
        elif self.type == PoolType.LABEL:
            pool_dict.pop(Neo4jPropertyGraph.FIELD_LABEL_POOL, None)
        # also pop the delegation field
        pool_dict.pop(Neo4jPropertyGraph.FIELD_DELEGATION, None)
        self.pool_details = pool_dict

    def get_pool_details(self) -> str:
        """
        Return pool label or capacity details as a jSON string.
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

    def get_pool_type(self) -> PoolType:
        return self.type

    def get_delegation(self) -> str:
        return self.delegation_id

    def __repr__(self) -> str:
        return f"{self.type} pool {self.pool_id} delegated to {self.delegation_id}: " \
               f"{self.on_}=> {self.for_} {self.pool_details} "


class Pools:
    """
    Map between node ids, pools and delegations
    """
    def __init__(self, atype: PoolType):
        self.pool_by_id = {}
        self.pools_by_delegation = None
        self.pool_type = atype

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
        Index all pools by delegation ids, raise RuntimeError if any of them
        don't have the delegation id defined
        :return:
        """
        self.pools_by_delegation = {}
        for pool in self.pool_by_id.values():
            if pool.get_delegation() is None:
                self.pools_by_delegation = None
                raise RuntimeError(f"Pool {pool.get_pool_id()} does not have a delegation id defined")
            self.pools_by_delegation[pool.get_delegation()] = pool

    def get_pools_by_delegation_id(self, *, delegation_id: str) -> Pool:
        """
        return a list of Pool(s) for a delegation. raises RuntimeError if the index based on
        delegation ids have not been built yet
        :param delegation_id:
        :return:
        """
        assert delegation_id is not None
        if self.pools_by_delegation is None:
            raise RuntimeError("Pools are node indexed by delegation, please run build_index_by_delegation_id()")
        return self.pools_by_delegation[delegation_id]

    def add_pool(self, *, pool: Pool) -> None:
        """
        add a pool to the index
        :param pool:
        :return:
        """
        assert pool is not None
        assert pool.get_pool_id() is not None
        self.pool_by_id[pool.get_pool_id()] = pool

    def __repr__(self):
        return f"{self.pool_by_id}"
