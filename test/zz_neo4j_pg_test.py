import unittest

import yaml

import fim.user as fu
from fim.graph.abc_property_graph import ABCPropertyGraphConstants, ABCPropertyGraph
from fim.graph.neo4j_property_graph import Neo4jGraphImporter, Neo4jPropertyGraph
from fim.graph.resources.neo4j_cbm import Neo4jCBMGraph
from fim.graph.slices.neo4j_asm import Neo4jASM, Neo4jASMFactory
from fim.graph.resources.neo4j_arm import Neo4jARMGraph

from fim.slivers.attached_components import AttachedComponentsInfo, ComponentSliver, ComponentType
from fim.slivers.network_node import NodeType


class Neo4jTests(unittest.TestCase):
    """
    Please note this depends on substrate_topology_test.py executing first as it
    creates graphml files needed here.
    """

    neo4j = {"url": "neo4j://0.0.0.0:7687",
             "user": "neo4j",
             "pass": "password",
             "import_host_dir": "neo4j/imports",
             "import_dir": "/imports"}

    FIM_CONFIG_YAML = "./fim_config.yml"

    try:
        with open(FIM_CONFIG_YAML, 'r') as config_file:
            yaml_config = yaml.safe_load(config_file)
            neo4j = yaml_config.get("neo4j")
            print(neo4j)
    except IOError:
        print(f"Unable to open config file {FIM_CONFIG_YAML}, Using the Default Config")

    def setUp(self) -> None:
        self.n4j_imp = Neo4jGraphImporter(url=self.neo4j["url"], user=self.neo4j["user"],
                                          pswd=self.neo4j["pass"],
                                          import_host_dir=self.neo4j["import_host_dir"],
                                          import_dir=self.neo4j["import_dir"])

    def test_basic_neo4j(self):
        """
        Some basic Neo4j tests
        :return:
        """

        n4j_pg = Neo4jPropertyGraph(graph_id="beef-beed", importer=self.n4j_imp)
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

        self.n4j_imp.delete_all_graphs()

    def test_neo4j_asm(self):
        """
        Test Neo4j ASM implementation
        :return:
        """
        n4j_asm = Neo4jASM(graph_id="bead-bead", importer=self.n4j_imp)
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

        # this is how to set a mapping to BQM, for example
        n4j_asm.set_mapping(node_id="dead-beef", to_graph_id="some_graph", to_node_id="some_id")
        map_graph, map_node = n4j_asm.get_mapping(node_id="dead-beef")

        assert(map_graph == "some_graph")
        assert(map_node == "some_id")

        tup = n4j_asm.get_mapping(node_id="beef-dead")
        assert(tup is None)

        self.n4j_imp.delete_all_graphs()

    def test_asm_transfer(self):
        """
        Test creating ASM in NetworkX and transition to Neo4j
        :return:
        """
        t = fu.ExperimentTopology()
        n1 = t.add_node(name='n1', site='RENC')
        cap = fu.Capacities(core=4, ram=64, disk=500)
        n1.set_properties(capacities=cap, image_type='qcow2', image_ref='default_centos_8')
        n1.add_component(ctype=fu.ComponentType.SmartNIC, model='ConnectX-6', name='nic1')
        n2 = t.add_node(name='n2', site='RENC')
        n2.set_properties(capacities=cap, image_type='qcow2', image_ref='default_centos_8')
        n2.add_component(ctype=fu.ComponentType.GPU, model='RTX6000', name='nic2')
        slice_graph = t.serialize()

        #t.serialize(file_name='slice_graph.graphml')
        generic_graph = self.n4j_imp.import_graph_from_string(graph_string=slice_graph,
                                                              graph_id=t.graph_model.graph_id)
        asm_graph = Neo4jASMFactory.create(generic_graph)
        node_ids = asm_graph.list_all_node_ids()
        print('ASM Node IDs')
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

        # set allocated capacities or labels
        # in orchestrator
        alloc_labels = fu.Labels(instance_parent="worker_node-1")
        neo4j_topo.nodes['n1'].set_properties(label_allocations=alloc_labels)
        # in AM
        provisioned_labels = fu.Labels(instance="open-stack-instance-id-123")
        neo4j_topo.nodes['n1'].set_properties(labels=provisioned_labels)
        ri = fu.ReservationInfo(reservation_id="01234", reservation_state='READY')
        neo4j_topo.nodes['n1'].set_properties(reservation_info=ri)

        self.n4j_imp.delete_all_graphs()

    def test_arm_load(self):
        """
        Load an ARM, transform to ADM, then merge into BQM
        :return:
        """

        plain_neo4j = self.n4j_imp.import_graph_from_file_direct(graph_file='RENCI-ad.graphml')

        print("Validating ARM graph")
        plain_neo4j.validate_graph()

        cbm = Neo4jCBMGraph(importer=self.n4j_imp)

        site_arm = Neo4jARMGraph(graph=Neo4jPropertyGraph(graph_id=plain_neo4j.graph_id,
                                                          importer=self.n4j_imp))
        # generate a dict of ADMs from site graph ARM
        site_adms = site_arm.generate_adms()
        print('ADMS' + str(site_adms.keys()))

        # desired ADM is under 'primary'
        site_adm = site_adms['primary']
        cbm.merge_adm(adm=site_adm)

        cbm.validate_graph()
        print('CBM ID is ' + cbm.graph_id)

        # test delegation format
        list_of_nodes = cbm.get_matching_nodes_with_components(
            label=ABCPropertyGraphConstants.CLASS_NetworkNode,
            props={'Name': 'renc-w3'})

        print('Deleting ADM and ARM graphs')
        for adm in site_adms.values():
            adm.delete_graph()
        site_arm.delete_graph()


        #print("Printing component models")
        #for n in cbm.get_all_nodes_by_class(label=ABCPropertyGraphConstants.CLASS_Component):
        #    _, prop = cbm.get_node_properties(node_id=n)
        #    if prop.get(ABCPropertyGraphConstants.PROP_MODEL, None) is not None:
        #        print(prop[ABCPropertyGraphConstants.PROP_MODEL])

        # test CBM querying
        node_props = { 'Site': 'RENC', 'Type': 'Server' }
        list_of_nodes = cbm.get_matching_nodes_with_components(label=ABCPropertyGraphConstants.CLASS_NetworkNode,
                                                               props=node_props)
        self.assertEqual(len(list_of_nodes), 3)

        # construct some components
        c1 = ComponentSliver()
        c1.resource_name = 'c1'
        c1.resource_type = ComponentType.GPU
        c1.resource_model = 'Tesla T4'
        c2 = ComponentSliver()
        c2.resource_name = 'c2'
        c2.resource_type = ComponentType.SharedNIC
        c3 = ComponentSliver()
        c3.resource_name = 'c3'
        c3.resource_type = ComponentType.SmartNIC
        c3.resource_model = 'ConnectX-5'
        c4 = ComponentSliver()
        c4.resource_name = 'c4'
        c4.resource_type = ComponentType.SmartNIC
        c4.resource_model = 'ConnectX-5'

        ci = AttachedComponentsInfo()
        ci.add_device(c1)
        ci.add_device(c2)
        ci.add_device(c3)
        ci.add_device(c4)
        list_of_nodes = cbm.get_matching_nodes_with_components(label=ABCPropertyGraphConstants.CLASS_NetworkNode,
                                                               props=node_props, comps=ci)
        print(f'Testing a mix of components #1 {list_of_nodes=}')
        self.assertEqual(len(list_of_nodes), 1)

        c5 = ComponentSliver()
        c5.resource_name = 'c5'
        c5.resource_type = ComponentType.SmartNIC
        c5.resource_model = 'ConnectX-5'
        ci.add_device(c5)
        list_of_nodes = cbm.get_matching_nodes_with_components(label=ABCPropertyGraphConstants.CLASS_NetworkNode,
                                                               props=node_props, comps=ci)
        print(f'Testing a mix of components #2 {list_of_nodes=} (expected empty)')
        self.assertEqual(len(list_of_nodes), 0)

        # test for SR-IOV shared cards
        ci = AttachedComponentsInfo()
        c6 = ComponentSliver()
        c6.resource_name = 'c6'
        c6.resource_type = ComponentType.SharedNIC
        c6.resource_model = 'ConnectX-6'
        ci.add_device(c6)

        c7 = ComponentSliver()
        c7.resource_name = 'c7'
        c7.resource_type = ComponentType.SharedNIC
        c7.resource_model = 'ConnectX-6'
        ci.add_device(c7)

        list_of_nodes = cbm.get_matching_nodes_with_components(label=ABCPropertyGraphConstants.CLASS_NetworkNode,
                                                               props=node_props, comps=ci)
        print(f'Testing a mix of components #3 {list_of_nodes=}')
        self.assertEqual(len(list_of_nodes), 3)

        self.n4j_imp.delete_all_graphs()

    def test_network_ad_load(self):

        cbm = Neo4jCBMGraph(importer=self.n4j_imp)

        ad = 'Network-ad.graphml'

        plain_neo4j = self.n4j_imp.import_graph_from_file_direct(graph_file=ad)
        print(f"Validating ARM graph {ad}")
        plain_neo4j.validate_graph()

        site_arm = Neo4jARMGraph(graph=Neo4jPropertyGraph(graph_id=plain_neo4j.graph_id,
                                                          importer=self.n4j_imp))
        print(f'ARM Graph {site_arm.graph_id}')

        # generate a dict of ADMs from site graph ARM
        site_adms = site_arm.generate_adms()
        print('ADMS ' + str(site_adms.keys()))

        # desired ADM is under 'primary'
        site_adm = site_adms['primary']
        cbm.merge_adm(adm=site_adm)

        print('Deleting ADM and ARM graphs')
        for adm in site_adms.values():
            adm.delete_graph()
        site_arm.delete_graph()

        cbm.validate_graph()
        print('CBM ID is ' + cbm.graph_id)

        self.n4j_imp.delete_all_graphs()

    def test_3_site_load(self):

        # these are produced by substrate tests
        site_ads = ['RENCI-ad.graphml', 'UKY-ad.graphml', 'LBNL-ad.graphml', 'Network-ad.graphml']

        cbm = Neo4jCBMGraph(importer=self.n4j_imp)

        adm_ids = dict()
        site_arms = dict()

        for ad in site_ads:
            plain_neo4j = self.n4j_imp.import_graph_from_file_direct(graph_file=ad)
            print(f"Validating ARM graph {ad} with id {plain_neo4j.graph_id}")
            plain_neo4j.validate_graph()

            site_arms[ad] = Neo4jARMGraph(graph=Neo4jPropertyGraph(graph_id=plain_neo4j.graph_id,
                                                                   importer=self.n4j_imp))
            # generate a dict of ADMs from site graph ARM
            site_adms = site_arms[ad].generate_adms()
            print('ADMS ' + str(site_adms.keys()))
            for adm_id in site_adms.keys():
                print(f'  ADM id {site_adms[adm_id].graph_id}')

            # desired ADM is under 'primary'
            site_adm = site_adms['primary']
            cbm.merge_adm(adm=site_adm)

            print('Deleting ADM and ARM graphs')
            for adm in site_adms.values():
                adm_ids[ad] = adm.graph_id
                adm.delete_graph()
            #site_arms[ad].delete_graph()

        cbm.validate_graph()
        print('CBM ID is ' + cbm.graph_id)

        print('Finding intersite links')
        links = cbm.get_intersite_links()
        print(links)
        self.assertTrue(len(links) == 3)
        ls = set()
        for l in links:
            ls.add(l[1])
        self.assertTrue('port+renc-data-sw:HundredGigE0/0/0/26-Wave' in ls and
               'port+renc-data-sw:HundredGigE0/0/0/27-Wave' in ls and
               'port+uky-data-sw:HundredGigE0/0/0/27-Wave' in ls)
        print('Done')

        ad = 'Network-ad.graphml'
        print(f"Unmerging graph {adm_ids[ad]}")
        cbm.unmerge_adm(graph_id=adm_ids[ad])
        print(f"Merging back")
        site_adms = site_arms[ad].generate_adms()
        site_adm = site_adms['primary']
        cbm.merge_adm(adm=site_adm)
        network_old_adm_id = adm_ids[ad]
        for adm in site_adms.values():
            adm_ids[ad] = adm.graph_id
            adm.delete_graph()

        ad = 'RENCI-ad.graphml'
        print(f"Unmerging graph {adm_ids[ad]}")
        cbm.unmerge_adm(graph_id=adm_ids[ad])
        print(f"Merging back with same adm_id {adm_ids[ad]}")
        site_adms = site_arms[ad].generate_adms(delegation_guids={'primary': adm_ids[ad]})
        site_adm = site_adms['primary']
        cbm.merge_adm(adm=site_adm)

        # verify the right ADM ids are used
        all_nodes = cbm.get_all_network_nodes()
        found = False
        node_props = None
        # find the node named 'renc-data-sw'. Its StructuralInfo adm_graph_ids
        # should have the adm_ids['RENCI-ad.graphml'] because it was reused
        # and it should NOT have the adm_ids['Network-ad.graphml'] because a
        # new one was generated
        for node in all_nodes:
            _, node_props = cbm.get_node_properties(node_id=node)
            if node_props[ABCPropertyGraph.PROP_NAME] == 'renc-data-sw':
                found = True
                break
        self.assertTrue(found)
        node_sliver = ABCPropertyGraph.node_sliver_from_graph_properties_dict(node_props)
        self.assertIn(adm_ids['RENCI-ad.graphml'],
                      node_sliver.structural_info.adm_graph_ids)
        self.assertNotIn(network_old_adm_id,
                         node_sliver.structural_info.adm_graph_ids)

        for adm in site_adms.values():
            adm_ids[ad] = adm.graph_id
            adm.delete_graph()

        self.n4j_imp.delete_all_graphs()

    def test_path_with_hops(self):
        self.n4j_imp.delete_all_graphs()

        # these are produced by substrate tests
        site_ads = ['models/RENC.graphml', 'models/UKY.graphml', 'models/LBNL.graphml', 'models/Network-dev.graphml']

        cbm = Neo4jCBMGraph(importer=self.n4j_imp)

        adm_ids = dict()
        site_arms = dict()

        for ad in site_ads:
            plain_neo4j = self.n4j_imp.import_graph_from_file_direct(graph_file=ad)
            print(f"Validating ARM graph {ad} with id {plain_neo4j.graph_id}")
            plain_neo4j.validate_graph()

            site_arms[ad] = Neo4jARMGraph(graph=Neo4jPropertyGraph(graph_id=plain_neo4j.graph_id,
                                                                   importer=self.n4j_imp))
            # generate a dict of ADMs from site graph ARM
            site_adms = site_arms[ad].generate_adms()
            print('ADMS ' + str(site_adms.keys()))
            for adm_id in site_adms.keys():
                print(f'  ADM id {site_adms[adm_id].graph_id}')

            # desired ADM is under 'primary'
            site_adm = site_adms['primary']
            cbm.merge_adm(adm=site_adm)

            print('Deleting ADM and ARM graphs')
            for adm in site_adms.values():
                adm_ids[ad] = adm.graph_id
                adm.delete_graph()
            #site_arms[ad].delete_graph()

        cbm.validate_graph()
        print('CBM ID is ' + cbm.graph_id)

        renc_sw_node_id = "node+renc-data-sw:ip+192.168.11.3"
        lbnl_sw_node_id = "node+lbnl-data-sw:ip+192.168.13.3"
        uky_sw_node_id = "node+uky-data-sw:ip+192.168.12.3"
        hops = [f"{renc_sw_node_id}-ns"]
        path = cbm.get_nodes_on_path_with_hops(node_a=lbnl_sw_node_id, node_z=uky_sw_node_id, hops=hops, cut_off=200)
        print(f"Source: {lbnl_sw_node_id}  End: {uky_sw_node_id} Hops: {hops} Path:  {path}")

        assert (len(path) == 11)

        hops = ["node+max-data-sw:ip+192.168.12.3-ns"]
        path = cbm.get_nodes_on_path_with_hops(node_a=renc_sw_node_id, node_z=lbnl_sw_node_id, hops=hops)

        assert (len(path) == 0)

        cbm.delete_graph()
