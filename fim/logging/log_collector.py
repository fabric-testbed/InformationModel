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

from fim.user.topology import ExperimentTopology
from fim.user.node import Node
from fim.user.network_service import NetworkService, ServiceType
from fim.user.component import Component
from fim.graph.slices.networkx_asm import NetworkxASM
from fim.slivers.topology_diff import TopologyDiff
from fim.slivers.network_service import NetworkServiceSliver
from fim.slivers.network_node import NodeSliver, NodeType
from fim.slivers.base_sliver import BaseSliver
from fim.slivers.attached_components import ComponentSliver
from fim.view_only_dict import ViewOnlyDict


class LogCollector:
    """
    This class collects information for use in logging facility use. It can collect information
    from ExperimentTopology object, ASMs and TopologyDiffs. The dictionary returned by attributes
    property has the following structure:
    'nodes': list of VM Capacity objects
    'core_count': total cores
    'vm_count': total VMs
    'p4_count': total P4 switches
    'components': dictionary of ComponentType:quantity
    'services': list of tuples (ServiceType, bw)
    'facilities': set of facility port names (unique)
    'sites': set of site names (unique)
    """
    METHOD_LUT = {
        ExperimentTopology: "topo",
        NetworkxASM: "asm",
        TopologyDiff: "topology_diff",
        NodeSliver: "node_sliver",
        NetworkServiceSliver: "ns_sliver",
        ComponentSliver: "component_sliver",
        BaseSliver: "base_sliver",
        Node: "node",
        NetworkService: "ns",
        Component: "component"
    }

    def __init__(self):
        self._attributes = dict()
        self._attributes['nodes'] = list()
        self._attributes['core_count'] = 0
        self._attributes['vm_count'] = 0
        self._attributes['p4_count'] = 0
        self._attributes['components'] = dict()
        self._attributes['services'] = list()
        self._attributes['facilities'] = set()
        self._attributes['sites'] = set()

    @property
    def attributes(self):
        return ViewOnlyDict(self._attributes)

    def _collect_attributes_from_component_sliver(self, comp: ComponentSliver):
        cnt = self._attributes['components'].get(str(comp.resource_type), 0)
        self._attributes['components'][str(comp.resource_type)] = cnt + 1

    def _collect_attributes_from_node_sliver(self, sliver: NodeSliver):

        if sliver.resource_type == NodeType.VM:
            self._attributes['vm_count'] += 1
            cap = None
            if sliver.capacity_allocations:
                cap = sliver.capacity_allocations
            elif sliver.capacities:
                cap = sliver.capacities
            if cap:
                self._attributes['core_count'] += cap.core
                self._attributes['nodes'].append(cap)
        elif sliver.resource_type == NodeType.Switch:
            self._attributes['p4_count'] += 1
        elif sliver.resource_type == NodeType.Facility:
            self._attributes['facilities'].add(sliver.get_name())
        if sliver.site:
            self._attributes['sites'].add(sliver.site)
        if sliver.attached_components_info:
            for c in sliver.attached_components_info.list_devices():
                self._collect_attributes_from_component_sliver(c)

    def _collect_attributes_from_ns_sliver(self, sliver: NetworkServiceSliver):
        bw = sliver.capacities.bw if sliver.capacities else 0
        service_tup = (str(sliver.resource_type), bw)
        self._attributes['services'].append(service_tup)
        if sliver.site:
            self._attributes['sites'].add(sliver.site)

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
            self._attributes['facilities'].add(fac.name)

    def _collect_attributes_from_component(self, comp: Component):
        self._collect_attributes_from_component_sliver(comp.get_sliver())

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

    def _collect_attributes_from_topology_diff(self, diff: TopologyDiff):
        """
        Use topology diff and only look at 'added' elements
        """
        for n in diff.added.nodes:
            self._collect_attributes_from_node(n)
        for ns in diff.added.services:
            self._collect_attributes_from_ns(ns)
        for c in diff.added.components:
            self._collect_attributes_from_component(c)

    def collect_resource_attributes(self, *, source: ExperimentTopology or
                                    NetworkxASM or
                                    TopologyDiff or
                                    NetworkService or Node or Component or
                                    NetworkServiceSliver or NodeSliver or ComponentSliver or None):
        """
        Take an ExperimentTopology or an ASM graph or TopologyDiff
        and extract all relevant attributes needed for logging, storing them
        as a Dict
        :param source: a source of attributes (ExperimentTopology, ASM or TopologyDiff)
        :return: dictionary
        """
        assert source

        method_suffix = LogCollector.METHOD_LUT.get(source.__class__)

        if not method_suffix:
            raise LogCollectorException(f'Unsupported resource type {source.__class__} '
                                        f'for collecting attributes')
        self.__getattribute__('_collect_attributes_from_' + method_suffix)(source)

    def __str__(self):
        """
        produce everything that goes after 'with' in a logging message
        """
        comp = ' compute ' + ','.join(['vms:' + str(self._attributes['vm_count']),
                                       'cores:' + str(self._attributes['core_count']),
                                       'p4s:' + str(self._attributes['p4_count'])])
        sites = facilities = components = services = vmdetails = ''

        if len(self._attributes['sites']):
            sites = ' sites ' + ','.join(self._attributes['sites'])

        if len(self._attributes['facilities']):
            facilities = ' facilities ' + ','.join(self._attributes['facilities'])

        if len(self._attributes['components']) > 0:
            cdict = self._attributes['components']
            clist = [k + ':' + str(v) for k, v in cdict.items()]
            components = ' components ' + ','.join(clist)

        if len(self._attributes['services']) > 0:
            slist = [t[0] + ':' + str(t[1]) for t in filter(lambda n: n[0] != 'OVS', self._attributes['services'])]
            services = ' services ' + ','.join(slist)

        # aggregate VM capacity information
        if len(self._attributes['nodes']) > 0:
            vmdict = defaultdict(int)
            for cap in self._attributes['nodes']:
                # these are capacity_allocation or capacity objects (if capacity_allocation is set it is preferred)
                vmdict[f'C{cap.core}/R{cap.ram}/D{cap.disk}'] += 1
            vmdetails = ' vmdetails ' + ','.join([i[0] + ':' + str(i[1]) for i in vmdict.items()])

        return ';'.join(filter(lambda n: len(n) > 0, [comp, sites, facilities, components, services, vmdetails]))

    def __repr__(self):
        return str(self.attributes)


class LogCollectorException(Exception):

    def __init__(self, msg: str):
        super().__init__(f"LogCollectorException: {msg}")