import unittest

from fim.graph.typed_tuples import Label, Capacity, Location
from fim.slivers.capacities_labels import Capacities, Labels
from fim.slivers.delegations import Pool, Pools, DelegationType


class TupleTests(unittest.TestCase):

    def testLabel(self):
        l = Label(atype="mac", aval="something")
        assert l.get_as_string() == "mac:something"
        l1 = Label(atype="mac", aval="something else")
        l2 = Label(atype="bdf", aval="other")
        assert l1.check_type(l2) is False
        assert l.check_type(l1) is True

    def testCapacity(self):
        c = Capacity(fromstring="cpu:2")
        a = c.get_as_string()
        c1 = Capacity(atype="ram", aval=1000)
        c1.parse_from_string(a)
        assert c.get_as_string() == c1.get_as_string()

    def testGetLabelFields(self):
        l = Label(atype="mac", aval="something")
        l1s = "mac:00:00:12:12:12:12"
        l.parse_from_string(l1s)

        assert l.get_type() == "mac"
        assert l.get_val() == "00:00:12:12:12:12"

    def testLocation(self):
        l2 = "latlon: 71.2345, 85.231"
        l = Location(fromstring=l2)
        assert l.get_type() == "latlon"
        assert l.get_val() == " 71.2345, 85.231"

    def testPool(self):
        p = Pool(atype=DelegationType.LABEL, pool_id="pool1")
        p.set_delegation_id(delegation_id="del1")
        assert p.get_delegation_id() == "del1"
        p.set_defined_on(node_id="node1")
        p.set_defined_for(node_id_list=["node4"])
        p.add_defined_for(node_ids=["node2", "node3", "node1"])
        assert "node1" == p.get_defined_on()
        assert "node2" in p.get_defined_for()
        assert "node1" in p.get_defined_for()

    def testPools(self):
        p = Pool(atype=DelegationType.LABEL, pool_id="pool1")
        p.set_delegation_id(delegation_id="del1")
        p.set_defined_on(node_id="node1")
        p.set_defined_for(node_id_list=["node4"])
        p.add_defined_for(node_ids=["node2", "node3", "node1"])
        p.set_pool_details(caporlab=Capacities(cpu=2, ram=1024))

        pp = Pools(atype=DelegationType.LABEL)
        pp.add_pool(pool=p)
        pp.build_index_by_delegation_id()
        p1l = pp.get_pools_by_delegation_id(delegation_id="del1")
        p2 = pp.get_pool_by_id(pool_id="pool1")
        assert p2 in p1l

if __name__ == "__main__":
    unittest.main()
