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
Neo4j implementation of ADM (Aggregate Delegation Model) functionality.
"""

import uuid
import json

from ..neo4j_property_graph import Neo4jPropertyGraph, Neo4jGraphImporter
from .abc_adm import ABCADMMixin


class Neo4jADMGraph(Neo4jPropertyGraph, ABCADMMixin):

    def __init__(self, *, graph_id: str = None, importer: Neo4jGraphImporter, logger=None):
        """
        Initialize CBM either from existing ID or generate new graph id
        :param graph_id:
        :param importer:
        """
        if graph_id is None:
            graph_id = str(uuid.uuid4())

        super().__init__(graph_id=graph_id, importer=importer, logger=logger)

    def rewrite_delegations(self, *, real_adm_id: str = None) -> None:
        """
        Rewrite label and capacity delegations on all nodes to be dictionaries
        referenced by ADM graph id. Note that external code should
        not interact with delegations on ADM graphs.
        Sometimes ADMs are cloned into temporary graphs so the method provides
        a way to pass original ADM id as an option.
        :param real_adm_id:
        :return:
        """
        for node_id in self.list_all_node_ids():
            _, node_props = self.get_node_properties(node_id=node_id)
            props_modified = False
            for delegation_prop_name in [self.PROP_LABEL_DELEGATIONS, self.PROP_CAPACITY_DELEGATIONS]:
                if delegation_prop_name in node_props.keys():
                    if node_props[delegation_prop_name] == self.NEO4j_NONE:
                        continue
                    props_modified = True
                    # turn delegation into Python object
                    delegation = json.loads(node_props[delegation_prop_name])
                    new_delegation = dict()
                    if real_adm_id is None:
                        new_delegation[self.graph_id] = delegation
                    else:
                        new_delegation[real_adm_id] = delegation
                    new_delegation_json = json.dumps(new_delegation)
                    node_props[delegation_prop_name] = new_delegation_json
            if props_modified:
                # write back
                self.update_node_properties(node_id=node_id, props=node_props)
