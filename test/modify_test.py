import unittest
import uuid
from typing import Any

import fim.user as f

from fim.graph.neo4j_property_graph import Neo4jGraphImporter
from fim.slivers.attached_components import ComponentType
from fim.slivers.network_service import ServiceType
from fim.user.topology import TopologyDiff, TopologyDiffTuple


class ModifyTest(unittest.TestCase):

    neo4j = {"url": "neo4j://0.0.0.0:7687",
             "user": "neo4j",
             "pass": "password",
             "import_host_dir": "neo4j/imports/",
             "import_dir": "/imports"}

    def initialTopo(self):
        """
        Define an initial topology before modify
        """
        nA = self.topoA.add_node(name='NodeA', site='RENC')
        nic1 = nA.add_component(name='nic1', ctype=ComponentType.SmartNIC, model='ConnectX-6')
        nic3 = nA.add_component(name='nic3', ctype=ComponentType.SharedNIC, model='ConnectX-6')
        nC = self.topoA.add_node(name='NodeC', site='RENC')
        nic2 = nC.add_component(name='nic2', ctype=ComponentType.SharedNIC, model='ConnectX-6')
        nC.add_component(name='drive1', ctype=ComponentType.NVME, model='P4510')
        self.topoA.add_network_service(name='bridge1', nstype=ServiceType.L2Bridge,
                                       interfaces=[nic3.interface_list[0], nic2.interface_list[0]])

        self.topoA.add_network_service(name='bridge2', nstype=ServiceType.L2Bridge)
        nD = self.topoA.add_node(name='NodeD', site='UKY')
        nic4 = nD.add_component(name='nic4', ctype=ComponentType.SharedNIC, model='ConnectX-6')
        self.topoA.network_services['bridge2'].connect_interface(nic4.interface_list[0])
        nE = self.topoA.add_node(name='NodeE', site='UKY')
        nic5 = nE.add_component(name='nic5', ctype=ComponentType.SharedNIC, model='ConnectX-6')
        self.topoA.network_services['bridge2'].connect_interface(nic5.interface_list[0])

        self.topoA.validate()

        self.diff = TopologyDiff(added=TopologyDiffTuple(nodes=set(), components=set(),
                                                         services=set(), interfaces=set()),
                                 removed=TopologyDiffTuple(nodes=set(), components=set(),
                                                           services=set(), interfaces=set()))

    def modifyActions(self):
        """
        Define modify actions on the initial topo
        """
        #
        # add a node with components, components won't show up as 'added'
        nB = self.topoB.add_node(name='NodeB', site='UKY')
        nic2 = nB.add_component(name='nic2', ctype=ComponentType.SmartNIC, model='ConnectX-5')
        nB.add_component(name='gpu2', ctype=ComponentType.GPU, model='RTX6000')
        self.diff.added.nodes.add(nB)

        #
        # add a network service between new node and old node (will show up as added)
        #
        s1 = self.topoB.add_network_service(name='ns2', nstype=ServiceType.L2PTP,
                                            interfaces=[self.topoB.nodes['NodeA'].components['nic1'].interface_list[0],
                                                        nic2.interface_list[0]])
        self.diff.added.services.add(s1)

        #
        # add a connection to a facility to the second port of nic1
        #
        f1 = self.topoB.add_facility(name='RENCI-DTN', site='RENC', capacities=f.Capacities(bw=10),
                                     labels=f.Labels(vlan='100'))
        sfac = self.topoB.add_network_service(name='s-fac', nstype=f.ServiceType.L2STS,
                                              interfaces=[f1.interface_list[0],
                                                          self.topoB.nodes['NodeA'].components['nic1'].interface_list[1]])
        self.diff.added.nodes.add(f1)
        self.diff.added.services.add(sfac)

        #
        # add a component to old node (will show up as added)
        #
        c1 = self.topoB.nodes['NodeA'].add_component(name='gpu1', ctype=ComponentType.GPU, model='RTX6000')
        self.diff.added.components.add(c1)

        #
        # remove old node (will show up as removed), should also
        #
        self.diff.removed.nodes.add(self.topoA.nodes['NodeC'])
        self.topoB.remove_node(name='NodeC')

        #
        # Remove the bridge service (as it now connects nothing)
        #
        self.diff.removed.services.add(self.topoA.network_services['bridge1'])
        self.topoB.remove_network_service(name='bridge1')

        #
        # add a node and connect to bridge2 (need connect/disconnect on services)
        #
        nF = self.topoB.add_node(name='NodeF', site='UKY')
        self.diff.added.nodes.add(nF)
        nic6 = nF.add_component(name='nic6', ctype=ComponentType.SharedNIC, model='ConnectX-6')
        self.topoB.network_services['bridge2'].connect_interface(nic6.interface_list[0])
        # add peer of this interface (that is attached to the service) to list of things we should find in a diff
        self.diff.added.interfaces.add(nic6.interface_list[0].get_peers()[0])

        #
        # disconnect Node D from bridge2
        #
        # we need to get the interface from topoA because in topoB it will be missing
        disconnected_interface = self.topoA.nodes['NodeD'].components['nic4'].interface_list[0]
        self.diff.removed.interfaces.add(disconnected_interface.get_peers()[0])
        self.topoB.network_services['bridge2'].disconnect_interface(disconnected_interface)

        self.topoB.validate()

    def setUp(self) -> None:
        self.n4j_imp = Neo4jGraphImporter(url=self.neo4j["url"], user=self.neo4j["user"],
                                          pswd=self.neo4j["pass"],
                                          import_host_dir=self.neo4j["import_host_dir"],
                                          import_dir=self.neo4j["import_dir"])
        self.topoA = f.ExperimentTopology(importer=self.n4j_imp)
        print(f'Created topology A with GUID {self.topoA.graph_model.graph_id}')
        # create initial topology
        self.initialTopo()
        # serialize
        graph_A_string = self.topoA.serialize()
        # load as topo B with alternate GUID, don't pass graph string
        # to constructor - it will re-use the GUID
        self.topoB = f.ExperimentTopology(importer=self.n4j_imp)
        new_id = str(uuid.uuid4())
        self.topoB.load(graph_string=graph_A_string, new_graph_id=new_id)
        print(f'Created topology B with new GUID {self.topoB.graph_model.graph_id}/{new_id}')
        self.modifyActions()

    @staticmethod
    def compare_sets(diff1: set[Any], diff2: set[Any], str):
        if diff1 != diff2:
            raise Exception(f"Topology differences don't match in {str}: {d}")

    @staticmethod
    def compare_tuples(diff1: TopologyDiffTuple, diff2: TopologyDiffTuple):
        ModifyTest.compare_sets(diff1.nodes, diff2.nodes, 'nodes')
        ModifyTest.compare_sets(diff1.services, diff2.services, 'services')
        ModifyTest.compare_sets(diff1.components, diff2.components, 'components')
        ModifyTest.compare_sets(diff1.interfaces, diff2.interfaces, 'interfaces')

    @staticmethod
    def compare_diffs(diff1: TopologyDiff, diff2: TopologyDiff):
        ModifyTest.compare_tuples(diff1.added, diff2.added)
        ModifyTest.compare_tuples(diff1.removed, diff2.removed)

    def tearDown(self) -> None:
        pass
        self.n4j_imp.delete_all_graphs()

    def testNodeAddRemove(self):
        """
        Run the diff between topoA and topoB and validate the results
        """
        diff_res = self.topoA.diff(self.topoB)

        ModifyTest.compare_diffs(diff_res, self.diff)

        print(f'Result {diff_res=}')
        #print(f'\nExpected {self.diff}')
        print(f'\nStartig Topo {self.topoA}')
        print(f'\nFinal Topo {self.topoB}')

