from fim.graph.typed_tuples import Label, Capacity

if __name__ == "__main__":

    l = Label(atype="mac", aval="something")
    print(l)
    print(l.get_as_json())
    l1 = Label(atype="mac", aval="something else")
    l2 = Label(atype="bdf", aval="other")
    assert l1.check_type(l2) is False
    assert l.check_type(l1) is True

    c = Capacity(atype="cpu", aval=2)
    print(c)
    print(c.get_as_json())

    a = c.get_as_json()

    c1 = Capacity(atype="ram", aval=1000)
    print(c1)
    c1.parse_from_json(a)
    print(c1)

    l1s = "mac:00:00:12:12:12:12"
    l.parse_from_string(l1s)
    print(l)
    print(l.get_type())