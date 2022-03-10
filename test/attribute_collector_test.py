import unittest

from fim.authz.attribute_collector import AuthZAttributes

from fim.user.topology import ExperimentTopology
from fim.slivers.capacities_labels import Capacities
from fim.user.component import ComponentModelType
from fim.slivers.network_service import ServiceType


class AttributeCollectorTest(unittest.TestCase):

    def testCollector(self):
        az = AuthZAttributes()
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
        # this will take just about any thing - an ASM, a Node, a NetworkService,
        # a sliver. However to get things like peering sites, facility sites, it is best to
        # call it on the ASM
        az.collect_attributes(source=t)
        # generally you also want to set the lifetime (provided externally)
        az.set_lifetime('blah')
        print(az)
        self.assertTrue('SmartNIC' in az.attributes[AuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue('NVME' in az.attributes[AuthZAttributes.RESOURCE_COMPONENT])
        self.assertTrue(25 in az.attributes[AuthZAttributes.RESOURCE_DISK])
        self.assertTrue(12 in az.attributes[AuthZAttributes.RESOURCE_BW])
        self.assertTrue('RENC' in az.attributes[AuthZAttributes.RESOURCE_SITE])
        self.assertTrue('UKY' in az.attributes[AuthZAttributes.RESOURCE_SITE])
