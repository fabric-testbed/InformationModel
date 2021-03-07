import fim.user as fu
from fim.graph.abc_property_graph import ABCPropertyGraphConstants
from fim.graph.neo4j_property_graph import Neo4jGraphImporter, Neo4jPropertyGraph
from fim.graph.slices.neo4j_asm import Neo4jASM, Neo4jASMFactory

neo4j = {"url": "neo4j://0.0.0.0:7687",
         "user": "neo4j",
         "pass": "password",
         "import_host_dir": "/Users/ibaldin/workspace-fabric/InfoModelTests/neo4j/imports/",
         "import_dir": "/imports"}

"""
This is not a unit test in a proper sense. It is a harness to manually validate operation
until proper unit tests are implemented.
"""


def test_basic_neo4j():
    """
    Some basic Neo4j tests
    :return:
    """
    n4j_imp = Neo4jGraphImporter(url=neo4j["url"], user=neo4j["user"],
                                 pswd=neo4j["pass"],
                                 import_host_dir=neo4j["import_host_dir"],
                                 import_dir=neo4j["import_dir"])
    n4j_pg = Neo4jPropertyGraph(graph_id="beef-beed", importer=n4j_imp)
    n4j_pg.add_node(node_id="dead-beef", label=ABCPropertyGraphConstants.CLASS_NetworkNode)
    n4j_pg.add_node(node_id="beef-dead", label=ABCPropertyGraphConstants.CLASS_Component,
                    props={"some_property": "some_value"})
    n4j_pg.add_link(node_a="dead-beef", node_b="beef-dead", rel=ABCPropertyGraphConstants.REL_HAS)
    n4j_imp.delete_all_graphs()


def test_neo4j_asm():
    """
    Test Neo4j ASM implementation
    :return:
    """
    n4j_imp = Neo4jGraphImporter(url=neo4j["url"], user=neo4j["user"],
                                 pswd=neo4j["pass"],
                                 import_host_dir=neo4j["import_host_dir"],
                                 import_dir=neo4j["import_dir"])
    n4j_asm = Neo4jASM(graph_id="bead-bead", importer=n4j_imp)
    n4j_asm.add_node(node_id="dead-beef", label=ABCPropertyGraphConstants.CLASS_NetworkNode)
    n4j_asm.update_node_property(node_id="dead-beef", prop_name=ABCPropertyGraphConstants.PROP_NAME,
                                 prop_val="MyNode")
    n4j_asm.add_node(node_id="beef-dead", label=ABCPropertyGraphConstants.CLASS_Component,
                     props={"Name": "MyComponent"})
    assert(n4j_asm.check_node_name(node_id="beef-dead", label=ABCPropertyGraphConstants.CLASS_Component,
                                   name="MyComponent"))
    assert(n4j_asm.check_node_unique(label=ABCPropertyGraphConstants.CLASS_Component,
                                     name="MyComponent") is False)
    assert (n4j_asm.check_node_unique(label=ABCPropertyGraphConstants.CLASS_NetworkNode,
                                      name="MyNode1") is True)
    n4j_asm.set_mapping(node_id="dead-beef", to_graph_id="some_graph", to_node_id="some_id")
    map_graph, map_node = n4j_asm.get_mapping(node_id="dead-beef")

    assert(map_graph == "some_graph")
    assert(map_node == "some_id")

    tup = n4j_asm.get_mapping(node_id="beef-dead")
    assert(tup is None)

    n4j_imp.delete_all_graphs()


def test_asm_transfer():
    """
    Test creating ASM in NetworkX and transition to Neo4j
    :return:
    """
    t = fu.ExperimentTopology()
    n1 = t.add_node(name='n1', site='RENC')
    cap = fu.Capacities()
    cap.set_fields(core=4, ram=64, disk=500)
    n1.set_properties(capacities=cap, image_type='qcow2', image_ref='default_centos_8')
    n1.add_component(ctype=fu.ComponentType.SmartNIC, model='ConnectX-6', name='nic1')
    n2 = t.add_node(name='n2', site='RENC')
    n2.set_properties(capacities=cap, image_type='qcow2', image_ref='default_centos_8')
    n2.add_component(ctype=fu.ComponentType.GPU, model='RTX6000', name='nic2')
    slice_graph = t.serialize()

    neo4j_graph_importer = Neo4jGraphImporter(url=neo4j["url"], user=neo4j["user"],
                                              pswd=neo4j["pass"],
                                              import_host_dir=neo4j["import_host_dir"],
                                              import_dir=neo4j["import_dir"])

    #t.serialize(file_name='slice_graph.graphml')
    generic_graph = neo4j_graph_importer.import_graph_from_string(graph_string=slice_graph,
                                                                  graph_id=t.graph_model.graph_id)
    asm_graph = Neo4jASMFactory.create(generic_graph)
    node_ids = asm_graph.list_all_node_ids()
    print(node_ids)
    node_id = next(iter(node_ids))
    asm_graph.set_mapping(node_id=node_id, to_graph_id="dead-beef",
                          to_node_id='beef-beef')
    to_graph, to_node = asm_graph.get_mapping(node_id=node_id)
    assert(to_graph == "dead-beef")
    assert(to_node == "beef-beef")
    #neo4j_graph_importer.delete_all_graphs()


if __name__ == "__main__":

    print("Running basic tests")
    test_basic_neo4j()

    print("Running Neo4j ASM tests")
    test_neo4j_asm()

    print("Running ASM transfer tests")
    test_asm_transfer()

