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

from collections import defaultdict

import uuid

from fim.graph.abc_property_graph import ABCPropertyGraph
from fim.graph.resources.abc_cbm import ABCCBMPropertyGraph
from fim.graph.resources.abc_bqm import ABCBQMPropertyGraph
from fim.graph.networkx_property_graph import NetworkXGraphImporter
from .networkx_abqm import NetworkXAggregateBQM
from fim.slivers.capacities_labels import Capacities
from fim.slivers.network_node import CompositeNodeSliver
from fim.slivers.attached_components import ComponentSliver


class AggregateBQMPlugin:
    """
    Implement a plugin for simple aggregation of CBM into BQM, transforming site
    topologies into CompositeNodes and linking them with (Composite)Links
    This is based on fim.pluggable BrokerPluggable
    """

    def __init__(self, logger=None):
        self.log = logger

    def plug_produce_bqm(self, *, cbm: ABCCBMPropertyGraph, **kwargs) -> ABCBQMPropertyGraph:
        """
        Take a CBM, sort nodes by site, aggregate servers, components and interfaces to
        create a site-based advertisement. Use a NetworkX-based implementation.
        :param cbm:
        :param kwargs:
        :return:
        """

        # do a one-pass aggregation of servers, their components and interfaces
        nnodes = cbm.get_all_nodes_by_class(label=ABCPropertyGraph.CLASS_NetworkNode)
        slivers_by_site = defaultdict(list)
        for n in nnodes:
            # build deep slivers, aggregate by site
            node_sliver = cbm.build_deep_node_sliver(node_id=n)
            slivers_by_site[node_sliver.site].append(node_sliver)

        # create a new blank Aggregated BQM NetworkX graph
        abqm = NetworkXAggregateBQM(graph_id=str(uuid.uuid4()),
                                    importer=NetworkXGraphImporter(logger=self.log),
                                    logger=self.log)
        for s, ls in slivers_by_site.items():

            # add up capacities and delegated capacities, skip labels for now
            # count up components and figure out links between sites
            site_sliver = CompositeNodeSliver()
            site_sliver.capacities = Capacities()
            site_sliver.resource_name = s
            # FIXME need a resource type too
            site_comps_by_type = defaultdict(dict)
            for sliver in ls:
                site_sliver.capacities = site_sliver.capacities + sliver.capacities
                # collect components in lists by type and model for the site
                if sliver.attached_components_info is None:
                    continue
                for comp in sliver.attached_components_info.list_devices():
                    if site_comps_by_type[comp.resource_type].get(comp.resource_model, None) is None:
                        site_comps_by_type[comp.resource_type][comp.resource_model] = list()
                    site_comps_by_type[comp.resource_type][comp.resource_model].append(comp)

            # create a Composite node for every site
            site_node_id = str(uuid.uuid4())
            site_props = abqm.node_sliver_to_graph_properties_dict(site_sliver)
            abqm.add_node(node_id=site_node_id, label=ABCPropertyGraph.CLASS_CompositeNode,
                          props=site_props)
            # create a component sliver for every component type/model pairing
            # and add a node for it linking back to site node
            for ctype, cdict in site_comps_by_type.items():
                for cmodel, comp_list in cdict.items():
                    comp_sliver = ComponentSliver()
                    comp_sliver.capacities = Capacities()
                    comp_sliver.set_type(ctype)
                    comp_sliver.set_model(cmodel)
                    comp_sliver.set_name(str(ctype) + '-' + cmodel)
                    for comp in comp_list:
                        comp_sliver.capacities = comp_sliver.capacities + comp.capacities
                    comp_node_id = str(uuid.uuid4())
                    comp_props = abqm.component_sliver_to_graph_properties_dict(comp_sliver)
                    abqm.add_node(node_id=comp_node_id, label=ABCPropertyGraph.CLASS_Component,
                                  props=comp_props)
                    abqm.add_link(node_a=site_node_id, rel=ABCPropertyGraph.REL_HAS,
                                  node_b=comp_node_id)

        return abqm
