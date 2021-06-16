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
from enum import Enum

import logging

from fim.slivers.attached_components import ComponentSliver, AttachedComponentsInfo
from fim.slivers.capacities_labels import Capacities, Labels, ReservationInfo, StructuralInfo, CapacityHints
from fim.slivers.delegations import Delegations, DelegationType
from fim.slivers.interface_info import InterfaceSliver, InterfaceInfo
from fim.slivers.base_sliver import BaseSliver
from fim.slivers.network_node import NodeSliver
from fim.slivers.network_link import NetworkLinkSliver
from fim.slivers.path_info import PathInfo, ERO
from fim.slivers.network_service import NetworkServiceSliver, NetworkServiceInfo
from fim.graph.abc_property_graph_constants import ABCPropertyGraphConstants


class GraphFormat(Enum):
    # default, works in Neo4j and NetworkX
    GRAPHML = 1
    # JSON formats are specific to NetworkX
    JSON_NODELINK = 2
    CYTOSCAPE = 3


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
        "capacity_hints": ABCPropertyGraphConstants.PROP_CAPACITY_HINTS,
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
        "node_map": ABCPropertyGraphConstants.PROP_NODE_MAP,
        "structural_info": ABCPropertyGraphConstants.PROP_STRUCTURAL_INFO,
        "ero": ABCPropertyGraphConstants.PROP_ERO,
        "path_info": ABCPropertyGraphConstants.PROP_PATH_INFO,
        "controller_url": ABCPropertyGraphConstants.PROP_CONTROLLER_URL
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
    def check_node_unique(self, *, label: str, name: str) -> bool:
        """
        Check no other node of this class/label and name exists. Doesn't
        apply universally as e.g. Component names are only unique
        within node, interface names are only unique within SF.
        :param label:
        :param name:
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
    def get_all_nodes_by_class_and_type(self, *, label: str, ntype: str) -> List[str]:
        """
        Get a list of nodes of the class and type
        :param label:
        :param ntype:
        :return:
        """

    def get_all_network_nodes(self) -> List[str]:

        return self.get_all_nodes_by_class(label=ABCPropertyGraphConstants.CLASS_NetworkNode)

    def get_all_network_links(self) -> List[str]:

        return self.get_all_nodes_by_class(label=ABCPropertyGraphConstants.CLASS_Link)

    def get_all_network_service_nodes(self) -> List[str]:

        return self.get_all_nodes_by_class(label=ABCPropertyGraphConstants.CLASS_NetworkService )

    @abstractmethod
    def serialize_graph(self, format: GraphFormat = GraphFormat.GRAPHML) -> str:
        """
        Serialize a given graph into a string
        :param format: indicate format (defaults to GraphML)
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
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=None,
                                              msg=f"Unable to find graph with id {self.graph_id} for cloning")
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
        :param props:
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
            if props[prop_name] is not None and len(props[prop_name]) > 0 and props[prop_name] != "None":
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
    def base_sliver_to_graph_properties_dict(sliver: BaseSliver) -> Dict[str, str]:
        """
        This method knows how to map base sliver fields to graph properties
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
        if sliver.site is not None:
            prop_dict[ABCPropertyGraph.PROP_SITE] = sliver.site
        if sliver.capacities is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITIES] = sliver.capacities.to_json()
        if sliver.capacity_hints is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITY_HINTS] = sliver.capacity_hints.to_json()
        if sliver.labels is not None:
            prop_dict[ABCPropertyGraph.PROP_LABELS] = sliver.labels.to_json()
        if sliver.capacity_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS] = \
                sliver.capacity_delegations.to_json()
        if sliver.label_delegations is not None:
            prop_dict[ABCPropertyGraph.PROP_LABEL_DELEGATIONS] = \
                sliver.label_delegations.to_json()
        if sliver.capacity_allocations is not None:
            prop_dict[ABCPropertyGraph.PROP_CAPACITY_ALLOCATIONS] = sliver.capacity_allocations.to_json()
        if sliver.label_allocations is not None:
            prop_dict[ABCPropertyGraph.PROP_LABEL_ALLOCATIONS] = sliver.label_allocations.to_json()
        if sliver.reservation_info is not None:
            prop_dict[ABCPropertyGraph.PROP_RESERVATION_INFO] = sliver.reservation_info.to_json()
        if sliver.structural_info is not None:
            prop_dict[ABCPropertyGraph.PROP_STRUCTURAL_INFO] = sliver.structural_info.to_json()
        if sliver.details is not None:
            prop_dict[ABCPropertyGraph.PROP_DETAILS] = sliver.details
        if sliver.node_map is not None:
            prop_dict[ABCPropertyGraph.PROP_NODE_MAP] = json.dumps(sliver.node_map)
        # boolean is always there. use json dumps for simplicity
        prop_dict[ABCPropertyGraph.PROP_STITCH_NODE] = json.dumps(sliver.stitch_node)

        return prop_dict

    @staticmethod
    def node_sliver_to_graph_properties_dict(sliver: NodeSliver) -> Dict[str, str]:
        """
        This method knows how to map sliver fields to graph properties
        :param sliver:
        :return:
        """
        prop_dict = ABCPropertyGraph.base_sliver_to_graph_properties_dict(sliver)

        if sliver.image_ref is not None and sliver.image_type is not None:
            prop_dict[ABCPropertyGraph.PROP_IMAGE_REF] = sliver.image_ref + ',' + str(sliver.image_type)
        if sliver.management_ip is not None:
            prop_dict[ABCPropertyGraph.PROP_MGMT_IP] = str(sliver.management_ip)
        if sliver.allocation_constraints is not None:
            prop_dict[ABCPropertyGraph.PROP_ALLOCATION_CONSTRAINTS] = sliver.allocation_constraints
        if sliver.service_endpoint is not None:
            prop_dict[ABCPropertyGraph.PROP_SERVICE_ENDPOINT] = str(sliver.service_endpoint)

        return prop_dict

    @staticmethod
    def link_sliver_to_graph_properties_dict(sliver: NetworkLinkSliver) -> Dict[str, str]:
        """
        This method knows how to map sliver fields to graph properties
        :param sliver:
        :return:
        """
        prop_dict = ABCPropertyGraph.base_sliver_to_graph_properties_dict(sliver)

        if sliver.layer is not None:
            prop_dict[ABCPropertyGraph.PROP_LAYER] = str(sliver.layer)
        if sliver.technology is not None:
            prop_dict[ABCPropertyGraph.PROP_TECHNOLOGY] = str(sliver.technology)

        return prop_dict

    @staticmethod
    def component_sliver_to_graph_properties_dict(sliver: ComponentSliver) -> Dict[str, str]:
        """
        This method knows how to map component sliver fields to graph properties
        :param sliver:
        :return:
        """
        prop_dict = ABCPropertyGraph.base_sliver_to_graph_properties_dict(sliver)

        return prop_dict

    @staticmethod
    def network_service_sliver_to_graph_properties_dict(sliver: NetworkServiceSliver) -> Dict[str, str]:
        """
        This method knows how to map network service sliver fields to graph properties
        :param sliver:
        :return:
        """
        prop_dict = ABCPropertyGraph.base_sliver_to_graph_properties_dict(sliver)
        if sliver.layer is not None:
            prop_dict[ABCPropertyGraph.PROP_LAYER] = str(sliver.layer)
        if sliver.technology is not None:
            prop_dict[ABCPropertyGraph.PROP_TECHNOLOGY] = str(sliver.technology)
        if sliver.allocation_constraints is not None:
            prop_dict[ABCPropertyGraph.PROP_ALLOCATION_CONSTRAINTS] = sliver.allocation_constraints
        if sliver.ero is not None:
            prop_dict[ABCPropertyGraph.PROP_ERO] = sliver.ero.to_json()
        if sliver.path_info is not None:
            prop_dict[ABCPropertyGraph.PROP_PATH_INFO] = sliver.path_info.to_json()
        if sliver.controller_url is not None:
            prop_dict[ABCPropertyGraph.PROP_CONTROLLER_URL] = sliver.controller_url

        return prop_dict

    @staticmethod
    def interface_sliver_to_graph_properties_dict(sliver: InterfaceSliver) -> Dict[str, str]:
        """
        This method knows how to map interface sliver fields to graph properties
        :param sliver:
        :return:
        """
        prop_dict = ABCPropertyGraph.base_sliver_to_graph_properties_dict(sliver)

        return prop_dict

    @staticmethod
    def set_base_sliver_properties_from_graph_properties_dict(sliver: BaseSliver, d: Dict[str, str]):
        """
        Sets base sliver properties on existing sliver
        :param sliver:
        :param d:
        :return:
        """
        # there is no setter for node id so users can't accidentally override it
        sliver.node_id = d.get(ABCPropertyGraph.NODE_ID, None)
        sliver.set_properties(name=d.get(ABCPropertyGraph.PROP_NAME, None),
                              type=sliver.type_from_str(d.get(ABCPropertyGraph.PROP_TYPE, None)),
                              model=d.get(ABCPropertyGraphConstants.PROP_MODEL, None),
                              site=d.get(ABCPropertyGraphConstants.PROP_SITE, None),
                              capacities=Capacities.from_json(d.get(ABCPropertyGraph.PROP_CAPACITIES, None)),
                              capacity_hints=CapacityHints.from_json(d.get(ABCPropertyGraph.PROP_CAPACITY_HINTS, None)),
                              labels=Labels.from_json(d.get(ABCPropertyGraph.PROP_LABELS, None)),
                              capacity_delegations=Delegations.from_json(atype=DelegationType.CAPACITY,
                                                                         json_str=d.get(
                                                                             ABCPropertyGraph.PROP_CAPACITY_DELEGATIONS,
                                                                             None)),
                              label_delegations=Delegations.from_json(atype=DelegationType.LABEL,
                                                                      json_str=d.get(
                                                                          ABCPropertyGraph.PROP_LABEL_DELEGATIONS,
                                                                          None)),
                              capacity_allocations=Capacities.from_json(
                                  d.get(ABCPropertyGraph.PROP_CAPACITY_ALLOCATIONS,
                                        None)),
                              label_allocations=Labels.from_json(d.get(ABCPropertyGraph.PROP_LABEL_ALLOCATIONS,
                                                                       None)),
                              structural_info=StructuralInfo.from_json(
                                  d.get(ABCPropertyGraph.PROP_STRUCTURAL_INFO, None)),
                              reservation_info=ReservationInfo.from_json(d.get(ABCPropertyGraph.PROP_RESERVATION_INFO,
                                                                               None)),
                              details=d.get(ABCPropertyGraph.PROP_DETAILS, None),
                              node_map=json.loads(d[ABCPropertyGraph.PROP_NODE_MAP]) if
                              d.get(ABCPropertyGraph.PROP_NODE_MAP, None) is not None else None,
                              stitch_node=json.loads(d[ABCPropertyGraph.PROP_STITCH_NODE]))

    @staticmethod
    def node_sliver_from_graph_properties_dict(d: Dict[str, str]) -> NodeSliver:
        n = NodeSliver()
        if d.get(ABCPropertyGraph.PROP_IMAGE_REF, None) is None:
            image_ref = None
            image_type = None
        else:
            image_ref, image_type = d[ABCPropertyGraph.PROP_IMAGE_REF].split(',')
        ABCPropertyGraph.set_base_sliver_properties_from_graph_properties_dict(n, d)
        n.set_properties(image_ref=image_ref,
                         image_type=image_type,
                         management_ip=d.get(ABCPropertyGraph.PROP_MGMT_IP, None),
                         allocation_constraints=d.get(ABCPropertyGraph.PROP_ALLOCATION_CONSTRAINTS, None),
                         service_endpoint=d.get(ABCPropertyGraph.PROP_SERVICE_ENDPOINT, None),
                         )
        return n

    @staticmethod
    def link_sliver_from_graph_properties_dict(d: Dict[str, str]) -> NetworkLinkSliver:
        n = NetworkLinkSliver()
        ABCPropertyGraph.set_base_sliver_properties_from_graph_properties_dict(n, d)
        n.set_properties(layer=d.get(ABCPropertyGraph.PROP_LAYER),
                         technology=d.get(ABCPropertyGraph.PROP_TECHNOLOGY),
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
        ABCPropertyGraph.set_base_sliver_properties_from_graph_properties_dict(cs, d)
        return cs

    @staticmethod
    def network_service_sliver_from_graph_properties_dict(d: Dict[str, str]) -> NetworkServiceSliver:
        """
        NetworkService sliver from node graph properties
        :param d:
        :return:
        """
        ns = NetworkServiceSliver()
        ABCPropertyGraph.set_base_sliver_properties_from_graph_properties_dict(ns, d)
        ns.set_properties(layer=d.get(ABCPropertyGraph.PROP_LAYER),
                          technology=d.get(ABCPropertyGraph.PROP_TECHNOLOGY),
                          allocation_constraints=d.get(ABCPropertyGraph.PROP_ALLOCATION_CONSTRAINTS, None),
                          ero=ERO.from_json(d.get(ABCPropertyGraph.PROP_ERO, None)),
                          path_info=PathInfo.from_json(d.get(ABCPropertyGraph.PROP_PATH_INFO, None)),
                          controller_url=d.get(ABCPropertyGraph.PROP_CONTROLLER_URL, None))
        return ns

    @staticmethod
    def interface_sliver_from_graph_properties_dict(d: Dict[str, str]) -> InterfaceSliver:
        """
        Interface sliver from node graph properties
        :param d:
        :return:
        """
        isl = InterfaceSliver()
        ABCPropertyGraph.set_base_sliver_properties_from_graph_properties_dict(isl, d)
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
        # find and build deep slivers of network services (if any) and components (if any)
        comps = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                        node_label=ABCPropertyGraph.CLASS_Component)
        if comps is not None and len(comps) > 0:
            aci = AttachedComponentsInfo()
            for c in comps:
                cs = self.build_deep_component_sliver(node_id=c)
                aci.add_device(cs)
            ns.attached_components_info = aci

        nss = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                      node_label=ABCPropertyGraph.CLASS_NetworkService)
        if nss is not None and len(nss) > 0:
            nsi = NetworkServiceInfo()
            for s in nss:
                nssl = self.build_deep_ns_sliver(node_id=s)
                nsi.add_network_service(nssl)
            ns.network_service_info = nsi

        return ns

    def build_deep_ns_sliver(self, *, node_id: str) -> NetworkServiceSliver:
        """
        Build a deep sliver for a NetworkService
        :param node_id:
        :return:
        """
        clazzes, props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_NetworkService not in clazzes:
            raise PropertyGraphQueryException(node_id=node_id, graph_id=self.graph_id,
                                              msg="Node is not of class NetworkService")
        # create top-level sliver
        nss = self.network_service_sliver_from_graph_properties_dict(props)
        # find interfaces and attach
        ifs = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_CONNECTS,
                                      node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
        if ifs is not None and len(ifs) > 0:
            ifi = InterfaceInfo()
            for i in ifs:
                _, iprops = self.get_node_properties(node_id=i)
                ifsl = self.interface_sliver_from_graph_properties_dict(iprops)
                ifi.add_interface(ifsl)
            nss.interface_info = ifi
        return nss

    def build_deep_component_sliver(self, *, node_id: str) -> ComponentSliver:
        clazzes, props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_Component not in clazzes:
            raise PropertyGraphQueryException(node_id=node_id, graph_id=self.graph_id,
                                              msg="Node is not of class Component")
        # create top-level sliver
        cs = self.component_sliver_from_graph_properties_dict(props)
        # find any network services, build and attach
        nss = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                      node_label=ABCPropertyGraph.CLASS_NetworkService)
        if nss is not None and len(nss) > 0:
            nsi = NetworkServiceInfo()
            for s in nss:
                nssl = self.build_deep_ns_sliver(node_id=s)
                nsi.add_network_service(nssl)
            cs.network_service_info = nsi
        return cs

    def remove_network_node_with_components_nss_cps_and_links(self, node_id: str):
        """
        Remove a network node, all of components and their interfaces, parent interfaces
        and connected links (as appropriate)
        :param node_id:
        :return:
        """
        # the network node itself
        # its components and network services
        # component network services
        # network service interfaces (if present)
        # their parent interfaces (if present)
        # the 'Link' objects connected to interfaces if only one or no other interface connects to them

        # check we are a network node
        labels, node_props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_NetworkNode not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg="This node type is not NetworkNode")
        # get a list of components
        components = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                             node_label=ABCPropertyGraph.CLASS_Component)
        for cid in components:
            self.remove_component_with_nss_cps_and_links(node_id=cid)

        # get a list of network services, delete the node
        network_services = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                                   node_label=ABCPropertyGraph.CLASS_NetworkService)
        self.delete_node(node_id=node_id)
        for cid in network_services:
            self.remove_ns_with_cps_and_links(node_id=cid)

    def remove_component_with_nss_cps_and_links(self, node_id: str):
        """
        Remove a component of a network node with all attached elements (network services
        and interfaces). Parent interfaces and links are removed if they have no other
        children or connected interfaces.
        :param node_id: component node id
        :return:
        """
        # check we are a component
        labels, node_props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_Component not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg="This node type is not Component")
        # get a list of NetworkServices, delete the node
        network_services = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_HAS,
                                                   node_label=ABCPropertyGraph.CLASS_NetworkService)
        self.delete_node(node_id=node_id)
        for ns in network_services:
            self.remove_ns_with_cps_and_links(node_id=ns)

    def remove_network_link(self, node_id: str):

        # check we are a link
        labels, node_props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_Link not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg="This node type is not Link")
        # edges to interfaces/connection points will disappear
        self.delete_node(node_id=node_id)

    def remove_ns_with_cps_and_links(self, node_id: str):
        """
        Remove network service with subtending interfaces and links
        :param node_id:
        :return:
        """
        # check we are a network service
        labels, node_props = self.get_node_properties(node_id=node_id)
        if ABCPropertyGraph.CLASS_NetworkService not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=node_id,
                                              msg="This node type is not NetworkService")
        # get a list of interfaces, delete the network service
        interfaces = self.get_first_neighbor(node_id=node_id, rel=ABCPropertyGraph.REL_CONNECTS,
                                             node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
        self.delete_node(node_id=node_id)
        for iif in interfaces:
            self.remove_cp_and_links(node_id=iif)

    def remove_cp_and_links(self, node_id: str):
        """
        Remove ConnectionPoint and links. Parent ConnectionPoints and links are removed
        if they have no other children or other connected connection points.
        :param node_id: interface node id
        :return:
        """
        # some interfaces may have parent interfaces, which can be deleted if they only have the
        # one child
        interfaces_to_delete = {node_id}
        parents = self.get_first_neighbor(node_id=node_id,
                                          rel=ABCPropertyGraph.REL_CONNECTS,
                                          node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
        for parent in parents:  # really should only be one parent interface
            children = self.get_first_neighbor(node_id=parent,
                                               rel=ABCPropertyGraph.REL_CONNECTS,
                                               node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
            if len(children) == 1:  # if only child, can delete parent
                interfaces_to_delete.add(parent)
        # interfaces themselves and parent interfaces
        # may be connected to links which can be deleted if nothing
        # else connects to them
        links_to_delete = set()
        for interface in interfaces_to_delete:
            links = self.get_first_neighbor(node_id=interface,
                                            rel=ABCPropertyGraph.REL_CONNECTS,
                                            node_label=ABCPropertyGraph.CLASS_Link)
            for link in links:  # should only be one
                connected_interfaces = self.get_first_neighbor(node_id=link,
                                                               rel=ABCPropertyGraph.REL_CONNECTS,
                                                               node_label=ABCPropertyGraph.CLASS_ConnectionPoint)
                if len(connected_interfaces) == 2:  # connected to us and another thing, can delete
                    links_to_delete.add(link)
        # delete nodes in these sets
        for deleted_id in interfaces_to_delete.union(links_to_delete):
            self.delete_node(node_id=deleted_id)

    def add_network_node_sliver(self, *, sliver: NodeSliver):

        assert sliver is not None
        assert sliver.node_id is not None

        if not self.check_node_unique(label=ABCPropertyGraph.CLASS_NetworkNode,
                                      name=sliver.resource_name):
            raise RuntimeError(f'Node name {sliver.resource_name} must be unique.')

        props = self.node_sliver_to_graph_properties_dict(sliver)
        self.add_node(node_id=sliver.node_id, label=ABCPropertyGraph.CLASS_NetworkNode, props=props)
        # if components aren't empty, add components, their network services and interfaces
        aci = sliver.attached_components_info
        if aci is not None:
            for csliver in aci.devices.values():
                self.add_component_sliver(parent_node_id=sliver.node_id,
                                          component=csliver)
        # if network services arent empty add them with their interfaces
        nsi = sliver.network_service_info
        if nsi is not None:
            for ns in nsi.network_services.values():
                self.add_network_service_sliver(parent_node_id=sliver.node_id,
                                                network_service=ns)

    def add_network_link_sliver(self, *, lsliver: NetworkLinkSliver, interfaces: List[str]):

        assert lsliver is not None
        assert lsliver.node_id is not None
        assert interfaces is not None

        props = self.link_sliver_to_graph_properties_dict(lsliver)
        self.add_node(node_id=lsliver.node_id, label=ABCPropertyGraph.CLASS_Link, props=props)
        # add edge links to specified interfaces
        for i in interfaces:
            self.add_link(node_a=lsliver.node_id, rel=ABCPropertyGraph.REL_CONNECTS, node_b=i)

    def add_component_sliver(self, *, parent_node_id: str, component: ComponentSliver):
        """
        Add network node component as a sliver, linking back to parent
        :param parent_node_id:
        :param component:
        :return:
        """
        assert component.node_id is not None
        assert parent_node_id is not None

        props = self.component_sliver_to_graph_properties_dict(component)
        self.add_node(node_id=component.node_id, label=ABCPropertyGraph.CLASS_Component, props=props)
        self.add_link(node_a=parent_node_id, rel=ABCPropertyGraph.REL_HAS, node_b=component.node_id)
        nsi = component.network_service_info
        if nsi is not None:
            for ns in nsi.network_services.values():
                self.add_network_service_sliver(parent_node_id=component.node_id,
                                                network_service=ns)

    def add_network_service_sliver(self, *, parent_node_id: str, network_service: NetworkServiceSliver):
        """
        Add network service as a sliver to either node or component, linking back to parent (if there is one).
        :param parent_node_id: can be None
        :param network_service:
        :return:
        """
        assert network_service.node_id is not None
        if parent_node_id is None and not self.check_node_unique(label=ABCPropertyGraph.CLASS_NetworkService,
                                                                 name=network_service.resource_name):
            # slice-wide network services must have unique names
            raise RuntimeError(f'Network service name {network_service.resource_name} must be unique.')

        props = self.network_service_sliver_to_graph_properties_dict(network_service)
        self.add_node(node_id=network_service.node_id, label=ABCPropertyGraph.CLASS_NetworkService, props=props)
        if parent_node_id is not None:
            self.add_link(node_a=parent_node_id, rel=ABCPropertyGraph.REL_HAS, node_b=network_service.node_id)
        ii = network_service.interface_info
        if ii is not None:
            for i in ii.interfaces.values():
                self.add_interface_sliver(parent_node_id=network_service.node_id,
                                          interface=i)

    def add_interface_sliver(self, *, parent_node_id: str, interface: InterfaceSliver):
        """
        Add interface to a network service, linking back to parent.
        :param parent_node_id: network service id
        :param interface: interface sliver description
        :return:
        """
        assert interface.node_id is not None
        assert parent_node_id is not None

        props = self.interface_sliver_to_graph_properties_dict(interface)
        self.add_node(node_id=interface.node_id, label=ABCPropertyGraph.CLASS_ConnectionPoint, props=props)
        self.add_link(node_a=parent_node_id, rel=ABCPropertyGraph.REL_CONNECTS, node_b=interface.node_id)

    def get_all_ns_or_link_connection_points(self, link_id: str) -> List[str]:
        """
        Get interfaces attached to a link or network service
        :param link_id:
        :return:
        """
        assert link_id is not None
        # check this is a link
        labels, parent_props = self.get_node_properties(node_id=link_id)
        if ABCPropertyGraph.CLASS_Link not in labels and ABCPropertyGraph.CLASS_NetworkService not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=link_id,
                                              msg="Node type is not Link or a NetworkService")
        return self.get_first_neighbor(node_id=link_id, rel=ABCPropertyGraph.REL_CONNECTS,
                                       node_label=ABCPropertyGraph.CLASS_ConnectionPoint)

    def get_all_node_or_component_connection_points(self, parent_node_id: str) -> List[str]:
        """
        Get a list of interfaces attached via network services
        :param parent_node_id:
        :return:
        """
        assert parent_node_id is not None
        labels, parent_props = self.get_node_properties(node_id=parent_node_id)
        if ABCPropertyGraph.CLASS_NetworkNode not in labels and \
                ABCPropertyGraph.CLASS_Component not in labels:
            raise PropertyGraphQueryException(graph_id=self.graph_id, node_id=parent_node_id,
                                              msg="Parent node type is not NetworkNode or Component")
        nss_ifs = self.get_first_and_second_neighbor(node_id=parent_node_id, rel1=ABCPropertyGraph.REL_HAS,
                                                     node1_label=ABCPropertyGraph.CLASS_NetworkService,
                                                     rel2=ABCPropertyGraph.REL_CONNECTS,
                                                     node2_label=ABCPropertyGraph.CLASS_ConnectionPoint)
        ret = list()
        # return only interface IDs, not interested in NetworkServices
        for tup in nss_ifs:
            ret.append(tup[1])
        return ret

    def get_parent(self, node_id: str, rel: str, parent: str) -> Tuple[str, str]:
        """
        Return name and node_id properties of a parent node (connected via 'has' relationship).
        NetworkNodes and Links have no parents, Components have NetworkNodes, NetworkServices have
        Components or NetworkNodes or None, ConnectionPoints have NetworkServices
        :param node_id:
        :param rel: relationship with parent
        :param parent: parent class
        :return:
        """
        assert node_id is not None
        assert rel is not None
        assert parent is not None
        parent_ids = self.get_first_neighbor(node_id=node_id, rel=rel,
                                             node_label=parent)
        if len(parent_ids) != 1:
            return None, None
        _, props = self.get_node_properties(node_id=parent_ids[0])
        return props[ABCPropertyGraph.PROP_NAME], parent_ids[0]

    @abstractmethod
    def get_stitch_nodes(self) -> List[str]:
        """
        Find out and return a list of nodes with StitchNode property
        set to 'true' (in JSON).
        :return:
        """


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
