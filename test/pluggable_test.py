import unittest

from fim.pluggable import PluggableType, PluggableRegistry, \
    ABCPluggable, AMPluggable, BrokerPluggable, OrchestratorPluggable
from fim.graph.abc_property_graph import ABCPropertyGraph


class MyPlug:

    def __init__(self):
        print("Initializing MyPlug")
        self.param = "param"

    def plug_produce_bqm(self, *, cbm: ABCPropertyGraph, **kwargs):
        return f"Graph is {cbm} with {self.param}"


class MyPlug1:

    def __init__(self):
        print("Initializing MyPlug1")

    def plug_blah(self):
        print("Blah")


class TestPluggable(unittest.TestCase):

    def testRegistrySingleton(self):
        r = PluggableRegistry()
        r1 = PluggableRegistry()

        assert r.instance is r1.instance

    def testEmptyRegistered(self):

        r = PluggableRegistry()

        assert r.pluggable_registered(t=PluggableType.AM) is False
        assert r.pluggable_registered(t=PluggableType.Broker) is False
        assert r.pluggable_registered(t=PluggableType.Orchestrator) is False

    def testRegistration(self):

        r = PluggableRegistry()

        r.register_pluggable(t=PluggableType.Broker, p=MyPlug)

        assert r.pluggable_registered(t=PluggableType.Broker) is True

        methods = r.get_implemented_methods(t=PluggableType.Broker)

        assert "plug_produce_bqm" in methods

        c = r.get_method_callable(t=PluggableType.Broker, method='plug_produce_bqm')

        assert callable(c) is True

        ret = c(cbm=4)

        assert ret == "Graph is 4 with param"


if __name__ == "__main__":

    unittest.main()