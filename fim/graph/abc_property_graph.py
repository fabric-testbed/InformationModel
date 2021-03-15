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
#
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
Abstract Base class representing operations on a property graph of resources.
Could be a delegation, a broker view of resources or a slice.
"""
import json
import uuid
import networkx as nx
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Set, Tuple

import logging

from fim.slivers.attached_components import ComponentSliver, AttachedComponentsInfo
from fim.slivers.capacities_labels import Capacities, Labels, ReservationInfo
from fim.slivers.delegations import Delegation
from fim.slivers.interface_info import InterfaceSliver, InterfaceInfo
from fim.slivers.network_node import NodeSliver
from fim.slivers.network_link import NetworkLinkSliver
from fim.slivers.switch_fabric import SwitchFabricSliver, SwitchFabricInfo
from fim.graph.abc_property_graph_constants import ABCPropertyGraphConstants


class ABCPropertyGraph(ABCPropertyGraphConstants):
    """
    Abstract Base class representing operations on a property graph of resources.
    Could be a delegation, a broker view of resources or a slice.
    NOTE: this makes a very fundamental assumption that all graphs are sharing
    a common store and nodes of different graphs can be connected to each other.
    Graphs are distinguished by GraphID property on each node.
    """

    SLIVER_PROPERTY_TO_GRAPH = {
        "name": ABCPropertyGraphConstants.PROP_NAME,
        "type": ABCPropertyGraphConstants.PROP_TYPE,
        "capacities": ABCPropertyGraphConstants.PROP_CAPACITIES,
        "labels": ABCPropertyGraphConstants.PROP_LABELS,
        "capacity_delegations": ABCPropertyGraphConstants.PROP_CAPACITY_DELEGATIONS,
        "label_delegations": ABCPropertyGraphConstants.PROP_LABEL_DELEGATIONS,
        "capacity_allocations": ABCPropertyGraphConstants.PROP_CAPACITY_ALLOCATIONS,
        "label_allocations": ABCPropertyGraphConstants.PROP_LABEL_ALLOCATIONS,
        "reservation_info": ABCPropertyGraphConstants.PROP_RESERVATION_INFO,
        "site": ABCPropertyGraphConstants.PROP_SITE,
        # note lack of image type in this mapping
        "image_ref": ABCPropertyGraphConstants.PROP_IMAGE_REF,
        "management_ip": ABCPropertyGraphConstants.PROP_MGMT_IP,
        "allocation_constraints": ABCPropertyGraphConstants.PROP_ALLOCATION_CONSTRAINTS,
        "service_endpoint": ABCPropertyGraphConstants.PROP_SERVICE_ENDPOINT,
        "details": ABCPropertyGraphConstants.PROP_DETAILS,
        "layer": ABCPropertyGraphConstants.PROP_LAYER,
        "technology": ABCPropertyGraphConstants.PROP_TECHNOLOGY,
        "model": ABCPropertyGraphConstants.PROP_MODEL,
        "node_map": ABCPropertyGraphConstants.PROP_NODE_MAP
    }

    @abstractmethod
    def __init__(self, *, graph_id: str, importer, logger=None):
        """
        New graph with an id
        :param graph_id:
        """
        assert graph_id is not None
        assert importer is not None
        self.graph_id = graph_id
        self.importer = importer
        if logger is None:
            self.log = logging.getLogger(__name__)
        else:
            self.log = logger

    def get_graph_id(self):
        return self.graph_id

    @abstractmethod
    def validate_graph(self) -> None:
        """
        validate graph according to a built-in set of rules
        :return: - None,
        """

    @abstractmethod
    def delete_graph(self) -> None:
        """
        delete a graph from the database
        :return: - None
        """

    @abstractmethod
    def get_node_properties(self, *, node_id: str) -> (List[str], Dict[str, Any]):
        """
        return a tuple of labels and properties of a node node_id in graph graph_id
        :param node_id:
        :return: List[str], dictionary[string, Any]
        """

    @abstractmethod
    def get_node_json_property_as_object(self, *, node_id: str, prop_name: str) -> Any:
        """
        Return node property as a python object (applies to JSON encoded properties), will
        fail on other property values.
        :param node_id:
        :param prop_name:
        :return:
        """

    @abstractmethod
    def get_link_properties(self, *, node_a: str, node_b: str) -> (str, Dict[str, Any]):
        """
        return a tuple of link kind and all properties of a link between two nodes node_a and node_b
        :param node_a:
        :param node_b:
        :param kind: kind of link/edge
        :return: (str, dictionary[string, Any])
        """

    @abstractmethod
    def update_node_property(self, *, node_id: str, prop_name: str,
                             prop_val: Any) -> None:
        """
        update a selected property of a node
        :param node_id:
        :param prop_name:
        :param prop_val:
        :return:
        """

    @abstractmethod
    def unset_node_property(self, *, node_id: str, prop_name: str) -> None:
        """
        Unset/remove this property from a node. Not all properties can be
        unset (e.g. graph id and node id cannot)
        :param node_id:
        :param prop_name:
        :return:
        """

    @abstractmethod
    def update_nodes_property(self, *, prop_name: str, prop_val: Any) -> None:
        """
        update a selected property on all nodes of the graph
        :param prop_name:
        :param prop_val:
        :return:
        """

    @abstractmethod
    def update_node_properties(self, *, node_id: str, props: Dict[str, Any]) -> None:
        """
        update multiple properties
        :param node_id:
        :param props:
        :return:
        """

    @abstractmethod
    def update_link_property(self, *, node_a: str, node_b: str, kind: str,
                             prop_name: str, prop_val: Any) -> None:
        """
        update a link property for a link between node_a and node_b
        :param node_a:
        :param node_b:
        :param kind: - link/relationship type
        :param prop_name:
        :param prop_val:
        :return:
        """

    @abstractmethod
    def unset_link_property(self, *, node_a: str, node_b: str, kind: str,
                             prop_name: str) -> None:
        """
        Unset a property on a specified link
        :param node_a:
        :param node_b:
        :param kind:
        :param prop_name:
        :return:
        """

    @abstractmethod
    def update_link_properties(self, *, node_a: str, node_b: str, kind: str,
                               props: Dict[str, Any]) -> None:
        """
        update multiple properties on a link between node_a and node_b
        :param node_a:
        :param node_b:
        :param kind: - link/relationship type
        :param props:
        :return:
        """

    @abstractmethod
    def list_all_node_ids(self) -> List[str]:
        """
        list all NodeID properties of a given graph
        :return:
        """

    @abstractmethod
    def get_all_nodes_by_class(self, *, label: str) -> List[str]:
        """
        Get a list of nodes of this class/label
        :param label:
        :return:
        """

    @abstractmethod
    def serialize_graph(self) -> str:
        """
        Serialize a given graph into a string
        :return:
        """

    def clone_graph(self, *, new_graph_id: str):
        """
        Clone a graph to a new graph_id by serializing/deserializing it
        :param new_graph_id:
        :return:
        """
        assert new_graph_id is not None
        graph_string = self.serialize_graph()
        if graph_string is None:
            raise PropertyGraphQueryException(msg=f"Unable to find graph with id {self.graph_id} for cloning")
        return self.importer.import_graph_from_string(graph_string=graph_string,
                                                      graph_id=new_graph_id)

    @abstractmethod
    def graph_exists(self) -> bool:
        """
        Does the graph with this ID exist?
        :return:
        """

    @abstractmethod
    def get_nodes_on_shortest_path(self, *, node_a: str, node_z: str, rel: str = None) -> List:
        """
        Get a list of node ids that lie on a shortest path between two nodes. Return empty
        list if no path can be found. Optionally specify the type of relationship that path
        should consist of.
        :param node_a:
        :param node_z:
        :param rel:
        :return:
        """

    @abstractmethod
    def get_first_neighbor(self, *, node_id: str, rel: str, node_label: str) -> List:
        """
        Return a list of ids of nodes of this label related via relationship. List may be empty.
        :param node_id:
        :param rel:
        :param node_label:
        :return:
        """

    @abstractmethod
    def get_first_and_second_neighbor(self, *, node_id: str, rel1: str, node1_label: str,
                                      rel2: str, node2_label: str) -> List:
        """
        Return a list of 2-member lists of node ids related to this node via two specified relationships.
        List may be empty.
        :param node_id:
        :param rel1:
        :param node1_label:
        :param rel2:
        :param node2_label:
        :return:
        """

    @abstractmethod
    def node_exists(self, *, node_id: str, label: str):
        """
        Check if this node exists
        :param node_id:
        :param label:
        :return:
        """

    @abstractmethod
    def add_node(self, *, node_id: str, label: str, props: Dict[str, Any] = None) -> None:
        """
        Add a new node with specified
        :param node_id:
        :param label: class or label of this node
        :param props: initial set of properties
        :return:
        """

    @abstractmethod
    def add_link(self, *, node_a: str, rel: str, node_b: str, props: Dict[str, Any] = None) -> None:
        """
        Add a link of specified type (rel) between the two nodes. Properties can be added
        at the same time.
        :param node_a:
        :param rel:
        :param node_b:
        :param props:
        :return:
        """

    @abstractmethod
    def delete_node(self, *, node_id: str):
        """
        Delete node from a graph (incident edges automatically deleted)
        :param node_id:
        :return:
        """

    @abstractmethod
    def find_matching_nodes(self, *, other_graph) -> Set:
        """
        Return a set of node ids that match between the two graphs
        :param other_graph:
        :return:
        """

    @abstractmethod
    def merge_nodes(self, node_id: str, other_graph, merge_properties=None):
        """
        Merge two nodes of the same id belonging to two graphs. Optionally
        specify merging behavior for individual properties
        :param node_id:
        :param other_graph:
        :param merge_properties:
        :return:
        """

    def __repr__(self):
        return f"Graph with id {self.graph_id}"

    def _validate_json_property(self, node_id: str, props: Dict, strict: bool = False) -> Tuple[str, str] or None:
        """
        Validate that JSON in a particular node in a particular property is valid or throw
        a JSONDecodeError exception. Strict set to true causes exception if property is not found.
        Default strict is set to False. If property is not a valid JSON it's value is returned.
        :param node_id:
        :param prop_name:
        :param strict
        :return:
        """
        for prop_name in ABCPropertyGraphConstants.JSON_PROPERTY_NAMES:
            if prop_name not in props.keys():
                if strict:
                    # if property is not there, raise exception
                    raise PropertyGraphImportException(graph_id=self.graph_id, node_id=node_id,
                                                       msg=f"Unable to find property {prop_name} on a node")
                else:
                    # if property is not there, just return
                    continue
            # try loading it as JSON. Exception may be thrown
            if props[prop_name] is not None and props[prop_name] != "None":
                try:
                    json.loads(props[prop_name])
                except json.decoder.JSONDecodeError:
                    return prop_name, props[prop_name]
            else:
                continue
        return None

    def _validate_all_json_properties(self) -> None:
        """
        Validate all expected JSON properties of all nodes in a given graph or raise an exception
        :return:
        """
        nodes = self.list_all_node_ids()
        if len(nodes) == 0:
            raise PropertyGraphQueryException(graph_id=self.graph_id,
                                              node_id=None, msg="Unable to list nodes of graph")
        for node in nodes:
            _, props = self.get_node_properties(node_id=node)
            prop_tuple = self._validate_json_property(node_id=node, props=props)
            if prop_tuple is not None:
                raise PropertyGraphImportException(graph_id=self.graph_id, node_id=node,
                                                   msg=f"Unable to parse JSON property {prop_tuple[0]} "
                                                       f"with value {prop_tuple[1]}")

    @staticmethod
    def map_sliver_property_to_graph(prop_name: str) -> str or None:
        """
        Map a property name in a sliver to a graph property or return None
        :param prop_name:
        :return:
        """
        return ABCPropertyGraph.SLIVER_PROPERTY_TO_GRAPH.get(prop_name, None)

    @staticmethod
    def node_sliver_to_graph_properties_dict(sliver: NodeSliver) -> Dict[str, str]:
        """
        This method knows how to map sliver fields to graph properties
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict[ABCPropertyGraph.PROP_NAME] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict[ABCPropertyGraph.PROP_TYPE] = str(sliver.resource_type)
        if sliver.resource_model is not None:
            prop_dict[ABCPropertyGraph.PROP_MODEL] = sliver.resource_model
        if sliver.capacities is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITIES] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict[ABCPropertyGraph.PROP_LABELS] = sliver.labels.to_json()
        if sliver.capacity_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS] = \
                Delegation.from_list_to_json(sliver.capacity_delegations)
        if sliver.label_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_LABEL_DELEGATIONS] = \
                Delegation.from_list_to_json(sliver.label_delegations)
        if sliver.capacity_allocations is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITY_ALLOCATIONS] = sliver.capacity_allocations.to_json()
        if sliver.label_allocations is not None:
            prop_dict[ABCPropertyGraph.PROP_LABEL_ALLOCATIONS] = sliver.label_allocations.to_json()
        if sliver.reservation_info is not None:
            prop_dict[ABCPropertyGraph.PROP_RESERVATION_INFO] = sliver.reservation_info.to_json()
        if sliver.site is not None:
            prop_dict[ABCPropertyGraph.PROP_SITE] = sliver.site
        if sliver.image_ref is not None and sliver.image_type is not None:
            prop_dict[ABCPropertyGraph.PROP_IMAGE_REF] = sliver.image_ref + ',' + str(sliver.image_type)
        if sliver.management_ip is not None:
            prop_dict[ABCPropertyGraph.PROP_MGMT_IP] = str(sliver.management_ip)
        if sliver.allocation_constraints is not None:
            prop_dict[ABCPropertyGraph.PROP_ALLOCATION_CONSTRAINTS] = sliver.allocation_constraints
        if sliver.service_endpoint is not None:
            prop_dict[ABCPropertyGraph.PROP_SERVICE_ENDPOINT] = str(sliver.service_endpoint)
        if sliver.details is not None:
            prop_dict[ABCPropertyGraph.PROP_DETAILS] = sliver.details
        if sliver.node_map is not None:
            prop_dict[ABCPropertyGraph.PROP_NODE_MAP] = json.dumps(sliver.node_map)
        return prop_dict

    @staticmethod
    def link_sliver_to_graph_properties_dict(sliver: NetworkLinkSliver) -> Dict[str, str]:
        """
        This method knows how to map sliver fields to graph properties
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict[ABCPropertyGraph.PROP_NAME] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict[ABCPropertyGraph.PROP_TYPE] = str(sliver.resource_type)
        if sliver.resource_model is not None:
            prop_dict[ABCPropertyGraph.PROP_MODEL] = sliver.resource_model
        if sliver.capacities is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITIES] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict[ABCPropertyGraph.PROP_LABELS] = sliver.labels.to_json()
        if sliver.capacity_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS] = \
                Delegation.from_list_to_json(sliver.capacity_delegations)
        if sliver.label_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_LABEL_DELEGATIONS] = \
                Delegation.from_list_to_json(sliver.label_delegations)
        if sliver.capacity_allocations is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITY_ALLOCATIONS] = sliver.capacity_allocations.to_json()
        if sliver.label_allocations is not None:
            prop_dict[ABCPropertyGraph.PROP_LABEL_ALLOCATIONS] = sliver.label_allocations.to_json()
        if sliver.reservation_info is not None:
            prop_dict[ABCPropertyGraph.PROP_RESERVATION_INFO] = sliver.reservation_info.to_json()
        if sliver.layer is not None:
            prop_dict[ABCPropertyGraph.PROP_LAYER] = str(sliver.layer)
        if sliver.technology is not None:
            prop_dict[ABCPropertyGraph.PROP_TECHNOLOGY] = str(sliver.technology)
        if sliver.details is not None:
            prop_dict[ABCPropertyGraph.PROP_DETAILS] = sliver.details
        if sliver.node_map is not None:
            prop_dict[ABCPropertyGraph.PROP_NODE_MAP] = json.dumps(sliver.node_map)

        return prop_dict

    @staticmethod
    def component_sliver_to_graph_properties_dict(sliver: ComponentSliver) -> Dict[str, str]:
        """
        This method knows how to map component sliver fields to graph properties
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict[ABCPropertyGraph.PROP_NAME] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict[ABCPropertyGraph.PROP_TYPE] = str(sliver.resource_type)
        if sliver.resource_model is not None:
            prop_dict[ABCPropertyGraph.PROP_MODEL] = sliver.resource_model
        if sliver.capacities is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITIES] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict[ABCPropertyGraph.PROP_LABELS] = sliver.labels.to_json()
        if sliver.capacity_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS] = \
                Delegation.from_list_to_json(sliver.capacity_delegations)
        if sliver.label_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_LABEL_DELEGATIONS] = \
                Delegation.from_list_to_json(sliver.label_delegations)
        if sliver.details is not None:
            prop_dict[ABCPropertyGraph.PROP_DETAILS] = sliver.details
        if sliver.node_map is not None:
            prop_dict[ABCPropertyGraph.PROP_NODE_MAP] = json.dumps(sliver.node_map)

        return prop_dict

    @staticmethod
    def switch_fabric_sliver_to_graph_properties_dict(sliver: SwitchFabricSliver) -> Dict[str, str]:
        """
        This method knows how to map switch fabric sliver fields to graph properties
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict[ABCPropertyGraph.PROP_NAME] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict[ABCPropertyGraph.PROP_TYPE] = str(sliver.resource_type)
        if sliver.resource_model is not None:
            prop_dict[ABCPropertyGraph.PROP_MODEL] = sliver.resource_model
        if sliver.capacities is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITIES] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict[ABCPropertyGraph.PROP_LABELS] = sliver.labels.to_json()
        if sliver.capacity_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS] = \
                Delegation.from_list_to_json(sliver.capacity_delegations)
        if sliver.label_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_LABEL_DELEGATIONS] = \
                Delegation.from_list_to_json(sliver.label_delegations)
        if sliver.layer is not None:
            prop_dict[ABCPropertyGraph.PROP_LAYER] = str(sliver.layer)
        if sliver.details is not None:
            prop_dict[ABCPropertyGraph.PROP_DETAILS] = sliver.details
        if sliver.node_map is not None:
            prop_dict[ABCPropertyGraph.PROP_NODE_MAP] = json.dumps(sliver.node_map)

        return prop_dict

    @staticmethod
    def interface_sliver_to_graph_properties_dict(sliver: InterfaceSliver) -> Dict[str, str]:
        """
        This method knows how to map interface sliver fields to graph properties
        :param sliver:
        :return:
        """
        prop_dict = dict()

        if sliver.resource_name is not None:
            prop_dict[ABCPropertyGraph.PROP_NAME] = sliver.resource_name
        if sliver.resource_type is not None:
            prop_dict[ABCPropertyGraph.PROP_TYPE] = str(sliver.resource_type)
        if sliver.resource_model is not None:
            prop_dict[ABCPropertyGraph.PROP_MODEL] = sliver.resource_model
        if sliver.capacities is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITIES] = sliver.capacities.to_json()
        if sliver.labels is not None:
            prop_dict[ABCPropertyGraph.PROP_LABELS] = sliver.labels.to_json()
        if sliver.capacity_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS] = \
                Delegation.from_list_to_json(sliver.capacity_delegations)
        if sliver.label_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_LABEL_DELEGATIONS] = \
                Delegation.from_list_to_json(sliver.label_delegations)
        if sliver.details is not None:
            prop_dict[ABCPropertyGraph.PROP_DETAILS] = sliver.details
        if sliver.node_map is not None:
            prop_dict[ABCPropertyGraph.PROP_NODE_MAP] = json.dumps(sliver.node_map)

        return prop_dict

    @staticmethod
    def node_sliver_from_graph_properties_dict(d: Dict[str, str]) -> NodeSliver:
        n = NodeSliver()
        if d.get(ABCPropertyGraph.PROP_IMAGE_REF, None) is None:
            image_ref = None
            image_type = None
        else:
            image_ref, image_type = d[ABCPropertyGraph.PROP_IMAGE_REF].split(',')
        n.set_properties(name=d.get(ABCPropertyGraph.PROP_NAME, None),
                         type=n.type_from_str(d.get(ABCPropertyGraph.PROP_TYPE, None)),
                         model=d.get(ABCPropertyGraphConstants.PROP_MODEL, None),
                         capacities=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITIES, None)),
                         labels=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABELS, None)),
                         capacity_allocations=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITY_ALLOCATIONS,
                                                                           None)),
                         label_allocations=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABEL_ALLOCATIONS,
                                                                    None)),
                         reservation_info=ReservationInfo().from_json(d.get(ABCPropertyGraph.PROP_RESERVATION_INFO,
                                                                            None)),
                         capacity_delegations=Delegation.from_json_to_list(
                             d.get(ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS, None)),
                         label_delegations=Delegation.from_json_to_list(
                             d.get(ABCPropertyGraph.PROP_LABEL_DELEGATIONS, None)),
                         site=d.get(ABCPropertyGraph.PROP_SITE, None),
                         image_ref=image_ref,
                         image_type=image_type,
                         management_ip=d.get(ABCPropertyGraph.PROP_MGMT_IP, None),
                         allocation_constraints=d.get(ABCPropertyGraph.PROP_ALLOCATION_CONSTRAINTS, None),
                         service_endpoint=d.get(ABCPropertyGraph.PROP_SERVICE_ENDPOINT, None),
                         details=d.get(ABCPropertyGraph.PROP_DETAILS, None),
                         node_map=json.loads(d[ABCPropertyGraph.PROP_NODE_MAP]) if
                         d.get(ABCPropertyGraph.PROP_NODE_MAP, None) is not None else None
                         )
        return n

    @staticmethod
    def link_sliver_from_graph_properties_dict(d: Dict[str, str]) -> NetworkLinkSliver:
        n = NetworkLinkSliver()
        n.set_properties(name=d.get(ABCPropertyGraph.PROP_NAME, None),
                         type=n.type_from_str(d.get(ABCPropertyGraph.PROP_TYPE, None)),
                         model=d.get(ABCPropertyGraphConstants.PROP_MODEL, None),
                         capacities=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITIES, None)),
                         labels=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABELS, None)),
                         capacity_allocations=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITY_ALLOCATIONS,
                                                                           None)),
                         label_allocations=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABEL_ALLOCATIONS,
                                                                    None)),
                         reservation_info=ReservationInfo().from_json(d.get(ABCPropertyGraph.PROP_RESERVATION_INFO,
                                                                            None)),
                         capacity_delegations=Delegation.from_json_to_list(
                             d.get(ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS, None)),
                         label_delegations=Delegation.from_json_to_list(
                             d.get(ABCPropertyGraph.PROP_LABEL_DELEGATIONS, None)),
                         allocation_constraints=d.get(ABCPropertyGraph.PROP_ALLOCATION_CONSTRAINTS, None),
                         details=d.get(ABCPropertyGraph.PROP_DETAILS, None),
                         layer=d.get(ABCPropertyGraph.PROP_LAYER),
                         technology=d.get(ABCPropertyGraph.PROP_TECHNOLOGY),
                         node_map=json.loads(d[ABCPropertyGraph.PROP_NODE_MAP]) if
                         d.get(ABCPropertyGraph.PROP_NODE_MAP, None) is not None else None
                         )
        return n

    @staticmethod
    def component_sliver_from_graph_properties_dict(d: Dict[str, str]) -> ComponentSliver:
        """
        Create component sliver from node graph properties
        :param d:
        :return:
        """
        cs = ComponentSliver()
        cs.set_properties(name=d.get(ABCPropertyGraph.PROP_NAME, None),
                          type=cs.type_from_str(d.get(ABCPropertyGraph.PROP_TYPE, None)),
                          model=d.get(ABCPropertyGraphConstants.PROP_MODEL, None),
                          capacities=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITIES, None)),
                          labels=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABELS, None)),
                          capacity_delegations=Delegation.from_json_to_list(
                              d.get(ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS, None)),
                          label_delegations=Delegation.from_json_to_list(
                              d.get(ABCPropertyGraph.PROP_LABEL_DELEGATIONS, None)),
                          details=d.get(ABCPropertyGraph.PROP_DETAILS, None),
                          node_map=json.loads(d[ABCPropertyGraph.PROP_NODE_MAP]) if
                          d.get(ABCPropertyGraph.PROP_NODE_MAP, None) is not None else None
                          )
        return cs

    @staticmethod
    def switch_fabric_sliver_from_graph_properties_dict(d: Dict[str, str]) -> SwitchFabricSliver:
        """
        SwitchFabric sliver from node graph properties
        :param d:
        :return:
        """
        sf = SwitchFabricSliver()
        sf.set_properties(name=d.get(ABCPropertyGraph.PROP_NAME, None),
                          type=sf.type_from_str(d.get(ABCPropertyGraph.PROP_TYPE, None)),
                          model=d.get(ABCPropertyGraphConstants.PROP_MODEL, None),
                          capacities=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITIES, None)),
                          labels=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABELS, None)),
                          capacity_delegations=Delegation.from_json_to_list(
                              d.get(ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS, None)),
                          label_delegations=Delegation.from_json_to_list(
                              d.get(ABCPropertyGraph.PROP_LABEL_DELEGATIONS, None)),
                          layer=sf.layer_from_str(d.get(ABCPropertyGraph.PROP_LAYER, None)),
                          details=d.get(ABCPropertyGraph.PROP_DETAILS, None),
                          node_map=json.loads(d[ABCPropertyGraph.PROP_NODE_MAP]) if
                          d.get(ABCPropertyGraph.PROP_NODE_MAP, None) is not None else None
                          )
        return sf

    @staticmethod
    def interface_sliver_from_graph_properties_dict(d: Dict[str, str]) -> InterfaceSliver:
        """
        Interface sliver from node graph properties
        :param d:
        :return:
        """
        isl = InterfaceSliver()
        isl.set_properties(name=d.get(ABCPropertyGraph.PROP_NAME, None),
                           type=isl.type_from_str(d.get(ABCPropertyGraph.PROP_TYPE, None)),
                           model=d.get(ABCPropertyGraphConstants.PROP_MODEL, None),
                           capacities=Capacities().from_json(d.get(ABCPropertyGraph.PROP_CAPACITIES, None)),
                           labels=Labels().from_json(d.get(ABCPropertyGraph.PROP_LABELS, None)),
                           capacity_delegations=Delegation.from_json_to_list(
                               d.get(ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS, None)),
                           label_delegations=Delegation.from_json_to_list(
                               d.get(ABCPropertyGraph.PROP_LABEL_DELEGATIONS, None)),
                           details=d.get(ABCPropertyGraph.PROP_DETAILS, None),
                           node_map=json.loads(d[ABCPropertyGraph.PROP_NODE_MAP]) if
                           d.get(ABCPropertyGraph.PROP_NODE_MAP, None) is not None else None
                           )
        return isl

    def build_deep_node_sliver(self, *, node_id: str) -> NodeSliver:
        """
        Build a deep NetworkNode or other similar (e.g.
        network-attached storage) sliver from a graph node
        :param node_id:
        :return:
        """
        clazzes, props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_NetworkNode not in clazzes:
            raise PropertyGraphQueryException(node_id=node_id, graph_id=self.graph_id,
                                              msg="Node is not of class NetworkNode")
        # create top-level sliver
        ns = self.node_sliver_from_graph_properties_dict(props)
        ns.node_id = node_id
        # find and build deep slivers of switch fabrics (if any) and components (if any)
        comps = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                        node_label=ABCPropertyGraph.CLASS_Component)
        if comps is not None and len(comps) > 0:
            aci = AttachedComponentsInfo()
            for c in comps:
                cs = self.build_deep_component_sliver(node_id=c)
                aci.add_device(cs)
            ns.attached_components_info = aci

        sfs = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                      node_label=ABCPropertyGraph.CLASS_SwitchFabric)
        if sfs is not None and len(sfs) > 0:
            sfi = SwitchFabricInfo()
            for s in sfs:
                sfsl = self.build_deep_sf_sliver(node_id=s)
                sfi.add_switch_fabric(sfsl)
            ns.switch_fabric_info = sfi

        return ns

    def build_deep_link_sliver(self, *, node_id: str) -> NetworkLinkSliver:
        """
        Build a deep NetworkLinkSliver from a graph node
        :param node_id:
        :return:
        """
        clazzes, props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_Link not in clazzes:
            raise PropertyGraphQueryException(node_id=node_id, graph_id=self.graph_id,
                                              msg="Node is not of class Link")
        # create top-level sliver
        ns = self.link_sliver_from_graph_properties_dict(props)
        ns.node_id = node_id
        # find interfaces and attach
        ifs = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_CONNECTS,
                                      node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
        if ifs is not None and len(ifs) > 0:
            ifi = InterfaceInfo()
            for i in ifs:
                _, iprops = self.get_node_properties(node_id=i)
                ifsl = self.interface_sliver_from_graph_properties_dict(iprops)
                ifsl.node_id = node_id
                ifi.add_interface(ifsl)
            ns.interface_info = ifi

        return ns

    def build_deep_sf_sliver(self, *, node_id: str) -> SwitchFabricSliver:
        clazzes, props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_SwitchFabric not in clazzes:
            raise PropertyGraphQueryException(node_id=node_id, graph_id=self.graph_id,
                                              msg="Node is not of class SwitchFabric")
        # create top-level sliver
        sfs = self.switch_fabric_sliver_from_graph_properties_dict(props)
        sfs.node_id = node_id
        # find interfaces and attach
        ifs = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_CONNECTS,
                                      node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
        if ifs is not None and len(ifs) > 0:
            ifi = InterfaceInfo()
            for i in ifs:
                _, iprops = self.get_node_properties(node_id=i)
                ifsl = self.interface_sliver_from_graph_properties_dict(iprops)
                ifsl.node_id = node_id
                ifi.add_interface(ifsl)
            sfs.interface_info = ifi
        return sfs

    def build_deep_component_sliver(self, *, node_id: str) -> ComponentSliver:
        clazzes, props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_Component not in clazzes:
            raise PropertyGraphQueryException(node_id=node_id, graph_id=self.graph_id,
                                              msg="Node is not of class Component")
        # create top-level sliver
        cs = self.component_sliver_from_graph_properties_dict(props)
        cs.node_id = node_id
        # find any switch fabrics, build and attach
        sfs = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                      node_label=ABCPropertyGraph.CLASS_SwitchFabric)
        if sfs is not None and len(sfs) > 0:
            sfi = SwitchFabricInfo()
            for s in sfs:
                sfsl = self.build_deep_sf_sliver(node_id=s)
                sfi.add_switch_fabric(sfsl)
            cs.switch_fabric_info = sfi
        return cs


class ABCGraphImporter(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def import_graph_from_string(self, *, graph_string: str, graph_id: str = None) -> ABCPropertyGraph:
        """
        import a graph from string adding GraphID to each node (new graph_id is generated
        if graph_id is None)
        :param graph_string: - graph represented by a string (e.g. GraphML)
        :param graph_id: - optional id of the graph in the database
        :return: - an instantiation of a property graph
        """

    @abstractmethod
    def import_graph_from_string_direct(self, *, graph_string: str) -> ABCPropertyGraph:
        """
        import a graph from string without any manipulations
        :param graph_string:
        :return:
        """

    def import_graph_from_file(self, *, graph_file: str, graph_id: str = None) -> ABCPropertyGraph:
        """
        import a graph from a file
        :param graph_file: - path to graph file (GraphML)
        :param graph_id: - optional id of the graph in the database
        :return: an instantiation of a property graph
        """
        assert graph_file is not None
        with open(graph_file, 'r') as f:
            graph_string = f.read()

        return self.import_graph_from_string(graph_string=graph_string, graph_id=graph_id)

    @abstractmethod
    def import_graph_from_file_direct(self, *, graph_file: str) -> ABCPropertyGraph:
        """
        import a graph from file without any manipulations
        :param graph_file:
        :return:
        """

    @abstractmethod
    def cast_graph(self, *, graph_id: str) -> ABCPropertyGraph:
        """
        Recast a graph with a given node id, checks that graph exists
        :param graph_id:
        :return:
        """

    @staticmethod
    def enumerate_graph_nodes(*, graph_file: str, new_graph_file: str, node_id_prop: str = "NodeID") -> None:
        """
        Read in a graph and add a NodeId property to every node assigning a unique GUID (unless present).
        Save into a new file
        :param graph_file: original graph file name
        :param new_graph_file: new file name
        :param node_id_prop: alternative property name for node id (default NodeId)
        :return:
        """
        assert graph_file is not None
        assert new_graph_file is not None

        # read using networkx
        g = nx.read_graphml(graph_file)
        # add node id to every node
        for n in list(g.nodes):
            if (node_id_prop not in g.nodes[n].keys()) or (len(g.nodes[n][node_id_prop]) == 0):
                g.nodes[n][node_id_prop] = str(uuid.uuid4())
        # save to a new file
        nx.write_graphml(g, new_graph_file)

    @staticmethod
    def enumerate_graph_nodes_to_string(*, graph_file: str, node_id_prop: str = "NodeID") -> str:
        """
        Read in a graph and add a NodeId property to every node assigning a unique GUID (unless present).
        Return GraphML string.
        :param graph_file: original graph file name
        :param node_id_prop: alternative property name for node id (default NodeId)
        :return:
        """
        assert graph_file is not None

        # read using networkx
        g = nx.read_graphml(graph_file)
        # add node id to every node
        for n in list(g.nodes):
            if (node_id_prop not in g.nodes[n].keys()) or (len(g.nodes[n][node_id_prop]) == 0):
                g.nodes[n][node_id_prop] = str(uuid.uuid4())
        graph_string = '\n'.join(nx.generate_graphml(g))
        return graph_string

    @abstractmethod
    def delete_graph(self, *, graph_id: str) -> None:
        """
        Delete a single graph with this ID
        :param graph_id:
        :return:
        """

    @abstractmethod
    def delete_all_graphs(self) -> None:
        """
        delete all graphs from the database
        :return:
        """

    @staticmethod
    def get_graph_id(*, graph_file: str) -> str:
        """
        Read graphml file using NetworkX to get GraphID property
        :param graph_file:
        :return:
        """
        assert graph_file is not None
        g = nx.read_graphml(graph_file)

        # check graph_ids on nodes
        graph_ids = set()
        try:
            for n in list(g.nodes):
                graph_ids.add(g.nodes[n][ABCPropertyGraph.GRAPH_ID])
        except KeyError:
            raise PropertyGraphImportException(graph_id=None, msg=f"Graph does not contain GraphID property")

        if len(graph_ids) > 1:
            raise PropertyGraphImportException(graph_id=None, msg=f"Graph contains more than one GraphID: {graph_ids}")
        return graph_ids.pop()


class PropertyGraphException(Exception):
    """
    base exception class for all graph exceptions
    """
    def __init__(self, *, graph_id: str or None, msg: Any = None):
        """
        initialize based on graph_id of the graph in question
        :param graph_id:
        :param msg:
        """
        if msg is None:
            super().__init__(f"Unspecified error importing graph {graph_id}")
        else:
            if graph_id is not None:
                super().__init__(f"{msg} in {graph_id}")
            else:
                super().__init__(msg)
        self.graph_id = graph_id
        self.msg = msg


class PropertyGraphImportException(PropertyGraphException):
    """
    import exception for a property graph
    """
    def __init__(self, *, graph_id: str or None,  msg: str, node_id: str = None):
        if node_id is None:
            super().__init__(graph_id=graph_id, msg=f"Error [{msg}] importing graph")
        else:
            super().__init__(graph_id=graph_id, msg=f"Error [{msg}] in node {node_id} importing graph")


class PropertyGraphQueryException(PropertyGraphException):
    """
    query exception for a property graph
    """
    def __init__(self, *, graph_id: str or None, node_id: str or None, msg: str, node_b: str = None, kind: str = None):
        """
        Query error for node or link
        :param graph_id:
        :param node_id:
        :param msg:
        :param node_b:
        :param kind:
        """
        if node_b is not None and node_id is not None:
            super().__init__(graph_id=graph_id, msg=f"[{msg}] in querying for link {kind} between {node_id} and {node_b}")
        elif node_b is None and node_id is not None:
            super().__init__(graph_id=graph_id, msg=f"[{msg}] in querying node {node_id}")
        else:
            super().__init__(graph_id=graph_id, msg=f"[{msg}]")
        self.node_id = node_id
