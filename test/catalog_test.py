import unittest
from typing import Dict

from fim.slivers.component_catalog import ComponentCatalog, CatalogException
from fim.slivers.attached_components import ComponentType


class CatalogTest(unittest.TestCase):

    def testCatalog(self):
        cata = ComponentCatalog()

        c = cata.generate_component(name='myNIC', model='ConnectX-6', ctype=ComponentType.SmartNIC)
        self.assertIsNotNone(c.network_service_info)
        self.assertEqual(len(c.network_service_info.get_network_service('myNIC-l2ovs').interface_info.interfaces.keys()), 2)
        c1 = cata.generate_component(name='myGPU', model='RTX6000', ctype=ComponentType.GPU)
        self.assertIsNone(c1.network_service_info)
        with self.assertRaises(CatalogException):
            cata.generate_component(name='some', model='blah', ctype=ComponentType.SmartNIC)
