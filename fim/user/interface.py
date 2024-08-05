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

from typing import Any, List, Tuple

import uuid

from .model_element import ModelElement, ElementType, TopologyException

from ..slivers.interface_info import InterfaceType, InterfaceSliver
from ..graph.abc_property_graph import ABCPropertyGraph
from ..slivers.capacities_labels import Labels
from ..view_only_dict import ViewOnlyDict


class Interface(ModelElement):

    def __init__(self, *, name: str, node_id: str = None, topo: Any,
                 etype: ElementType = ElementType.EXISTING,
                 parent_node_id: str = None,
                 itype: InterfaceType = None,
                 check_existing: bool = False,
                 **kwargs):
        """
        Don't call this method yourself, call node.add_interface()
        node_id will be generated if not provided for experiment topologies

        :param name:
        :param node_id:
        :param topo:
        :param etype: is this supposed to exist or new should be created
        :param parent_node_id: parent network service or parent interface
        :param itype: node type if it is new
        :param check_existing: check if the Interface exists in the graph
        :param kwargs: any additional properties
        """
        assert name is not None
        assert topo is not None

        if etype == ElementType.NEW:
            # cant use isinstance as it would create circular import dependencies
            # node id myst be specified for new nodes in substrate topologies
            if str(topo.__class__) == "<class 'fim.user.topology.SubstrateTopology'>" and \
                    node_id is None:
                raise TopologyException("When adding new nodes to substrate topology nodes you must specify static Node ID")
            if node_id is None:
                node_id = str(uuid.uuid4())
            if itype is None:
                raise TopologyException("When creating interfaces you must specify InterfaceType")
            super().__init__(name=name, node_id=node_id, topo=topo)
            sliver = InterfaceSliver()
            sliver.node_id = self.node_id
            sliver.set_name(self.name)
            sliver.set_type(itype)
            sliver.set_properties(**kwargs)

            self.topo.graph_model.add_interface_sliver(parent_node_id=parent_node_id, interface=sliver)
            self._interfaces = list()
        else:
            assert node_id is not None
            super().__init__(name=name, node_id=node_id, topo=topo)
            if check_existing and not self.topo.graph_model.check_node_name(node_id=node_id, name=name,
                                                                            label=ABCPropertyGraph.CLASS_ConnectionPoint):
                raise TopologyException(f"Interface with this id {node_id} and name {name} doesn't exist")
            # collect a list of interface nodes it attaches to for DedicatedPorts only
            self._interfaces = list()
            if self.type == InterfaceType.DedicatedPort:
                interface_list = self.topo.graph_model.get_all_child_connection_points(interface_id=self.node_id)
                name_id_tuples = list()
                # need to look up their names - a bit inefficient, need to think about this /ib
                for iff in interface_list:
                    _, props = self.topo.graph_model.get_node_properties(node_id=iff)
                    name_id_tuples.append((props[ABCPropertyGraph.PROP_NAME], iff))
                self._interfaces = [Interface(node_id=tup[1], topo=topo, name=tup[0]) for tup in name_id_tuples]

    @property
    def type(self):
        return self.get_property('type') if self.__dict__.get('topo', None) is not None else None

    def add_child_interface(self, *, name: str, node_id: str = None, **kwargs):
        """
        Add an interface to network service
        :param name:
        :param node_id:
        :param itype: interface type e.g. TrunkPort, AccessPort or VINT
        :param kwargs: additional parameters
        :return:
        """
        assert name is not None
        assert self.type is InterfaceType.DedicatedPort

        # check uniqueness
        all_names = [n.name for n in self._interfaces]
        if name in all_names:
            raise TopologyException(f'Sub Interface {name} is not unique within the interface')

        labels = kwargs.get('labels')
        if not labels or not labels.vlan:
            raise TopologyException(f'Vlan must be specified for Sub Interface within the interface')

        all_vlans = []
        for i in self._interfaces:
            if i.labels and i.labels.vlan:
                all_vlans.append(i.labels.vlan)

        if labels.vlan in all_vlans:
            raise TopologyException(f'Vlan in use by another Sub Interface within the interface')

        if self.labels:
            labels.local_name = self.labels.local_name
        else:
            raise TopologyException(f'Local name for the dedicated interface not available')

        iff = Interface(name=name, node_id=node_id, parent_node_id=self.node_id,
                        etype=ElementType.NEW, topo=self.topo, itype=InterfaceType.SubInterface,
                        **kwargs)

        self._interfaces.append(iff)
        return iff

    def remove_child_interface(self, *, name: str) -> None:
        """
        Remove an ServicePort interface from the network service.
        :param name:
        :return:
        """
        assert name is not None
        assert self.type is InterfaceType.DedicatedPort

        # cant use isinstance as it would create circular import dependencies
        #if str(self.topo.__class__) == "<class 'fim.user.topology.ExperimentTopology'>":
        #    raise TopologyException("Cannot remove child interface interface from Interface in Experiment topology")
        node_id = self.topo.graph_model.find_child_connection_point_by_name(parent_node_id=self.node_id,
                                                                            iname=name)

        self.topo.graph_model.remove_cp_and_links(node_id=node_id, delete_parent=False)

    def __list_interfaces(self) -> ViewOnlyDict:
        """
        List all interfaces of the network service as a dictionary
        :return:
        """
        ret = dict()
        for intf in self._interfaces:
            ret[intf.name] = intf
        return ViewOnlyDict(ret)

    def __list_of_interfaces(self) -> tuple:
        """
        Return a list of names of interfaces of network service
        :return:
        """
        return tuple(self._interfaces)

    @property
    def interface_list(self):
        """
        List of names of service interfaces
        """
        return self.__list_of_interfaces()

    @property
    def interfaces(self):
        """
        Dictionary name->Interface for all interfaces
        """
        return self.__list_interfaces()

    @property
    def peer_labels(self):
        return self.get_property('peer_labels') if self.__dict__.get('topo', None) is not None else None

    @peer_labels.setter
    def peer_labels(self, value: Labels):
        if self.__dict__.get('topo', None) is not None:
            self.set_property('peer_labels', value)

    def get_property(self, pname: str) -> Any:
        """
        Retrieve a interface property
        :param pname:
        :return:
        """
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        if_sliver = self.topo.graph_model.interface_sliver_from_graph_properties_dict(node_properties)
        return if_sliver.get_property(pname)

    def set_property(self, pname: str, pval: Any):
        """
        Set a interface property or unset if pval is None
        :param pname:
        :param pval:
        :return:
        """
        if pval is None:
            self.unset_property(pname)
            return
        if_sliver = InterfaceSliver()
        if_sliver.set_property(prop_name=pname, prop_val=pval)
        # write into the graph
        prop_dict = self.topo.graph_model.interface_sliver_to_graph_properties_dict(if_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    def set_properties(self, **kwargs):
        """
        Set multiple properties of the interface
        :param kwargs:
        :return:
        """
        if_sliver = InterfaceSliver()
        if_sliver.set_properties(**kwargs)
        # write into the graph
        prop_dict = self.topo.graph_model.interface_sliver_to_graph_properties_dict(if_sliver)
        self.topo.graph_model.update_node_properties(node_id=self.node_id, props=prop_dict)

    @staticmethod
    def list_properties() -> Tuple[str]:
        return InterfaceSliver.list_properties()

    def get_peers(self, itype: InterfaceType = None) -> List[Any] or None:
        """
        Find 'peer' interfaces connected across a Link. Returns a list of Interface objects
        (matching optional itype if specified, otherwise all).
        :parm itype: optional type of peer interface we are looking for
        :return: peer Interface object or None
        """
        peer_ids = self.topo.graph_model.find_peer_connection_points(node_id=self.node_id)
        if peer_ids is None:
            return None
        ret = list()
        for peer_id in peer_ids:
            clazzes, node_props = self.topo.graph_model.get_node_properties(node_id=peer_id)
            assert node_props.get(ABCPropertyGraph.PROP_NAME, None) is not None
            assert ABCPropertyGraph.CLASS_ConnectionPoint in clazzes
            i = Interface(name=node_props[ABCPropertyGraph.PROP_NAME], node_id=peer_id,
                          topo=self.topo)
            if itype is not None:
                if i.type == itype:
                    ret.append(i)
            else:
                ret.append(i)
        return ret

    def get_sliver(self) -> InterfaceSliver:
        """
        Get a deep sliver representation of this interface from graph
        :return:
        """
        return self.topo.graph_model.build_deep_interface_sliver(node_id=self.node_id)

    def __repr__(self):
        _, node_properties = self.topo.graph_model.get_node_properties(node_id=self.node_id)
        if_sliver = self.topo.graph_model.interface_sliver_from_graph_properties_dict(node_properties)
        return if_sliver.__repr__()

    def __str__(self):
        return self.__repr__()
