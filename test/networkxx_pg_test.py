import unittest
from typing import Dict

import uuid
import json

import networkx as nx

import fim.graph.networkx_property_graph as nx_graph
from fim.graph.abc_property_graph import ABCPropertyGraphConstants, ABCPropertyGraph, GraphFormat


class NetworkXPropertyGraphTests(unittest.TestCase):

    GRAPH_FILE = "test/models/site-2-am-1broker-ad.graphml"
    NET_FILE_DEV = "test/models/Network-dev.graphml"
    NET_FILE = "test/models/network-am-ad.graphml"
    FAVORITE_NODES = ['Worker1', 'SwitchFabric1', 'GPU1', 'NIC1', 'NICSwitchFabric1']
    # this one set in file, should not be overwritten
    GIVEN_NODEID = '43BB2199-8248-48DE-86C5-E94112BFE401'

    def setUp(self) -> None:
        self.imp = nx_graph.NetworkXGraphImporter()
        graph_string = self.imp.enumerate_graph_nodes_to_string(graph_file=self.GRAPH_FILE)
        self.g = self.imp.import_graph_from_string(graph_string=graph_string)

    def tearDown(self) -> None:
        self.imp.delete_all_graphs()

    def _find_favorite_nodes(self, g=None) -> Dict[str, str]:
        # find a few favorite nodes
        ret = dict()
        if g is None:
            graph = self.g
        else:
            graph = g
        for f in self.FAVORITE_NODES:
            for n in graph.storage.get_graph(1).nodes:
                if graph.storage.get_graph(1).nodes[n].get('Name', None) == f:
                    ret[f] = graph.storage.get_graph(1).nodes[n]['NodeID']
        return ret

    def test_validate(self):
        """
        Load and validate a graph from file
        :return:
        """
        self.g.validate_graph()

    def test_basic(self):
        """
        Basic create/delete tests
        :return:
        """
        nx_imp = nx_graph.NetworkXGraphImporter()
        nx_pg = nx_graph.NetworkXPropertyGraph(graph_id="beef-beed", importer=nx_imp)
        nx_pg.add_node(node_id="dead-beef", label=ABCPropertyGraphConstants.CLASS_NetworkNode)
        nx_pg.add_node(node_id="beef-dead", label=ABCPropertyGraphConstants.CLASS_Component,
                       props={"some_property": "some_value"})
        _, props = nx_pg.get_node_properties(node_id='beef-dead')
        print(props)
        assert props.get('some_property', None) is not None
        nx_pg.unset_node_property(node_id='beef-dead', prop_name='some_property')
        _, props = nx_pg.get_node_properties(node_id='beef-dead')
        print(props)
        assert props.get('some_property', None) is None

        nx_pg.add_link(node_a='dead-beef', node_b='beef-dead', rel=ABCPropertyGraphConstants.REL_HAS,
                        props={'some_prop': 2})
        lt, props = nx_pg.get_link_properties(node_a='dead-beef', node_b='beef-dead')
        assert lt == ABCPropertyGraph.REL_HAS
        assert 'some_prop' in props.keys()
        nx_pg.unset_link_property(node_a='dead-beef', node_b='beef-dead', kind=ABCPropertyGraph.REL_HAS,
                                  prop_name='some_prop')
        lt, props = nx_pg.get_link_properties(node_a='dead-beef', node_b='beef-dead')
        assert 'some_prop' not in props.keys()
        nx_imp.delete_all_graphs()

    def test_node_properties(self):
        """
        Test node property manipulation
        :return:
        """
        favs = self._find_favorite_nodes()
        assert(favs.get('Worker1'), None) is not None
        worker1 = favs['Worker1']
        gpu1 = favs['GPU1']
        worker1_labels, worker1_props = self.g.get_node_properties(node_id=worker1)
        assert('NetworkNode' in worker1_labels)
        assert('Capacities' in worker1_props
               and worker1_props['Type'] == 'Server'
               and worker1_props['Model'] == 'Dell R7525')
        with self.assertRaises(nx_graph.PropertyGraphQueryException):
            self.g.update_node_property(node_id=worker1, prop_name='Class', prop_val='NewNetworkNode')

        with self.assertRaises(nx_graph.PropertyGraphQueryException):
            props=dict()
            props['Class'] = 'NewClass'
            self.g.update_node_properties(node_id=worker1, props=props)

        with self.assertRaises(nx_graph.PropertyGraphQueryException):
            self.g.update_nodes_property(prop_name='Class', prop_val='NewNetworkNode')

        self.g.update_node_property(node_id=worker1, prop_name='Type', prop_val='NewServer')
        _, worker1_props = self.g.get_node_properties(node_id=worker1)
        assert(worker1_props['Type'] == 'NewServer')

        new_props = dict()
        new_props['Type'] = 'Server'
        new_props['RandomProp'] = 'RandomVal'
        self.g.update_node_properties(node_id=worker1, props=new_props)
        _, worker1_props = self.g.get_node_properties(node_id=worker1)
        assert(worker1_props['Type'] == 'Server' and worker1_props['RandomProp'] == 'RandomVal')

        self.g.update_nodes_property(prop_name='RandomProp', prop_val='NewRandomVal')
        _, worker1_props = self.g.get_node_properties(node_id=worker1)
        assert(worker1_props['Type'] == 'Server' and worker1_props['RandomProp'] == 'NewRandomVal')

        self.g.unset_node_property(node_id=worker1, prop_name='RandomProp')
        _, worker1_props = self.g.get_node_properties(node_id=worker1)
        assert(worker1_props.get('RandomProp', None) is None)

    def test_edge_properties(self):
        favs = self._find_favorite_nodes()
        assert((favs.get('Worker1'), None) is not None)
        assert((favs.get('GPU1'), None) is not None)
        worker1 = favs['Worker1']
        gpu1 = favs['GPU1']
        link_class, link_props = self.g.get_link_properties(node_a=worker1, node_b=gpu1)
        assert(link_class == 'has')
        self.g.update_link_property(node_a=gpu1, node_b=worker1, prop_name='NewProp', prop_val='NewVal', kind='has')
        link_class, link_props = self.g.get_link_properties(node_a=worker1, node_b=gpu1)
        assert(link_props['NewProp'] == 'NewVal')
        props = dict()
        props['NewProp'] = 'NewNewVal'
        props['OtherProp'] = 'OtherVal'
        props['label'] = ''
        self.g.update_link_properties(node_a=worker1, node_b=gpu1, props=props, kind='has')
        link_class, link_props = self.g.get_link_properties(node_a=worker1, node_b=gpu1)
        assert(link_props['NewProp'] == 'NewNewVal' and link_props['OtherProp'] == 'OtherVal'
               and link_props['label'] == '')

    def test_clone(self):
        favs = self._find_favorite_nodes()
        assert((favs.get('Worker1'), None) is not None)
        worker1 = favs['Worker1']

        h = self.g.clone_graph(new_graph_id='dead-beef')
        assert(h.graph_id == 'dead-beef')
        extract_h = h.storage.extract_graph('dead-beef')
        count = 0
        for f in self.FAVORITE_NODES:
            for n in extract_h.nodes:
                if extract_h.nodes[n].get('Name', None) == f:
                    count = count + 1

        assert(count == 5)
        _, node_props = h.get_node_properties(node_id=worker1)

    def test_list_node_ids(self):
        favs = self._find_favorite_nodes()
        assert((favs.get('Worker1'), None) is not None)
        node_ids = self.g.list_all_node_ids()
        for f in favs.values():
            assert(f in node_ids)

        assert('43BB2199-8248-48DE-86C5-E94112BFE401' in node_ids)

    def test_serialize_graph(self):
        favs = self._find_favorite_nodes()
        assert((favs.get('Worker1'), None) is not None)
        worker1 = favs['Worker1']
        graph_string = self.g.serialize_graph()
        new_graph = self.imp.import_graph_from_string(graph_string=graph_string)
        count = 0
        # will see two copies since storage has all graphs
        for f in self.FAVORITE_NODES:
            for n in new_graph.storage.get_graph(1).nodes:
                if new_graph.storage.get_graph(1).nodes[n].get('Name', None) == f:
                    count = count + 1

        assert(count == 10)
        node_ids = new_graph.list_all_node_ids()
        assert ('43BB2199-8248-48DE-86C5-E94112BFE401' in node_ids)

    def test_delete_exists(self):
        assert(self.g.graph_exists())
        self.g.delete_graph()
        assert(not self.g.graph_exists())

    def test_shortest_path(self):
        favs = self._find_favorite_nodes()
        assert((favs.get('Worker1'), None) is not None)
        assert((favs.get('SwitchFabric1'), None) is not None)
        worker1 = favs['Worker1']
        sf1 = favs['SwitchFabric1']
        splist = self.g.get_nodes_on_shortest_path(node_a=worker1, node_z=sf1)
        assert(len(splist) == 6)
        edge_labels = ['has', 'connects', 'connects', 'connects', 'connects']
        edges = [(splist[i], splist[i+1], edge_labels[i]) for i in range(len(splist) - 1)]
        for e in edges:
            edge_kind, edge_props = self.g.get_link_properties(node_a=e[0], node_b=e[1])
            assert(edge_kind == e[2])

    def test_path_exists_with_hops(self):
        graph_string = self.imp.enumerate_graph_nodes_to_string(graph_file=self.NET_FILE_DEV)
        net_graph = self.imp.import_graph_from_string(graph_string=graph_string)

        renc_sw_node_id = "node+renc-data-sw:ip+192.168.11.3"
        lbnl_sw_node_id = "node+lbnl-data-sw:ip+192.168.13.3"
        hops = ["node+uky-data-sw:ip+192.168.12.3-ns"]
        path = net_graph.get_nodes_on_path_with_hops(node_a=renc_sw_node_id, node_z=lbnl_sw_node_id, hops=hops)

        assert(len(path) == 11)

        hops = ["node+max-data-sw:ip+192.168.12.3-ns"]
        path = net_graph.get_nodes_on_path_with_hops(node_a=renc_sw_node_id, node_z=lbnl_sw_node_id, hops=hops)

        assert (len(path) == 0)

    def test_first_neighbor(self):
        favs = self._find_favorite_nodes()
        assert((favs.get('Worker1'), None) is not None)
        assert((favs.get('GPU1'), None) is not None)
        worker1 = favs['Worker1']
        gpu1 = favs['GPU1']
        neighbors = self.g.get_first_neighbor(node_id=worker1, rel='has', node_label='Component')
        assert(gpu1 in neighbors)
        assert(len(neighbors) == 3)

    def test_second_neighbor(self):
        favs = self._find_favorite_nodes()
        assert((favs.get('Worker1'), None) is not None)
        assert((favs.get('GPU1'), None) is not None)
        worker1 = favs['Worker1']
        neighbor_list = self.g.get_first_and_second_neighbor(node_id=worker1, rel1='has', node1_label='Component',
                                                             rel2='connects', node2_label='SwitchFabric')
        assert(len(neighbor_list) == 1)
        node1_labels, node1_props = self.g.get_node_properties(node_id=neighbor_list[0][0])
        node2_labels, node2_props = self.g.get_node_properties(node_id=neighbor_list[0][1])
        assert('Component' in node1_labels)
        assert('SwitchFabric' in node2_labels)
        assert(node1_props['Name'] == 'NIC1')
        assert(node2_props['Name'] == 'NICSwitchFabric1')

    def test_match_and_merge(self):
        favs = self._find_favorite_nodes()
        assert((favs.get('SwitchFabric1'), None) is not None)
        sf1 = favs['SwitchFabric1']

        # count CPs on sf1
        original_cps = set(self.g.get_first_neighbor(node_id=sf1, rel='connects', node_label='ConnectionPoint'))

        # load network graph
        graph_string = self.imp.enumerate_graph_nodes_to_string(graph_file=self.NET_FILE)
        net_graph = self.imp.import_graph_from_string(graph_string=graph_string)
        common_node_id = 'F9DC6EEC-DE18-464D-92C2-7D87385B0B42'
        assert(common_node_id in self.g.list_all_node_ids())
        assert(common_node_id in net_graph.list_all_node_ids())

        cp_id = 'F9DC6EEC-DE18-464D-92C2-7D87385B0B42'

        matching_nodes = list(self.g.find_matching_nodes(other_graph=net_graph))
        assert(cp_id in matching_nodes)
        # get neighbors of CP in original graph
        original_neighbors = self.g.get_first_neighbor(node_id=cp_id,
                                                       rel='connects',
                                                       node_label='SwitchFabric')
        for n in matching_nodes:
            self.g.merge_nodes(node_id=n, other_graph=net_graph)

        _, node_props = self.g.get_node_properties(node_id=cp_id)

        new_neighbors = self.g.get_first_neighbor(node_id=cp_id,
                                                  rel='connects',
                                                  node_label='SwitchFabric')
        assert(original_neighbors == new_neighbors)

        net_graph.update_nodes_property(prop_name=self.g.GRAPH_ID, prop_val=self.g.graph_id)

        # count CPs on sf1 again
        new_cps = set(self.g.get_first_neighbor(node_id=sf1, rel='connects', node_label='ConnectionPoint'))

        assert(len(new_cps.difference(original_cps)) == 1)
        assert(new_cps.intersection(original_cps) == original_cps)

    def test_add_nodes(self):
        favs = self._find_favorite_nodes()
        assert ((favs.get('Worker1'), None) is not None)
        assert ((favs.get('NIC1'), None) is not None)
        assert ((favs.get('NICSwitchFabric1'), None) is not None)
        worker1 = favs['Worker1']
        sf1 = favs['NICSwitchFabric1']
        nic1 = favs['NIC1']
        new_sf_id = str(uuid.uuid4())
        max_id = max(list(self.g.storage.get_graph(self.g.graph_id).nodes))

        self.g.add_node(node_id=new_sf_id, label='SwitchFabric', props={'Name': 'NewSwitchFabric'})
        self.g.add_link(node_a=new_sf_id, rel='has', node_b=nic1)

        neighbors = self.g.get_first_neighbor(node_id=nic1, rel='has', node_label='SwitchFabric')
        self.assertEqual(len(neighbors), 2, "Should be 2")

        new_max_id = max(list(self.g.storage.get_graph(self.g.graph_id).nodes))
        self.assertEqual(max_id + 1, new_max_id)

    def test_string_serialize(self):
        graph_string = self.g.serialize_graph()
        self.assertTrue(len(graph_string) > 0)

        new_graph = self.imp.import_graph_from_string_direct(graph_string=graph_string)
        self.assertEqual(new_graph.importer, self.g.importer)
        self.assertEqual(new_graph.graph_id, self.g.graph_id)

        new_favs = self._find_favorite_nodes(new_graph)
        favs = self._find_favorite_nodes()
        self.assertTrue((new_favs.get('Worker1'), None) is not None)
        self.assertTrue((new_favs.get('GPU1'), None) is not None)
        self.assertEqual(new_favs['Worker1'], favs['Worker1'])

    def test_json_serialize(self):
        graph_string = self.g.serialize_graph(format=GraphFormat.JSON_NODELINK)
        json_object = json.loads(graph_string)
        assert(json_object["directed"] is False)
        assert(len(json_object["nodes"]) == 17)

    def test_cytoscape_serialize(self):
        graph_string = self.g.serialize_graph(format=GraphFormat.CYTOSCAPE)
        json_object = json.loads(graph_string)
        assert(json_object["directed"] is False)
        assert(len(json_object["elements"]["nodes"]) == 17)
