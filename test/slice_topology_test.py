import datetime
import unittest
import json
import os

import fim.user as f

from fim.graph.slices.neo4j_asm import Neo4jASM, Neo4jASMFactory
from fim.graph.neo4j_property_graph import Neo4jGraphImporter
from fim.slivers.gateway import Gateway
from fim.slivers.capacities_labels import Labels
from fim.user.model_element import TopologyException
from fim.slivers.json_data import MeasurementDataError, UserDataError, LayoutDataError
from fim.logging.log_collector import LogCollector
from fim.slivers.component_catalog import ComponentModelType
from fim.slivers.network_service import ServiceType, MirrorDirection
from fim.slivers.maintenance_mode import MaintenanceInfo, MaintenanceState, \
    MaintenanceEntry, MaintenanceModeException
from fim.slivers.capacities_labels import Capacities


class SliceTest(unittest.TestCase):

    neo4j = {"url": "neo4j://0.0.0.0:7687",
             "user": "neo4j",
             "pass": "password",
             "import_host_dir": "neo4j/imports",
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
        # validate sets node names on services
        self.topo.validate()
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

        # validate
        self.topo.validate()

        self.assertTrue(len(self.topo.links), 1)
        self.assertTrue(len(self.topo.nodes), 2)

        n1.remove_component(name='nic1')
        self.assertEqual(len(self.topo.links), 1)
        # validate
        self.topo.validate()

        # GPU left
        self.assertEqual(len(n1.components), 1)

        n1.remove_component('gpu1')
        self.topo.validate()

        # no components left
        self.assertEqual(len(n1.components), 0)

        n3.remove_component(name='nic3')
        self.assertEqual(len(self.topo.links), 0)

        # 0 interfaces left attached to bridge
        with self.assertRaises(TopologyException):
            self.topo.validate()

        self.assertEqual(len(self.topo.network_services), 1)
        self.topo.remove_network_service(name='s1')
        self.assertEqual(len(self.topo.network_services), 0)

        self.topo.validate()

        # remove remaining nodes
        self.topo.remove_node(name='node3')
        self.topo.remove_node(name='Node1')
        self.assertEqual(len(self.topo.nodes), 0)
        self.assertEqual(len(self.topo.interface_list), 0)
        self.assertEqual(len(self.topo.links), 0)

        self.n4j_imp.delete_all_graphs()

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

        # flags on model elements
        n1.flags = f.Flags(auto_config=True, ipv4_management=True)
        self.assertTrue(n1.flags.auto_config)
        self.assertTrue(n1.flags.ipv4_management)
        n1.flags = None
        self.assertEqual(n1.flags, None)

        self.assertEqual(nc3.boot_script, '#!/bin/bash echo *')

        #boot script on nodes only
        n1.boot_script = """
        #!/bin/bash
        
        echo *
        """
        self.assertTrue("bash" in n1.boot_script)
        n1.boot_script = None
        self.assertIsNone(n1.boot_script)

        gpu1 = n1.components['gpu1']
        nic1 = n1.components['nic1']
        nic2 = n2.components['nic2']

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
        p1 = n1.interface_list[0]

        # facilities
        fac1 = self.topo.add_facility(name='RENCI-DTN', site='RENC', capacities=f.Capacities(bw=10),
                                      labels=f.Labels(vlan='100'))
        # facility needs to be connected via a service to something else
        sfac = self.topo.add_network_service(name='s-fac', nstype=f.ServiceType.L2STS,
                                             interfaces=[fac1.interface_list[0],
                                                         n1.interface_list[2]])

        self.topo.validate()
        self.assertEqual(s1.layer, f.Layer.L2)
        print(fac1.network_services['RENCI-DTN-ns'].labels)
        self.assertEqual(fac1.network_services['RENCI-DTN-ns'].layer, f.Layer.L2)
        self.assertEqual(fac1.interface_list[0].labels.vlan, '100')

        # this is typically done by orchestrator
        s1.gateway = Gateway(Labels(ipv4_subnet="192.168.1.0/24", ipv4="192.168.1.1", mac="00:11:22:33:44:55"))

        self.assertEqual(s1.gateway.gateway, "192.168.1.1")
        self.assertEqual(s1.gateway.subnet, "192.168.1.0/24")

        print(f'S1 has these interfaces: {s1.interface_list}')
        self.assertEqual(len(s1.interface_list), 3)
        self.topo.validate()

        # Import it in the neo4j as ASM
        slice_graph = self.topo.serialize()
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        asm_graph.validate_graph()
        self.n4j_imp.delete_all_graphs()

        s1p = self.topo.network_services['s1']

        print(f'S1 has these interfaces: {s1p.interface_list}')
        print(f'Disconnecting {p1} from S1')
        s1p.disconnect_interface(interface=p1)
        print(f'Now S1 has these interfaces: {s1p.interface_list}')
        self.assertEqual(len(s1p.interface_list), 2)

        # validate the topology
        self.topo.validate()

        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        asm_graph.validate_graph()
        self.n4j_imp.delete_all_graphs()

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
        self.n4j_imp.delete_all_graphs()

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
        self.n4j_imp.delete_all_graphs()

    def testSerDes(self):
        self.topo.add_node(name='n1', site='RENC')
        self.topo.nodes['n1'].add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic1')
        gs = self.topo.serialize()
        self.topo.graph_model.importer.delete_all_graphs()
        t1 = f.ExperimentTopology(graph_string=gs)
        self.assertEqual(t1.graph_model.graph_id, self.topo.graph_model.graph_id)
        self.assertTrue('n1' in t1.nodes.keys())
        self.assertTrue('nic1' in t1.nodes['n1'].components.keys())
        self.n4j_imp.delete_all_graphs()

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
        self.n4j_imp.delete_all_graphs()

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

    def testSerDes3(self):
        # multi-format serialization-deserialization test
        topo = f.ExperimentTopology()
        topo.add_node(name='n1', site='RENC')
        cap = f.Capacities(core=1, unit=2)
        topo.nodes['n1'].capacities = cap
        topo.nodes['n1'].add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic1')
        topo.add_node(name='n2', site='UKY')
        topo.nodes['n2'].add_component(ctype=f.ComponentType.SharedNIC, model='ConnectX-6', name='nic2')
        topo.add_network_service(name='s1', nstype=f.ServiceType.L2STS, interfaces=topo.interface_list)
        slice_graph = topo.serialize(fmt=f.GraphFormat.JSON_NODELINK)

        print(f'NODE_LINK {slice_graph=}')

        t1 = f.ExperimentTopology(graph_string=slice_graph)

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

        # Import it in the neo4j as ASM
        slice_graph = self.topo.serialize()
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        asm_graph.validate_graph()
        self.n4j_imp.delete_all_graphs()

    def testBasicOneSiteSliceNeo4jImp(self):
        # Produce same graph as above but using Neo4j instead of NetworkX and serialize to file
        # This is used to compare serializations between NetworkX and Neo4j
        topo = f.ExperimentTopology(importer=self.n4j_imp)
        topo.add_node(name='n1', site='RENC', ntype=f.NodeType.VM)
        topo.add_node(name='n2', site='RENC')
        topo.add_node(name='n3', site='RENC')
        topo.nodes['n1'].add_component(model_type=f.ComponentModelType.SharedNIC_ConnectX_6, name='nic1')
        topo.nodes['n1'].add_component(model_type=f.ComponentModelType.NVME_P4510, name='drive1')
        topo.nodes['n2'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_6, name='nic1')
        topo.nodes['n2'].add_component(model_type=f.ComponentModelType.GPU_RTX6000, name='gpu1')
        topo.nodes['n3'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_5, name='nic1')
        topo.add_network_service(name='bridge1', nstype=f.ServiceType.L2Bridge,
                                      interfaces=topo.interface_list)
        topo.serialize(file_name='single-site-neo4jimp.graphml')
        topo.validate()
        os.unlink('single-site-neo4jimp.graphml')

    def testBasicTwoSiteSlice(self):
        # create a basic slice and export to GraphML and JSON
        self.topo.add_node(name='n1', site='RENC', ntype=f.NodeType.VM, capacities=Capacities(core=4, disk=10))
        self.topo.add_node(name='n2', site='RENC', capacities=Capacities(core=8, ram=2))
        self.topo.add_node(name='n3', site='UKY', capacities=Capacities(core=8, ram=2))
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

        # test log on topology
        lc = LogCollector()
        lc.collect_resource_attributes(source=self.topo)
        print('----LOG TOPO TEST-----')
        print(f'with {lc}')
        print('----END TOPO LOG TEST-----')
        self.assertEqual(lc.attributes['vm_count'], 3)
        self.assertIn(('L2STS', 0), lc.attributes['services'])
        self.assertIn('UKY', lc.attributes['sites'])
        self.assertIn('RENC', lc.attributes['sites'])
        self.assertEqual(lc.attributes['core_count'], 20)

        # test log on Node
        lc = LogCollector()
        lc.collect_resource_attributes(source=self.topo.nodes['n1'])
        self.assertEqual(lc.attributes['core_count'], 4)
        self.assertEqual(lc.attributes['vm_count'], 1)
        self.assertIn('RENC', lc.attributes['sites'])
        print('----LOG NODE TEST-----')
        print(f'with {lc}')
        print('----END NODE LOG TEST-----')

        # test log on NodeSliver
        lc = LogCollector()
        lc.collect_resource_attributes(source=self.topo.nodes['n1'].get_sliver())
        self.assertEqual(lc.attributes['core_count'], 4)
        self.assertEqual(lc.attributes['vm_count'], 1)
        self.assertIn('RENC', lc.attributes['sites'])
        print('----LOG NODE SLIVER TEST-----')
        print(f'with {lc}')
        print('----END NODE LOG SLIVER TEST-----')

        # Import it in the neo4j as ASM
        slice_graph = self.topo.serialize()
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        asm_graph.validate_graph()
        self.n4j_imp.delete_all_graphs()

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
        # site property is set automagically by validate
        # NOTE: site property NO LONGER SET BY CONSTRUCTOR
        self.topo.validate()
        self.assertEqual(s1.site, 'UKY')
        self.assertEqual(s2.site, 'RENC')

        slice_graph = self.topo.serialize()

        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        asm_graph.validate_graph()
        self.n4j_imp.delete_all_graphs()

    '''
    def testL3ServiceFail(self):
        """
        Test validaton of max 1 L3 service per site of a given type
        No longer a valid test case as validation constraint number of Fabnets per site was removed
        """
        self.topo.add_node(name='n1', site='RENC', ntype=f.NodeType.VM)
        self.topo.add_node(name='n2', site='RENC')
        self.topo.add_node(name='n3', site='UKY')
        self.topo.nodes['n1'].add_component(model_type=f.ComponentModelType.SharedNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n2'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n3'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_5, name='nic1')

        s1 = self.topo.add_network_service(name='v4UKY', nstype=f.ServiceType.FABNetv4,
                                           interfaces=self.topo.nodes['n3'].interface_list)
        s2 = self.topo.add_network_service(name='v4RENC', nstype=f.ServiceType.FABNetv4,
                                           interfaces=[self.topo.nodes['n1'].interface_list[0]])
        # this one is a no-no - should attach to s2 instead
        s3 = self.topo.add_network_service(name='v4RENCbad', nstype=f.ServiceType.FABNetv4,
                                           interfaces=[self.topo.nodes['n2'].interface_list[0]])

        # site property is set automagically by validate
        with self.assertRaises(TopologyException):
            self.topo.validate()

        slice_graph = self.topo.serialize()

        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        # the following validation just uses cypher or networkx_query and is not as capable
        # as self.topo.validate() but is much faster
        asm_graph.validate_graph()
        self.n4j_imp.delete_all_graphs()
    '''

    def testL3ServiceFail2(self):
        """
        Test validaton of L3 service required per site
        """
        self.topo.add_node(name='n1', site='RENC', ntype=f.NodeType.VM)
        self.topo.add_node(name='n2', site='RENC')
        self.topo.add_node(name='n3', site='UKY')
        self.topo.nodes['n1'].add_component(model_type=f.ComponentModelType.SharedNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n2'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n3'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_5, name='nic1')

        s1 = self.topo.add_network_service(name='globalL3', nstype=f.ServiceType.FABNetv4,
                                           interfaces=[self.topo.nodes['n1'].interface_list[0],
                                                       self.topo.nodes['n2'].interface_list[0],
                                                       self.topo.nodes['n3'].interface_list[0]])

        # site property is set automagically by validate
        with self.assertRaises(TopologyException):
            self.topo.validate()

        slice_graph = self.topo.serialize()

        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        # the following validation just uses cypher or networkx_query and is not as capable
        # as self.topo.validate() but is much faster
        asm_graph.validate_graph()
        self.n4j_imp.delete_all_graphs()

    def testSubInterfaces_1(self):
        n1 = self.topo.add_node(name='Node1', site='RENC')
        n1_nic1 = n1.add_component(ctype=f.ComponentType.SmartNIC, model='ConnectX-6', name='nic1')
        n1_nic1_interface1 = n1_nic1.interface_list[0]

        with self.assertRaises(TopologyException):
            n1_nic1_interface1.add_child_interface(name="child1")

        n1_nic1_interface1.add_child_interface(name="child1", labels=Labels(vlan="100"))

        with self.assertRaises(TopologyException):
            n1_nic1_interface1.add_child_interface(name="child1", labels=Labels(vlan="200"))

        with self.assertRaises(TopologyException):
            n1_nic1_interface1.add_child_interface(name="child2", labels=Labels(vlan="100"))

        n1_nic1_interface1.add_child_interface(name="child2", labels=Labels(vlan="200"))

        self.assertEqual(len(n1_nic1_interface1.interface_list), 2)
        self.assertEqual(n1_nic1_interface1.interface_list[0].type, f.InterfaceType.SubInterface)
        self.assertEqual(n1_nic1_interface1.interface_list[1].type, f.InterfaceType.SubInterface)

        self.topo.validate()

        slice_graph = self.topo.serialize()
        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        asm_graph.validate_graph()
        for n in asm_graph.get_all_network_nodes():
            node_sliver = asm_graph.build_deep_node_sliver(node_id=n)
            print(node_sliver)
            for c in node_sliver.attached_components_info.devices.values():
                print(f"\t{c}")
                for ns in c.network_service_info.network_services.values():
                    print(f"\t\t{ns}")
                    for ifs in ns.interface_info.interfaces.values():
                        print(f"\t\t\t{ifs}")
                        if "p1" in ifs.get_name():
                            self.assertTrue(ifs.interface_info is not None)
                            for cifs in ifs.interface_info.interfaces.values():
                                self.assertEqual(cifs.get_type(), f.InterfaceType.SubInterface)
                                print(f"\t\t\t\t{cifs}")

        self.n4j_imp.delete_all_graphs()

    def testSubInterfaces(self):
        n1 = self.topo.add_node(name='Node1', site='RENC')
        n2 = self.topo.add_node(name='Node2', site='RENC')
        n1_nic1 = n1.add_component(ctype=f.ComponentType.SmartNIC, model='ConnectX-6', name='nic1')
        n1_nic1_interface1 = n1_nic1.interface_list[0]
        n1_nic1_interface1.add_child_interface(name="child1", labels=Labels(vlan="100"))

        self.assertTrue(len(n1_nic1_interface1.interface_list) != 0)
        self.assertEqual(n1_nic1_interface1.interface_list[0].type, f.InterfaceType.SubInterface)

        n2_nic1 = n2.add_component(ctype=f.ComponentType.SmartNIC, model='ConnectX-6', name='nic1')
        n2_nic1_interface1 = n2_nic1.interface_list[0]
        n2_nic1_interface1.add_child_interface(name="child1", labels=Labels(vlan="200"))

        self.assertTrue(len(n2_nic1_interface1.interface_list) != 0)
        self.assertEqual(n2_nic1_interface1.interface_list[0].type, f.InterfaceType.SubInterface)

        ns = self.topo.add_network_service(name='ns1', nstype=f.ServiceType.L2Bridge,
                                           interfaces=[n2_nic1_interface1.interface_list[0],
                                                       n1_nic1_interface1.interface_list[0]])
        self.assertTrue(len(ns.interface_list) != 0)
        self.topo.validate()

        slice_graph = self.topo.serialize()
        print(f"SubInterfaces: {slice_graph}")

        print(self.topo.network_services)

        self.topo.remove_network_service(name='ns1')
        self.topo.validate()

        slice_graph_after_removal = self.topo.serialize()
        print(f"SubInterfaces after removing network service: {slice_graph_after_removal}")

        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        asm_graph.validate_graph()
        print(self.topo.network_services)

        self.n4j_imp.delete_all_graphs()

    def testL3ServiceFail2(self):
        """
        Test validaton of L3 service required per site
        """
        self.topo.add_node(name='n1', site='RENC', ntype=f.NodeType.VM)
        self.topo.add_node(name='n2', site='RENC')
        self.topo.add_node(name='n3', site='UKY')
        self.topo.nodes['n1'].add_component(model_type=f.ComponentModelType.SharedNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n2'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_6, name='nic1')
        self.topo.nodes['n3'].add_component(model_type=f.ComponentModelType.SmartNIC_ConnectX_5, name='nic1')

        s1 = self.topo.add_network_service(name='globalL3', nstype=f.ServiceType.FABNetv4,
                                           interfaces=[self.topo.nodes['n1'].interface_list[0],
                                                       self.topo.nodes['n2'].interface_list[0],
                                                       self.topo.nodes['n3'].interface_list[0]])

        # site property is set automagically by validate
        with self.assertRaises(TopologyException):
            self.topo.validate()

        slice_graph = self.topo.serialize()

        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        # the following validation just uses cypher or networkx_query and is not as capable
        # as self.topo.validate() but is much faster
        asm_graph.validate_graph()
        self.n4j_imp.delete_all_graphs()

    def testPortMirrorService(self):
        t = self.topo

        n1 = t.add_node(name='n1', site='MASS')
        n1.add_component(name='nic1', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n2 = t.add_node(name='n2', site='RENC')
        n2.add_component(name='nic1', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n3 = t.add_node(name='n3', site='RENC')
        n3.add_component(name='nic1', model_type=ComponentModelType.SmartNIC_ConnectX_6)

        t.add_network_service(name='ns1', nstype=ServiceType.PortMirror,
                              interfaces=[n1.interface_list[0], n2.interface_list[0]])
        with self.assertRaises(TopologyException):
            t.validate()

        t.remove_network_service(name='ns1')
        t.validate()
        t.add_network_service(name='ns1', nstype=ServiceType.L2STS,
                              interfaces=[n1.interface_list[0], n2.interface_list[0]])
        t.add_port_mirror_service(name='pm1', from_interface_name='blahname',
                                  to_interface=n3.interface_list[0])
        n3.add_storage(name='st1', labels=Labels(local_name='volume_x'))

        self.assertEqual(t.network_services['pm1'].mirror_port, 'blahname')
        self.assertEqual(t.network_services['pm1'].mirror_direction, MirrorDirection.Both)
        t.validate()

        slice_graph = t.serialize()
        print(f"PortMirror: {slice_graph}")

        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        asm_graph.validate_graph()

        t.remove_network_service(name='pm1')
        self.n4j_imp.delete_all_graphs()

    def testNoNetworkServiceValidate(self):
        t = self.topo

        n1 = t.add_node(name='n1', site='MASS')
        n1.add_component(name='nic1', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n2 = t.add_node(name='n2', site='RENC')
        n2.add_component(name='nic1', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n3 = t.add_node(name='n3', site='RENC')
        n3.add_component(name='nic1', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        n3.add_storage(name='st1', labels=Labels(local_name='volume_x'))

        t.validate()

        slice_graph = t.serialize()

        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        asm_graph.validate_graph()
        self.n4j_imp.delete_all_graphs()

    def testFPGAComponent(self):
        t = self.topo

        n1 = t.add_node(name='n1', site='MASS')
        n1.add_component(name='fpga1', model_type=ComponentModelType.FPGA_Xilinx_U280)
        n2 = t.add_node(name='n2', site='MASS')
        n2.add_component(name='nic1', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        t.add_network_service(name='ns1', nstype=ServiceType.L2Bridge,
                              interfaces=[n1.interface_list[0], n2.interface_list[0]])

        t.validate()

        slice_graph = t.serialize(file_name='fpga_slice.graphml')
        slice_graph = t.serialize()

        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        asm_graph.validate_graph()
        self.n4j_imp.delete_all_graphs()
        os.unlink('fpga_slice.graphml')

    def testMultiConnectedFacility(self):
        t = self.topo

        n1 = t.add_node(name='n1', site='MASS')
        n1.add_component(name='nic1', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        n2 = t.add_node(name='n2', site='RENC')
        n2.add_component(name='nic1', model_type=ComponentModelType.SmartNIC_ConnectX_6)

        # add facility
        fac1 = t.add_facility(name='RENCI-DTN', site='RENC',
                              interfaces=[('to_mass', f.Labels(vlan='100'), f.Capacities(bw=10)),
                              ('to_renc', f.Labels(vlan='101'), f.Capacities(bw=1))])

        t.add_network_service(name='ns1', nstype=ServiceType.L2PTP,
                              interfaces=[n1.interface_list[0], fac1.interface_list[0]])
        t.add_network_service(name='ns2', nstype=ServiceType.L2PTP,
                              interfaces=[n2.interface_list[0], fac1.interface_list[1]])

        print(f'{fac1.interface_list[0].name=}')
        print(f'{fac1.interface_list[1].name=}')
        self.assertEqual(fac1.interface_list[0].name, 'to_mass')
        self.assertEqual(fac1.interface_list[1].name, 'to_renc')

        t.validate()

        self.n4j_imp.delete_all_graphs()

    def testP4Switch(self):
        t = self.topo

        n1 = t.add_node(name='n1', site='MASS')
        n1.add_component(name='nic1', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        n2 = t.add_node(name='n2', site='RENC')
        n2.add_component(name='nic1', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        n3 = t.add_node(name='n3', site='MASS')
        n3.add_component(name='nic1', model_type=ComponentModelType.SmartNIC_ConnectX_6)

        # add P4 switch at another site
        sw = t.add_switch(name='p4switch', site='STAR')

        # instead of sw.interfaces['p1'] you can also use sw.list_interfaces[0] however
        # for p4 switches referencing by name may be more appropriate for the users
        t.add_network_service(name='ns1', nstype=ServiceType.L2PTP,
                              interfaces=[n1.interface_list[0], sw.interfaces['p1']])
        t.add_network_service(name='ns2', nstype=ServiceType.L2PTP,
                              interfaces=[n2.interface_list[0], sw.interfaces['p2']])
        t.add_network_service(name='ns3', nstype=ServiceType.L2PTP,
                              interfaces=[n3.interface_list[0], sw.interfaces['p3']])

        t.validate()

        t.serialize(file_name='p4_switch_slice.graphml')

        self.n4j_imp.delete_all_graphs()

        os.unlink('p4_switch_slice.graphml')

    def testL3VPNWithCloudService(self):
        t = self.topo

        n1 = t.add_node(name='n1', site='MASS')
        n1.add_component(name='nic1', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n2 = t.add_node(name='n2', site='RENC')
        n2.add_component(name='nic1', model_type=ComponentModelType.SharedNIC_ConnectX_6)

        ns1 = t.add_network_service(name='ns1', nstype=ServiceType.L3VPN,
                              interfaces=[n1.interface_list[0], n2.interface_list[0]],
                              # you can also specify ipv4/ipv6 addresses, subnets as usual
                              labels=Labels(asn='654342', ipv4_subnet='192.168.1.1/24'))

        # add facility
        fac1 = self.topo.add_facility(name='RENCI-DTN', site='RENC', capacities=f.Capacities(bw=10),
                                      labels=f.Labels(vlan='100'))
        # facility needs to be connected via a service (in this case AL2S stand-in)
        al2s = self.topo.add_network_service(name='al2s', nstype=f.ServiceType.L3VPN,
                                             interfaces=[fac1.interface_list[0]])

        al2s.peer(ns1, labels=Labels(asn='12345', bgp_key='secret', ipv4_subnet='192.168.1.1/24'))
        # normally called by orchestrator, but generally idempotent
        ns1.copy_to_peer_labels()

        # check values set on copy
        self.assertEqual(ns1.interfaces[ns1.name + '-' + al2s.name].peer_labels.bgp_key, 'secret')

        t.validate()

        print('---- LOG TEST FACILITY ----')
        lc = LogCollector()
        lc.collect_resource_attributes(source=t)
        print(lc)
        print('----- END LOG TEST -----')

        slice_graph = t.serialize()
        #t.serialize("peered-slice.graphml")

        # Import it in the neo4j as ASM
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        asm_graph.validate_graph()

        # unpeer
        ns1.unpeer(al2s)
        t.validate()
        #t.serialize("peered-slice.graphml")

        self.n4j_imp.delete_all_graphs()

    def test_json_data(self):
        """
        Test various JSON data blobs - MF DATA, User Data and Layout Data
        """
        t = self.topo

        n1 = t.add_node(name='n1', site='MASS')
        n2 = t.add_node(name='n2', site='UKY')

        # maintenance mode - the object needs to be constructed prior to being assigned to the property
        minfo = MaintenanceInfo()
        minfo.add(name=n1.name, minfo=MaintenanceEntry(state=MaintenanceState.Active))
        n1.maintenance_info = minfo

        self.assertEqual(n1.maintenance_info.get(n1.name).state, MaintenanceState.Active)
        # check it is finalized
        self.assertEqual(n1.maintenance_info._lock, True)

        # try to modify after assignment
        with self.assertRaises(MaintenanceModeException):
            n1.maintenance_info.add(name='n3', minfo=MaintenanceEntry(state=MaintenanceState.PreMaint,
                                                                      deadline=datetime.datetime.now()))

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

        # user data on model elements (nodes, links, components, interfaces, network services)
        # can be set simply as json string (string length not to exceed 1M)
        n1.user_data = json.dumps({'k1': ['some', 'user', 'configuration']})
        # you are guaranteed that whatever is on user_data is JSON parsable and can be reconstituted into
        # an object
        user_object1 = n1.user_data
        self.assertTrue(user_object1['k1'] == ['some', 'user', 'configuration'])
        # when nothing is set, it is None
        self.assertEqual(n2.user_data, None)

        # you can also set it as UserData object
        my_user_data_object = {'key1': {'user2': ['v1', 2]}}
        n1.user_data = f.UserData(json.dumps(my_user_data_object))

        # you can also just pass a JSON serializable object to UserData constructor:
        n1.user_data = f.UserData(my_user_data_object)
        # or even an serializable object itself.
        n1.user_data = my_user_data_object

        # for most uses, just set the object
        my_user_data_object = {'key1': {'key2': ['some', 'user', 'info']}}
        n1.user_data = my_user_data_object

        # you get back your object (in this case a dict)
        self.assertTrue(isinstance(n1.user_data, dict))
        user_object2 = n1.user_data
        self.assertTrue(user_object2['key1'] == {'key2': ['some', 'user', 'info']})

        class MyClass:
            def __init__(self, val):
                self.val = val

        # this is not a valid object - json.dumps() will fail on it
        bad_user_data_object = {'key1': MyClass(3)}
        with self.assertRaises(UserDataError):
            n1.user_data = bad_user_data_object

        # also cannot use bad strings
        with self.assertRaises(UserDataError):
            # you cannot assign non-json string to measurement data either as MeasurementData object
            n1.user_data = f.UserData("not parsable json")
        with self.assertRaises(UserDataError):
            # or directly as string
            n1.user_data = 'random string'

        # most settable properties can be unset by setting them to None (there are exceptions, like e.g. name)
        n1.user_data = None
        self.assertIsNone(n1.user_data)

        # layout data on model elements (nodes, links, components, interfaces, network services)
        # can be set simply as json string (string length not to exceed 1M)
        n1.layout_data = json.dumps({'k1': ['some', 'layout', 'configuration']})
        # you are guaranteed that whatever is on layout_data is JSON parsable and can be reconstituted into
        # an object
        layout_object1 = n1.layout_data
        self.assertTrue(layout_object1['k1'] == ['some', 'layout', 'configuration'])
        # when nothing is set, it is None
        self.assertEqual(n2.layout_data, None)

        # you can also set it as LayoutData object
        my_layout_data_object = {'key1': {'layout2': ['v1', 2]}}
        n1.layout_data = f.LayoutData(json.dumps(my_layout_data_object))

        # you can also just pass a JSON serializable object to LayoutData constructor:
        n1.layout_data = f.LayoutData(my_layout_data_object)
        # or even an serializable object itself.
        n1.layout_data = my_layout_data_object

        # for most uses, just set the object
        my_layout_data_object = {'key1': {'key2': ['some', 'layout', 'info']}}
        n1.layout_data = my_layout_data_object

        # you get back your object (in this case a dict)
        self.assertTrue(isinstance(n1.layout_data, dict))
        layout_object2 = n1.layout_data
        self.assertTrue(layout_object2['key1'] == {'key2': ['some', 'layout', 'info']})

        class MyClass:
            def __init__(self, val):
                self.val = val

        # this is not a valid object - json.dumps() will fail on it
        bad_layout_data_object = {'key1': MyClass(3)}
        with self.assertRaises(LayoutDataError):
            n1.layout_data = bad_layout_data_object

        # also cannot use bad strings
        with self.assertRaises(LayoutDataError):
            # you cannot assign non-json string to measurement data either as MeasurementData object
            n1.layout_data = f.LayoutData("not parsable json")
        with self.assertRaises(LayoutDataError):
            # or directly as string
            n1.layout_data = 'random string'

        # most settable properties can be unset by setting them to None (there are exceptions, like e.g. name)
        n1.layout_data = None
        self.assertIsNone(n1.layout_data)

    def test_SubInterface_NetworkX(self):
        t = f.ExperimentTopology()
        n1 = t.add_node(name='Node1', site='RENC')
        n1_nic1 = n1.add_component(ctype=f.ComponentType.SmartNIC, model='ConnectX-6', name='nic1')
        n1_nic1_interface1 = n1_nic1.interface_list[0]

        from fim.user.model_element import TopologyException
        with self.assertRaises(TopologyException):
            n1_nic1_interface1.add_child_interface(name="child1")

        ch1 = n1_nic1_interface1.add_child_interface(name="child1", labels=f.Labels(vlan="100"))

        with self.assertRaises(TopologyException):
            n1_nic1_interface1.add_child_interface(name="child1", labels=f.Labels(vlan="200"))

        with self.assertRaises(TopologyException):
            n1_nic1_interface1.add_child_interface(name="child2", labels=f.Labels(vlan="100"))

        ch2 = n1_nic1_interface1.add_child_interface(name="child2", labels=f.Labels(vlan="200"))

        t.add_network_service(name="net1", nstype=f.ServiceType.L2Bridge, interfaces=[ch1])
        t.network_services["net1"].connect_interface(ch2)

        t.validate()
        t.network_services["net1"].disconnect_interface(ch1)
        n1_nic1_interface1.remove_child_interface(name="child1")
        t.validate()
        t.remove_network_service("net1")
        t.validate()
        n1_nic1_interface1.remove_child_interface(name="child2")
        t.validate()