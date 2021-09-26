import unittest

import fim.user as f


class SliceTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self) -> None:
        pass

    def testAd(self) -> None:
        self.topo = f.AdvertisedTopology(graph_file='test/models/advertised_topo.graphml')
        self.assertEqual(self.topo.get_owner_node(self.topo.links['port+lbnl-data-sw:HundredGigE0/0/0/0.2401-link'].interface_list[0]).name, 'UKY')

