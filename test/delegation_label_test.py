import unittest
from typing import Dict

from fim.slivers.capacities_labels import Labels, Capacities


class DelegationTests(unittest.TestCase):

    def testDelegationAssignment(self):
        c = Capacities()

        c.set_fields(cpu=1, core=2)

        self.assertEqual(c.cpu, 1)
        self.assertEqual(c.core, 2)

        s = '{"core": 32, "disk": 3000, "ram": 384, "unit": 1}'
        c1 = Capacities()
        c1.from_json(s)
        self.assertEqual(c1.unit, 1)
        self.assertEqual(c1.ram, 384)
        # because we sort the dict
        self.assertEqual(c1.to_json(), s)
        self.assertEqual(c1.core, 32)

    def testLabelAssignment(self):
        c = Labels()

        c.set_fields(mac=['0C:42:A1:BE:8F:D5', '0C:42:A1:BE:8F:E9'],
                     bdf=['0000:41:00.0', '0000:41:00.1'])

        self.assertEqual(c.bdf, ['0000:41:00.0', '0000:41:00.1'])
        s = '{"bdf": ["0000:41:00.0", "0000:41:00.1"], ' \
            '"ipv4": ["192.168.1.1", "192.168.1.2"], ' \
            '"vlan": ["100", "101", "102"]}'
        l1 = Labels()
        l1.from_json(s)
        self.assertEqual(l1.vlan, ["100", "101", "102"])
        print(s)
        print(l1.to_json())
        self.assertEqual(l1.to_json(), s)


