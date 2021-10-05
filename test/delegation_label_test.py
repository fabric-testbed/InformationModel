import unittest

from fim.slivers.capacities_labels import Labels, Capacities
from fim.slivers.delegations import Delegation, Delegations, DelegationType, \
    DelegationFormat, DelegationException, Pool, Pools, PoolException


class DelegationTests(unittest.TestCase):

    def testCapacityAssignment(self):
        c = Capacities(cpu=1, core=2)

        self.assertEqual(c.cpu, 1)
        self.assertEqual(c.core, 2)

        s = '{"core": 32, "disk": 3000, "ram": 384, "unit": 1}'
        c1 = Capacities.from_json(s)
        self.assertEqual(c1.unit, 1)
        self.assertEqual(c1.ram, 384)
        # because we sort the dict
        self.assertEqual(c1.to_json(), s)
        self.assertEqual(c1.core, 32)

    def testLabelAssignment(self):
        c = Labels(mac=['0C:42:A1:BE:8F:D5', '0C:42:A1:BE:8F:E9'],
                       bdf=['0000:41:00.0', '0000:41:00.1'])

        self.assertEqual(c.bdf, ['0000:41:00.0', '0000:41:00.1'])
        s = '{"bdf": ["0000:41:00.0", "0000:41:00.1"], ' \
            '"ipv4": ["192.168.1.1", "192.168.1.2"], ' \
            '"vlan": ["100", "101", "102"]}'
        l1 = Labels.from_json(s)
        self.assertEqual(l1.vlan, ["100", "101", "102"])
        print(s)
        print(l1.to_json())
        self.assertEqual(l1.to_json(), s)

    def testDelegationsSerDes(self):
        d1 = Delegation(atype=DelegationType.LABEL, aformat=DelegationFormat.SinglePool,
                       delegation_id='del1')
        d2 = Delegation(atype=DelegationType.LABEL, aformat=DelegationFormat.PoolDefinition,
                        delegation_id='del2', pool_id='pool1')
        d3 = Delegation(atype=DelegationType.LABEL, aformat=DelegationFormat.PoolReference,
                        delegation_id='del3', pool_id='pool1')
        ds = Delegations(atype=DelegationType.LABEL)
        d1.set_details(Labels(vlan_range='1-100'))
        d2.set_details(Labels(vlan_range='101-200'))
        with self.assertRaises(DelegationException) as de:
            d2.set_details(Capacities(unit=1))

        with self.assertRaises(DelegationException) as de:
            d3.set_details(Labels(vlan_range='100-200'))

        ds.add_delegations(d1)
        ds.add_delegations(d2, d3)

        json_str = ds.to_json()

        #print(json_str)

        ds1 = Delegations.from_json(json_str=json_str, atype=DelegationType.LABEL)

        self.assertEqual(ds1.delegations['del1'].get_details().vlan_range, '1-100')
        self.assertEqual(ds1.delegations['del2'].get_format(), DelegationFormat.PoolDefinition)
        self.assertEqual(ds1.delegations['del3'].get_format(), DelegationFormat.PoolReference)

        with self.assertRaises(AssertionError) as de:
            d3 = Delegation(atype=DelegationType.CAPACITY, aformat=DelegationFormat.PoolReference,
                            delegation_id='del3', pool_id='pool1')
            ds.add_delegations(d3)

    def testPools(self):
        p1 = Pool(atype=DelegationType.LABEL, pool_id='pool1', delegation_id='del1',
                  defined_on='node1', defined_for=['node2', 'node3'])
        p1.set_pool_details(Labels(vlan_range='1-100'))
        p2 = Pool(atype=DelegationType.LABEL, pool_id='pool2', delegation_id='del2',
                  defined_on='node2', defined_for=['node1', 'node4', 'node5'])
        p2.set_pool_details(Labels(vlan_range='101-200'))
        ps = Pools(atype=DelegationType.CAPACITY)
        with self.assertRaises(PoolException) as pe:
            ps.add_pool(pool=p1)
        ps = Pools(atype=DelegationType.LABEL)
        ps.add_pool(pool=p1)
        ps.add_pool(pool=p2)
        ps.build_index_by_delegation_id()
        ps.validate_pools()

        delegs = ps.generate_delegations_by_node_id()
        d1 = Delegation(atype=DelegationType.LABEL, delegation_id='del3', aformat=DelegationFormat.SinglePool)
        d1.set_details(Labels(ipv4_range='192.168.1.1-192.168.1.10'))
        delegs['node1'].add_delegations(d1)

        print(delegs)

        ps1 = Pools(atype=DelegationType.LABEL)

        for n, d in delegs.items():
            ps1.incorporate_delegation(deleg=d, node_id=n)

        self.assertEqual(ps1.get_pool_by_id(pool_id='pool2').get_delegation_id(), 'del2')
        self.assertEqual(ps1.get_pool_by_id(pool_id='pool2').get_pool_details().vlan_range, '101-200')
        print(ps1)


