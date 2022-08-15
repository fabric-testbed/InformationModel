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
        cns = c.network_service_info.get_network_service(c.network_service_info.get_network_service_names()[0])
        cport = cns.interface_info.get_interface(cns.interface_info.get_interface_names()[0])
        self.assertEqual(cport.get_property('capacities').bw, 100)
        c1 = cata.generate_component(name='myGPU', model='RTX6000', ctype=ComponentType.GPU)
        self.assertIsNone(c1.network_service_info)
        c2 = cata.generate_component(name='myGPU', model='Quadro RTX 6000/8000', ctype=ComponentType.GPU)
        with self.assertRaises(CatalogException):
            cata.generate_component(name='some', model='blah', ctype=ComponentType.SmartNIC)
        c3 = cata.generate_component(name='SharedNIC', ctype=ComponentType.SharedNIC, model='ConnectX-6')
        c3ns = c3.network_service_info.get_network_service(c3.network_service_info.get_network_service_names()[0])
        c3port = c3ns.interface_info.get_interface(c3ns.interface_info.get_interface_names()[0])
        self.assertEqual(c3port.get_property('capacities').bw, 0)

    def testInstanceCatalog(self):
        cata = InstanceCatalog()
        cap = Capacities(ram=4, core=1, disk=90)
        c = cata.map_capacities_to_instance(cap=cap)
        print(f'For {cap=} instance is {c}')
        cap1 = cata.get_instance_capacities(instance_type=c)
        self.assertTrue(cap1.core >= cap.core and cap1.ram >= cap.ram and cap1.disk >= cap.disk)
        cap = Capacities(ram=20, core=9, disk=110)
        c = cata.map_capacities_to_instance(cap=cap)
        print(f'For {cap=} instance is {c}')
        cap1 = cata.get_instance_capacities(instance_type=c)
        self.assertTrue(cap1.core >= cap.core and cap1.ram >= cap.ram and cap1.disk >= cap.disk)

    def testComponentTypeModel(self):
        cata = ComponentCatalog()
        c = cata.generate_component(name='myNIC', model_type=ComponentModelType.SmartNIC_ConnectX_6)
        self.assertEqual(
            len(c.network_service_info.get_network_service('myNIC-l2ovs').interface_info.interfaces.keys()), 2)