import unittest

import fim.user as f


class AdTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self) -> None:
        pass

    def testAd(self) -> None:
        self.topo = f.AdvertisedTopology(graph_file='test/models/advertised_topo.graphml')

        #
        # site capacity (what is total)
        #
        self.assertEqual(self.topo.nodes['TACC'].capacities.core, 320)
        # site allocated capacity (what is taken, in this case 18 cores)
        self.assertEqual(self.topo.nodes['TACC'].capacity_allocations.core, 18)
        # computing the difference
        # option 1 (suggested)
        ft = f.FreeCapacity(total=self.topo.nodes['TACC'].capacities,
                            allocated=self.topo.nodes['TACC'].capacity_allocations)
        self.assertIsInstance(ft, f.FreeCapacity)
        # ft (FreeCapacity) has the same fields as a regular capacity object
        # computed as a difference between total and allocated (i.e. what is free)
        """
        Possible Capacities or FreeCapacity fields
        self.cpu = 0
        self.core = 0
        self.ram = 0
        self.disk = 0
        self.bw = 0
        self.burst_size = 0
        self.unit = 0
        self.mtu = 0
        """
        self.assertEqual(ft.core, 302)
        # you can also access total like this:
        self.assertEqual(ft.total.core, 320)
        # and free like this (same as ft.core)
        self.assertEqual(ft.free.core, 302)
        print(f'{ft.core} of {ft.total.core} cores are available at TACC')

        # option 2 - Capacities object understands subtraction and addition, so
        ft1 = self.topo.nodes['TACC'].capacities - self.topo.nodes['TACC'].capacity_allocations
        # this time the result is a Capacities object, not FreeCapacity and it doesn't know the total
        self.assertIsInstance(ft1, f.Capacities)
        self.assertEqual(ft1.core, 302)

        #
        # Components
        #
        # you can get the list of keys in components dictionary:
        print(list(self.topo.nodes['TACC'].components.keys()))
        # typical capacities on components are just unit counts, some have disk space etc
        ft = f.FreeCapacity(total=self.topo.nodes['TACC'].components['GPU-Tesla T4'].capacities,
                            allocated=self.topo.nodes['TACC'].components['GPU-Tesla T4'].capacity_allocations)
        self.assertEqual(ft.unit, 4)
        print(f'{ft.unit} of {ft.total.unit} units of Tesla T4 is available at TACC')
        # you can get component type and model (types print as strings, but are enums; model is always a string
        self.assertIsInstance(self.topo.nodes['TACC'].components['GPU-Tesla T4'].type, f.ComponentType)
        self.assertEqual(self.topo.nodes['TACC'].components['GPU-Tesla T4'].type, f.ComponentType.GPU)
        print(f"Model string is {self.topo.nodes['TACC'].components['GPU-Tesla T4'].model}")


        #
        # Interfaces
        #
        # interfaces are attached to nodes in Advertisements (in slices can be attached to nodes or components)
        print(self.topo.nodes['TACC'].interface_list)
        ft = f.FreeCapacity(total=self.topo.nodes['TACC'].interfaces['TACC_DALL'].capacities,
                            allocated=self.topo.nodes['TACC'].interfaces['TACC_DALL'].capacity_allocations)
        # full 100Gbps bandwidth is available in this case
        self.assertEqual(ft.bw, 100)
        # interface type
        self.assertEqual(self.topo.nodes['TACC'].interfaces['TACC_DALL'].type, f.InterfaceType.TrunkPort)

        #
        # Links
        #
        print(list(self.topo.links.keys()))
        print(f"{self.topo.links['port+ncsa-data-sw:HundredGigE0/0/0/22.3000 to port+star-data-sw:HundredGigE0/0/0/31.3000']}")
        # link attributes
        self.assertEqual(self.topo.links['port+ncsa-data-sw:HundredGigE0/0/0/22.3000 to port+star-data-sw:HundredGigE0/0/0/31.3000'].layer,
                         f.Layer.L2)
        self.assertEqual(self.topo.links['port+ncsa-data-sw:HundredGigE0/0/0/22.3000 to port+star-data-sw:HundredGigE0/0/0/31.3000'].type,
                         f.LinkType.L2Path)
        # links have interfaces of nodes and you can reference interfaces from topology level, not just node or component level
        # but only as a list, not a dictionary, because name collisions are possible on keys which are interface names
        self.assertIn('STAR_NCSA', [x.name for x in self.topo.interface_list])
        print(f"{self.topo.nodes['STAR'].interfaces['STAR_NCSA']}")
        self.assertEqual(self.topo.nodes['STAR'].interfaces['STAR_NCSA'].capacities.bw, 100)

