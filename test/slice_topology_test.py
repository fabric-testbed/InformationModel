import unittest
import json

import fim.user as f

from fim.graph.slices.neo4j_asm import Neo4jASM, Neo4jASMFactory
from fim.graph.neo4j_property_graph import Neo4jGraphImporter
from fim.slivers.gateway import Gateway
from fim.slivers.capacities_labels import Labels
from fim.user.model_element import TopologyException
from fim.slivers.measurement_data import MeasurementDataError
from fim.slivers.attached_components import ComponentType
from fim.slivers.component_catalog import ComponentModelType
from fim.slivers.network_service import ServiceType, MirrorDirection


class SliceTest(unittest.TestCase):

    neo4j = {"url": "neo4j://0.0.0.0:7687",
             "user": "neo4j",
             "pass": "password",
             "import_host_dir": "neo4j/imports/",
             "import_dir": "/imports"}

    def setUp(self) -> None:
        self.topo = f.ExperimentTopology()
        self.n4j_imp = Neo4jGraphImporter(url=self.neo4j["url"], user=self.neo4j["user"],
                                          pswd=self.neo4j["pass"],
                                          import_host_dir=self.neo4j["import_host_dir"],
                                          import_dir=self.neo4j["import_dir"])

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
        self.assertEqual(n3.details, 'some details')
        n3.details = 'other details'
        self.assertEqual(n3.details, 'other details')

        self.assertTrue('capacities' in n3.list_properties())
        self.assertEqual(n3.get_property('image_ref'), 'http://some.image')
        self.assertEqual(n3.image_ref, 'http://some.image')
        n3.image_ref = 'http://other.image'
        self.assertEqual(n3.image_ref, 'http://other.image')

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

        p1 = nic1.interfaces['nic1-p1']
        p1lab = p1.get_property('labels')
        self.assertEqual(p1lab.local_name, "p1")

        p1 = nic2.interfaces['nic2-p1']
        p1lab = p1.get_property('labels')
        self.assertEqual(p1lab.local_name, "p1")
        p1lab = p1.labels
        self.assertEqual(p1lab.local_name, "p1")

        p2 = nic2.interfaces['nic2-p2']
        p2lab = p2.get_property('labels')
        self.assertEqual(p2lab.local_name, "p2")
        p2lab = p2.labels
        self.assertEqual(p2lab.local_name, "p2")
        # check parent code
        assert(self.topo.get_parent_element(e=gpu1) == n1)
        assert(self.topo.get_parent_element(e=p1) == self.topo.get_parent_element(e=p2))

        # name uniqueness enforcement
        with self.assertRaises(TopologyException) as e:
            self.topo.add_node(name='Node1', site='UKY')

        # storage
        n1.add_storage(name='mystorage', labels=Labels(local_name='volume_name'))

        with self.assertRaises(Exception) as e:
            n1.remove_storage(name='wrong_name')

        n1.remove_storage(name='mystorage')

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
        assert(len(list(nic1.network_services.values())[0].interface_list) == 1)

        self.assertTrue(len(gpu1.interfaces) == 0)
        self.assertTrue(len(nic1.interfaces) == 1)
        nic1.interface_list[0].update_capacities(bw=50, unit=1)
        nic1.interface_list[0].update_labels(ipv4="192.168.1.12")
        self.assertEqual(nic1.interface_list[0].get_property('capacities').bw, 50)
        self.assertEqual(nic1.interface_list[0].capacities.unit, 1)
        self.assertEqual(nic1.interface_list[0].capacities.disk, 0)
        self.assertEqual(nic1.interface_list[0].labels.local_name, 'p1')
        self.assertEqual(n1.components['nic1'].interface_list[0].get_property('labels').ipv4, "192.168.1.12")
        self.assertEqual(n1.components['nic1'].interface_list[0].labels.ipv4, "192.168.1.12")

        # comparisons
        nic11 = n1.components['nic1']
        self.assertEqual(nic1, nic11)

        # interfaces and links
        self.assertEqual(len(self.topo.interface_list), 4)

        # no peers yet
        service_port = self.topo.interface_list[0].get_peers()
        self.assertEqual(service_port, None)

        self.topo.add_network_service(name='s1', nstype=f.ServiceType.L2Bridge, interfaces=self.topo.interface_list)
        print(self.topo.network_services['s1'])
        assert(self.topo.network_services['s1'].get_property('site') == 'RENC')

        # test peer code
        service_port = self.topo.interface_list[0].get_peers()[0]
        print(f'This is a service port {service_port}')
        self.assertEqual(service_port.get_property('type'), f.InterfaceType.ServicePort)
        # back to self
        self_port = service_port.get_peers()[0]
        self.assertEqual(self_port, self.topo.interface_list[0])

        # nodemap and unset
        n1.set_properties(node_map=('dead-beef-graph', 'dead-beef-node'))
        assert n1.get_property('node_map') == ('dead-beef-graph', 'dead-beef-node')
        n1.unset_property('node_map')
        assert n1.get_property('node_map') is None

        n1.node_map = ('dead-beef-graph', 'dead-beef-node')
        assert n1.node_map == ('dead-beef-graph', 'dead-beef-node')
        n1.unset_property('node_map')
        assert n1.get_property('node_map') is None

        self.assertEqual(len(self.topo.links), 4)
        # 4 services - 3 in NICs, one global
        self.assertEqual(len(self.topo.network_services), 4)
        # removal checks
        self.topo.remove_node(name='Node2')

        self.assertTrue(len(self.topo.links), 1)
        self.assertTrue(len(self.topo.nodes), 2)

        n1.remove_component(name='nic1')
        self.assertEqual(len(self.topo.links), 1)

        n3.remove_component(name='nic3')
        self.assertEqual(len(self.topo.links), 0)

        # GPU left
        self.assertTrue(len(n1.components), 1)

        # remove remaining nodes
        self.topo.remove_node(name='node3')
        self.topo.remove_node(name='Node1')
        self.assertEqual(len(self.topo.nodes), 0)
        self.assertEqual(len(self.topo.interface_list), 0)
        self.assertEqual(len(self.topo.links), 0)
        self.assertEqual(len(self.topo.network_services), 1)
        self.topo.remove_network_service(name='s1')
        self.assertEqual(len(self.topo.network_services), 0)

    def testNetworkServices(self):
        n1 = self.topo.add_node(name='Node1', site='RENC')
        n2 = self.topo.add_node(name='Node2', site='UKY', ntype=f.NodeType.Server)
        n3 = self.topo.add_node(name='Node3', site='RENC', management_ip='123.45.67.98',
                                image_ref='http://some.image', image_type='image type')

        # component checks
        n1.add_component(ctype=f.ComponentType.GPU, model='RTX6000', name='gpu1')
        n1.add_component(model_type=f.ComponentModelType.SharedNIC_ConnectX_6, name='nic1')
        n1.add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_6, name='nic4')
        n2.add_component(ctype=f.ComponentType.SmartNIC, model='ConnectX-6', name='nic2')
        nc3 = n3.add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic3',
                         boot_script='#!/bin/bash echo *')

        #tags on model elements (nodes, links, components, interfaces, network services)
        n1.tags = f.Tags('blue', 'heavy')
        self.assertTrue('blue' in n1.tags)
        # unset the tags
        n1.tags = None
        self.assertEqual(n1.tags, None)

        self.assertEqual(nc3.boot_script, '#!/bin/bash echo *')

        #boot script on nodes only
        n1.boot_script = """
        #!/bin/bash
        
        echo *
        """
        self.assertTrue("bash" in n1.boot_script)
        n1.boot_script = None
        self.assertIsNone(n1.boot_script)

        # measurement data on model elements (nodes, links, components, interfaces, network services)
        # can be set simply as json string (string length not to exceed 1M)
        n1.mf_data = json.dumps({'k1': ['some', 'measurement', 'configuration']})
        # you are guaranteed that whatever is on mf_data is JSON parsable and can be reconstituted into
        # an object
        mf_object1 = n1.mf_data
        self.assertTrue(mf_object1['k1'] == ['some', 'measurement', 'configuration'])
        # when nothing is set, it is None
        self.assertEqual(n2.mf_data, None)

        # you can also set it as MeasurementData object
        my_meas_data_object = {'key1': {'key2': ['v1', 2]}}
        n1.mf_data = f.MeasurementData(json.dumps(my_meas_data_object))

        # you can also just pass a JSON serializable object to MeasurementData constructor:
        n1.mf_data = f.MeasurementData(my_meas_data_object)
        # or even an serializable object itself. Either way the limit of 1M on the JSON string
        # length is enforced
        n1.mf_data = my_meas_data_object

        # for most uses, just set the object
        my_meas_data_object = {'key1': {'key2': ['some', 'config', 'info']}}
        n1.mf_data = my_meas_data_object

        # you get back your object (in this case a dict)
        self.assertTrue(isinstance(n1.mf_data, dict))
        mf_object2 = n1.mf_data
        self.assertTrue(mf_object2['key1'] == {'key2': ['some', 'config', 'info']})

        class MyClass:
            def __init__(self, val):
                self.val = val

        # this is not a valid object - json.dumps() will fail on it
        bad_meas_data_object = {'key1': MyClass(3)}
        with self.assertRaises(MeasurementDataError):
            n1.mf_data = bad_meas_data_object

        # also cannot use bad strings
        with self.assertRaises(MeasurementDataError):
            # you cannot assign non-json string to measurement data either as MeasurementData object
            n1.mf_data = f.MeasurementData("not parsable json")
        with self.assertRaises(MeasurementDataError):
            # or directly as string
            n1.mf_data = 'random string'

        # most settable properties can be unset by setting them to None (there are exceptions, like e.g. name)
        n1.mf_data = None
        self.assertIsNone(n1.mf_data)

        gpu1 = n1.components['gpu1']
        nic1 = n1.components['nic1']
        nic2 = n2.components['nic2']

        p1 = nic2.interfaces['nic2-p1']
        p2 = nic2.interfaces['nic2-p2']

        cap = f.Capacities(bw=50, unit=1)
        nic1.capacities = cap
        lab = f.Labels(ipv4="192.168.1.12")
        nic1.labels = lab
        caphints = f.CapacityHints(instance_type='blah')
        n1.capacity_hints = caphints

        # check capacities, hints labels on the graph
        n1p = self.topo.nodes['Node1']
        caphints1 = n1p.get_property('capacity_hints')
        assert(caphints.instance_type == caphints1.instance_type)
        caphints1 = n1p.capacity_hints
        assert (caphints.instance_type == caphints1.instance_type)

        #s1 = self.topo.add_network_service(name='s1', nstype=f.ServiceType.L2Bridge, interfaces=self.topo.interface_list)

        s1 = self.topo.add_network_service(name='s1', nstype=f.ServiceType.L2STS, interfaces=[n1.interface_list[0],
                                                                                              n2.interface_list[0],
                                                                                              n3.interface_list[0]])

        # facilities
        fac1 = self.topo.add_facility(name='RENCI-DTN', site='RENC', capacities=f.Capacities(bw=10))
        sfac = self.topo.add_network_service(name='s-fac', nstype=f.ServiceType.L2STS,
                                             interfaces=[fac1.interface_list[0],
                                             n1.interface_list[2]])

        self.assertEqual(s1.layer, f.Layer.L2)
        self.assertEqual(sfac.layer, f.Layer.L2)

        # this is typically done by orchestrator
        s1.gateway = Gateway(Labels(ipv4_subnet="192.168.1.0/24", ipv4="192.168.1.1", mac="00:11:22:33:44:55"))

        self.assertEqual(s1.gateway.gateway, "192.168.1.1")
        self.assertEqual(s1.gateway.subnet, "192.168.1.0/24")

        print(f'S1 has these interfaces: {s1.interface_list}')
        self.assertEqual(len(s1.interface_list), 3)
        self.topo.validate()

        s1p = self.topo.network_services['s1']

        print(f'S1 has these interfaces: {s1p.interface_list}')

        s1.disconnect_interface(interface=p1)

        print(f'S1 has these interfaces: {s1.interface_list}')
        self.assertEqual(len(s1.interface_list), 2)

        # validate the topology
        self.topo.validate()

        self.topo.remove_network_service('s1')

        with self.assertRaises(TopologyException):
            # connection conflict because we have an interface connecting to s-fac
            s2 = self.topo.add_network_service(name='s2', nstype=f.ServiceType.L2PTP,
                                               interfaces=self.topo.interface_list)

        s2 = self.topo.add_network_service(name='s2', nstype=f.ServiceType.L2PTP,
                                           interfaces=[n1.interface_list[1],
                                                       n2.interface_list[1]])
        self.assertEqual(len(s2.interface_list), 2)
        print(f'S2 has these interfaces: {s2.interface_list}')

        print(f'There are {self.topo.links}  links left in topology')
        self.assertEqual(len(self.topo.links), 4)
        print(f'There are {self.topo.network_services} Network services  in topology')
        self.assertEqual(len(self.topo.network_services), 7)
        self.topo.validate()
        self.topo.remove_network_service('s2')
        self.topo.validate()
        self.assertEqual(len(self.topo.network_services), 6)
        n1.remove_component('nic1')
        self.assertEqual(len(self.topo.network_services), 5)

        #self.topo.add_link(name='l3', ltype=f.LinkType.L2Bridge, interfaces=self.topo.interface_list)

    def testDeepSliver(self):
        self.topo.add_node(name='n1', site='RENC')
        self.topo.nodes['n1'].add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic1')
        deep_sliver = self.topo.graph_model.build_deep_node_sliver(node_id=self.topo.nodes['n1'].node_id)
        self.assertNotEqual(deep_sliver, None)
        self.assertNotEqual(deep_sliver.attached_components_info, None)
        self.assertNotEqual(deep_sliver.attached_components_info.devices['nic1'].network_service_info, None)

        # note that names given to NetworkServices attached to NICs have GUIDs in them - they must be unique
        network_service_name = deep_sliver.attached_components_info.devices['nic1'].network_service_info.get_network_service_names()[0]
        self.assertNotEqual(deep_sliver.attached_components_info.
                            devices['nic1'].network_service_info.network_services[network_service_name].interface_info, None)
        self.assertEqual(len(deep_sliver.attached_components_info.
                             devices['nic1'].network_service_info.network_services[network_service_name].
                             interface_info.interfaces), 1)
        self.topo.add_network_service(name='s1', nstype=f.ServiceType.L2Bridge, interfaces=self.topo.interface_list)
        deep_sliver1 = self.topo.graph_model.build_deep_ns_sliver(node_id=self.topo.network_services['s1'].node_id)
        self.assertNotEqual(deep_sliver1, None)
        self.assertNotEqual(deep_sliver1.interface_info, None)
        self.assertEqual(len(deep_sliver1.interface_info.interfaces), 1)
        print(f'Network deep sliver interfaces: {deep_sliver1.interface_info.interfaces}')

    def testSerDes(self):
        self.topo.add_node(name='n1', site='RENC')
        self.topo.nodes['n1'].add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic1')
        gs = self.topo.serialize()
        self.topo.graph_model.importer.delete_all_graphs()
        t1 = f.ExperimentTopology(graph_string=gs)
        self.assertEqual(t1.graph_model.graph_id, self.topo.graph_model.graph_id)
        self.assertTrue('n1' in t1.nodes.keys())
        self.assertTrue('nic1' in t1.nodes['n1'].components.keys())

    def testSerDes1(self):
        # more thorough serialization-deserialization test
        self.topo.add_node(name='n1', site='RENC')
        self.topo.nodes['n1'].add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic1')
        self.topo.add_node(name='n2', site='UKY')
        self.topo.nodes['n2'].add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic1')
        self.topo.add_network_service(name='s1', nstype=f.ServiceType.L2STS, interfaces=self.topo.interface_list)
        gs = self.topo.serialize()
        self.topo.graph_model.importer.delete_all_graphs()
        t1 = f.ExperimentTopology(graph_string=gs)
        self.assertEqual(t1.graph_model.graph_id, self.topo.graph_model.graph_id)
        self.assertTrue('n1' in t1.nodes.keys())
        self.assertTrue('nic1' in t1.nodes['n1'].components.keys())
        print(f'LIST COMPONENTS of n1 {t1.nodes["n1"].components}')
        print(f'LIST COMPONENTS of n2 {t1.nodes["n2"].components}')

    def testSerDes2(self):
        # more thorough serialization-deserialization test
        topo = f.ExperimentTopology()
        topo.add_node(name='n1', site='RENC')
        cap = f.Capacities(core=1, unit=2)
        topo.nodes['n1'].capacities = cap
        topo.nodes['n1'].add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic1')
        topo.add_node(name='n2', site='UKY')
        topo.nodes['n2'].add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic2')
        topo.add_network_service(name='s1', nstype=f.ServiceType.L2STS, interfaces=topo.interface_list)
        slice_graph = topo.serialize()
        print('\n\n\nINITIAL TOPO')
        print(topo)

        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)

        # Serialize ASM
        orch_graph = asm_graph.serialize_graph()

        # Reload Experiment topology from serialized ASM
        t1 = f.ExperimentTopology(graph_string=orch_graph)

        print('\n\n\nRELOADED TOPO')
        print(t1)
        self.assertTrue('n1' in t1.nodes.keys())
        self.assertTrue('nic1' in t1.nodes['n1'].components.keys())
        cap1 = t1.nodes['n1'].capacities
        self.assertEqual(cap1.core, 1)
        self.assertEqual(cap1.unit, 2)

        print(f'LIST COMPONENTS of n1 {t1.nodes["n1"].components}')
        print(f'LIST COMPONENTS of n2 {t1.nodes["n2"].components}')
        self.n4j_imp.delete_all_graphs()

    def testBasicOneSiteSlice(self):
        # create a basic slice and export to GraphML and JSON
        self.topo.add_node(name='n1', site='RENC', ntype=f.NodeType.VM)
        self.topo.add_node(name='n2', site='RENC')
        self.topo.add_node(name='n3', site='RENC')
        self.topo.nodes['n1'].add_component(model_type=f.ComponentModelType.SharedNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n1'].add_component(model_type=f.ComponentModelType.NVME_P4510, name='drive1')
        self.topo.nodes['n2'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n2'].add_component(model_type=f.ComponentModelType.GPU_RTX6000, name='gpu1')
        self.topo.nodes['n3'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_5, name='nic1')
        self.topo.add_network_service(name='bridge1', nstype=f.ServiceType.L2Bridge,
                                      interfaces=self.topo.interface_list)
        self.topo.serialize(file_name='single-site.graphml')
        self.topo.serialize(file_name='single-site.json', fmt=f.GraphFormat.JSON_NODELINK)
        self.topo.serialize(file_name='single-site.cyt.json', fmt=f.GraphFormat.CYTOSCAPE)
        self.topo.validate()

    def testBasicTwoSiteSlice(self):
        # create a basic slice and export to GraphML and JSON
        self.topo.add_node(name='n1', site='RENC', ntype=f.NodeType.VM)
        self.topo.add_node(name='n2', site='RENC')
        self.topo.add_node(name='n3', site='UKY')
        self.topo.nodes['n1'].add_component(model_type=f.ComponentModelType.SharedNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n1'].add_component(model_type=f.ComponentModelType.NVME_P4510, name='drive1')
        self.topo.nodes['n2'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n2'].add_component(model_type=f.ComponentModelType.GPU_RTX6000, name='gpu1')
        self.topo.nodes['n3'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_5, name='nic1')
        self.topo.add_network_service(name='bridge1', nstype=f.ServiceType.L2STS,
                                      interfaces=self.topo.interface_list)
        self.topo.serialize(file_name='two-site.graphml')
        self.topo.serialize(file_name='two-site.json', fmt=f.GraphFormat.JSON_NODELINK)
        self.topo.serialize(file_name='two-site.cyt.json', fmt=f.GraphFormat.CYTOSCAPE)
        self.topo.validate()

    def testL3Service(self):
        self.topo.add_node(name='n1', site='RENC', ntype=f.NodeType.VM)
        self.topo.add_node(name='n2', site='RENC')
        self.topo.add_node(name='n3', site='UKY')
        self.topo.nodes['n1'].add_component(model_type=f.ComponentModelType.SharedNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n2'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n3'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_5, name='nic1')

        # one L3 service per site
        s1 = self.topo.add_network_service(name='v4UKY', nstype=f.ServiceType.FABNetv4,
                                           interfaces=self.topo.nodes['n3'].interface_list)
        s2 = self.topo.add_network_service(name='v4RENC', nstype=f.ServiceType.FABNetv4,
                                           interfaces=[self.topo.nodes['n1'].interface_list[0],
                                                  self.topo.nodes['n2'].interface_list[0]])
        # adding interfaces belonging to nodes from diffeerent sites is a no no
        with self.assertRaises(TopologyException):
            self.topo.add_network_service(name='bad_service', nstype=f.ServiceType.FABNetv4,
                                          interfaces=self.topo.interface_list)
        # site property is set automagically
        self.assertEqual(s1.site, 'UKY')
        self.assertEqual(s2.site, 'RENC')
        self.topo.validate()

    def testPortMirrorService(self):
        t = self.topo

        n1 = t.add_node(name='n1', site='MASS')
        n1.add_component(name='nic1', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n2 = t.add_node(name='n2', site='RENC')
        n2.add_component(name='nic1', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n3 = t.add_node(name='n3', site='RENC')
        n3.add_component(name='nic1', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        with self.assertRaises(TopologyException) as e:
            t.add_network_service(name='ns1', nstype=ServiceType.PortMirror,
                                  interfaces=[n1.interface_list[0], n2.interface_list[0]])
        t.add_network_service(name='ns1', nstype=ServiceType.L2STS,
                              interfaces=[n1.interface_list[0], n2.interface_list[0]])
        t.add_port_mirror_service(name='pm1', from_interface_name='blahname',
                                  to_interface=n3.interface_list[0])
        n3.add_storage(name='st1', labels=Labels(local_name='volume_x'))

        self.assertEqual(t.network_services['pm1'].mirror_port, 'blahname')
        self.assertEqual(t.network_services['pm1'].mirror_direction, MirrorDirection.Both)
        t.validate()
        t.remove_network_service(name='pm1')