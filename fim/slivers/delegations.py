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
from typing import List, Dict, Set, Tuple
import json

from fim.graph.abc_property_graph_constants import ABCPropertyGraphConstants
from .capacities_labels import Capacities, Labels


class DelegationType(Enum):
    CAPACITY = 1
    LABEL = 2


class DelegationFormat(Enum):
    PoolDefinition = 1
    PoolReference = 2
    SinglePool = 3


class Delegation:
    """
    Single label and capacity delegation (pool definition or reference).
    Encodes a single entry in a dictionary describing multiple delegations.
    This object by itself is not JSON serializable, for that look at Delegations object.
    """
    def __init__(self, *, atype: DelegationType, delegation_id: str,
                 aformat: DelegationFormat = DelegationFormat.SinglePool,
                 pool_id: str = None):
        """
        Define a delegation of resources on a given node (for a given pool - either
        as definition or reference)
        :param atype:
        :param delegation_id:
        :param aformat:
        :param pool_id:
        """
        assert atype is not None
        assert delegation_id is not None
        self.type = atype
        self.format = aformat
        self.delegation_id = delegation_id
        self.delegation_details = None
        self.pool_id = pool_id
        if aformat != DelegationFormat.SinglePool:
            assert pool_id is not None

    def get_delegation_type(self) -> DelegationType:
        return self.type

    def get_pool_name(self) -> str:
        return self.pool_id

    def get_format(self) -> DelegationFormat:
        return self.format

    def get_delegation_id(self) -> str:
        return self.delegation_id

    def set_details(self, caporlab) -> None:
        """
        set details of the delegation dictionary from either a Labels or Capacities
        object
        :param caporlab: either Labels or Capacities
        :return:
        """
        assert caporlab is not None
        assert (isinstance(caporlab, Labels) or isinstance(caporlab, Capacities))
        if self.format == DelegationFormat.PoolReference:
            raise DelegationException(msg=f'Trying to add Labels or Capacities object to PoolReference delegation')
        if (isinstance(caporlab, Labels) and self.type == DelegationType.CAPACITY) or \
            (isinstance(caporlab, Capacities) and self.type == DelegationType.LABEL):
            raise DelegationException(msg=f'Trying to add Capacities to a LABEL type delegation or vice versa')
        self.delegation_details = caporlab

    def get_details(self) -> Labels or Capacities:
        """
        get delegation details as either Labels or Capacities object
        :return:
        """
        if self.delegation_details is None:
            return None
        return self.delegation_details

    def get_details_as_dict(self) -> Dict[str, str] or None:
        """
        get details of labels/capacities as a dictionary
        :return:
        """
        if self.delegation_details is None:
            return None
        return self.delegation_details.to_dict()

    def __repr__(self) -> str:
        return f"{self.type} delegation delegated to {self.delegation_id}: " \
               f"format {self.format} for pool {self.pool_id} with {self.delegation_details} "


class Delegations:
    """
    Multiple delegations referenced by delegation id within them on a single
    model element. Serializable to and from JSON so used in models and slivers.
    Delegation id can be graph id or a unique string (depending on whether this
    is on CBM, or ADM/ARM)
    """
    def __init__(self, *, atype: DelegationType):

        self.type = atype
        self.delegations = dict()

    def add_delegations(self, *args) -> None:
        """
        Include well-formed Delegation objects into the dictionary.
        Delegation types must match the type of this container object.
        :param args: sequence of Delegation objects
        :return:
        """
        for delegation in args:
            assert delegation.delegation_id is not None
            assert delegation.get_delegation_type() == self.type

            if self.delegations.get(delegation.delegation_id, None) is not None:
                raise DelegationException(msg=f'Delegation with id {delegation.delegation_id} is already present')
            if self.type != delegation.get_delegation_type():
                raise DelegationException(msg=f'Delegation with id {delegation.delegation_id} type '
                                              f'{delegation.get_delegation_type()} does not match delegations '
                                              f'type {self.type}')
            self.delegations[delegation.delegation_id] = delegation

    def get_by_delegation_id(self, delegation_id: str) -> Delegation:
        """
        retrieve a list of delegations by their id or None
        :param delegation_id:
        :return:
        """
        assert delegation_id is not None
        return self.delegations.get(delegation_id, None)

    def get_sole_delegation(self) -> Tuple[str, Delegation]:
        """
        Checks that delegations object has just one delegation and returns
        a tuple of delegation id and delegation object. Useful primarily on CBMs.
        :return:
        """
        if len(self.delegations) != 1:
            raise DelegationException(msg=f"Expected to find only one delegation in Delegations object {self}")
        for k, v in self.delegations.items():
            return k, v

    def get_delegations_as_list(self) -> List[Delegation]:
        """
        Return individual delegation objects as a list
        :return:
        """
        return list(self.delegations.values())

    def get_delegation_ids(self) -> Set:
        """
        get a set of all delegation ids
        :return:
        """
        return set(self.delegations.keys())

    def remove_by_id(self, delegation_id: str) -> None:
        """
        Remove a delegation with this id from container
        :param delegation_id:
        :return:
        """
        assert delegation_id is not None
        if delegation_id not in self.delegations.keys():
            return
        self.delegations.pop(delegation_id)

    def return_delegations_for_id(self, delegation_id: str):
        """
        Return a delegations object limited to this delegation id or None.
        :param delegation_id:
        :return:
        """
        if delegation_id not in self.delegations.keys():
            return None
        ds = Delegations(atype=self.type)
        ds.add_delegations(self.delegations[delegation_id])
        return ds

    def to_json(self) -> str:
        """
        convert object to JSON. Example objects:
        { "del1": {
            "pool_name": "_",
            "capacities": { <capacities dictionary> } }
        or
        { "del1": {
            "pool_name": "pool1",
            "labels": { <labels dictionary> } }
        or
        { "del1": {
            "pool": "pool1" }
        :return:
        """
        json_dict = {}
        for k, v in self.delegations.items():
            inner_dict = {}
            if v.get_format() == DelegationFormat.SinglePool:
                assert v.get_details_as_dict() is not None
                inner_dict[ABCPropertyGraphConstants.FIELD_POOL_ID] = ABCPropertyGraphConstants.SINGLE_POOL_NAME
                if self.type == DelegationType.CAPACITY:
                    inner_dict[ABCPropertyGraphConstants.FIELD_CAPACITIES] = v.get_details_as_dict()
                else:
                    inner_dict[ABCPropertyGraphConstants.FIELD_LABELS] = v.get_details_as_dict()
            elif v.get_format() == DelegationFormat.PoolDefinition:
                assert v.get_pool_name() is not None
                assert v.get_details_as_dict() is not None
                inner_dict[ABCPropertyGraphConstants.FIELD_POOL_ID] = v.get_pool_name()
                if self.type == DelegationType.CAPACITY:
                    inner_dict[ABCPropertyGraphConstants.FIELD_CAPACITIES] = v.get_details_as_dict()
                else:
                    inner_dict[ABCPropertyGraphConstants.FIELD_LABELS] = v.get_details_as_dict()
            elif v.get_format() == DelegationFormat.PoolReference:
                assert v.get_pool_name() is not None
                inner_dict[ABCPropertyGraphConstants.FIELD_POOL] = v.get_pool_name()
            json_dict[k] = inner_dict

        return json.dumps(json_dict)

    @classmethod
    def from_json(cls, *, json_str: str, atype: DelegationType):
        """
        convert from a JSON representation producing a Delegations object. Returns None
        if json_str is None
        :param json_str:
        :param atype: one of DelegationType
        :return:
        """
        if json_str is None or len(json_str) == 0 or json_str == ABCPropertyGraphConstants.NEO4j_NONE:
            return None
        ds = Delegations(atype=atype)
        json_dict = json.loads(json_str)
        for k, v in json_dict.items():
            if ABCPropertyGraphConstants.FIELD_POOL_ID in v.keys():
                # single element pool or pool definition
                if v[ABCPropertyGraphConstants.FIELD_POOL_ID] == ABCPropertyGraphConstants.SINGLE_POOL_NAME:
                    format = DelegationFormat.SinglePool
                    pool_id = None
                else:
                    format = DelegationFormat.PoolDefinition
                    pool_id = v[ABCPropertyGraphConstants.FIELD_POOL_ID]
                if atype == DelegationType.CAPACITY:
                    caporlabdict = v[ABCPropertyGraphConstants.FIELD_CAPACITIES]
                    caporlab = Capacities(**caporlabdict)
                else:
                    caporlabdict = v[ABCPropertyGraphConstants.FIELD_LABELS]
                    caporlab = Labels(**caporlabdict)
            elif ABCPropertyGraphConstants.FIELD_POOL in v.keys():
                # pool reference
                format = DelegationFormat.PoolReference
                pool_id = v[ABCPropertyGraphConstants.FIELD_POOL]
                caporlab = None
            else:
                raise DelegationException(msg='Invalid dictionary format when parsing delegation from JSON')
            d = Delegation(atype=atype, delegation_id=k, aformat=format, pool_id=pool_id)
            if caporlab is not None:
                d.set_details(caporlab)
            ds.add_delegations(d)
        return ds

    def __repr__(self):
        return f"{self.type} consisting of {self.delegations}"


class Pool:
    """
    Label and capacity pools. Each pool knows which node defined it and which nodes it
    applies to and can be set/queried for that information. These structures help
    transform ARM into ADM, but themselves don't serialize.
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
            self.for_ = set()
        else:
            self.for_ = set(defined_for)
        if defined_on in self.for_:
            self.for_.remove(defined_on)
        self.pool_id = pool_id
        self.pool_details = None

    def set_defined_on(self, node_id: str) -> None:
        """
        Set ID of node on which this pool is defined
        :param node_id:
        :return:
        """
        assert node_id is not None
        self.on_ = node_id

    def set_defined_for(self, node_id_list: List[str]) -> None:
        """
        set/replace the pool's defined_for list of nodes
        :param node_id_list:
        :return:
        """
        assert node_id_list is not None
        assert len(node_id_list) != 0

        self.for_ = set(node_id_list)

    def add_defined_for(self, node_ids: str or List) -> None:
        """
        Add to the list of nodes for which the pool is defined for.
        Individual items or lists
        :param node_ids:
        :return:
        """
        assert node_ids is not None
        if isinstance(node_ids, str):
            self.for_.add(node_ids)
        elif isinstance(node_ids, list):
            self.for_.update(node_ids)

    def set_pool_details(self, caporlab: Capacities or Labels) ->None:
        """
        set details of the pool to a Capacities or Labels object
        :param caporlab:
        :return:
        """
        assert (isinstance(caporlab, Labels) or isinstance(caporlab, Capacities))
        self.pool_details = caporlab

    def get_pool_details(self) -> Capacities or Labels:
        """
        Return label or capacity pool details as Capacities or Labels object
        :return:
        """
        return self.pool_details

    def set_delegation_id(self, *, delegation_id: str) -> None:
        assert delegation_id is not None
        self.delegation_id = delegation_id

    def is_defined_on(self, node_id: str) -> bool:
        """
        Is this pool defined on this node?
        :param node_id:
        :return:
        """
        return node_id == self.on_

    def is_defined_for(self, node_id: str) -> bool:
        """
        Is this pool defined for this node?
        :param node_id:
        :return:
        """
        return node_id in self.for_

    def get_defined_on(self) -> str:
        return self.on_

    def get_defined_for(self) -> Set[str]:
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
        if self.get_pool_details() is None:
            raise PoolException(f"Pool {self.pool_id} does not have any resource details")

    def __repr__(self) -> str:
        return f"{self.type} pool {self.pool_id} delegated to {self.delegation_id}: " \
               f"{self.on_}=> {self.for_} with {self.pool_details} "


class Pools:
    """
    Define/extract multiple pools for a given ARM, ADM or CBM model
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
            el = self.pools_by_delegation.get(pool.get_delegation_id(), list())
            el.append(pool)
            self.pools_by_delegation[pool.get_delegation_id()] = el

    def get_pools_by_delegation_id(self, delegation_id: str) -> List[Pool]:
        """
        return a list of Pool(s) for a delegation. Raises PoolException if the index based on
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
        if pool.get_pool_type() != self.pool_type:
            raise PoolException(msg=f'Pool type {pool.get_pool_type()} does not match Pools '
                                    f'container type {self.pool_type}')
        self.pool_by_id[pool.get_pool_id()] = pool

    def incorporate_delegation(self, *, node_id: str, deleg: Delegations):
        """
        Take a Delegations object (e.g. extracted from a model element) and
        add its information to construct pools. Ignores single element pools.
        Node id is the id of the node where it was found.
        :param node_id:
        :param deleg:
        :return:
        """
        assert node_id is not None
        assert deleg is not None
        if deleg.type != self.pool_type:
            raise PoolException(msg=f'Delegation type {deleg.type} does not match '
                                    f'Pools container type {self.pool_type}')
        # ignore single element pools in delegations
        for k, d in deleg.delegations.items():
            if d.get_format() == DelegationFormat.SinglePool:
                continue
            p = self.get_pool_by_id(pool_id=d.get_pool_name())
            if d.get_format() == DelegationFormat.PoolDefinition:
                if p.get_defined_on() is not None:
                    raise PoolException(msg=f'Pool {d.get_pool_name} has already been defined')
                p.set_defined_on(node_id)
                p.set_pool_details(d.get_details())
                p.set_delegation_id(delegation_id=d.get_delegation_id())
            else:
                # PoolReference
                p.add_defined_for(node_id)
                p.set_delegation_id(delegation_id=d.get_delegation_id())

    def generate_delegations_by_node_id(self) -> Dict[str, Delegations]:
        """
        Produce a dictionary of delegations objects indexed
        by node id they pertain to (to support serialization onto the model).
        :return:
        """
        ret = dict()
        if self.pools_by_delegation is None:
            return ret
        for delegation_id, pool_list in self.pools_by_delegation.items():
            for pool in pool_list:
                # pool definition
                pd = Delegation(atype=self.pool_type, delegation_id=delegation_id,
                                aformat=DelegationFormat.PoolDefinition, pool_id=pool.get_pool_id())
                pd.set_details(pool.get_pool_details())
                node = pool.get_defined_on()
                ds = ret.get(node, None)
                if ds is None:
                    ret[node] = Delegations(atype=self.pool_type)
                    ds = ret[node]
                ds.add_delegations(pd)
                # pool references
                for node in pool.get_defined_for():
                    pr = Delegation(atype=self.pool_type, delegation_id=delegation_id,
                                    aformat=DelegationFormat.PoolReference, pool_id=pool.get_pool_id())
                    ds = ret.get(node, None)
                    if ds is None:
                        ret[node] = Delegations(atype=self.pool_type)
                        ds = ret[node]
                    ds.add_delegations(pr)
        return ret

    def get_delegation_ids(self) -> Set:
        """
        return a set of all delegation ids
        :return:
        """
        if self.pools_by_delegation is None:
            raise PoolException("Pools are not indexed by delegation, unable to get set of delegation ids")
        return set(self.pools_by_delegation.keys())

    def get_node_ids(self, delegation_id: str) -> Set:
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