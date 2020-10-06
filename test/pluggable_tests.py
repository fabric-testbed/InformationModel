from fim.pluggable import PluggableType, PluggableRegistry, \
    ABCPluggable, AMPluggable, BrokerPluggable, OrchestratorPluggable
import inspect
from fim.graph.abc_property_graph import ABCPropertyGraph


class MyPlug:

    def __init__(self):
        print("Initializing MyPlug")
        self.param = "param"

    def plug_produce_bqm(self, *, cbm: ABCPropertyGraph, **kwargs) -> ABCPropertyGraph:
        print(f"Graph is {cbm} with {self.param}")
        return None

class MyPlug1:

    def __init__(self):
        print("Initializing MyPlug1")

    def plug_blah(self):
        print("Blah")


if __name__ == "__main__":

    print(ABCPluggable.get_pluggable_methods())
    print(AMPluggable.get_pluggable_methods())
    print(BrokerPluggable.get_pluggable_methods())
    print(OrchestratorPluggable.get_pluggable_methods())

    print(ABCPluggable.get_implemented_methods(MyPlug))

    r = PluggableRegistry()

    print(r.pluggable_registered(t=PluggableType.AM))
    print(r.pluggable_registered(t=PluggableType.Orchestrator))
    print(r.pluggable_registered(t=PluggableType.Broker))

    r.register_pluggable(t=PluggableType.Broker, p=MyPlug)
    #r.register_pluggable(t=PluggableType.Orchestrator, p=MyPlug1)

    print(r.pluggable_registered(t=PluggableType.AM))
    print(r.pluggable_registered(t=PluggableType.Orchestrator))
    print(r.pluggable_registered(t=PluggableType.Broker))

    print("Implemented methods are " + str(r.get_implemented_methods(t=PluggableType.Broker)))

    c = r.get_method_callable(t=PluggableType.Broker, method='plug_produce_bqm')

    print(f"Calling callable {c}")

    c(cbm=4)

    p = PluggableRegistry()

    print(p.pluggable_registered(t=PluggableType.Broker))

    print(p.get_implemented_methods(t=PluggableType.Broker))

    #p.register_pluggable(t=PluggableType.Broker, p=MyPlug)