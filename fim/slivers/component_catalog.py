#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2021 FABRIC Testbed
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
import enum
from typing import Dict, Any, List, Tuple
import os
import json
import uuid
import re

from .attached_components import ComponentSliver, ComponentType
from .interface_info import InterfaceInfo, InterfaceSliver, InterfaceType
from .network_service import NetworkServiceSliver, NetworkServiceInfo, NSLayer, ServiceType
from .capacities_labels import Capacities, Labels
from fim.view_only_dict import ViewOnlyDict


ComponentModelTypeMap = dict()
ComponentModelType = None


class ComponentCatalog:
    """
    Reading/parsing of component catalog resource file, generation of
    component slivers based on models, search, details etc.
    This class relies on a resource file fim/slivers/data/component_catalog.json
    """
    catalog_instance = None

    def __init__(self):
        pass

    @staticmethod
    def __read_catalog() -> Tuple[Any]:
        if ComponentCatalog.catalog_instance is None:
            catalog_file = os.path.join(os.path.dirname(__file__), 'data', 'component_catalog.json')
            with open(catalog_file) as f:
                catalog = json.load(f)
            assert isinstance(catalog, list)
            ComponentCatalog.catalog_instance = catalog
        return tuple(ComponentCatalog.catalog_instance)

    def generate_component(self, *, name: str, ctype: ComponentType = None, model: str = None,
                           model_type: ComponentModelType = None,
                           ns_node_id: str = None,
                           interface_node_ids: List[str] = None,
                           interface_labels: List[Labels] = None,
                           parent_name: str = None) -> ComponentSliver:
        """
        Generate a component sliver with this name and model (encoded as separate type/model fields or
        a combined comp_model type) and properties, and interfaces as needed
        based on the catalog description. Interfaces if present are named
        as a concatenation of component name and port name from the catalog with
        and '_' connecting them.
        Raises CatalogException if the model is not found
        :param name: name to give to the component
        :param ctype: type of the component
        :param model:
        :param model_type: type and model encoded together - specify model type together or separately
        :param ns_node_id: if specified and if component has a network service, put that there
        :param interface_node_ids: list of node ids for expected interfaces if component has any
        :param interface_labels: list of labels for expected interfaces if component has any
        :param parent_name: helps generate unique ids
        :return:
        """
        assert name is not None
        if model_type is not None:
            model = ComponentModelTypeMap[model_type]['Model']
            ctype_str = ComponentModelTypeMap[model_type]['Type']
        else:
            if ctype is None or model is None:
                raise RuntimeError('Either ctype and model must be specified, or comp_model.')
            ctype_str = str(ctype)
        catalog = self.__read_catalog()
        component_dict = None
        for c in catalog:
            main_model = c['Model']
            also_model_list = c.get('AlsoModels', None)

            if model == main_model and ctype_str == c['Type']:
                component_dict = c
                break
            if also_model_list is not None:
                if model in also_model_list and ctype_str == c['Type']:
                    component_dict = c
                    break

        if component_dict is None:
            raise CatalogException(f'Unable to find model {model} of type {ctype_str} in the catalog')

        cs = ComponentSliver()
        cs.set_name(name)
        cs.set_model(component_dict['Model'])
        cs.set_type(cs.type_from_str(component_dict['Type']))
        cs.set_details(component_dict['Details'])
        if 'Interfaces' in component_dict.keys():
            # for components with interfaces
            if cs.get_type() in [ComponentType.FPGA]:
                ns_suffix = '-l2p4'
                ns_type = ServiceType.P4
            else:
                ns_suffix = '-l2ovs'
                ns_type = ServiceType.OVS

            interfaces_dict = component_dict['Interfaces']
            if interface_node_ids is not None:
                if len(interface_node_ids) != len(interfaces_dict.keys()):
                    raise RuntimeError("The number of interface IDs provided is insufficient for this component "
                                       f"(need {len(interfaces_dict.keys())} instead of {len(interface_node_ids)}")
                if len(interface_labels) != len(interfaces_dict.keys()):
                    raise RuntimeError("The number of PCI labels and MAC addresses provided is insufficient for this"
                                       f" component (need {len(interfaces_dict.keys())} instead of "
                                       f"{len(interface_labels)}")
            iinfo = InterfaceInfo()
            id_index = 0
            for interface_name in interfaces_dict.keys():
                isliver = InterfaceSliver()
                isliver.set_name(name + '-' + interface_name)
                if cs.get_type() in [ComponentType.SmartNIC, ComponentType.FPGA]:
                    isliver.set_type(InterfaceType.DedicatedPort)
                elif cs.get_type() == ComponentType.SharedNIC:
                    isliver.set_type(InterfaceType.SharedPort)
                if interface_node_ids is not None:
                    isliver.node_id = interface_node_ids[id_index]
                else:
                    isliver.node_id = str(uuid.uuid4())
                if interface_labels is not None:
                    isliver.set_labels(interface_labels[id_index])
                # set local_name to port name from catalog, however for sr-iov cards it needs to
                # be a list of identical names. We use bdf labels as indicator of how many devices
                # are behind it.
                if isliver.labels is not None:
                    if isliver.labels.bdf is not None and \
                            isinstance(isliver.labels.bdf, list):
                        isliver.labels._set_fields(local_name=[interface_name for k in range(len(isliver.labels.bdf))])
                    else:
                        isliver.labels._set_fields(local_name=interface_name)
                else:
                    isliver.set_labels(Labels(local_name=interface_name))
                # if labels are lists, extract the length to make it the number of units
                lab = isliver.get_labels()
                units = len(lab.bdf) if lab is not None and lab.bdf is not None else 1
                id_index = id_index + 1
                # set port speed and units (inferring from length of bdf array)
                # for SR-IOV bw==0 to indicate best-effort by default
                if cs.get_type() == ComponentType.SharedNIC:
                    cap = Capacities(unit=units)
                else:
                    cap = Capacities(unit=units, bw=int(interfaces_dict[interface_name]))
                isliver.set_capacities(cap=cap)
                iinfo.add_interface(isliver)
            ns = NetworkServiceSliver()
            if ns_node_id is None:
                ns_node_id = str(uuid.uuid4())
            ns.node_id = ns_node_id
            # network service names are supposed to be unique within a graph
            if parent_name is not None:
                ns.set_name(parent_name + "-" + name + ns_suffix)
            else:
                ns.set_name(name + ns_suffix)
            ns.set_type(ns_type)
            # default to L2 for now
            ns.set_layer(NSLayer.L2)
            ns.interface_info = iinfo
            nsinfo = NetworkServiceInfo()
            nsinfo.add_network_service(ns)
            cs.set_network_service_info(nsinfo)
        return cs

    def component_details(self, *, model: str) -> str:
        """
        List details of a component specified by model
        :param model:
        :return:
        """
        assert model is not None
        catalog = self.__read_catalog()
        component_dict = None
        for c in catalog:
            if model == c['Model']:
                component_dict = c

        if component_dict is None:
            raise CatalogException(f'Unable to find model {model} in the catalog')
        return component_dict['Details']

    def search_catalog(self, *, ctype: ComponentType) -> ViewOnlyDict:
        """
        Provide a dictionaty of matching component models and their details
        based on component type
        :param ctype:
        :return:
        """
        catalog = self.__read_catalog()
        matching_components = list()
        for c in catalog:
            if str(ctype) == c['Type']:
                matching_components.append(c)

        if len(matching_components) == 0:
            raise CatalogException(f'Unable to find type {ctype} in the catalog')
        ret = dict()
        for c in matching_components:
            ret[c['Model']] = c['Details']
        return ViewOnlyDict(ret)

    @staticmethod
    def __massage_name(name: str) -> str:
        """
        Massage to make it python friendly
        :param name:
        :return:
        """
        return re.sub(r'[ -]', '_', name)

    def populate_catalog_models_and_types(self):
        """
        Called via __init__.py to populate ComponentModelType
        :return:
        """
        global ComponentModelType
        global ComponentModelTypeMap
        catalog = self.__read_catalog()
        enum_dict = dict()
        enum_idx = 1
        for c in catalog:
            type_model_name = '_'.join([self.__massage_name(c['Type']),
                                        self.__massage_name(c['Model'])])
            enum_dict[type_model_name] = enum_idx
            enum_idx += 1
        # create dynamic enum
        ComponentModelType = enum.Enum('ComponentModelType', enum_dict)
        # populate mapping
        for k, v in enum_dict.items():
            ComponentModelTypeMap[ComponentModelType(v)] = catalog[v-1]


class CatalogException(Exception):
    """
    Component catalog exception
    """
    def __init__(self, msg: str):
        super().__init__(msg)