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
This collection of classes helps collect authorization attributes about various resources
"""

from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import json

from fim.user.topology import ExperimentTopology
from fim.user.node import Node, NodeType
from fim.user.network_service import NetworkService, ServiceType
from fim.graph.slices.networkx_asm import NetworkxASM
from fim.slivers.base_sliver import BaseSliver
from fim.slivers.network_node import NodeSliver
from fim.slivers.network_service import NetworkServiceSliver
from fim.view_only_dict import ViewOnlyDict


class ResourceAuthZAttributes:

    # standard resource attributes we are able to send to PDP
    RESOURCE_TYPE = "urn:fabric:xacml:attributes:resource-type"
    RESOURCE_CPU = "urn:fabric:xacml:attributes:resource-cpu"
    RESOURCE_RAM = "urn:fabric:xacml:attributes:resource-ram"
    RESOURCE_DISK = "urn:fabric:xacml:attributes:resource-disk"
    RESOURCE_BW = "urn:fabric:xacml:attribute:resource-bw"
    RESOURCE_SITE = "urn:fabric:xacml:attribute:resource-site"
    RESOURCE_COMPONENT = "urn:fabric:xacml:attribute:resource-component"
    RESOURCE_FABNETV4_EXT = "urn:fabric:xacml:attribute:resource-fabnetv4-ext-site"
    RESOURCE_FABNETV6_EXT = "urn:fabric:xacml:attribute:resource-fabnetv6-ext-site"
    RESOURCE_MIRROR_SITE = "urn:fabric:xacml:attribute:resource-mirrorsite"
    RESOURCE_FACILITY_PORT = "urn:fabric:xacml:attribute:resource-facility-port"
    RESOURCE_MEASUREMENTS = "urn:fabric:xacml:attribute:resource-with-measurements"
    RESOURCE_LIFETIME = "urn:fabric:xacml:attributes:resource-lifetime"
    RESOURCE_PROJECT = "urn:fabric:xacml:attributes:resource-project"
    RESOURCE_SUBJECT = "urn:fabric:xacml:attributes:resource-subject"
    ACTION_ID = "urn:oasis:names:tc:xacml:1.0:action:action-id"
    SUBJECT_ID = "urn:oasis:names:tc:xacml:1.0:subject:subject-id"
    SUBJECT_PROJECT = "urn:fabric:xacml:attributes:subject-project"
    PROJECT_TAG = "urn:fabric:xacml:attributes:project-tag"

    ATTRIBUTE_TYPES_AND_CATEGORIES = {
        RESOURCE_TYPE: ("http://www.w3.org/2001/XMLSchema#string",
                        "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_CPU: ("http://www.w3.org/2001/XMLSchema#integer",
                       "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_RAM: ("http://www.w3.org/2001/XMLSchema#integer",
                       "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_DISK: ("http://www.w3.org/2001/XMLSchema#integer",
                        "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_BW: ("http://www.w3.org/2001/XMLSchema#integer",
                      "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_SITE: ("http://www.w3.org/2001/XMLSchema#string",
                        "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_COMPONENT: ("http://www.w3.org/2001/XMLSchema#string",
                             "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_FABNETV4_EXT: ("http://www.w3.org/2001/XMLSchema#string",
                             "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_FABNETV6_EXT: ("http://www.w3.org/2001/XMLSchema#string",
                                "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_MIRROR_SITE: ("http://www.w3.org/2001/XMLSchema#string",
                               "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_FACILITY_PORT: ("http://www.w3.org/2001/XMLSchema#string",
                                 "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_MEASUREMENTS: ("http://www.w3.org/2001/XMLSchema#boolean",
                                "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_PROJECT: ("http://www.w3.org/2001/XMLSchema#string",
                           "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        RESOURCE_SUBJECT: ("http://www.w3.org/2001/XMLSchema#string",
                           "urn:oasis:names:tc:xacml:3.0:attribute-category:resource"),
        ACTION_ID: ("http://www.w3.org/2001/XMLSchema#string",
                    "urn:oasis:names:tc:xacml:3.0:attribute-category:action"),
        RESOURCE_LIFETIME: ("http://www.w3.org/2001/XMLSchema#dayTimeDuration",
                            "urn:oasis:names:tc:xacml:3.0:attribute-category:action"),
        SUBJECT_ID: ("http://www.w3.org/2001/XMLSchema#string",
                     "urn:oasis:names:tc:xacml:1.0:subject-category:access-subject"),
        SUBJECT_PROJECT: ("http://www.w3.org/2001/XMLSchema#string",
                          "urn:oasis:names:tc:xacml:1.0:subject-category:access-subject"),
        PROJECT_TAG: ("http://www.w3.org/2001/XMLSchema#string",
                      "urn:oasis:names:tc:xacml:1.0:subject-category:access-subject")
    }

    METHOD_LUT = {
        ExperimentTopology: "topo",
        Node: "node",
        NetworkService: "ns",
        NetworkxASM: "asm",
        NodeSliver: "node_sliver",
        NetworkServiceSliver: "ns_sliver",
        BaseSliver: "base_sliver"
    }

    NSTYPE_LUT = {
        ServiceType.PortMirror: "urn:fabric:xacml:attribute:resource-mirrorsite",
        ServiceType.FABNetv4Ext: "urn:fabric:xacml:attribute:resource-fabnetv4-ext-site",
        ServiceType.FABNetv6Ext: "urn:fabric:xacml:attribute:resource-fabnetv6-ext-site"
    }

    def __init__(self):
        # using list because sets arent jsonifiable
        self._attributes = defaultdict(list)
        # for now resource type is always sliver
        self._attributes[self.RESOURCE_TYPE] = ["sliver"]

    @property
    def attributes(self):
        return ViewOnlyDict(self._attributes)

    def _collect_attributes_from_node_sliver(self, sliver: NodeSliver):
        if sliver.get_type() == NodeType.Switch:
            self._attributes[self.RESOURCE_TYPE] = ["switch-p4"]
        if sliver.capacities:
            self._attributes[self.RESOURCE_CPU].append(sliver.capacities.core)
            self._attributes[self.RESOURCE_RAM].append(sliver.capacities.ram)
            self._attributes[self.RESOURCE_DISK].append(sliver.capacities.disk)
        if sliver.site:
            if sliver.site not in self._attributes[self.RESOURCE_SITE]:
                self._attributes[self.RESOURCE_SITE].append(sliver.site)
        if sliver.attached_components_info:
            for c in sliver.attached_components_info.list_devices():
                self._attributes[self.RESOURCE_COMPONENT].append(str(c.get_type()))

    def _collect_attributes_from_ns_sliver(self, sliver: NetworkServiceSliver):
        if sliver.capacities:
            self._attributes[self.RESOURCE_BW].append(sliver.capacities.bw)
        if sliver.site:
            if sliver.site not in self._attributes[self.RESOURCE_SITE]:
                self._attributes[self.RESOURCE_SITE].append(sliver.site)
        if sliver.resource_type in {ServiceType.PortMirror, ServiceType.FABNetv4Ext, ServiceType.FABNetv6Ext}:
            # we list sites using each type of service separately
            resource_name = self.NSTYPE_LUT[sliver.resource_type]
            # site must be set (typically set by Topology.validate())
            if not sliver.site:
                sliver.site = "UNKNOWN-SITE"
            if sliver.site not in self._attributes[resource_name]:
                self._attributes[resource_name].append(sliver.site)

    def _collect_attributes_from_base_sliver(self, sliver: BaseSliver):
        if isinstance(sliver, NetworkServiceSliver):
            self._collect_attributes_from_ns_sliver(sliver)
        elif isinstance(sliver, NodeSliver):
            self._collect_attributes_from_node_sliver(sliver)

    def _collect_attributes_from_topo(self, topo: ExperimentTopology):
        for n in topo.nodes.values():
            self._collect_attributes_from_node(n)
        for ns in topo.network_services.values():
            self._collect_attributes_from_ns(ns)
        for fac in topo.facilities.values():
            self._attributes[self.RESOURCE_FACILITY_PORT].append(fac.name)

    def _collect_attributes_from_node(self, node: Node):
        self._collect_attributes_from_node_sliver(node.get_sliver())

    def _collect_attributes_from_ns(self, ns: NetworkService):
        self._collect_attributes_from_ns_sliver(ns.get_sliver())

    def _collect_attributes_from_asm(self, asm: NetworkxASM):
        # convert to experiment topology
        asm.validate_graph()
        t = ExperimentTopology(graph_string=asm.serialize_graph())
        t.validate()
        self._collect_attributes_from_topo(t)

    def collect_resource_attributes(self, *, source: ExperimentTopology or
                                    NetworkxASM or
                                    BaseSliver or NodeSliver or
                                    NetworkServiceSliver or Node or
                                    NetworkService or None):
        """
        Take an ExperimentTopology or an ASM graph or a Sliver or a member of topology
        and extract all relevant authorization attributes, storing them
        as a Dict suitable for converting into an AuthZ request to a PDP.
        :param source: a source of attributes (ExperimentTopology, ASM or Sliver)
        :return: dictionary
        """
        assert source

        method_suffix = ResourceAuthZAttributes.METHOD_LUT.get(source.__class__)

        if not method_suffix:
            raise AuthZResourceAttributeException(f'Unsupported resource type {source.__class__} '
                                                  f'for collecting attributes')
        self.__getattribute__('_collect_attributes_from_' + method_suffix)(source)

    def set_lifetime(self, end_time: datetime):
        """
        Convert endtime of a slice to XML dayTimeDuration and set in dictionary.
        Uses utcnow to compute timedelta first.
        See http://www.datypic.com/sc/xsd/t-xsd_dayTimeDuration.html for format details
        """
        # convert to dayTimeDuration
        td = end_time - datetime.now(timezone.utc)
        days, hours, minutes, seconds = self.fromtimedelta(td)
        self._attributes[self.RESOURCE_LIFETIME].append(f'P{days}DT{hours}H{minutes}M{seconds}S')

    def set_resource_subject_and_project(self, *, subject_id: List[str] or str, project: List[str] or str):
        """
        Set resource subject (who created it) and resource project (which project it was created in
        :param subject_id: string or list of strings
        :param project: string or list of strings
        """
        if subject_id:
            if isinstance(subject_id, list):
                self._attributes[self.RESOURCE_SUBJECT].extend(subject_id)
            else:
                self._attributes[self.RESOURCE_SUBJECT].append(subject_id)

        if project:
            if isinstance(project, list):
                self._attributes[self.RESOURCE_PROJECT].extend(project)
            else:
                self._attributes[self.RESOURCE_PROJECT].append(project)

    def set_action(self, action: str):
        """
        Set the action attribute of the request
        :param action: string
        """
        if action:
            self._attributes[self.ACTION_ID].append(action)

    def set_subject_attributes(self, *, subject_id: str or None, project: str or List[str] or None,
                               project_tag: str or List[str] or None):
        """
        Set subject attributes.
        :param subject_id: string
        :param project: string or list of strings
        :param project_tag: string or list of strings
        """
        if subject_id:
            self._attributes[self.SUBJECT_ID].append(subject_id)

        if project:
            if isinstance(project, list):
                self._attributes[self.SUBJECT_PROJECT].extend(project)
            else:
                self._attributes[self.SUBJECT_PROJECT].append(project)

        if project_tag:
            if isinstance(project_tag, list):
                self._attributes[self.PROJECT_TAG].extend(project_tag)
            else:
                self._attributes[self.PROJECT_TAG].append(project_tag)

    __SECONDS_IN_DAY = 24 * 60 * 60
    __SECONDS_IN_HOUR = 60 * 60
    __SECONDS_IN_MINUTE = 60

    @staticmethod
    def fromtimedelta(td: timedelta):
        """
        Convert time delta to a tuple of days, hours, minutes and seconds
        """
        assert td.total_seconds() > 0

        ts = int(td.total_seconds())
        days = td.days
        seconds = ts - days * ResourceAuthZAttributes.__SECONDS_IN_DAY
        hours = seconds // ResourceAuthZAttributes.__SECONDS_IN_HOUR
        seconds %= ResourceAuthZAttributes.__SECONDS_IN_HOUR
        minutes = seconds // ResourceAuthZAttributes.__SECONDS_IN_MINUTE
        seconds %= ResourceAuthZAttributes.__SECONDS_IN_MINUTE
        return days, hours, minutes, seconds

    def transform_to_pdp_request(self, *, as_json: bool = True,
                                 return_policy_id_list: bool = False,
                                 combined_decision: bool = False) -> Dict[str, Any] or str:
        """
        Transform the collected attributes into a proper PDP request.
        Depending on as_json parameter returns a JSON string or a complex dict
        :param as_json: bool (default True)
        :param return_policy_id_list: bool (default False)
        :param combined_decision: bool (default False)
        """
        ret = {"Request": {
                "ReturnPolicyIdList": return_policy_id_list,
                "CombinedDecision": combined_decision,
                "Category": [
                    { "CategoryId": "urn:oasis:names:tc:xacml:3.0:attribute-category:resource",
                      "Attribute": []},
                    { "CategoryId": "urn:oasis:names:tc:xacml:3.0:attribute-category:action",
                      "Attribute": []},
                    { "CategoryId": "urn:oasis:names:tc:xacml:1.0:subject-category:access-subject",
                      "Attribute": []}
                ]}}

        cat_list = ret["Request"]["Category"]
        for k, v in self._attributes.items():
            attribute_dict = {"IncludeInResult": False, "Value": v, "AttributeId": k,
                              "DataType": self.ATTRIBUTE_TYPES_AND_CATEGORIES[k][0]}
            cat_id = self.ATTRIBUTE_TYPES_AND_CATEGORIES[k][1]
            for atcat in cat_list:
                if atcat["CategoryId"] == cat_id:
                    atcat["Attribute"].append(attribute_dict)

        if as_json:
            return json.dumps(ret)
        else:
            return ret

    def __str__(self):
        return str(self.attributes)


class AuthZResourceAttributeException(Exception):

    def __init__(self, msg: str):
        super().__init__(f"AuthZResourceAttributeException: {msg}")