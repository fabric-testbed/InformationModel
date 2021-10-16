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
from typing import Tuple, Any, List

import uuid

from .model_element import ModelElement, ElementType, TopologyException

from fim.graph.abc_property_graph import ABCPropertyGraph
from fim.user.interface import Interface
from fim.slivers.network_link import NetworkLinkSliver, LinkType
from fim.slivers.network_service import NSLayer


class Link(ModelElement):
    """
    A link object in a topology connecting interfaces together.
    In addition to public methods the following calls
    return various dictionaries or lists:
    link.interface_list - a list of interfaces attached to this link
    """
    def __init__(self, *, name: str, node_id: str = None, topo: Any,
                 etype: ElementType = ElementType.EXISTING,
                 interfaces: List[Interface] = None,
                 ltype: LinkType = None, technology: str = None, **kwargs):
        """
        Don't call this method yourself, call topology.add_link()
        node_id will be generated if not provided for experiment topologies

        :param name:
        :param node_id:
        :param topo:
        :param etype: is this supposed to exist or new should be created
        :param interfaces: list of interface objects to connect
        :param ltype: link type if new
        :param technology: link technology
        :param kwargs: any additional properties
        """
        assert name is not None
        assert topo is not None

        if etype == ElementType.NEW:
            # cant use isinstance as it would create circular import dependencies
            # node id myst be specified for new nodes in substrate topologies
            if str(topo.__class__) == "<class 'fim.user.topology.SubstrateTopology'>" and \
                    node_id is None:
                raise TopologyException("When adding new links to substrate topology nodes you must specify static Node ID")
            if node_id is None:
                node_id = str(uuid.uuid4())
            super().__init__(name=name, node_id=node_id, topo=topo)
            if ltype is None:
                raise TopologyException("When creating new links you must specify LinkType")
            # FIXME isinstance
            if interfaces is None or len(interfaces) == 0 or (not isinstance(interfaces, tuple) and
                                                              not isinstance(interfaces, list)):
                raise TopologyException("When creating new links you must specify the list of interfaces to connect.")
            self._interfaces = interfaces
            sliver = NetworkLinkSliver()
            sliver.node_id = self.node_id
            sliver.set_name(self.name)
            sliver.set_type(ltype)
            # set layer based on type
            sliver.set_layer(NetworkLinkSliver.LinkConstraints[ltype].layer)
            sliver.set_technology(technology)
            sliver.set_properties(**kwargs)

            # get a list of node_ids for interfaces
            interface_ids = (iff.node_id for iff in interfaces)
            self.topo.graph_model.add_network_link_sliver(interfaces=interface_ids, lsliver=sliver)
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            # check that this node exists
            existing_node_id = self.topo.\
                graph_model.find_node_by_name(node_name=name,
                                              label=ABCPropertyGraph.CLASS_Link)
            if existing_node_id != node_id:
                raise TopologyException(f'Link name {name} is not unique within the topology.')
            # collect a list of interfaces it attaches to
            interface_list = self.topo.graph_model.get_all_ns_or_link_connection_points(link_id=self.node_id)
            name_id_tuples = list()
            # need to look up their names - a bit inefficient, need to think about this /ib
            for iff in interface_list:
                _, props = self.topo.graph_model.get_node_properties(node_id=iff)
                name_id_tuples.append((props[ABCPropertyGraph.PROP_NAME], iff))
            self._interfaces = [Interface(node_id=tup[1], topo=topo, name=tup[0]) for tup in name_id_tuples]

    @property
    def type(self):
        return self.get_property('type') if self.__dict__.get('topo', None) is not None else None

    @property
    def technology(self):
        return self.get_property('technology') if self.__dict__.get('topo', None) is not None else None

    @property
    def layer(self):
        return self.get_property('layer') if self.__dict__.get('topo', None) is not None else None

    def get_property(self, pname: str) -> Any:
        """
        Retrieve a link property
        :param pname:
        :return:
        """
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        if_sliver = self.topo.graph_model.link_sliver_from_graph_properties_dict(node_properties)
        return if_sliver.get_property(pname)

    def set_property(self, pname: str, pval: Any):
        """
        Set a link property or unset if pval is None
        :param pname:
        :param pval:
        :return:
        """
        if pval is None:
            self.unset_property(pname)
            return
        link_sliver = NetworkLinkSliver()
        link_sliver.set_property(prop_name=pname, prop_val=pval)
        # write into the graph
        prop_dict = self.topo.graph_model.link_sliver_to_graph_properties_dict(link_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    def set_properties(self, **kwargs):
        """
        Set multiple properties of the link
        :param kwargs:
        :return:
        """
        link_sliver = NetworkLinkSliver()
        link_sliver.set_properties(**kwargs)
        # write into the graph
        prop_dict = self.topo.graph_model.link_sliver_to_graph_properties_dict(link_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    @staticmethod
    def list_properties() -> Tuple[str]:
        return NetworkLinkSliver.list_properties()

    def __list_of_interfaces(self) -> List[Interface] or None:
        """
        Make a copy and return a list of interface objects
        :return:
        """
        if self._interfaces is not None:
            return self._interfaces.copy()
        return None

    @property
    def interface_list(self):
        return self.__list_of_interfaces()

    def __repr__(self):
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        link_sliver = self.topo.graph_model.link_sliver_from_graph_properties_dict(node_properties)
        interface_names = [iff.name for iff in self._interfaces]
        return link_sliver.__repr__() + str(interface_names)

    def __str__(self):
        return self.__repr__()