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
import yaml
import logging
import traceback

from fim.graph.abc_property_graph import ABCPropertyGraph
from fim.graph.neo4j_property_graph import Neo4jPropertyGraph, Neo4jGraphImporter, PropertyGraphImportException
from fim.graph.resources.neo4j_arm import Neo4jARMGraph
from fim.graph.resources.neo4j_cbm import Neo4jCBMGraph
from fim.pluggable import PluggableRegistry

FIM_CONFIG_YAML = "fim_config.yaml"


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
    logging.info(f"Loading graph into Neo4j")
    _graph = neo4j_graph_importer.import_graph_from_file(graph_file=filename, graph_id=graph_id)
    logging.info(f"Created graph {_graph}")
    try:
        _graph.validate_graph()
        return _graph.graph_id
    except PropertyGraphImportException as pe:
        logging.info(f"Unable to load graph due to error {pe.msg}, deleting")
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
    return neo4j_graph_importer.import_graph_from_file_direct(graph_file=filename).graph_id


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


def merge_ads(*, neo4j_config, file_names, delete_arms, delete_adms, info=False):
    """
    Merge these advertisements together in the order provided
    :param neo4j_config:
    :param file_names: list of file names
    :return:
    """
    neo4j_graph_importer = Neo4jGraphImporter(url=neo4j_config["url"], user=neo4j_config["user"],
                                              pswd=neo4j_config["pass"],
                                              import_host_dir=neo4j_config["import_host_dir"],
                                              import_dir=neo4j_config["import_dir"])
    cbm = Neo4jCBMGraph(importer=neo4j_graph_importer)
    logging.info(f'Created blank CBM {cbm.graph_id}')

    arms = dict()
    for file_name in file_names:
        _graph = neo4j_graph_importer.import_graph_from_file(graph_file=file_name)
        logging.info(f'Loaded {file_name} as graph ID {_graph.graph_id}')
        _graph.validate_graph()
        if arms.get(file_name, None) is not None:
            logging.error(f'Encountered model {file_name} more than once, please revise parameters.')
            sys.exit(-1)
        arms[file_name] = Neo4jARMGraph(graph=Neo4jPropertyGraph(graph_id=_graph.graph_id,
                                                                 importer=neo4j_graph_importer))
        # generate a dict of ADMs from site graph ARM
        site_adms = arms[file_name].generate_adms()
        logging.info(f'ADMS for {file_name}:')
        for adm_id in site_adms.keys():
            logging.info(f'  ADM id {adm_id}: {site_adms[adm_id].graph_id}')

        # desired ADM is under 'primary'
        site_adm = site_adms['primary']

        logging.info(f'Merging into CBM')
        cbm.merge_adm(adm=site_adm)
        cbm.validate_graph()

        if delete_arms:
            logging.info(f'Deleting ARM {file_name}')
            arms[file_name].delete_graph()
        if delete_adms:
            logging.info(f'Deleting ADMs for {file_name}')
            for adm in site_adms.values():
                adm.delete_graph()
    logging.info('Completed')
    if info:
        logging.info(f'List of sites in the model: {cbm.get_sites()}')
        logging.info(f'List of connected sites in the model: {cbm.get_connected_sites()}')
        logging.info(f'List of disconnected sites in the model: {cbm.get_disconnected_sites()}')
        logging.info(f'List of facility ports in the model: {cbm.get_facility_ports()}')


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


def main():

    parser = argparse.ArgumentParser()
    # split into different mutually exclusive operations

    operations = parser.add_mutually_exclusive_group()
    operations.add_argument("-l", "--load", action="store_true",
                            help="load specified file into Neo4j (requires one or more -f, optional -g, -r)")
    parser.add_argument("-m", "--merge", action="store_true",
                        help="generate ADMs from provided ARMs and merge into CBM")
    operations.add_argument("-w", "--wipe", action="store_true",
                            help="wipe neo4j instance of all graphs (optional -g)")
    operations.add_argument("-e", "--enumerate", action="store_true",
                            help="enumerate all nodes in a graph in specified file"
                                 " assigning them unique GUIDs and save (requires -f and -o)")
    operations.add_argument("-s", "--save", action="store_true",
                            help="save a specific graph into a file (requires -o and -g)")
    parser.add_argument("-c", "--config", action="store", default=FIM_CONFIG_YAML,
                        help="provide alternative configuration file")
    parser.add_argument("-f", "--file", action="append",
                        help="GraphML file(s) to be operated on")
    parser.add_argument("-o", "--outfile", action="append",
                        help="output GraphML file(s)")
    parser.add_argument("-g", "--graph", action="append",
                        help="identifier of the graph in the Neo4j database")
    parser.add_argument("-r", "--direct", action="store_true",
                        help="load file directly without validation or any manipulations")
    parser.add_argument("-d", "--debug", action="count",
                        help="turn on debugging")
    parser.add_argument("-i", "--info", action="store_true",
                        help="used with -m/--merge, provide information about merged CBM")

    args = parser.parse_args()

    if args.debug is None:
        logging.basicConfig(level=logging.INFO)
    elif args.debug >= 1:
        logging.basicConfig(level=logging.DEBUG)

    try:
        with open(args.config, 'r') as config_file:
            yaml_config = yaml.safe_load(config_file)
    except IOError:
        logging.error(f"Unable to open config file {args.config}, exiting", file=sys.stderr)
        sys.exit(-1)

    if args.load:
        if args.file is None or len(args.file) == 0:
            logging.error("Must specify at least one -f option", file=sys.stderr)
            sys.exit(-1)
        if not args.direct and (args.graph is None or len(args.graph) != len(args.file)):
            logging.error("Must specify the same number of -g options as -f")
            sys.exit(-1)
        # load a file with a given id (or generated id)
        logging.info(f'Loading {args.file}')
        try:
            if not args.direct:
                for file, graph in zip(args.file, args.graph):
                    gid = load_file(filename=file, neo4j_config=yaml_config["neo4j"],
                                    graph_id=args.graph)
                    if gid is not None:
                        logging.info(f"Graph {file} successfully loaded with id {gid}")
                    else:
                        sys.exit(-1)
            else:
                for file in args.file:
                    gid = load_file_direct(filename=file, neo4j_config=yaml_config["neo4j"])
                    if gid is not None:
                        logging.info(f"Graph {file} successfully loaded with id {gid}")
                    else:
                        sys.exit(-1)
        except Exception as e:
            logging.error(f"Unable to load file {args.file} to Neo4j due to {e.args}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(-1)
    elif args.merge:
        if args.file is None or len(args.file) == 0:
            logging.error('Must specify at least one -f option', file=sys.stderr)
            sys.exit(-1)
        # merge specified files into a CBM
        try:
            merge_ads(neo4j_config=yaml_config["neo4j"], file_names=args.file,
                      delete_arms=True, delete_adms=True, info=args.info)
        except Exception as e:
            logging.error(f"Unable to merge files {args.file} to Neo4j due to {e.args}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(-1)
    elif args.wipe:
        # wipe one graph or whole database
        delete_graphs(neo4j_config=yaml_config["neo4j"], graph_id=args.graph)
        if args.graph is not None:
            logging.info(f"Deleted graph {args.graph} from the database")
        else:
            logging.info("Deleted all graphs from the database")
    elif args.enumerate:
        if args.file is None or len(args.file) == 0:
            logging.error('Must specify at least one -f option', file=sys.stderr)
            sys.exit(-1)
        if args.outfile is None or len(args.outfile) != len(args.file):
            logging.error('Must specify same number of -o options as -f options', file=sys.stderr)
            sys.exit(-1)
        # enumerate a file
        for infile, outfile in zip(args.file, args.outfile):
            logging.info(f"Enumerating nodes in {infile} and saving as {outfile}")
            enumerate_nodes(filename=infile, new_filename=outfile, neo4j_config=yaml_config["neo4j"])
    elif args.save:
        if args.outfile is None or len(args.outfile) != 1:
            logging.error('Must specify one -o option', file=sys.stderr)
            sys.exit(-1)
        # save graph
        if args.graph is None:
            logging.error("Must specify graph id (-g)", file=sys.stderr)
            sys.exit(-1)

        for file, graph in zip(args.outfile, args.graph):
            logging.info(f"Saving graph {graph} into file {file}")
            save_graph(outfile=file, graph_id=graph, neo4j_config=yaml_config["neo4j"])
    else:
        logging.error("Please specify one of -h, -l, -e or -w", file=sys.stderr)


if __name__ == "__main__":
    main()