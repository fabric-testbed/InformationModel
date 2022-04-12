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
from abc import ABC


class ABCPropertyGraphConstants(ABC):

    # When a property is present, but not field, Neo4j returns word 'None'
    # NetworkX just has python None
    NEO4j_NONE = "None"

    SINGLE_POOL_NAME = "_"
    FIELD_POOL = "pool"
    FIELD_POOL_ID = "pool_id"
    FIELD_CAPACITIES = "capacities"
    FIELD_LABELS = "labels"
    PROP_CAPACITY_DELEGATIONS = "CapacityDelegations"
    PROP_LABEL_DELEGATIONS = "LabelDelegations"
    PROP_CAPACITIES = "Capacities"
    PROP_CAPACITY_HINTS = "CapacityHints"
    PROP_LABELS = "Labels"
    PROP_LABEL_ALLOCATIONS = "LabelAllocations"
    PROP_CAPACITY_ALLOCATIONS = "CapacityAllocations"
    GRAPH_ID = 'GraphID'
    NODE_ID = 'NodeID'
    PROP_NAME = 'Name'
    PROP_CLASS = 'Class'
    PROP_TYPE = 'Type'
    PROP_MODEL = 'Model'
    PROP_LAYER = 'Layer'
    PROP_TECHNOLOGY = 'Technology'
    PROP_SITE = 'Site'
    PROP_LOCATION = 'Location'
    PROP_IMAGE_REF = 'ImageRef'
    PROP_MGMT_IP = 'MgmtIp'
    PROP_ALLOCATION_CONSTRAINTS = 'AllocationConstraints'
    PROP_SERVICE_ENDPOINT = 'ServiceEndpoint'
    PROP_DETAILS = 'Details'
    PROP_RESERVATION_INFO = 'ReservationInfo'
    PROP_NODE_MAP = "NodeMap"
    PROP_STRUCTURAL_INFO = "StructuralInfo"
    PROP_STITCH_NODE = "StitchNode"
    PROP_ERO = "ERO"
    PROP_PATH_INFO = "PathInfo"
    PROP_CONTROLLER_URL = "ControllerURL"
    PROP_GATEWAY = "Gateway"
    PROP_MIRROR_PORT = "MirrorPort"
    PROP_MIRROR_DIRECTION = "MirrorDirection"
    PROP_TAGS = "Tags"
    PROP_FLAGS = "Flags"
    PROP_MEAS_DATA = "MeasurementData"
    PROP_BOOT_SCRIPT = "BootScript"
    # these properties get validated to be valid JSON objects whenever someone validates the graph
    JSON_PROPERTY_NAMES = [PROP_LABELS, PROP_CAPACITIES, PROP_LABEL_DELEGATIONS,
                           PROP_CAPACITY_DELEGATIONS, PROP_LABEL_ALLOCATIONS,
                           PROP_CAPACITY_ALLOCATIONS, PROP_RESERVATION_INFO, PROP_STRUCTURAL_INFO,
                           PROP_ERO, PROP_PATH_INFO, PROP_CAPACITY_HINTS, PROP_GATEWAY,
                           PROP_TAGS, PROP_FLAGS, PROP_MEAS_DATA]
    # these properties cannot be unset
    NO_UNSET_PROPERTIES = [GRAPH_ID, NODE_ID, PROP_TYPE, PROP_CLASS, PROP_NAME]

    CLASS_NetworkNode = 'NetworkNode'
    CLASS_NetworkService = 'NetworkService'
    CLASS_Component = 'Component'
    CLASS_ConnectionPoint = 'ConnectionPoint'
    CLASS_Link = 'Link'
    CLASS_CompositeLink = 'CompositeLink'
    CLASS_CompositeNode = 'CompositeNode'
    CLASS_MeasurementPoint = 'MeasurementPoint'

    REL_HAS = 'has'
    REL_CONNECTS = 'connects'
    REL_DEPENDS = 'depends'
    REL_ADAPTS = 'adapts'
    REL_PEERS = 'peers'