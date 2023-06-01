import unittest

from fim.slivers.attached_components import ComponentSliver, ComponentType, AttachedComponentsInfo
from fim.slivers.network_node import NodeSliver, NodeType
from fim.slivers.network_link import NetworkLinkSliver
from fim.slivers.network_service import NetworkServiceSliver, NetworkServiceInfo
from fim.slivers.interface_info import InterfaceSliver
from fim.slivers.path_info import ERO, PathInfo, Path
from fim.slivers.capacities_labels import Capacities, Labels, CapacityHints, Location, LabelException, Flags
from fim.slivers.tags import Tags
from fim.slivers.gateway import Gateway, GatewayException
from fim.slivers.maintenance_mode import MaintenanceInfo, MaintenanceState, MaintenanceEntry


class TestSlivers(unittest.TestCase):

    def testComponentSliver(self):
        cs = ComponentSliver()
        cs.set_property('details', 'these are details')
        cs.set_properties(type=ComponentType.GPU, name='name')

        self.assertEqual(cs.get_details(), 'these are details')
        self.assertEqual(cs.get_type(), ComponentType.GPU)
        self.assertEqual(cs.get_name(), 'name')

        cs1 = ComponentSliver()
        cs1.set_property('details', 'these are other details')
        cs1.set_properties(type=ComponentType.GPU, name='name1')

        cs2 = ComponentSliver()
        cs2.set_property('details', 'these are some details')
        cs2.set_properties(type=ComponentType.SmartNIC, name='name2')

        acs = AttachedComponentsInfo()
        acs.add_device(cs)
        acs.add_device(cs1)
        acs.add_device(cs2)

        self.assertEqual(len(acs.by_type[ComponentType.GPU]), 2)
        self.assertEqual(len(acs.by_type[ComponentType.SmartNIC]), 1)
        self.assertEqual(len(acs.get_devices_by_type(ComponentType.SharedNIC)), 0)

        acs.remove_device(name='name')
        acs.remove_device(name='name1')
        self.assertEqual(len(acs.get_devices_by_type(ComponentType.GPU)), 0)
        self.assertEqual(len(acs.get_devices_by_type(ComponentType.SmartNIC)), 1)

    def testNodeSliver(self):
        minfo = MaintenanceInfo()
        minfo.add('node1', minfo=MaintenanceEntry(state=MaintenanceState.Active))
        ns = NodeSliver()
        ns.set_properties(name='node1', type=NodeType.Server,
                          management_ip='192.168.1.1',
                          maintenance_info=minfo)
        with self.assertRaises(ValueError) as ve:
            ns.set_property('management_ip', '192.168.1.x')

        self.assertEqual(ns.get_maintenance_info().get('node1').state, MaintenanceState.Active)

    def testNetworkServiceSliver(self):
        ns = NetworkServiceSliver()
        p = Path()
        p.set_symmetric(['a', 'b', 'c'])
        pi = PathInfo()
        pi.set(payload=p)
        ns.set_properties(path_info=pi)
        e = ERO()
        e.set(payload=p)
        ns.set_properties(ero=e)
        pi1 = ns.get_property('path_info')
        assert(pi.get() == pi1.get())

    def testCapacitiesLabels(self):
        ns = NodeSliver()
        cap_hint = CapacityHints(instance_type='blah')
        lab = Labels(vlan_range='1-4096')
        ns.set_properties(capacities=Capacities(unit=1, core=2), labels=lab, capacity_hints=cap_hint)
        assert(ns.get_capacity_hints().instance_type == 'blah')
        assert(ns.get_labels().vlan_range == '1-4096')
        assert(ns.get_capacities().core == 2)

        with self.assertRaises(LabelException):
            Labels(vlan_range='1-8000')

        with self.assertRaises(LabelException):
            Labels(asn='60000000000')

        with self.assertRaises(LabelException):
            Labels(vlan='4098')

        with self.assertRaises(LabelException):
            Labels(inner_vlan='6000')

    def testNuma(self):
        ns = NodeSliver()
        cap_hint = CapacityHints(instance_type='blah')
        lab = Labels(numa='-1')
        ns.set_properties(labels=lab, capacity_hints=cap_hint)

        self.assertEqual(ns.labels.numa, '-1')

        with self.assertRaises(LabelException):
            Labels(numa='-5')

        with self.assertRaises(LabelException):
            Labels(numa='8')

    def testLabelEq(self):
        lab = Labels(vlan_range='1-4096', asn='123', numa='0')
        lab1 = Labels(vlan_range='1-1024', asn='345')

        self.assertNotEqual(lab, lab1)

        lab2 = Labels(vlan_range='1-4096', asn='123', numa='0')
        self.assertEqual(lab, lab2)

        lab2 = Labels(vlan_range='1-4096', asn='123', local_name='myvlan')
        self.assertNotEqual(lab, lab2)

    def testFlagsAndTags(self):
        isl = InterfaceSliver()
        isl.flags = Flags(auto_config=True)
        isl.tags = Tags('blue', 'soft')
        self.assertTrue('blue' in isl.tags)
        self.assertTrue(isl.flags.auto_config)

    def testLocation(self):
        ns = NodeSliver()
        loc = Location(postal='100 Europa Dr., Chapel Hill, NC 27517')
        assert(loc.postal is not None)
        ns.set_properties(location=loc)
        loc1 = ns.get_property('location')
        lat, lon = loc1.to_latlon()
        self.assertGreater(lat, 35.00)
        self.assertLess(lon, -79.00)
        #print(f'{lat=} {lon=}')

    def testGateway(self):

        gw = Gateway(Labels(ipv4="192.168.1.1", ipv4_subnet="192.168.1.0/24", mac="00:11:22:33:44:55"))

        self.assertEqual(gw.gateway, "192.168.1.1")
        self.assertEqual(gw.subnet, "192.168.1.0/24")
        self.assertEqual(gw.mac, "00:11:22:33:44:55")

        with self.assertRaises(GatewayException):
            Gateway(Labels(ipv4="192.168.1.1"))

    def testNaming(self):

        s = NodeSliver()

        bad_name = 'cant have spaces'

        with self.assertRaises(ValueError):
            s.set_name(bad_name)

        s = ComponentSliver()

        bad_name = 'cant have a plus +'

        with self.assertRaises(ValueError):
            s.set_name(bad_name)

        s = NetworkServiceSliver()

        bad_name = 'cant have a :'

        with self.assertRaises(ValueError):
            s.set_name(bad_name)







