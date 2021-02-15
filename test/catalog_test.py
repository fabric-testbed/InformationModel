import unittest
from typing import Dict

from fim.slivers.component_catalog import ComponentCatalog, CatalogException


class CatalogTest(unittest.TestCase):

    def testCatalog(self):
        cata = ComponentCatalog()

        c = cata.generate_component(name='myNIC', model='ConnectX-6')
        self.assertIsNotNone(c.interface_info)
        self.assertEqual(len(c.interface_info.interfaces.keys()), 2)
        c1 = cata.generate_component(name='myGPU', model='RTX6000')
        self.assertIsNone(c1.interface_info)
        with self.assertRaises(CatalogException):
            cata.generate_component(name='some', model='blah')
