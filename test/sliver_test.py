import unittest

from fim.slivers.attached_components import ComponentSliver, ComponentType, AttachedComponentsInfo
from fim.slivers.network_node import NodeSliver, NodeType
from fim.slivers.network_link import NetworkLinkSliver
from fim.slivers.switch_fabric import SwitchFabricSliver, SwitchFabricInfo


class TestSlivers(unittest.TestCase):

    def testComponentSliver(self):
        cs = ComponentSliver()
        cs.set_property('details', 'these are details')
        cs.set_properties(resource_type=ComponentType.GPU, resource_name='name')

        self.assertEqual(cs.get_details(), 'these are details')
        self.assertEqual(cs.get_resource_type(), ComponentType.GPU)
        self.assertEqual(cs.get_resource_name(), 'name')

        cs1 = ComponentSliver()
        cs1.set_property('details', 'these are other details')
        cs1.set_properties(resource_type=ComponentType.GPU, resource_name='name1')

        cs2 = ComponentSliver()
        cs2.set_property('details', 'these are some details')
        cs2.set_properties(resource_type=ComponentType.SmartNIC, resource_name='name2')

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
        ns = NodeSliver()
        ns.set_properties(resource_name='node1', resource_type=NodeType.Server,
                          management_ip='192.168.1.1')
        with self.assertRaises(ValueError) as ve:
            ns.set_property('management_ip', '192.168.1.x')
