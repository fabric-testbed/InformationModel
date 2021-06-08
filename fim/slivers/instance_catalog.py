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

from typing import Dict, Any, List, Tuple

import os
import json

from fim.view_only_dict import ViewOnlyDict

from .capacities_labels import Capacities


class InstanceCatalog:
    """
    This class helps list available VM instance sizes in FABRIC and
    map between instance size names and actual requirements for cores
    RAM and disk. The class relies on a resource file
    fim/slivers/data/instance_sizes.json
    """
    __catalog_instance = None

    def __init__(self):
        pass

    @staticmethod
    def __read_catalog() -> ViewOnlyDict:
        if InstanceCatalog.__catalog_instance is None:
            catalog_file = os.path.join(os.path.dirname(__file__), 'data', 'instance_sizes.json')
            with open(catalog_file) as f:
                catalog = json.load(f)
            assert isinstance(catalog, dict)
            InstanceCatalog.__catalog_instance = {k: Capacities().set_fields(**v) for (k, v) in catalog.items()}
        return ViewOnlyDict(InstanceCatalog.__catalog_instance)

    def get_instance_capacities(self, *, instance_type: str) -> Capacities or None:
        """
        Return Capacities object for a given instance name or None
        :param instance_type:
        :return:
        """
        assert instance_type is not None
        c = self.__read_catalog()
        return c.get(instance_type, None)

    def map_capacities_to_instance(self, *, cap: Capacities) -> str:
        """
        Return closest instance (name) for these capacities. Return largest
        possible instance request exceeds what is possible.
        :param cap:
        :return: instance type name
        """
        assert cap is not None
        c = self.__read_catalog()
        keys = list(c.keys())
        values = list(c.values())
        candidates = list(filter(lambda x: (x.core >= cap.core and x.ram >= cap.ram and x.disk >= cap.disk),
                                 values))
        candidates.sort()
        if len(candidates) > 0:
            return keys[values.index(candidates[0])]
        # return the largest instance
        return keys[-1]

    def list_instances(self) -> ViewOnlyDict:
        """
        List available instance types and their capacities
        :return:
        """
        return self.__read_catalog()




