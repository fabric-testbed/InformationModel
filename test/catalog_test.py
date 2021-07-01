import unittest
from typing import Dict

from fim.slivers.component_catalog import ComponentCatalog, CatalogException, ComponentModelType
from fim.slivers.instance_catalog import InstanceCatalog
from fim.slivers.attached_components import ComponentType
from fim.slivers.capacities_labels import Capacities


class CatalogTest(unittest.TestCase):

    def testCatalog(self):
        cata = ComponentCatalog()

        c = cata.generate_component(name='myNIC', model='ConnectX-6', ctype=ComponentType.SmartNIC)
        self.assertIsNotNone(c.network_service_info)
        self.assertEqual(len(c.network_service_info.get_network_service('myNIC-l2ovs').interface_info.interfaces.keys()), 2)
        c1 = cata.generate_component(name='myGPU', model='RTX6000', ctype=ComponentType.GPU)
        self.assertIsNone(c1.network_service_info)
        c2 = cata.generate_component(name='myGPU', model='Quadro RTX 6000/8000', ctype=ComponentType.GPU)
        with self.assertRaises(CatalogException):
            cata.generate_component(name='some', model='blah', ctype=ComponentType.SmartNIC)

    def testInstanceCatalog(self):
        cata = InstanceCatalog()
        cap = Capacities().set_fields(ram=20, cpu=1, core=9, disk=110)
        c = cata.map_capacities_to_instance(cap=cap)
        cap1 = cata.get_instance_capacities(instance_type=c)
        self.assertTrue(cap1.core > cap.core and cap1.ram > cap.ram and cap1.disk > cap.disk)
        cap = Capacities(ram=20, cpu=1, core=9, disk=110)
        c = cata.map_capacities_to_instance(cap=cap)
        cap1 = cata.get_instance_capacities(instance_type=c)
        self.assertTrue(cap1.core > cap.core and cap1.ram > cap.ram and cap1.disk > cap.disk)

    def testComponentTypeModel(self):
        cata = ComponentCatalog()
        c = cata.generate_component(name='myNIC', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        self.assertEqual(
            len(c.network_service_info.get_network_service('myNIC-l2ovs').interface_info.interfaces.keys()), 2)