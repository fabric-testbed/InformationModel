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
Definitions of topology differences for modify operations - used in topology and sliver diff methods
"""
import dataclasses
from typing import Any, Tuple
from enum import Flag, auto


class WhatsModifiedFlag(Flag):
    """
    As we work on enabling more and more modifications, this list will grow
    """
    NONE = 0
    LABELS = auto()
    CAPACITIES = auto()
    USER_DATA = auto()
    SUB_INTERFACES = auto()


@dataclasses.dataclass
class TopologyDiffTuple:
    """
    Note that in case of diffs between topologies these sets contain
    network elements. In case of diffs between slivers they contain slivers
    """
    nodes: set[Any]
    components: set[Any]
    services: set[Any]
    interfaces: set[Any]


@dataclasses.dataclass
class TopologyDiffModifiedTuple:
    """
    Note that in case of diffs between topologies these lists contain
    network elements. In case of diffs between slivers they contain slivers
    """
    nodes: list[Tuple[Any, WhatsModifiedFlag]]
    components: list[Tuple[Any, WhatsModifiedFlag]]
    services: list[Tuple[Any, WhatsModifiedFlag]]
    interfaces: list[Tuple[Any, WhatsModifiedFlag]]


@dataclasses.dataclass
class TopologyDiff:
    """
    Note that for added and removed the sets are just tuple of sets of Elements,
    while for modified it is a tuple of lists of tuples [Element, WhatsModifiedFlag]
    """
    added: TopologyDiffTuple
    removed: TopologyDiffTuple
    modified: TopologyDiffModifiedTuple
