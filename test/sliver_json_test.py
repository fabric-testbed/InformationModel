import json
import unittest

import fim.user as f
from fim.slivers.json import JSONSliver
from fim.graph.abc_property_graph import ABCPropertyGraph


class TupleTests(unittest.TestCase):

    def testNodeAndServiceSlivers(self):
        t = f.ExperimentTopology()
        t.add_node(name='n1', site='RENC')
        t.nodes['n1'].capacities = f.Capacities(core=1)
        c = t.nodes['n1'].add_component(name='c1', ctype=f.ComponentType.SmartNIC, model='ConnectX-6')
        c.interface_list[0].add_child_interface(name="child1", labels=f.Labels(vlan="100"))
        d = ABCPropertyGraph.sliver_to_dict(t.nodes['n1'].get_sliver())
        t.add_node(name='n2', site='RENC')
        t.nodes['n2'].add_component(name='c2', ctype=f.ComponentType.SmartNIC, model='ConnectX-6')
        t.nodes['n2'].add_component(name='c3', ctype=f.ComponentType.NVME, model='P4510')
        t.add_network_service(name='s1', nstype=f.ServiceType.L2Bridge, interfaces=t.interface_list)
        jns = JSONSliver.sliver_to_json(t.nodes['n1'].get_sliver())
        ns1 = JSONSliver.node_sliver_from_json(jns)
        jns = JSONSliver.sliver_to_json(t.nodes['n2'].get_sliver())
        ns2 = JSONSliver.node_sliver_from_json(jns)
        ness = JSONSliver.sliver_to_json(t.network_services['s1'].get_sliver())
        nss1 = JSONSliver.network_service_sliver_from_json(ness)

        self.assertEqual(ns1.capacities.core, 1)
        self.assertEqual(len(ns1.attached_components_info.list_devices()), 1)
        for c in ns1.attached_components_info.list_devices():
            print(c)
            for ns in c.network_service_info.network_services.values():
                for ifs in ns.interface_info.interfaces.values():
                    print(ifs)
                    if "p1" in ifs.get_name():
                        self.assertTrue(ifs.interface_info is not None)
                        for cifs in ifs.interface_info.interfaces.values():
                            print(cifs)

        self.assertEqual(len(ns2.attached_components_info.list_devices()), 2)
        self.assertEqual(len(nss1.interface_info.list_interfaces()), 4)
        inames = [i.resource_name for i in nss1.interface_info.list_interfaces()]
        self.assertTrue('n2-c2-p1' in inames)
        self.assertEqual(ns1.attached_components_info.list_devices()[0].
                         network_service_info.list_services()[0].
                         interface_info.list_interfaces()[0].capacities.bw, 100)



