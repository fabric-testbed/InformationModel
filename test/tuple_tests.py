from fim.graph.typed_tuples import Label, Capacity, Location
from fim.graph.delegations import Pool, Pools, DelegationType

if __name__ == "__main__":

    l = Label(atype="mac", aval="something")
    print(l)
    print(l.get_as_string())
    l1 = Label(atype="mac", aval="something else")
    l2 = Label(atype="bdf", aval="other")
    assert l1.check_type(l2) is False
    assert l.check_type(l1) is True

    c = Capacity(fromstring="cpu:2")
    print(c)
    print(c.get_as_string())

    a = c.get_as_string()

    c1 = Capacity(atype="ram", aval=1000)
    print(c1)
    c1.parse_from_string(a)
    print(c1)

    l1s = "mac:00:00:12:12:12:12"
    print(f"Parsing {l1s}")
    l.parse_from_string(l1s)
    print(l)
    print(l.get_type())
    print(l.get_val())

    l2 = "latlon: 71.2345, 85.231"
    l = Location(fromstring=l2)
    print(l)
    print(l.get_type())
    print(l.get_val())

    p = Pool(atype=DelegationType.LABEL, pool_id="pool1")
    p.set_delegation_id(delegation_id="del1")
    print(p)

    p.set_defined_on(node_id="node1")
    p.set_defined_for(node_id_list=["node4"])
    p.add_defined_for(node_ids=["node2", "node3"])
    print(p)

    print("POOLS")
    pp = Pools(atype=DelegationType.LABEL)
    pp.add_pool(pool=p)
    p1 = pp.get_pools_by_delegation(delegation_id="del1")
    print(f"Returned pool {p1}")
    pp.add_pool_defined_for(pool_id="pool1", node_ids=[ "node7"])
    p1 = pp.get_pools_by_delegation(delegation_id="del1")
    print(f"Returned pool {p1}")
    p2 = pp.get_pool_by_id(pool_id="pool1")
    assert p1 is p2