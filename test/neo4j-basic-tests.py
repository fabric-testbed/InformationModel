import fim.user as fu
from fim.graph.abc_property_graph import ABCPropertyGraphConstants, ABCPropertyGraph
from fim.graph.neo4j_property_graph import Neo4jGraphImporter, Neo4jPropertyGraph
from fim.graph.resources.neo4j_cbm import Neo4jCBMGraph
from fim.graph.slices.neo4j_asm import Neo4jASM, Neo4jASMFactory
from fim.graph.resources.neo4j_arm import Neo4jARMGraph

import fim.user as fu

neo4j = {"url": "neo4j://0.0.0.0:7687",
         "user": "neo4j",
         "pass": "password",
         "import_host_dir": "/Users/ibaldin/workspace-fabric/InfoModelTests/neo4j/imports/",
         "import_dir": "/imports"}

"""
This is not a unit test in a proper sense. It is a harness to manually validate operation
until proper unit tests are implemented.
"""

class MyPlug:
    """
    Fake pluggable BQM broker class for FIM testing
    """
    def __init__(self):
        print("Creating MyPlug")

    def plug_produce_bqm(self, *, cbm: ABCPropertyGraph, **kwargs) -> ABCPropertyGraph:
        print(f"Producing CBM as BQM {kwargs}")
        return cbm

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
    _, props = n4j_pg.get_node_properties(node_id='beef-dead')
    print(props)
    assert props.get('some_property', None) is not None
    n4j_pg.unset_node_property(node_id='beef-dead', prop_name='some_property')
    _, props = n4j_pg.get_node_properties(node_id='beef-dead')
    print(props)
    assert props.get('some_property', None) is None

    n4j_pg.add_link(node_a='dead-beef', node_b='beef-dead', rel=ABCPropertyGraphConstants.REL_HAS,
                    props={'some_prop': 2})
    lt, props = n4j_pg.get_link_properties(node_a='dead-beef', node_b='beef-dead')
    assert lt == ABCPropertyGraph.REL_HAS
    assert 'some_prop' in props.keys()
    n4j_pg.unset_link_property(node_a='dead-beef', node_b='beef-dead', kind=ABCPropertyGraph.REL_HAS,
                               prop_name='some_prop')
    lt, props = n4j_pg.get_link_properties(node_a='dead-beef', node_b='beef-dead')
    assert 'some_prop' not in props.keys()

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

    # this is how you map  to BQM
    asm_graph.set_mapping(node_id=node_id, to_graph_id="dead-beef",
                          to_node_id='beef-beef')
    to_graph, to_node = asm_graph.get_mapping(node_id=node_id)

    assert(to_graph == "dead-beef")
    assert(to_node == "beef-beef")

    # test creating an experiment topology as a cast of an ASM loaded into Neo4j
    neo4j_topo = fu.ExperimentTopology()
    neo4j_topo.cast(asm_graph=asm_graph)

    print(f'New topology on top of {neo4j_topo.graph_model.graph_id}')
    print(neo4j_topo.nodes)

    neo4j_graph_importer.delete_all_graphs()


def test_arm_load():
    """
    Load an ARM, transform to ADM, then merge into BQM
    :return:
    """

    n4j_imp = Neo4jGraphImporter(url=neo4j["url"], user=neo4j["user"],
                                 pswd=neo4j["pass"],
                                 import_host_dir=neo4j["import_host_dir"],
                                 import_dir=neo4j["import_dir"])
    plain_neo4j = n4j_imp.import_graph_from_file_direct(graph_file='../RENCI-ad.graphml')

    print("Validating ARM graph")
    plain_neo4j.validate_graph()

    cbm = Neo4jCBMGraph(importer=n4j_imp)

    site_arm = Neo4jARMGraph(graph=Neo4jPropertyGraph(graph_id=plain_neo4j.graph_id,
                                                      importer=n4j_imp))
    # generate a dict of ADMs from site graph ARM
    site_adms = site_arm.generate_adms()
    print('ADMS' + str(site_adms.keys()))

    # desired ADM is under 'primary'
    site_adm = site_adms['primary']
    cbm.merge_adm(adm=site_adm)

    print('Deleting ADM and ARM graphs')
    for adm in site_adms.values():
        adm.delete_graph()
    site_arm.delete_graph()

    print('CBM ID is ' + cbm.graph_id)


if __name__ == "__main__":

    print("Running basic tests")
    test_basic_neo4j()

    print("Running Neo4j ASM tests")
    test_neo4j_asm()

    print("Running ASM transfer tests")
    test_asm_transfer()

    print("Testing loading ARM")
    test_arm_load()

