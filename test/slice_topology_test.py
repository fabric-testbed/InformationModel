import unittest

import fim.user as f


class SliceTest(unittest.TestCase):

    def setUp(self) -> None:
        self.topo = f.ExperimentTopology()

    def tearDown(self) -> None:
        pass

    def testNodesAndComponents(self):
        n1 = self.topo.add_node(name='Node1', site='RENC')
        n2 = self.topo.add_node(name='Node2', site='RENC', ntype=f.NodeType.Server)
        n3 = self.topo.add_node(name='Node3', site='RENC', management_ip='123.45.67.98',
                                image_ref='http://some.image', image_type='image type')

        n3.rename('node3')
        assert(self.topo.nodes['Node1'] is not None)
        assert(self.topo.nodes['Node2'] is not None)
        assert(self.topo.nodes['node3'] is not None)
        with self.assertRaises(KeyError):
            n = self.topo.nodes['Node3']

        # properties checks
        n3.set_properties(details='some details')
        self.assertEqual(n3.get_property('details'), 'some details')

        self.assertTrue('capacities' in n3.list_properties())
        self.assertEqual(n3.get_property('image_ref'), 'http://some.image')

        # component checks
        n1.add_component(ctype=f.ComponentType.GPU, model='RTX6000', name='gpu1')
        n1.add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic1')
        n2.add_component(ctype=f.ComponentType.SmartNIC, model='ConnectX-6', name='nic2')
        n3.add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic3')

        self.assertEqual(len(n1.components), 2)
        self.assertEqual(len(n2.components), 1)
        gpu1 = n1.components['gpu1']
        nic1 = n1.components['nic1']
        nic2 = n2.components['nic2']

        # name uniqueness enforcement
        with self.assertRaises(AssertionError) as e:
            self.topo.add_node(name='Node1', site='UKY')

        gpu1_1 = n2.add_component(ctype=f.ComponentType.GPU, model='RTX6000', name='gpu1')
        n2.remove_component(name='gpu1')
        nic1_1 = n2.add_component(ctype=f.ComponentType.SmartNIC, model='ConnectX-6', name='nic1')
        n2.remove_component(name='nic1')

        # check various modes of access
        assert(self.topo.nodes['Node1'] == n1)
        assert(self.topo.nodes['Node1'].components['gpu1'] == gpu1)
        assert(len(self.topo.interface_list) == 4)
        assert(len(nic1.interface_list) == 1)
        assert(len(nic2.interface_list) == 2)
        assert(len(list(nic1.switch_fabrics.values())[0].interface_list) == 1)

        self.assertTrue(len(gpu1.interfaces) == 0)
        self.assertTrue(len(nic1.interfaces) == 1)
        cap = f.Capacities()
        cap.set_fields(bw=50, unit=1)
        nic1.set_properties(capacities=cap)
        lab = f.Labels()
        lab.set_fields(ipv4="192.168.1.12")
        nic1.set_properties(labels=lab)
        self.assertEqual(nic1.get_property('capacities').bw, 50)
        self.assertEqual(nic1.get_property('capacities').unit, 1)
        self.assertEqual(nic1.get_property('capacities').disk, 0)
        self.assertEqual(n1.components['nic1'].get_property('labels').ipv4, "192.168.1.12")

        # comparisons
        nic11 = n1.components['nic1']
        self.assertEqual(nic1, nic11)

        # interfaces and links
        self.assertEqual(len(self.topo.interface_list), 4)

        self.topo.add_link(name='l1', ltype=f.LinkType.Wave, interfaces=self.topo.interface_list)

        with self.assertRaises(AssertionError) as e:
            self.topo.add_link(name='l1', ltype=f.LinkType.Wave, interfaces=self.topo.interface_list)

        #print(self.topo)

        # nodemap and unset
        n1.set_properties(node_map=('dead-beef-graph', 'dead-beef-node'))
        assert n1.get_property('node_map') == ('dead-beef-graph', 'dead-beef-node')
        n1.unset_property('node_map')
        assert n1.get_property('node_map') is None

        self.assertEqual(len(self.topo.links), 1)
        # removal checks
        self.topo.remove_node(name='Node2')

        self.assertTrue(len(self.topo.links), 1)
        self.assertTrue(len(self.topo.nodes), 2)

        # should remove the link since only one interface left
        n1.remove_component(name='nic1')
        self.assertEqual(len(self.topo.links), 0)
        # GPU left
        self.assertTrue(len(n1.components), 1)
        self.assertTrue(len(self.topo.interface_list), 1)
        # remove remaining nodes
        self.topo.remove_node(name='node3')
        self.topo.remove_node(name='Node1')
        self.assertEqual(len(self.topo.nodes), 0)
        self.assertEqual(len(self.topo.interface_list), 0)
        self.assertEqual(len(self.topo.links), 0)

    def testDeepSliver(self):
        self.topo.add_node(name='n1', site='RENC')
        self.topo.nodes['n1'].add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic1')
        deep_sliver = self.topo.graph_model.build_deep_node_sliver(node_id=self.topo.nodes['n1'].node_id)
        self.assertNotEqual(deep_sliver, None)
        self.assertNotEqual(deep_sliver.attached_components_info, None)
        self.assertNotEqual(deep_sliver.attached_components_info.devices['nic1'].switch_fabric_info, None)
        self.assertNotEqual(deep_sliver.attached_components_info.
                            devices['nic1'].switch_fabric_info.switch_fabrics['nic1-l2sf'].interface_info, None)
        self.assertEqual(len(deep_sliver.attached_components_info.
                             devices['nic1'].switch_fabric_info.switch_fabrics['nic1-l2sf'].
                             interface_info.interfaces), 1)

    def testSerDes(self):
        self.topo.add_node(name='n1', site='RENC')
        self.topo.nodes['n1'].add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic1')
        gs = self.topo.serialize()
        self.topo.graph_model.importer.delete_all_graphs()
        t1 = f.ExperimentTopology(graph_string=gs)
        self.assertEqual(t1.graph_model.graph_id, self.topo.graph_model.graph_id)
        self.assertTrue('n1' in t1.nodes.keys())
        self.assertTrue('nic1' in t1.nodes['n1'].components.keys())
