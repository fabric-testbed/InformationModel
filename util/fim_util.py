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
This utility implements a number of operations to make it easier to develop and debug
information models in FABRIC. It

- takes in a serialized model in GraphML (typically produced by yEd) and
adds various identifiers (node, graph, etc) as necessary for models to become readable
by CF actors.
- loads a model from a file into an indicated Neo4j instance
- remove a specific graph or all graphs from the database

Configuration is done using a yaml file named by default fim_config.yaml structured as:

# default fim_config configuration file for FIM utilities
neo4j:
  url: neo4j://0.0.0.0:7687
  user: neo4j
  pass: password
  import_host_dir: /host/directory/seen/by/neo4j/docker/as/imports
  import_dir: /imports

Designed to work with Neo4j-APOC Docker
https://hub.docker.com/repository/docker/fabrictestbed/neo4j-apoc
"""

import argparse
import sys
import logging
import yaml

from fim.graph.abc_property_graph import ABCPropertyGraph
from fim.graph.neo4j_property_graph import Neo4jPropertyGraph, Neo4jGraphImporter, PropertyGraphImportException
from fim.graph.resources.neo4j_arm import Neo4jARMGraph
from fim.graph.resources.neo4j_cbm import Neo4jCBMGraph
from fim.pluggable import PluggableRegistry, PluggableType
from fim.graph.delegations import DelegationType

FIM_CONFIG_YAML = "fim_config.yaml"


class MyPlug:
    """
    Fake pluggable BQM broker class for FIM testing
    """
    def __init__(self):
        print("Creating MyPlug")

    def plug_produce_bqm(self, *, cbm: ABCPropertyGraph, **kwargs) -> ABCPropertyGraph:
        print(f"Producing CBM as BQM {kwargs}")
        return cbm


def load_file(*, filename, graph_id, neo4j_config):
    """
    load graph from file
    :param filename:
    :param graph_id:
    :param neo4j_config:
    :return:
    """
    neo4j_graph_importer = Neo4jGraphImporter(url=neo4j_config["url"], user=neo4j_config["user"],
                                              pswd=neo4j_config["pass"],
                                              import_host_dir=neo4j_config["import_host_dir"],
                                              import_dir=neo4j_config["import_dir"])
    print(f"Loading graph into Neo4j")
    _graph = neo4j_graph_importer.import_graph_from_file(graph_file=filename, graph_id=graph_id)
    print(f"Created graph {_graph}")
    try:
        return _graph.validate_graph()
    except PropertyGraphImportException as pe:
        print(f"Unable to load graph due to error {pe.msg}, deleting")
        _graph.delete_graph()
        return None


def load_file_direct(*, filename, neo4j_config):
    """
    Load specified file directly with no manipulations or validation
    :param filename:
    :param neo4j_config:
    :return:
    """
    neo4j_graph_importer = Neo4jGraphImporter(url=neo4j_config["url"], user=neo4j_config["user"],
                                              pswd=neo4j_config["pass"],
                                              import_host_dir=neo4j_config["import_host_dir"],
                                              import_dir=neo4j_config["import_dir"])
    return neo4j_graph_importer.import_graph_from_file_direct(graph_file=filename)


def enumerate_nodes(*, filename, new_filename, neo4j_config):
    """
    Add unique NodeId property to each node in the graph and save under
    a new name
    :param filename:
    :param new_filename:
    :param neo4j_config
    :return:
    """
    neo4j_graph_importer = Neo4jGraphImporter(url=neo4j_config["url"], user=neo4j_config["user"],
                                              pswd=neo4j_config["pass"],
                                              import_host_dir=neo4j_config["import_host_dir"],
                                              import_dir=neo4j_config["import_dir"])
    neo4j_graph_importer.enumerate_graph_nodes(graph_file=filename, new_graph_file=new_filename)


def delete_graphs(*, neo4j_config, graph_id=None):
    """
    Delete a specific graph or all graphs if graph_id is none
    :param neo4j_config
    :param graph_id:
    :return:
    """
    neo4j_graph = Neo4jGraphImporter(url=neo4j_config["url"], user=neo4j_config["user"],
                                     pswd=neo4j_config["pass"],
                                     import_host_dir=neo4j_config["import_host_dir"],
                                     import_dir=neo4j_config["import_dir"])
    if graph_id is None:
        neo4j_graph.delete_all_graphs()
    else:
        neo4j_graph.delete_graph(graph_id=graph_id)


def save_graph(*, outfile, graph_id, neo4j_config):
    """
    Save indicated graph id into a file
    :param outfile:
    :param graph_id:
    :param new4j_config:
    :return:
    """
    neo4j_graph_importer = Neo4jGraphImporter(url=neo4j_config["url"], user=neo4j_config["user"],
                                              pswd=neo4j_config["pass"],
                                              import_host_dir=neo4j_config["import_host_dir"],
                                              import_dir=neo4j_config["import_dir"])
    graph = Neo4jPropertyGraph(graph_id=graph_id, importer=neo4j_graph_importer)
    graph_string = graph.serialize_graph()
    with open(outfile, 'w') as f:
        f.write(graph_string)


def test_graph(*, graph_ids, neo4j_config):
    """
    crutch for running test functions quickly
    :param graph_id:
    :param neo4j_config:
    :return:
    """
    neo4j_graph_importer = Neo4jGraphImporter(url=neo4j_config["url"], user=neo4j_config["user"],
                                              pswd=neo4j_config["pass"],
                                              import_host_dir=neo4j_config["import_host_dir"],
                                              import_dir=neo4j_config["import_dir"])

    r = PluggableRegistry()
    #r.register_pluggable(t=PluggableType.Broker, p=MyPlug)

    cbm = Neo4jCBMGraph(importer=neo4j_graph_importer)
    print(f"CBM graph ID is {cbm.graph_id}")

    net_graph = Neo4jARMGraph(graph=Neo4jPropertyGraph(graph_id=graph_ids[0], importer=neo4j_graph_importer))
    for node_id in net_graph.list_all_node_ids():
        print(net_graph.get_delegations(node_id=node_id, delegation_type=DelegationType.LABEL))
        print(net_graph.get_delegations(node_id=node_id, delegation_type=DelegationType.CAPACITY))

    net_adms = net_graph.generate_adms()
    print(f"Delegation graph(s) for net AM {net_adms}")
    net_adm = net_adms['del1']
    print("Merging Net ADM")
    cbm.merge_adm(adm=net_adm)
    for graph in net_adms.values():
        graph.delete_graph()

    arm_graph = Neo4jARMGraph(graph=Neo4jPropertyGraph(graph_id=graph_ids[1], importer=neo4j_graph_importer))
    am_adms = arm_graph.generate_adms()
    print(f"Delegation graph(s) for site AM {am_adms}")
    # use del1
    am_adm = am_adms['del1']
    print("Merging AM ADM")
    cbm.merge_adm(adm=am_adm)
    for graph in am_adms.values():
        graph.delete_graph()

    arm_graph = Neo4jARMGraph(graph=Neo4jPropertyGraph(graph_id=graph_ids[2], importer=neo4j_graph_importer))
    am_adms = arm_graph.generate_adms()
    print(f"Delegation graph(s) for site AM {am_adms}")
    # use del1
    am_adm = am_adms['del1']
    print("Merging AM ADM")
    cbm.merge_adm(adm=am_adm)
    for graph in am_adms.values():
        graph.delete_graph()

    arm_graph = Neo4jARMGraph(graph=Neo4jPropertyGraph(graph_id=graph_ids[3], importer=neo4j_graph_importer))
    am_adms = arm_graph.generate_adms()
    print(f"Delegation graph(s) for site AM {am_adms}")
    # use del1
    am_adm = am_adms['del1']
    print("Merging AM ADM")
    cbm.merge_adm(adm=am_adm)
    for graph in am_adms.values():
        graph.delete_graph()

    for node_id in cbm.list_all_node_ids():
        print(cbm.get_delegations(node_id=node_id, delegation_type=DelegationType.LABEL, adm_id=am_adm.graph_id))
        print(cbm.get_delegations(node_id=node_id, delegation_type=DelegationType.CAPACITY, adm_id=am_adm.graph_id))

    cbm.get_bqm(some=5)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    # split into different mutually exclusive operations

    operations = parser.add_mutually_exclusive_group()
    operations.add_argument("-l", "--load", action="store_true",
                            help="load specified file into Neo4j (requires -f, optional -g, -r)")
    operations.add_argument("-w", "--wipe", action="store_true",
                            help="wipe neo4j instance of all graphs (optional -g)")
    operations.add_argument("-e", "--enumerate", action="store_true",
                            help="enumerate all nodes in a graph in specified file"
                                 " assigning them unique GUIDs and save (requires -f and -o)")
    operations.add_argument("-t", "--test", action="store_true",
                            help="invoke test action (-g)")
    operations.add_argument("-s", "--save", action="store_true",
                            help="save a specific graph into a file (requires -o and -g)")
    parser.add_argument("-c", "--config", action="store", default=FIM_CONFIG_YAML,
                        help="provide alternative configuration file")
    parser.add_argument("-f", "--file", action="store",
                        help="GraphML file to be operated on")
    parser.add_argument("-o", "--outfile", action="store",
                        help="output GraphML file")
    parser.add_argument("-g", "--graph", action="store",
                        help="identifier of the graph in the Neo4j database")
    parser.add_argument("-r", "--direct", action="store_true",
                        help="load file directly without validation or any manipulations")
    parser.add_argument("-d", "--debug", action="count",
                        help="turn on debugging")

    args = parser.parse_args()

    if args.debug is None:
        logging.basicConfig(level=logging.INFO)
    elif args.debug >= 1:
        logging.basicConfig(level=logging.DEBUG)

    try:
        with open(args.config, 'r') as config_file:
            yaml_config = yaml.safe_load(config_file)
    except IOError:
        print(f"Unable to open config file {args.config}, exiting", file=sys.stderr)
        sys.exit(-1)

    if args.load:
        if args.file is None:
            print("Must specify -f option", file=sys.stderr)
        # load a file with a given id (or generated id)
        try:
            if args.direct:
                gid = load_file_direct(filename=args.file, neo4j_config=yaml_config["neo4j"])
            else:
                gid = load_file(filename=args.file, neo4j_config=yaml_config["neo4j"], graph_id=args.graph)
            if gid is not None:
                print(f"Graph successfully loaded with id {gid}")
                sys.exit(0)
            else:
                sys.exit(-1)
        except Exception as e:
            print(f"Unable to load file {args.file} to Neo4j due to {e.args}", file=sys.stderr)
            sys.exit(-1)
    elif args.wipe:
        # wipe one graph or whole database
        delete_graphs(neo4j_config=yaml_config["neo4j"], graph_id=args.graph)
        if args.graph is not None:
            print(f"Deleted graph {args.graph} from the database")
        else:
            print("Deleted all graphs from the database")
    elif args.enumerate:
        # enumerate a file
        file = args.file
        newfile = args.outfile
        if file is None or newfile is None:
            print("Must specify -f and -o options", file=sys.stderr)
            sys.exit(-1)

        print(f"Enumerating nodes in {file} and saving as {newfile}")
        enumerate_nodes(filename=file, new_filename=newfile, neo4j_config=yaml_config["neo4j"])
    elif args.save:
        # save graph
        outfile = args.outfile
        graph = args.graph
        if outfile is None or graph is None:
            print("Must specify output file and graph id (-o and -g)", file=sys.stderr)
            sys.exit(-1)

        print(f"Saving graph {graph} into file {outfile}")
        save_graph(outfile=outfile, graph_id=graph, neo4j_config=yaml_config["neo4j"])
    elif args.test:
        # some test action
        graph = args.graph
        print(f"Running test command on {graph}")
        #test_graph(graph_id=graph, neo4j_config=yaml_config["neo4j"])
        test_graph(graph_ids=["807ce9f2-c02c-401a-8f19-b13d4ffbd398",
                              "d752722a-4598-48dc-a34e-62e0a1426218",
                              "caca8303-ca19-424a-ab13-45cdd502e120",
                              "6038b4e7-ae79-41ba-bad2-9d0ad2feb9d5"],
                   neo4j_config=yaml_config["neo4j"])
    else:
        print("Please specify one of -h, -l, -e or -w", file=sys.stderr)
