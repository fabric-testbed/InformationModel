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

from fim.user.topology import ExperimentTopology
from fim.user.node import Node
from fim.user.network_service import NetworkService
from fim.graph.slices.abc_asm import ABCASMPropertyGraph
from fim.slivers.base_sliver import BaseSliver
from fim.slivers.network_node import NodeSliver
from fim.slivers.network_service import NetworkServiceSliver
from fim.view_only_dict import ViewOnlyDict


class ResourceAuthZAttributes:

    # standard resource attributes we are able to send to PDP
    RESOURCE_TYPE = "urn:fabric:xacml:attributes:resource-type"
    RESOURCE_CPUS = "urn:fabric:xacml:attributes:resource-cpu"
    RESOURCE_RAM = "urn:fabric:xacml:attributes:resource-ram"
    RESOURCE_DISK = "urn:fabric:xacml:attributes:resource-disk"
    RESOURCE_BW = "urn:fabric:xacml:attribute:resource-bw"
    RESOURCE_SITE = "urn:fabric:xacml:attribute:resource-site"
    RESOURCE_COMPONENT = "urn:fabric:xacml:attribute:resource-component"
    RESOURCE_PEER_SITE = "urn:fabric:xacml:attribute:resource-peersite"
    RESOURCE_FACILITY_PORT = "urn:fabric:xacml:attribute:resource-facility-port"
    RESOURCE_MEASUREMENTS = "urn:fabric:xacml:attribute:resource-with-measurements"
    RESOURCE_LIFETIME = "urn:fabric:xacml:attributes:resource-lifetime"

    METHOD_LUT = {
        ExperimentTopology: "topo",
        Node: "node",
        NetworkService: "ns",
        ABCASMPropertyGraph: "asm",
        NodeSliver: "node_sliver",
        NetworkServiceSliver: "ns_sliver",
        BaseSliver: "base_sliver"
    }

    def __init__(self):
        self._attributes = defaultdict(list)

    @property
    def attributes(self):
        return ViewOnlyDict(self._attributes)

    def _collect_attributes_from_node_sliver(self, sliver: NodeSliver):
        if sliver.capacities:
            self._attributes[self.RESOURCE_CPUS].append(sliver.capacities.core)
            self._attributes[self.RESOURCE_RAM].append(sliver.capacities.ram)
            self._attributes[self.RESOURCE_DISK].append(sliver.capacities.disk)
        if sliver.site:
            self._attributes[self.RESOURCE_SITE].append(sliver.site)
        if sliver.attached_components_info:
            for c in sliver.attached_components_info.list_devices():
                self._attributes[self.RESOURCE_COMPONENT].append(str(c.get_type()))

    def _collect_attributes_from_ns_sliver(self, sliver: NetworkServiceSliver):
        if sliver.capacities:
            self._attributes[self.RESOURCE_BW].append(sliver.capacities.bw)
        if sliver.site:
            self._attributes[self.RESOURCE_SITE].append(sliver.site)

    def _collect_attributes_from_base_sliver(self, sliver: BaseSliver):
        if isinstance(sliver, NetworkServiceSliver):
            self._collect_attributes_from_ns_sliver(sliver)
        elif isinstance(sliver, NodeSliver):
            self._collect_attributes_from_node_sliver(sliver)

    def _collect_attributes_from_topo(self, topo: ExperimentTopology):
        # reset the dictionary (only here, other calls are additive)
        self._attributes = defaultdict(list)

        for n in topo.nodes.values():
            self._collect_attributes_from_node(n)
        for ns in topo.network_services.values():
            self._collect_attributes_from_ns(ns)
        for fac in topo.facilities.values():
            self._attributes[self.RESOURCE_FACILITY_PORT] = fac.name

    def _collect_attributes_from_node(self, node: Node):
        self._collect_attributes_from_node_sliver(node.get_sliver())

    def _collect_attributes_from_ns(self, ns: NetworkService):
        self._collect_attributes_from_ns_sliver(ns.get_sliver())

    def _collect_attributes_from_asm(self, asm: ABCASMPropertyGraph):
        # reset the dictionary (only here, other calls are additive)
        self._attributes = defaultdict(list)
        raise RuntimeError('Not implemented')

    def collect_attributes(self, *, source: ExperimentTopology or
                           ABCASMPropertyGraph or
                           BaseSliver or NodeSliver or
                           NetworkServiceSliver or Node or
                           NetworkService or None):
        """
        Take an ExperimentTopology or an ASM graph or a Sliver or a member of topology
        and extract all relevant authorization attributes, storing them as a Dict suitable for
        converting into an AuthZ request to a PDP.
        :param source: a source of attributes (ExperimentTopology, ASM or Sliver)
        :return: dictionary
        """
        assert source

        method_suffix = ResourceAuthZAttributes.METHOD_LUT.get(source.__class__)

        if not method_suffix:
            raise AuthZResourceAttributeException(f'Unsupported resource type {source.__class__} '
                                                  f'for collecting attributes')
        self.__getattribute__('_collect_attributes_from_' + method_suffix)(source)
        # for now resource type is always sliver
        self._attributes[self.RESOURCE_TYPE] = ["sliver"]

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

    def __str__(self):
        return str(self.attributes)


class AuthZResourceAttributeException(Exception):

    def __init__(self, msg: str):
        super().__init__(f"AuthZResourceAttributeException: {msg}")