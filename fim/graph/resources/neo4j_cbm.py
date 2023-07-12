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

from typing import List, Dict, Tuple

from collections import defaultdict

from ..abc_property_graph import ABCPropertyGraph, ABCPropertyGraphConstants, PropertyGraphQueryException
from ..neo4j_property_graph import Neo4jPropertyGraph, Neo4jGraphImporter
from .abc_cbm import ABCCBMPropertyGraph
from .neo4j_adm import Neo4jADMGraph
from fim.slivers.capacities_labels import StructuralInfo, StructuralInfoException
from fim.slivers.delegations import DelegationType, Delegations
from fim.slivers.attached_components import AttachedComponentsInfo, ComponentType

from ...pluggable import PluggableRegistry, BrokerPluggable, PluggableType


class Neo4jCBMGraph(Neo4jPropertyGraph, ABCCBMPropertyGraph):
    """
    Neo4j implementation of CBM
    """
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
        :param adm:
        :return:
        """
        _, cbm_node_props = self.get_node_properties(node_id=node_id)
        _, adm_node_props = adm.get_node_properties(node_id=node_id)
        props_modified = False
        for delegation_prop_name in [self.PROP_LABEL_DELEGATIONS, self.PROP_CAPACITY_DELEGATIONS]:
            # one or both of properties can have data, however only CBM or ADM
            # can have information about delegations - only one aggregate can speak for a resource
            if cbm_node_props.get(delegation_prop_name, None) is None:
                cbm_delegations = None
            else:
                cbm_delegations = Delegations.from_json(json_str=cbm_node_props[delegation_prop_name],
                                                        atype=DelegationType.LABEL if
                                                        delegation_prop_name == self.PROP_LABEL_DELEGATIONS else
                                                        DelegationType.CAPACITY)

            if adm_node_props.get(delegation_prop_name, None) is None:
                adm_delegations = None
            else:
                adm_delegations = Delegations.from_json(json_str=adm_node_props[delegation_prop_name],
                                                        atype=DelegationType.LABEL if
                                                        delegation_prop_name == self.PROP_LABEL_DELEGATIONS else
                                                        DelegationType.CAPACITY)

            if adm_delegations is None and cbm_delegations is None:
                continue
            if adm_delegations is not None and cbm_delegations is not None:
                raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                                  msg=f'This node contains delegations from both CBM and ADM graph,'
                                                      f'which is not allowed.')
            props_modified = True
            # take the non-None dictionary and write back
            new_delegations = cbm_delegations if cbm_delegations is not None else adm_delegations
            cbm_node_props[delegation_prop_name] = new_delegations.to_json()
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
        self.log.debug('CREATED TEMPORARY ADM GRAPH ID ' + temp_adm_graph_id +
                      ' when merging graph ' + adm.graph_id + ' into ' + self.graph_id)
        temp_graph = adm.clone_graph(new_graph_id=temp_adm_graph_id)
        # crude typecasting
        temp_adm_graph = Neo4jADMGraph(graph_id=temp_graph.graph_id,
                                       importer=temp_graph.importer,
                                       logger=temp_graph.log)

        # rewrite delegations into dictionaries keyed by ADM graph id,
        # but be sure to use original ADM graph ID when rewriting
        temp_adm_graph.rewrite_delegations(real_adm_id=adm.graph_id)

        # update the structural info adm_graph_ids field to a single member list on all CBM nodes
        si = StructuralInfo(adm_graph_ids=[adm.graph_id])
        temp_adm_graph.update_nodes_property(prop_name=self.PROP_STRUCTURAL_INFO,
                                             prop_val=si.to_json())

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
        # LabelDelegations: delegations can be provided only by one graph - either CBM or ADM
        # CapacityDelegations: delegations can be provided only by one graph - either CBM or ADM
        for node_id in common_node_ids:
            # update Label and Capacity delegation prior to merge
            # when nodes are merged, these properties are kept, ADM properties
            # are discarded
            self._update_node_delegations(node_id=node_id, adm=temp_adm_graph)

            # default behavior - keep CBM node properties, discard
            # temp_adm_graph properties
            self.merge_nodes(node_id=node_id,
                             other_graph=temp_adm_graph)

            # add delegation graph id to ADMGraphIDs property on common (merged) nodes
            _, cbm_node_props = self.get_node_properties(node_id=node_id)
            si = StructuralInfo.from_json(cbm_node_props[self.PROP_STRUCTURAL_INFO])
            si.adm_graph_ids.append(adm.graph_id)
            self.update_node_property(node_id=node_id, prop_name=self.PROP_STRUCTURAL_INFO,
                                      prop_val=si.to_json())

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
            _, adm_node_props = self.get_node_properties(node_id=node)
            si = StructuralInfo.from_json(adm_node_props[self.PROP_STRUCTURAL_INFO])

            if si.adm_graph_ids is None:
                self.log.warn(f'When unmerging ADMs encountered node {node} '
                              f'without adm_graph_ids field in property {adm_node_props[self.PROP_STRUCTURAL_INFO]}')
                continue
            if not isinstance(si.adm_graph_ids, list):
                raise PropertyGraphQueryException(node_id=node, graph_id=self.graph_id,
                                                  msg=f"When unmerging graph {graph_id}, encountered wrongly"
                                                      f"formatted {self.PROP_STRUCTURAL_INFO} field "
                                                      f"{adm_node_props[self.PROP_STRUCTURAL_INFO]}")
            if graph_id in si.adm_graph_ids:
                # update the ADM Graph IDs field
                si.adm_graph_ids.remove(graph_id)
                if len(si.adm_graph_ids) == 0:
                    delete_nodes.append(node)
                else:
                    # update
                    self.update_node_property(node_id=node, prop_name=self.PROP_STRUCTURAL_INFO,
                                              prop_val=si.to_json())
            # also unmerge delegations
            for del_prop in [self.PROP_CAPACITY_DELEGATIONS, self.PROP_LABEL_DELEGATIONS]:
                if del_prop not in adm_node_props.keys():
                    continue
                delegations = Delegations.from_json(json_str=adm_node_props[del_prop],
                                                    atype=DelegationType.LABEL if
                                                    del_prop == self.PROP_LABEL_DELEGATIONS
                                                    else DelegationType.CAPACITY)
                if delegations is None:
                    continue
                if graph_id in delegations.get_delegation_ids():
                    delegations.remove_by_id(graph_id)
                    if len(delegations.get_delegation_ids()) != 0:
                        raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node,
                                                          msg=f'This node had more than one delegation, remaining:'
                                                              f'{delegations}')
                    # under normal circumstances we should erase the delegation after unmerge if
                    # it belonged to the graph being removed
                    self.update_node_property(node_id=node, prop_name=del_prop,
                                              prop_val='')

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

    def get_matching_nodes_with_components(self, *, label: str, props: Dict,
                                           comps: AttachedComponentsInfo = None) -> List[str]:
        assert label is not None
        assert props is not None

        # collect unique types, models and count them
        component_counts = defaultdict(int)
        if comps is not None:
            for comp in comps.list_devices():
                assert(comp.resource_model is not None or comp.resource_type is not None)
                # shared nic count should always be 1
                if comp.resource_type != ComponentType.SharedNIC:
                    component_counts[(comp.resource_type, comp.resource_model)] = \
                        component_counts[(comp.resource_type, comp.resource_model)] + 1
                else:
                    component_counts[(comp.resource_type, comp.resource_model)] = 1
        # unroll properties
        node_props = ", ".join([x + ": " + '"' + props[x] + '"' for x in props.keys()])

        if len(component_counts.values()) == 0:
            # simple query on the properties of the node (no components)
            query = f"MATCH(n:GraphNode:{label} {{GraphID: $graphId, {node_props} }}) RETURN collect(n.NodeID) as candidate_ids"
        else:
            # build a query list
            node_query = f"MATCH(n:GraphNode:{label} {{GraphID: $graphId, {node_props} }}) WHERE "
            component_clauses = list()
            # add a clause for every tuple
            for k, v in component_counts.items():
                comp_props_list = list()
                if k[0] is not None:
                    comp_props_list.append('Type: ' + '"' + str(k[0]) + '"' + ' ')
                if k[1] is not None:
                    comp_props_list.append('Model: ' + '"' + k[1] + '"' + ' ')
                comp_props = ", ".join(comp_props_list)

                # uses pattern comprehension rather than pattern matching as per Neo4j v4+
                component_clauses.append(f"size([(n) -[:has]- (:Component {{GraphID: $graphId, "
                                         f"{comp_props}}}) | n.NodeID])>={str(v)}")
            query = node_query + " and ".join(component_clauses) + " RETURN collect(n.NodeID) as candidate_ids"

        #print(f'**** Resulting query {query=}')

        with self.driver.session() as session:

            val = session.run(query, graphId=self.graph_id).single()
            #print(f'VAL= {val}')
        if val is None:
            return list()
        return val.data()['candidate_ids']

    def get_intersite_links(self) -> List[Tuple[str, str, str]]:
        # does a lexicographic comparison of Site properties to ensure only unique links are returned
        query = 'match p= (n:GraphNode:NetworkNode {Type:"Switch", GraphID: $graphId}) -[:has]- (:GraphNode:NetworkService) ' \
                '-[:connects]- (cp1:ConnectionPoint) -[:connects]- (l:Link) ' \
                '-[:connects]- (cp2:ConnectionPoint) -[:connects]- (:GraphNode:NetworkService) ' \
                '-[:has]- (m:GraphNode:NetworkNode {Type:"Switch", GraphID: $graphId}) where n.Site > m.Site ' \
                'return n.NodeID as source, l.NodeID as link, m.NodeID as sink, n.Site as source_site, ' \
                'm.Site as sink_site, cp1.NodeID as source_cp, cp2.NodeID as sink_cp'
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id).values()
        if val is None:
            return list()
        return val

    def get_sites(self) -> List[str]:
        query = 'match(na:GraphNode:NetworkNode {Type:"Switch", GraphID: $graphId}) return ' \
                'collect(distinct na.Site) as allSites'
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id).single()
        if val is None:
            return list()
        return sorted(val.value())

    def get_disconnected_sites(self) -> List[str]:
        query = 'match(na:GraphNode:NetworkNode {Type:"Switch", GraphID: $graphId}) with collect(na.Site) ' \
                'as allSites match(n:GraphNode:NetworkNode {Type:"Switch", GraphID: $graphId}) ' \
                '-[:has]- (ns1:GraphNode:NetworkService {Type:"MPLS", GraphID: $graphId}) -[:connects*1..4]- ' \
                '(ns2:GraphNode:NetworkService {Type:"MPLS", GraphID: $graphId}) -[:has]- ' \
                '(m:GraphNode:NetworkNode {Type:"Switch", GraphID: $graphId}) ' \
                'with allSites, collect(distinct n.Site) as connectedSites ' \
                'return [x in allSites where not x in connectedSites] as disconnectedSites'
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id).single()
        if val is None:
            return list()
        return sorted(val.value())

    def get_connected_sites(self) -> List[str]:
        query = 'match(n:GraphNode:NetworkNode {Type:"Switch", GraphID: $graphId}) ' \
                '-[:has]- (ns1:GraphNode:NetworkService {Type:"MPLS", GraphID: $graphId}) -[:connects*1..4]- ' \
                '(ns2:GraphNode:NetworkService {Type:"MPLS", GraphID: $graphId}) -[:has]- ' \
                '(m:GraphNode:NetworkNode {Type:"Switch", GraphID: $graphId}) ' \
                'return collect(distinct n.Site) as connectedSites '
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id).single()
        if val is None:
            return list()
        return sorted(val.value())

    def get_facility_ports(self) -> List[str]:
        query = 'match(n:GraphNode:NetworkNode {Type: "Facility", GraphID: $graphId}) return ' \
                'collect(distinct n.Name) as allFPs'
        with self.driver.session() as session:
            val = session.run(query, graphId=self.graph_id).single()
        if val is None:
            return list()
        return sorted(val.value())


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
