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
# Author Ilya Baldin (ibaldin@renci.org)
from typing import Dict, Any

import json

from .network_node import NodeSliver
from .network_service import NetworkServiceSliver
from fim.graph.abc_property_graph import ABCPropertyGraph


class JSONSliver:
    """
    This class uses ABC Property Graph dictionary serialization
    to also convert slivers to and from JSON. It is made into a
    separate class to avoid circular dependencies.
    """

    @staticmethod
    def sliver_to_json(sliver) -> str:
        """
        Take an object that is a descendant of a BaseSliver and
        convert it to JSON
        :param sliver:
        :return:
        """
        d = ABCPropertyGraph.sliver_to_dict(sliver)
        if d is not None:
            return json.dumps(d)

    @staticmethod
    def node_sliver_from_json(s: str) -> NodeSliver:
        """
        Recover a node sliver from JSON
        :param s:
        :return:
        """
        d = json.loads(s)
        if not isinstance(d, dict):
            raise RuntimeError(f'Unable to decode NodeSliver from {s=}')
        return ABCPropertyGraph.build_deep_node_sliver_from_dict(props=d)

    @staticmethod
    def network_service_sliver_from_json(s: str) -> NetworkServiceSliver:
        """
        Recover a network service sliver from JSON
        :param s:
        :return:
        """
        d = json.loads(s)
        if not isinstance(d, dict):
            raise RuntimeError(f'Unable to decode NetworkServiceSliver from {s=}')
        return ABCPropertyGraph.build_deep_ns_sliver_from_dict(props=d)
