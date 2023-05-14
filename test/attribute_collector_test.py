import unittest
from datetime import datetime, timedelta, timezone

from fim.authz.attribute_collector import ResourceAuthZAttributes

from fim.user.topology import ExperimentTopology
from fim.slivers.capacities_labels import Capacities
from fim.user.component import ComponentModelType
from fim.slivers.network_service import ServiceType
from fim.graph.slices.networkx_asm import NetworkxASM, NetworkXGraphImporter, NetworkXASMFactory


class AttributeCollectorTest(unittest.TestCase):

    def testCollector(self):
        az = ResourceAuthZAttributes()
        print(az)
        t = ExperimentTopology()
        n1 = t.add_node(name='n1', site='RENC', capacities=Capacities(core=1, ram=10, disk=25))
        c1 = n1.add_component(name='c1', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        c2 = n1.add_component(name='c2', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n1.add_component(name='c3', model_type=ComponentModelType.NVME_P4510)
        n2 = t.add_node(name='n2', site='UKY', capacities=Capacities(core=10, ram=10, disk=35))
        c4 = n2.add_component(name='c4', model_type=ComponentModelType.SmartNIC_ConnectX_5)
        c5 = n2.add_component(name='c5', model_type=ComponentModelType.FPGA_Xilinx_U280)
        s1 = t.add_network_service(name='s1', nstype=ServiceType.L2PTP,
                                   interfaces=[c1.interface_list[0], c4.interface_list[0]],
                                   capacities=Capacities(bw=12))
        s2 = t.add_network_service(name='s2', nstype=ServiceType.L2Bridge,
                                   interfaces=[c5.interface_list[0], c5.interface_list[1]])
        fac1 = t.add_facility(name='RENCI-DTN', site='RENC', capacities=Capacities(bw=10))
        sfac = t.add_network_service(name='s-fac', nstype=ServiceType.L2STS,
                                     interfaces=[fac1.interface_list[0],
                                                 c2.interface_list[0]])
        # this will take just about anything - an ASM, a Node, a NetworkService,
        # a sliver. So it can be called in AM, Broker or Orchestrator
        #
        # However to get things like peering sites, facility sites, it is best to
        # call it on the ASM (in Orchestrator)
        az.collect_resource_attributes(source=t)
        # generally you also want to set the lifetime (provided externally)
        now = datetime.now(timezone.utc)
        delta = timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta
        az.set_lifetime(future)
        print(az)
        self.assertTrue('SmartNIC' in az.attributes[ResourceAuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue('FPGA' in az.attributes[ResourceAuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue('NVME' in az.attributes[ResourceAuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue(25 in az.attributes[ResourceAuthZAttributes.RESOURCE_DISK])
        self.assertTrue(12 in az.attributes[ResourceAuthZAttributes.RESOURCE_BW])
        self.assertTrue('RENC' in az.attributes[ResourceAuthZAttributes.RESOURCE_SITE])
        self.assertTrue('UKY' in az.attributes[ResourceAuthZAttributes.RESOURCE_SITE])
        self.assertTrue('P13DT11H7M4S' in az.attributes[ResourceAuthZAttributes.RESOURCE_LIFETIME])
        self.assertEqual(az.attributes[ResourceAuthZAttributes.RESOURCE_TYPE], ["sliver"])

        az.set_subject_attributes(subject_id="user@gmail.com", project=["Project1"],
                                  project_tag=["Tag1", "Tag2"])
        az.set_action("create")
        az.set_resource_subject_and_project(subject_id="user@gmail.com", project="Project1")

        # convert to full PDP request after adding attributes
        req_json = az.transform_to_pdp_request()
        req_dict = az.transform_to_pdp_request(as_json=False)

        print(f'JSON {req_json}')

        print(f'Dict {req_dict}')

    def testCollector1(self):
        # test without sliver/slice or time info for things like delete
        az = ResourceAuthZAttributes()
        az.set_subject_attributes(subject_id="user@gmail.com", project=["Project1"],
                                  project_tag=["Tag1", "Tag2"])
        az.set_action("delete")
        az.set_resource_subject_and_project(subject_id="user@gmail.com", project="Project1")

        # convert to full PDP request after adding attributes
        req_json = az.transform_to_pdp_request()
        req_dict = az.transform_to_pdp_request(as_json=False)

        self.assertEqual(az.attributes[ResourceAuthZAttributes.RESOURCE_TYPE], ["sliver"])

        print(f'1: JSON {req_json}')

    def testCollector2(self):
        # test without sliver/slice info for things like extend
        az = ResourceAuthZAttributes()
        az.set_subject_attributes(subject_id="user@gmail.com", project=["Project1"],
                                  project_tag=["Tag1", "Tag2"])
        # generally you also want to set the lifetime (provided externally)
        now = datetime.now(timezone.utc)
        delta = timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta
        az.set_lifetime(future)

        az.set_action("extend")
        az.set_resource_subject_and_project(subject_id="user@gmail.com", project="Project1")

        self.assertEqual(az.attributes[ResourceAuthZAttributes.RESOURCE_TYPE], ["sliver"])

        # convert to full PDP request after adding attributes
        req_json = az.transform_to_pdp_request()
        req_dict = az.transform_to_pdp_request(as_json=False)

        print(f'2: JSON {req_json}')

    def testCollector4(self):
        # test from ASM
        az = ResourceAuthZAttributes()
        print(az)
        t = ExperimentTopology()
        n1 = t.add_node(name='n1', site='RENC', capacities=Capacities(core=1, ram=10, disk=25))
        c1 = n1.add_component(name='c1', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        c2 = n1.add_component(name='c2', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n1.add_component(name='c3', model_type=ComponentModelType.NVME_P4510)
        n2 = t.add_node(name='n2', site='UKY', capacities=Capacities(core=10, ram=10, disk=35))
        c4 = n2.add_component(name='c4', model_type=ComponentModelType.SmartNIC_ConnectX_5)
        s1 = t.add_network_service(name='s1', nstype=ServiceType.L2PTP,
                                   interfaces=[c1.interface_list[0], c4.interface_list[0]],
                                   capacities=Capacities(bw=12))
        fac1 = t.add_facility(name='RENCI-DTN', site='RENC', capacities=Capacities(bw=10))
        sfac = t.add_network_service(name='s-fac', nstype=ServiceType.L2STS,
                                     interfaces=[fac1.interface_list[0],
                                                 c2.interface_list[0]])

        serial_asm = t.serialize()

        asm_imp = NetworkXGraphImporter()
        pgraph = asm_imp.import_graph_from_string(graph_string=serial_asm)
        asm = NetworkXASMFactory.create(pgraph)

        # this will take just about anything - an ASM, a Node, a NetworkService,
        # a sliver. So it can be called in AM, Broker or Orchestrator
        #
        # However to get things like peering sites, facility sites, it is best to
        # call it on the ASM (in Orchestrator)
        az.collect_resource_attributes(source=asm)
        # generally you also want to set the lifetime (provided externally)
        now = datetime.now(timezone.utc)
        delta = timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta
        az.set_lifetime(future)
        print(az)
        self.assertTrue('SmartNIC' in az.attributes[ResourceAuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue('NVME' in az.attributes[ResourceAuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue(25 in az.attributes[ResourceAuthZAttributes.RESOURCE_DISK])
        self.assertTrue(12 in az.attributes[ResourceAuthZAttributes.RESOURCE_BW])
        self.assertTrue('RENC' in az.attributes[ResourceAuthZAttributes.RESOURCE_SITE])
        self.assertTrue('UKY' in az.attributes[ResourceAuthZAttributes.RESOURCE_SITE])
        self.assertTrue('P13DT11H7M4S' in az.attributes[ResourceAuthZAttributes.RESOURCE_LIFETIME])
        self.assertEqual(az.attributes[ResourceAuthZAttributes.RESOURCE_TYPE], ["sliver"])

        az.set_subject_attributes(subject_id="user@gmail.com", project=["Project1"],
                                  project_tag=["Tag1", "Tag2"])
        az.set_action("create")
        az.set_resource_subject_and_project(subject_id="user@gmail.com", project="Project1")

        # convert to full PDP request after adding attributes
        req_json = az.transform_to_pdp_request()
        req_dict = az.transform_to_pdp_request(as_json=False)

        print(f'4: JSON {req_json}')

    def testCollector5(self):
        # test single-site make sure site is reflected only once on the list

        az = ResourceAuthZAttributes()
        print(az)
        t = ExperimentTopology()
        n1 = t.add_node(name='n1', site='RENC', capacities=Capacities(core=1, ram=10, disk=25))
        c1 = n1.add_component(name='c1', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        c2 = n1.add_component(name='c2', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n1.add_component(name='c3', model_type=ComponentModelType.NVME_P4510)
        n2 = t.add_node(name='n2', site='RENC', capacities=Capacities(core=10, ram=10, disk=35))
        c4 = n2.add_component(name='c4', model_type=ComponentModelType.SmartNIC_ConnectX_5)
        s1 = t.add_network_service(name='s1', nstype=ServiceType.L2PTP,
                                   interfaces=[c1.interface_list[0], c4.interface_list[0]],
                                   capacities=Capacities(bw=12))

        # this will take just about anything - an ASM, a Node, a NetworkService,
        # a sliver. So it can be called in AM, Broker or Orchestrator
        #
        # However to get things like peering sites, facility sites, it is best to
        # call it on the ASM (in Orchestrator)
        az.collect_resource_attributes(source=t)
        # generally you also want to set the lifetime (provided externally)
        now = datetime.now(timezone.utc)
        delta = timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta
        az.set_lifetime(future)
        print(az)
        self.assertTrue('SmartNIC' in az.attributes[ResourceAuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue('NVME' in az.attributes[ResourceAuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue(25 in az.attributes[ResourceAuthZAttributes.RESOURCE_DISK])
        self.assertTrue(12 in az.attributes[ResourceAuthZAttributes.RESOURCE_BW])
        self.assertEqual(az.attributes[ResourceAuthZAttributes.RESOURCE_SITE], ['RENC'])
        self.assertTrue('P13DT11H7M4S' in az.attributes[ResourceAuthZAttributes.RESOURCE_LIFETIME])
        self.assertEqual(az.attributes[ResourceAuthZAttributes.RESOURCE_TYPE], ["sliver"])

        az.set_subject_attributes(subject_id="user@gmail.com", project=["Project1"],
                                  project_tag=["Tag1", "Tag2"])
        az.set_action("create")
        az.set_resource_subject_and_project(subject_id="user@gmail.com", project="Project1")

        # convert to full PDP request after adding attributes
        req_json = az.transform_to_pdp_request()
        req_dict = az.transform_to_pdp_request(as_json=False)

        print(f'5: JSON {req_json}')

    def testCollector6(self):
        # single-site with port-mirroring

        az = ResourceAuthZAttributes()
        print(az)
        t = ExperimentTopology()
        n1 = t.add_node(name='n1', site='RENC', capacities=Capacities(core=1, ram=10, disk=25))
        c1 = n1.add_component(name='c1', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        c2 = n1.add_component(name='c2', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n1.add_component(name='c3', model_type=ComponentModelType.NVME_P4510)
        n2 = t.add_node(name='n2', site='RENC', capacities=Capacities(core=10, ram=10, disk=35))
        c4 = n2.add_component(name='c4', model_type=ComponentModelType.SmartNIC_ConnectX_5)
        s1 = t.add_network_service(name='s1', nstype=ServiceType.L2PTP,
                                   interfaces=[c1.interface_list[0], c4.interface_list[0]],
                                   capacities=Capacities(bw=12))
        s2 = t.add_port_mirror_service(name='pm1', from_interface_name='blahname1',
                                       to_interface=c1.interface_list[1])
        s3 = t.add_port_mirror_service(name='pm2', from_interface_name='blahname2',
                                       to_interface=c4.interface_list[1])

        t.validate()
        # this will take just about anything - an ASM, a Node, a NetworkService,
        # a sliver. So it can be called in AM, Broker or Orchestrator
        #
        # However to get things like peering sites, facility sites, it is best to
        # call it on the ASM (in Orchestrator)
        az.collect_resource_attributes(source=t)
        # generally you also want to set the lifetime (provided externally)
        now = datetime.now(timezone.utc)
        delta = timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta
        az.set_lifetime(future)
        print(az)
        self.assertTrue('SmartNIC' in az.attributes[ResourceAuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue('NVME' in az.attributes[ResourceAuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue(25 in az.attributes[ResourceAuthZAttributes.RESOURCE_DISK])
        self.assertTrue(12 in az.attributes[ResourceAuthZAttributes.RESOURCE_BW])
        self.assertEqual(az.attributes[ResourceAuthZAttributes.RESOURCE_SITE], ['RENC'])
        self.assertTrue('P13DT11H7M4S' in az.attributes[ResourceAuthZAttributes.RESOURCE_LIFETIME])
        self.assertEqual(az.attributes[ResourceAuthZAttributes.RESOURCE_TYPE], ["sliver"])

        az.set_subject_attributes(subject_id="user@gmail.com", project=["Project1"],
                                  project_tag=["Tag1", "Tag2"])
        az.set_action("create")
        az.set_resource_subject_and_project(subject_id="user@gmail.com", project="Project1")

        # convert to full PDP request after adding attributes
        req_json = az.transform_to_pdp_request()
        req_dict = az.transform_to_pdp_request(as_json=False)

        print(f'6: JSON {req_json}')

    def testCollector7(self):
        # multi-site with FABNetv4Ext

        az = ResourceAuthZAttributes()
        print(az)
        t = ExperimentTopology()
        n1 = t.add_node(name='n1', site='RENC', capacities=Capacities(core=1, ram=10, disk=25))
        c1 = n1.add_component(name='c1', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        c2 = n1.add_component(name='c2', model_type=ComponentModelType.SharedNIC_ConnectX_6)
        n1.add_component(name='c3', model_type=ComponentModelType.NVME_P4510)
        n2 = t.add_node(name='n2', site='UKY', capacities=Capacities(core=10, ram=10, disk=35))
        c4 = n2.add_component(name='c4', model_type=ComponentModelType.SmartNIC_ConnectX_5)
        s1 = t.add_network_service(name='s1', nstype=ServiceType.FABNetv4Ext,
                                   interfaces=[c1.interface_list[0]])
        s2 = t.add_network_service(name='s2', nstype=ServiceType.FABNetv4Ext,
                                   interfaces=[c4.interface_list[0]])
        # this sets site property on fabnet, which is a must
        t.validate()

        # this will take just about anything - an ASM, a Node, a NetworkService,
        # a sliver. So it can be called in AM, Broker or Orchestrator
        #
        # However to get things like peering sites, facility sites, it is best to
        # call it on the ASM (in Orchestrator)
        az.collect_resource_attributes(source=t)
        # generally you also want to set the lifetime (provided externally)
        now = datetime.now(timezone.utc)
        delta = timedelta(days=13, hours=11, minutes=7, seconds=4, milliseconds=10)
        future = now + delta
        az.set_lifetime(future)
        print(az)
        self.assertTrue('SmartNIC' in az.attributes[ResourceAuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue('NVME' in az.attributes[ResourceAuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue(25 in az.attributes[ResourceAuthZAttributes.RESOURCE_DISK])
        self.assertEqual(az.attributes[ResourceAuthZAttributes.RESOURCE_SITE], ['RENC', 'UKY'])
        self.assertTrue('P13DT11H7M4S' in az.attributes[ResourceAuthZAttributes.RESOURCE_LIFETIME])
        self.assertEqual(az.attributes[ResourceAuthZAttributes.RESOURCE_TYPE], ["sliver"])
        self.assertTrue('RENC' in az.attributes[ResourceAuthZAttributes.RESOURCE_FABNETV4_EXT])
        self.assertTrue('UKY' in az.attributes[ResourceAuthZAttributes.RESOURCE_FABNETV4_EXT])

        az.set_subject_attributes(subject_id="user@gmail.com", project=["Project1"],
                                  project_tag=["Tag1", "Tag2"])
        az.set_action("create")
        az.set_resource_subject_and_project(subject_id="user@gmail.com", project="Project1")

        # convert to full PDP request after adding attributes
        req_json = az.transform_to_pdp_request()
        req_dict = az.transform_to_pdp_request(as_json=False)

        print(f'7: JSON {req_json}')