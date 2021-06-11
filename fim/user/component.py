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

from typing import Any, Dict, List, Tuple
import recordclass
import uuid

from fim.view_only_dict import ViewOnlyDict
from ..graph.abc_property_graph import ABCPropertyGraph
from .model_element import ModelElement, ElementType
from .network_service import NetworkService, ServiceType
from .interface import Interface
from ..slivers.capacities_labels import Labels
from ..slivers.attached_components import ComponentSliver, ComponentType
from ..slivers.network_service import NSLayer
from ..slivers.component_catalog import ComponentCatalog, ComponentModelType


class Component(ModelElement):
    """
    A component, like a GPU, a NIC, an FPGA or an NVMe drive of a node in a model.
    In addition to public methods the following calls
    return various dictionaries or lists:
    component.interfaces - a dictionary of interfaces
    component.interface_list - a list of interfaces
    component.network_services - a dictionary of network services
    """

    def __init__(self, *, name: str, node_id: str = None, topo: Any,
                 etype: ElementType = ElementType.EXISTING, model: str = None,
                 ctype: ComponentType = None, comp_model: ComponentModelType = None,
                 parent_node_id: str = None,
                 network_service_node_id: str = None, interface_node_ids: List[str] = None,
                 interface_labels: List[Labels] = None, **kwargs):
        """
        Don't call this yourself, use Node.add_component(). Instantiates components based on
        catalog resource file.
        :param name:
        :param node_id:
        :param topo:
        :param etype: is this supposed to be new or existing
        :param model: must be specified if a new component
        :param ctype: component type
        :param comp_model: Component and Model combined
        :param parent_node_id: node_id of the parent Node (for new components)
        :param network_service_node_id: node id of network_service if one needs to be added (for substrate models only)
        :param interface_node_ids: a list of node ids for expected interfaces (for substrate models only)
        :param interface_labels: a list of Labels structure to associate with each interface
        """

        assert name is not None
        assert topo is not None

        if etype == ElementType.NEW:
            # cant use isinstance as it would create circular import dependencies
            if str(topo.__class__) == "<class 'fim.user.topology.SubstrateTopology'>" and node_id is None:
                raise RuntimeError("When adding components to substrate topology nodes you must specify static Node ID")
            if node_id is None:
                node_id = str(uuid.uuid4())
            if parent_node_id is None:
                raise RuntimeError("Parent node id must be specified for new components")
            if (model is None or ctype is None) and comp_model is None:
                raise RuntimeError("Model and component type or comp_model must be specified for new components")
            if str(topo.__class__) == "<class 'fim.user.topology.SubstrateTopology'>" and \
                    (ctype == ComponentType.SharedNIC or ctype == ComponentType.SmartNIC) and \
                    (network_service_node_id is None or interface_node_ids is None or interface_labels is None):
                raise RuntimeError('For substrate topologies and components with network interfaces '
                                   'static network service node id, interface node ids and interface labels'
                                   'must be specified')
            super().__init__(name=name, node_id=node_id, topo=topo)
            cata = ComponentCatalog()

            # get the name of the parent node to pass to component generation
            _, parent_props = self.topo.graph_model.get_node_properties(node_id=parent_node_id)
            parent_name = parent_props.get(ABCPropertyGraph.PROP_NAME, None)

            comp_sliver = cata.generate_component(name=name, model=model, ctype=ctype,
                                                  model_type=comp_model,
                                                  ns_node_id=network_service_node_id,
                                                  interface_node_ids=interface_node_ids,
                                                  interface_labels=interface_labels,
                                                  parent_name=parent_name)
            comp_sliver.node_id = node_id
            comp_sliver.set_properties(**kwargs)

            self.topo.graph_model.add_component_sliver(parent_node_id=parent_node_id, component=comp_sliver)
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            if not self.topo.graph_model.check_node_name(node_id=node_id, name=name,
                                                         label=ABCPropertyGraph.CLASS_Component):
                raise RuntimeError(f"Component with this id and name {name} doesn't exist")

    def get_property(self, pname: str) -> Any:
        """
        Retrieve a component property
        :param pname:
        :return:
        """
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        comp_sliver = self.topo.graph_model.component_sliver_from_graph_properties_dict(node_properties)
        return comp_sliver.get_property(pname)

    def set_property(self, pname: str, pval: Any):
        """
        Set a component property
        :param pname:
        :param pval:
        :return:
        """
        comp_sliver = ComponentSliver()
        comp_sliver.set_property(prop_name=pname, prop_val=pval)
        # write into the graph
        prop_dict = self.topo.graph_model.component_sliver_to_graph_properties_dict(comp_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    def set_properties(self, **kwargs):
        """
        Set multiple properties of the component
        :param kwargs:
        :return:
        """
        comp_sliver = ComponentSliver()
        comp_sliver.set_properties(**kwargs)
        # write into the graph
        prop_dict = self.topo.graph_model.component_sliver_to_graph_properties_dict(comp_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    @staticmethod
    def list_properties() -> Tuple[str]:
        return ComponentSliver.list_properties()

    def __get_interface_by_id(self, node_id: str) -> Interface:
        """
        Get an interface of a node by its node_id, return Interface object
        :param node_id:
        :return:
        """
        assert node_id is not None
        _, node_props = self.topo.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        return Interface(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id,
                         topo=self.topo)

    def __get_ns_by_id(self, node_id: str) -> NetworkService:
        """
        Get an network service of a node by its node_id, return NetworkService object
        :param node_id:
        :return:
        """
        assert node_id is not None
        _, node_props = self.topo.graph_model.get_node_properties(node_id=node_id)
        assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
        return NetworkService(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=node_id,
                              topo=self.topo)

    def __list_interfaces(self) -> ViewOnlyDict:
        """
        List all interfaces of the component as a dictionary
        :return:
        """
        node_id_list = self.topo.graph_model.get_all_node_or_component_connection_points(parent_node_id=self.node_id)
        # Could consider using frozendict here
        ret = dict()
        for nid in node_id_list:
            i = self.__get_interface_by_id(nid)
            ret[i.name] = i
        return ViewOnlyDict(ret)

    def __list_of_interfaces(self) -> Tuple[Interface]:
        """
        List all interfaces of the component
        :return:
        """
        node_id_list = self.topo.graph_model.get_all_node_or_component_connection_points(parent_node_id=self.node_id)
        # Could consider using frozendict here
        ret = list()
        for nid in node_id_list:
            i = self.__get_interface_by_id(nid)
            ret.append(i)
        return tuple(ret)

    def __list_network_services(self) -> ViewOnlyDict:
        """
        List all network service children of a node as a dictionary organized
        by network service name. Modifying the dictionary will not affect
        the underlying model, but modifying Components in the dictionary will.
        :return:
        """
        node_id_list = self.topo.graph_model.get_all_network_node_or_component_nss(parent_node_id=self.node_id)
        # Could consider using frozendict or other immutable idioms
        ret = dict()
        for nid in node_id_list:
            c = self.__get_ns_by_id(nid)
            ret[c.name] = c
        return ViewOnlyDict(ret)

    def __getattr__(self, item):
        """
        Special handling for attributes like 'components' and 'interfaces' -
        which query into the model. They return dicts and list
        containers. Modifying containers does not affect the underlying
        graph mode, but modifying elements of lists or values of dicts does.
        :param item:
        :return:
        """
        if item == 'interfaces':
            return self.__list_interfaces()
        if item == 'interface_list':
            return self.__list_of_interfaces()
        if item == 'network_services':
            return self.__list_network_services()
        raise RuntimeError(f'Attribute {item} not available')

    def __repr__(self):
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        comp_sliver = self.topo.graph_model.component_sliver_from_graph_properties_dict(node_properties)
        return comp_sliver.__repr__()

    def __str__(self):
        return self.__repr__()

