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
Neo4j implementation of CBM (Combined Broker Model) functionality.
"""
import uuid
import json

from typing import List

from ..abc_property_graph import ABCPropertyGraph, ABCPropertyGraphConstants, PropertyGraphQueryException
from ..neo4j_property_graph import Neo4jPropertyGraph, Neo4jGraphImporter
from .abc_cbm import ABCCBMPropertyGraph
from .neo4j_adm import Neo4jADMGraph
from fim.slivers.delegations import DelegationType

from ...pluggable import PluggableRegistry, BrokerPluggable, PluggableType


class Neo4jCBMGraph(Neo4jPropertyGraph, ABCCBMPropertyGraph):
    """
    Neo4j implementation of CBM
    """
    PROP_ADM_GRAPH_IDS = "ADMGraphIDs"
    BQM_MERGED_FIELDS = ['LabelDelegations', 'CapacityDelegations']
    DELEGATION_TYPE_TO_PROP_NAME = {DelegationType.LABEL: ABCPropertyGraph.PROP_LABEL_DELEGATIONS,
                                    DelegationType.CAPACITY: ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS
                                    }

    def __init__(self, *, graph_id: str = None, importer: Neo4jGraphImporter, logger=None):
        """
        Initialize CBM either from existing ID or generate new graph id
        :param graph_id:
        :param importer:
        """
        if graph_id is None:
            graph_id = str(uuid.uuid4())

        super().__init__(graph_id=graph_id, importer=importer, logger=logger)

    def _update_node_delegations(self, *, node_id: str, adm: ABCPropertyGraph) -> None:
        """
        Update the CBM node by-ADM-id delegation dictionary (it is assumed to exist already
        on common nodes) from corresponding ADM node.
        Must be invoked before ADM is merged into CBM.
        :param node_id:
        :param adm_id:
        :return:
        """
        _, cbm_node_props = self.get_node_properties(node_id=node_id)
        _, adm_node_props = adm.get_node_properties(node_id=node_id)
        props_modified = False
        for delegation_prop_name in [self.PROP_LABEL_DELEGATIONS, self.PROP_CAPACITY_DELEGATIONS]:
            # one or both of properties can have data
            if cbm_node_props.get(delegation_prop_name, None) is None or \
                    cbm_node_props[delegation_prop_name] == self.NEO4j_NONE:
                cbm_delegation_dict = dict()
            else:
                cbm_delegation_dict = json.loads(cbm_node_props[delegation_prop_name])

            if adm_node_props.get(delegation_prop_name, None) is None or \
                    adm_node_props[delegation_prop_name] == self.NEO4j_NONE:
                continue
            props_modified = True
            # turn delegation into Python object by merging two dictionaries
            adm_delegation = json.loads(adm_node_props[delegation_prop_name])
            cbm_delegation_dict.update(adm_delegation)
            new_delegation_json = json.dumps(cbm_delegation_dict)
            cbm_node_props[delegation_prop_name] = new_delegation_json
        if props_modified:
            # write back
            self.update_node_properties(node_id=node_id, props=cbm_node_props)

    def merge_adm(self, *, adm: ABCPropertyGraph) -> None:
        """
        Merge an ADM into the CBM
        :param adm:
        :return:
        """
        assert adm is not None
        assert adm.graph_exists()

        # clone ADM with temporary ID - we will be changing its properties
        temp_adm_graph_id = str(uuid.uuid4())
        self.log.info('CREATED TEMPORARY ADM GRAPH ID ' + temp_adm_graph_id +
                      ' when merging graph ' + adm.graph_id + ' into ' + self.graph_id)
        temp_graph = adm.clone_graph(new_graph_id=temp_adm_graph_id)
        # crude typecasting
        temp_adm_graph = Neo4jADMGraph(graph_id=temp_graph.graph_id,
                                       importer=temp_graph.importer,
                                       logger=temp_graph.log)

        # rewrite delegations into dictionaries keyed by ADM graph id,
        # but be sure to use original ADM graph ID when rewriting
        temp_adm_graph.rewrite_delegations(real_adm_id=adm.graph_id)

        # update the ADMGraphIDs property to a single member list on all CBM nodes
        temp_adm_graph.update_nodes_property(prop_name=self.PROP_ADM_GRAPH_IDS,
                                             prop_val=json.dumps([adm.graph_id]))

        # if CBM is empty, just force ADM into it
        if not self.graph_exists():
            temp_adm_graph.update_nodes_property(prop_name=ABCPropertyGraphConstants.GRAPH_ID,
                                                 prop_val=self.graph_id)
            return

        # CBM is not empty - need to merge ADM with it

        # locate nodes with matching IDs
        common_node_ids = self.find_matching_nodes(other_graph=temp_adm_graph)

        # Merging CBM properties with ADM (on merged nodes):
        # edited after the fact.
        # GraphID: use CBM
        # NodeID: use CBM (should be same anyway)
        # Labels: use CBM - may have information from reservations already
        # Capacities: use CBM - may have information from reservations already - should be same
        # in both graphs initially
        # LabelDelegations: use CBM, edit/add from ADM
        # CapacityDelegations: use CBM, edit/add from ADM
        for node_id in common_node_ids:
            # update Label and Capacity delegation (now they are dictionaries, not lists)
            # prior to merge
            self._update_node_delegations(node_id=node_id, adm=temp_adm_graph)

            # default behavior - keep CBM node properties, discard
            # temp_adm_graph properties
            self.merge_nodes(node_id=node_id,
                             other_graph=temp_adm_graph)

            # add delegation graph id to ADMGraphIDs property on common (merged) nodes
            _, cbm_node_props = self.get_node_properties(node_id=node_id)
            adm_list = json.loads(cbm_node_props[self.PROP_ADM_GRAPH_IDS])
            adm_list.append(adm.graph_id)
            self.update_node_property(node_id=node_id, prop_name=self.PROP_ADM_GRAPH_IDS,
                                      prop_val=json.dumps(adm_list))

        # rewrite GraphID on the remaining nodes of
        # temporary ADM graph (after that it ceases to exist)
        # NOTE: this takes advantage of Neo4j semantics of common store for all graphs
        # and changing the GraphID property effectively makes graph takes on a new identity
        temp_adm_graph.update_nodes_property(prop_name=ABCPropertyGraphConstants.GRAPH_ID,
                                             prop_val=self.graph_id)

    def unmerge_adm(self, *, graph_id: str) -> None:
        # Search ADMGraphIDs property and remove those nodes where it is the only
        # member of the list. For those that have two members, update the list
        # to remove.
        delete_nodes = list()
        for node in self.list_all_node_ids():
            adm_graph_ids = self.get_node_json_property_as_object(node_id=node,
                                                                  prop_name=self.PROP_ADM_GRAPH_IDS)
            if adm_graph_ids is None:
                self.log.warn(f'When unmerging ADMs encountered node {node} '
                              f'without {self.PROP_ADM_GRAPH_IDS} property')
                continue
            if not isinstance(adm_graph_ids, list):
                raise PropertyGraphQueryException(node_id=node, graph_id=self.graph_id,
                                                  msg=f"When unmerging graph {graph_id}, encountered wrongly"
                                                      f"formatted {self.PROP_ADM_GRAPH_IDS} field")
            if graph_id in adm_graph_ids:
                # update the ADM Graph IDs field
                adm_graph_ids.remove(graph_id)
                if len(adm_graph_ids) == 0:
                    delete_nodes.append(node)
                else:
                    # update
                    self.update_node_property(node_id=node, prop_name=self.PROP_ADM_GRAPH_IDS,
                                              prop_val=json.dumps(adm_graph_ids))
        # remove the merged nodes
        for node in delete_nodes:
            self.delete_node(node_id=node)

    def get_bqm(self, **kwargs) -> ABCPropertyGraph:
        """
        Get a Broker Query Model (e.g. in response to a listResources() call)
        :param kwargs:
        :return:
        """
        p = PluggableRegistry()
        if p.pluggable_registered(t=PluggableType.Broker) and \
                BrokerPluggable.PLUGGABLE_PRODUCE_BQM in p.get_implemented_methods(t=PluggableType.Broker):
            # invoke the callable for plug_produce_bqm() otherwise default behavior
            c = p.get_method_callable(t=PluggableType.Broker,
                                      method=BrokerPluggable.PLUGGABLE_PRODUCE_BQM)
            return c(cbm=self, **kwargs)
        # default for now - simplest possible - return a cloned CBM

        bqm = self.clone_graph(new_graph_id=str(uuid.uuid4()))
        return bqm

    def get_delegations(self, *, node_id: str, adm_id: str, delegation_type: DelegationType) -> List or None:
        """
        Retrieve Label or Capacity delegations attribuited to a particular ADM. A delegation property
        is a dictionary of per ADM graph id delegations. Individual delegations
        are lists of dictionaries with possible pool designators. Returns None if delegation property is
        not defined at all or delegation dictionary doesn't contain ADM graph id.
        :param node_id:
        :param adm_id:
        :param delegation_type:
        :return:
        """
        assert node_id is not None
        assert adm_id is not None
        prop_field_name = self.DELEGATION_TYPE_TO_PROP_NAME[delegation_type]
        deleg_prop_val = self.get_node_json_property_as_object(node_id=node_id, prop_name=prop_field_name)
        if deleg_prop_val is None:
            return None
        if not isinstance(deleg_prop_val, dict):
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg=f"Expected CBM {delegation_type.name} "
                                                  f"delegation to be a dictionary, got {deleg_prop_val} "
                                                  f"of {type(deleg_prop_val)}")
        #print(f"Looking for {delegation_type} delegation from {adm_id} in {deleg_prop_val}")
        return deleg_prop_val.get(adm_id, None)


class Neo4jCBMFactory:
    """
    Help convert graphs between formats so long as they are rooted in Neo4jPropertyGraph
    """
    @staticmethod
    def create(graph: Neo4jPropertyGraph) -> Neo4jCBMGraph:
        assert graph is not None
        assert isinstance(graph.importer, Neo4jGraphImporter)

        return Neo4jCBMGraph(graph_id=graph.graph_id,
                             importer=graph.importer,
                             logger=graph.log)
