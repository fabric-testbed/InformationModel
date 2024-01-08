import unittest

from typing import Tuple
import fim.user as f
from fim.graph.abc_property_graph import ABCPropertyGraph
from fim.slivers.identifiers import *


class AdTest(unittest.TestCase):

    def setUp(self) -> None:
        self.topo = f.SubstrateTopology()

    def tearDown(self) -> None:
        pass

    def testRENCSiteAd(self):
        # create a site advertisement
        site = 'RENC'
        loc = f.Location(postal='100 Europa Dr., Chapel Hill, NC 27517')
        head_model = 'R7515'
        worker_model = 'R7525'
        hn_cap = f.Capacities(core=32, cpu=1, unit=1, ram=128, disk=100000)
        network_worker_cap = f.Capacities(core=32, cpu=2, unit=1, ram=512, disk=4800)
        gpu_worker_cap = f.Capacities(core=32, cpu=2, unit=1, ram=512, disk=100000)
        #hn = self.topo.add_node(name='headnode', model=head_model, site=site,
        #                        node_id='702C4409-6635-4051-91A0-9C5A45CA28EC',
        #                        ntype=f.NodeType.Server, capacities=hn_cap)

        #
        # HOSTS
        #

        gpuw = self.topo.add_node(name='renc-w1',
                                  model=worker_model, site=site, location=loc,
                                  node_id='HX6VQ53',
                                  ntype=f.NodeType.Server,
                                  capacities=gpu_worker_cap)

        fnw = self.topo.add_node(name='renc-w2',
                                 model=worker_model, site=site, location=loc,
                                 node_id='HX7LQ53',
                                 ntype=f.NodeType.Server,
                                 capacities=network_worker_cap)
        snw = self.topo.add_node(name='renc-w3',
                                 model=worker_model, site=site, location=loc,
                                 node_id='HX7KQ53',
                                 ntype=f.NodeType.Server,
                                 capacities=network_worker_cap)

        #
        # Disks
        #

        nvme_cap = f.Capacities(unit=1, disk=1000)
        gpu_nvme1 = gpuw.add_component(name=gpuw.name + '-nvme1', model='P4510',
                                       node_id='PHLJ016004CC1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=nvme_cap,
                                       labels=f.Labels(bdf='0000:21:00.0'))
        gpu_nvme2 = gpuw.add_component(name=gpuw.name + '-nvme2', model='P4510',
                                       node_id='PHLJ0160047K1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=nvme_cap,
                                       labels=f.Labels(bdf='0000:22:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301TU1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='000:21:00.0'))
        fn_nvme2 = fnw.add_component(name=fnw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ016004CK1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:22:00.0'))
        fn_nvme3 = fnw.add_component(name=fnw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ016002P61P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:23:00.0'))
        fn_nvme4 = fnw.add_component(name=fnw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ016004CL1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:24:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301V81P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:21:00.0'))
        sn_nvme2 = snw.add_component(name=snw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ0160047L1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:22:00.0'))
        sn_nvme3 = snw.add_component(name=snw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ016004CJ1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:23:00.0'))
        sn_nvme4 = snw.add_component(name=snw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ016004C91P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:24:00.0'))

        #
        # GPUs (serial #s not available so made up of node serial # + uniq but
        # consistent string
        #

        unit_cap = f.Capacities(unit=1)
        gpu_gpu1 = gpuw.add_component(name=gpuw.name + '-gpu1', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu1',
                                      ctype=f.ComponentType.GPU,
                                      capacities=unit_cap,
                                      labels=f.Labels(bdf='0000:25:00.0'))
        gpu_gpu2 = gpuw.add_component(name=gpuw.name + '-gpu2', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu2',
                                      ctype=f.ComponentType.GPU,
                                      capacities=unit_cap,
                                      labels=f.Labels(bdf='0000:81:00.0'))

        fn_gpu1 = fnw.add_component(name=fnw.name + '-gpu1', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels(bdf='0000:25:00.0'))
        fn_gpu2 = fnw.add_component(name=fnw.name + '-gpu2', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels(bdf='0000:81:00.0'))

        sn_gpu1 = snw.add_component(name=snw.name + '-gpu1', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels(bdf='0000:25:00.0'))
        sn_gpu2 = snw.add_component(name=snw.name + '-gpu2', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels(bdf='0000:81:00.0'))

        #
        # NICs. Interface node ids are MAC addresses of the ports,
        # node id is concatenation of node serial # and unique name
        #

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:14:EC'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:14:ED', '04:3F:72:B7:14:EE', '04:3F:72:B7:14:EF', '04:3F:72:B7:14:F0']
        vf_vlans = ['1001', '1002', '1003', '1004']
        # Usually slot 7, second port not connected
        gpuw_shnic = gpuw.add_component(name=gpuw.name + '-shnic', model='ConnectX-6',
                                        node_id=gpuw.node_id + '-shnic',
                                        network_service_node_id=gpuw.node_id + '-shnic-sf',
                                        interface_node_ids=[mac_to_node_id(pf_mac)],
                                        interface_labels=[f.Labels(bdf=vf_ids,
                                                                                  mac=vf_macs,
                                                                                  vlan=vf_vlans)],
                                        capacities=f.Capacities(unit=4),
                                        labels=f.Labels(bdf=vf_ids),
                                        ctype=f.ComponentType.SharedNIC,
                                        details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        gpu_shnic_lab = gpuw.components[gpuw.name + '-shnic'].interfaces[gpuw.name + '-shnic' + '-p1'].get_property('labels')
        print(f'Shared NIC labels {gpu_shnic_lab}')
        self.assertTrue(isinstance(gpu_shnic_lab.local_name, list))
        self.assertEqual(gpu_shnic_lab.local_name, ["p1", "p1", "p1", "p1"])

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:18:B4'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:18:B5', '04:3F:72:B7:18:B6', '04:3F:72:B7:18:B7', '04:3F:72:B7:18:B8']
        vf_vlans = ['1001', '1002', '1003', '1004']
        fnw_shnic = fnw.add_component(name=fnw.name + '-shnic', model='ConnectX-6',
                                      node_id=fnw.node_id + '-shnic',
                                      network_service_node_id=fnw.node_id + '-shnic-sf',
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels(bdf=vf_ids,
                                                                                mac=vf_macs,
                                                                                vlan=vf_vlans)],
                                      capacities=f.Capacities(unit=4),
                                      labels=f.Labels(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:16:14'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:16:15', '04:3F:72:B7:16:16', '04:3F:72:B7:16:17', '04:3F:72:B7:16:18']
        vf_vlans = ['1001', '1002', '1003', '1004']
        snw_shnic = snw.add_component(name=snw.name + '-shnic', model='ConnectX-6',
                                      node_id=snw.node_id + '-shnic',
                                      network_service_node_id=snw.node_id + '-shnic-sf',
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels(bdf=vf_ids,
                                                                                mac=vf_macs,
                                                                                vlan=vf_vlans)],
                                      capacities=f.Capacities(unit=4),
                                      labels=f.Labels(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        #
        # Dataplane NICs
        # Usually Slot 3 and Slot 6

        fnw_nic1 = fnw.add_component(name=fnw.name + '-nic1', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic1',
                                     network_service_node_id=fnw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('04:3F:72:B7:15:74'),
                                                         mac_to_node_id('04:3F:72:B7:15:75')],
                                     interface_labels=[f.Labels(mac='04:3F:72:B7:15:74',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='04:3F:72:B7:15:75',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        fnw_shnic_lab = fnw.components[fnw.name + '-nic1'].interfaces[fnw.name + '-nic1' + '-p1'].get_property('labels')
        print(f'Dedicated NIC labels {fnw_shnic_lab}')
        self.assertTrue(isinstance(fnw_shnic_lab.local_name, str))
        self.assertEqual(fnw_shnic_lab.local_name, "p1")

        fnw_nic2 = fnw.add_component(name=fnw.name + '-nic2', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic2',
                                     network_service_node_id=fnw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('04:3F:72:B7:19:5C'),
                                                         mac_to_node_id('04:3F:72:B7:19:5D')],
                                     interface_labels=[f.Labels(mac='04:3F:72:B7:19:5C',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='04:3F:72:B7:19:5D',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        snw_nic1 = snw.add_component(name=snw.name + '-nic1', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic1',
                                     network_service_node_id=snw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:D4'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:D5')],
                                     interface_labels=[f.Labels(mac='0C:42:A1:BE:8F:D4',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='0C:42:A1:BE:8F:D5',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        snw_nic2 = snw.add_component(name=snw.name + '-nic2', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic2',
                                     network_service_node_id=snw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:E8'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:E9')],
                                     interface_labels=[f.Labels(mac='0C:42:A1:BE:8F:E8',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='0C:42:A1:BE:8F:E9',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        # NAS
        nas_model = 'ME4084'
        nas = self.topo.add_node(name=site.lower() + '-nas', model=nas_model, site=site, ntype=f.NodeType.NAS,
                                 node_id='BDXTQ53',
                                 capacities=f.Capacities(unit=1, disk=100000))

        # P4 switch
        # FIXME: Need to have a unique ID for the P4 switch
        p4sw = self.topo.add_switch(name=site.lower() + '-p4', site='RENC', node_id='p4-switch-at-RENC')
        # list of DP switch ports connected to the P4 switch in the order of port IDs 0-8 -> p1-p8
        # they would typically be 400G->100G breakouts
        dp_to_p4_ports = ['HundredGigeE0/0/0/0/26.1', 'HundredGigeE0/0/0/0/26.2', 'HundredGigeE0/0/0/0/26.3',
                          'HundredGigeE0/0/0/0/26.4',
                          'HundredGigeE0/0/0/0/27.1', 'HundredGigeE0/0/0/0/27.2', 'HundredGigeE0/0/0/0/27.3',
                          'HundredGigeE0/0/0/0/27.4']

        # DP switch
        switch_model = 'NCS 55A1-36H' # new switches have  NCS-57B1-6D24-SYS
        switch_ip = "192.168.11.3"
        switch = self.topo.add_node(name=dp_switch_name_id(site, switch_ip)[0],
                                    node_id=dp_switch_name_id(site, switch_ip)[1], site=site,
                                    ntype=f.NodeType.Switch, stitch_node=True)
        dp_ns = switch.add_network_service(name=switch.name+'-ns',
                                           node_id=switch.node_id + '-ns',
                                           nstype=f.ServiceType.MPLS, stitch_node=True)

        # add ports. no capacities are added, these are stitch ports - NetAM owns these
        # we specify the list of names of server ports these are connected to and initialize
        # everything at once (ports and links between them)
        dp_ports = ['HundredGigE0/0/0/5', 'HundredGigE0/0/0/13', 'HundredGigE0/0/0/15', 'HundredGigE0/0/0/9',
                    'HundredGigE0/0/0/17', 'HundredGigE0/0/0/19', 'HundredGigE0/0/0/21', 'HundredGigE0/0/0/25.1',
                    'HundredGigE0/0/0/25.2', 'HundredGigE0/0/0/25.3', 'HundredGigE0/0/0/25.4']
        server_ports = [[gpuw, 'renc-w1-shnic-p1'], [fnw, 'renc-w2-shnic-p1'], [fnw, 'renc-w2-nic1-p1'],
                        [fnw, 'renc-w2-nic1-p2'], [fnw, 'renc-w2-nic2-p1'], [fnw, 'renc-w2-nic2-p2'],
                        [snw, 'renc-w3-shnic-p1'], [snw, 'renc-w3-nic1-p1'], [snw, 'renc-w3-nic1-p2'],
                        [snw, 'renc-w3-nic2-p1'], [snw, 'renc-w3-nic2-p2']]

        # create dp switch ports and links to server ports
        link_idx = 1
        for dp, sr in zip(dp_ports, server_ports):
            sp = dp_ns.add_interface(name=dp, itype=f.InterfaceType.TrunkPort,
                                     node_id=dp_port_id(switch.name, dp), stitch_node=True)
            self.topo.add_link(name='l' + str(link_idx), ltype=f.LinkType.Patch,
                               interfaces=[sr[0].interfaces[sr[1]], sp],
                               node_id=sp.node_id + '-DAC')
            link_idx += 1

        # add dp switch ports that link to P4 switch ports (note they are not stitch nodes!!)
        for dp, p4idx in zip(dp_to_p4_ports, range(1, 8+1)):
            sp = dp_ns.add_interface(name=dp, itype=f.InterfaceType.TrunkPort,
                                     node_id=dp_port_id(switch.name, dp), stitch_node=False)
            self.topo.add_link(name='l' + str(link_idx), ltype=f.LinkType.Patch,
                               interfaces=[p4sw.interfaces[f'p{p4idx}'], sp],
                               node_id=sp.node_id + '-DAC')
            link_idx += 1

        self.topo.validate()
        #
        # delegations
        #
        # Capacity delegations go on network nodes (workers), components and interfaces.
        # They are not going on switches, switch fabrics. They are typically not pooled.
        # Label delegations and pools go on interfaces.
        #
        delegation1 = 'primary'

        # pools are blank - all delegations for interfaces are in the network ad
        self.topo.single_delegation(delegation_id=delegation1,
                                    label_pools=f.Pools(atype=f.DelegationType.LABEL),
                                    capacity_pools=f.Pools(atype=f.DelegationType.CAPACITY))

        self.topo.serialize(file_name='RENCI-ad.graphml')

    def testUKYSiteAd(self):
        # create a site advertisement
        site = 'UKY'
        loc = f.Location(postal='301 Hilltop Ave Lexington, KY 40506')
        head_model = 'R7515'
        worker_model = 'R7525'
        hn_cap = f.Capacities(core=32, cpu=1, unit=1, ram=128, disk=100000)
        network_worker_cap = f.Capacities(core=32, cpu=2, unit=1, ram=512, disk=4800)
        gpu_worker_cap = f.Capacities(core=32, cpu=2, unit=1, ram=512, disk=100000)
        #hn = self.topo.add_node(name='headnode', model=head_model, site=site,
        #                        node_id='702C4409-6635-4051-91A0-9C5A45CA28EC',
        #                        ntype=f.NodeType.Server, capacities=hn_cap)

        #
        # HOSTS
        #

        gpuw = self.topo.add_node(name='uky-w1',
                                  model=worker_model, site=site, location=loc,
                                  node_id='3JB2R53',
                                  ntype=f.NodeType.Server, capacities=gpu_worker_cap)
        fnw = self.topo.add_node(name='uky-w2',
                                 model=worker_model, site=site, location=loc,
                                 node_id='3JB0R53',
                                 ntype=f.NodeType.Server, capacities=network_worker_cap)
        snw = self.topo.add_node(name='uky-w3',
                                 model=worker_model, site=site, location=loc,
                                 node_id='3JB1R53',
                                 ntype=f.NodeType.Server, capacities=network_worker_cap)

        #
        # Disks
        #

        gpu_nvme1 = gpuw.add_component(name=gpuw.name + '-nvme1', model='P4510',
                                       node_id='PHLJ0160046A1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=f.Capacities(unit=1, disk=1000),
                                       labels=f.Labels(bdf='0000:21:00.0'))
        gpu_nvme2 = gpuw.add_component(name=gpuw.name + '-nvme2', model='P4510',
                                       node_id='PHLJ016003SU1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=f.Capacities(unit=1, disk=1000),
                                       labels=f.Labels(bdf='0000:22:00.0'))

        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ0160047A1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='000:21:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ0160041X1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:22:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ016100981P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:23:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ0161008L1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:24:00.0'))

        sn_nvme1 = snw.add_component(name=snw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ016100951P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:21:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ0160046F1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:22:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ0161000L1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:23:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ015301VG1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:24:00.0'))

        #
        # GPUs (serial #s not available so made up of node serial # + uniq but
        # consistent string
        #

        gpu_gpu1 = gpuw.add_component(name=gpuw.name + '-gpu1', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu1',
                                      ctype=f.ComponentType.GPU,
                                      capacities=f.Capacities(unit=1),
                                      labels=f.Labels(bdf='0000:25:00.0'))
        gpu_gpu2 = gpuw.add_component(name=gpuw.name + '-gpu2', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu2',
                                      ctype=f.ComponentType.GPU,
                                      capacities=f.Capacities(unit=1),
                                      labels=f.Labels(bdf='0000:81:00.0'))

        fn_gpu1 = fnw.add_component(name=fnw.name + '-gpu1', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities(unit=1),
                                    labels=f.Labels(bdf='0000:25:00.0'))
        fn_gpu2 = fnw.add_component(name=fnw.name + '-gpu2', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities(unit=1),
                                    labels=f.Labels(bdf='0000:81:00.0'))

        sn_gpu1 = snw.add_component(name=snw.name + '-gpu1', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities(unit=1),
                                    labels=f.Labels(bdf='0000:25:00.0'))
        sn_gpu2 = snw.add_component(name=snw.name + '-gpu2', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities(unit=1),
                                    labels=f.Labels(bdf='0000:81:00.0'))

        #
        # NICs. Interface node ids are MAC addresses of the ports,
        # node id is concatenation of node serial # and unique name
        #

        pf_id = '0000:a1:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '0C:42:A1:EA:C7:60'
        vf_ids = ['0000:a1:00.2', '0000:a1:00.3', '0000:a1:00.4', '0000:a1:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['0C:42:A1:EA:C7:61', '0C:42:A1:EA:C7:62', '0C:42:A1:EA:C7:63', '0C:42:A1:EA:C7:64']
        vf_vlans = ['1001', '1002', '1003', '1004']
        # Usually slot 7, second port not connected (Uky in slot 6)
        gpuw_shnic = gpuw.add_component(name=gpuw.name + '-shnic', model='ConnectX-6',
                                        node_id=gpuw.node_id + '-shnic',
                                        network_service_node_id=gpuw.node_id + '-shnic-sf',
                                        # there is one interface and we need one name
                                        interface_node_ids=[mac_to_node_id(pf_mac)],
                                        interface_labels=[f.Labels(bdf=vf_ids,
                                                                                  mac=vf_macs,
                                                                                  vlan=vf_vlans)],
                                        capacities=f.Capacities(unit=4),
                                        labels=f.Labels(bdf=vf_ids),
                                        ctype=f.ComponentType.SharedNIC,
                                        details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')
        # test that labels propagated to the port
        ilabs = gpuw_shnic.interface_list[0].get_property('labels')
        assert(ilabs.vlan == ['1001', '1002', '1003', '1004'])
        assert(ilabs.mac == ['0C:42:A1:EA:C7:61', '0C:42:A1:EA:C7:62', '0C:42:A1:EA:C7:63', '0C:42:A1:EA:C7:64'])

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '0C:42:A1:EA:C7:E8'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['0C:42:A1:EA:C7:E9', '0C:42:A1:EA:C7:EA', '0C:42:A1:EA:C7:EB', '0C:42:A1:EA:C7:EC']
        vf_vlans = ['1001', '1002', '1003', '1004']
        fnw_shnic = fnw.add_component(name=fnw.name + '-shnic', model='ConnectX-6',
                                      node_id=fnw.node_id + '-shnic',
                                      network_service_node_id=fnw.node_id + '-shnic-sf',
                                      # there is one interface and we need one name
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels(bdf=vf_ids,
                                                                                mac=vf_macs,
                                                                                vlan=vf_vlans)],
                                      capacities=f.Capacities(unit=4),
                                      labels=f.Labels(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '0C:42:A1:78:F8:1C'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['0C:42:A1:78:F8:1D', '0C:42:A1:78:F8:1E', '0C:42:A1:78:F8:1F', '0C:42:A1:78:F8:20']
        vf_vlans = ['1001', '1002', '1003', '1004']
        snw_shnic = snw.add_component(name=snw.name + '-shnic', model='ConnectX-6',
                                      node_id=snw.node_id + '-shnic',
                                      network_service_node_id=snw.node_id + '-shnic-sf',
                                      # there is one interface and we need one name
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels(bdf=vf_ids,
                                                                                mac=vf_macs,
                                                                                vlan=vf_vlans)],
                                      capacities=f.Capacities(unit=4),
                                      labels=f.Labels(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        #
        # Dataplane NICs
        # Usually Slot 3 and Slot 6

        fnw_nic1 = fnw.add_component(name=fnw.name + '-nic1', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic1',
                                     network_service_node_id=fnw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:EA:C7:50'),
                                                         mac_to_node_id('0C:42:A1:EA:C7:51')],
                                     interface_labels=[f.Labels(mac='0C:42:A1:EA:C7:50',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='0C:42:A1:EA:C7:51',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        ilabs = fnw_nic1.interface_list[0].get_property('labels')
        assert(ilabs.vlan_range == '1-4096')
        assert(ilabs.mac == '0C:42:A1:EA:C7:50' or ilabs.mac == '0C:42:A1:EA:C7:51')
        ilabs = fnw_nic1.interface_list[1].get_property('labels')
        assert (ilabs.vlan_range == '1-4096')
        assert (ilabs.mac == '0C:42:A1:EA:C7:51' or ilabs.mac == '0C:42:A1:EA:C7:50')

        fnw_nic2 = fnw.add_component(name=fnw.name + '-nic2', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic2',
                                     network_service_node_id=fnw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:78:F8:04'),
                                                         mac_to_node_id('0C:42:A1:78:F8:05')],
                                     interface_labels=[f.Labels(mac='0C:42:A1:78:F8:04',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='0C:42:A1:78:F8:05',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        snw_nic1 = snw.add_component(name=snw.name + '-nic1', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic1',
                                     network_service_node_id=snw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:F8'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:F9')],
                                     interface_labels=[f.Labels(mac='0C:42:A1:BE:8F:F8',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='0C:42:A1:BE:8F:F9',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        snw_nic2 = snw.add_component(name=snw.name + '-nic2', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic2',
                                     network_service_node_id=snw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:DC'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:DD')],
                                     interface_labels=[f.Labels(mac='0C:42:A1:BE:8F:DC',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='0C:42:A1:BE:8F:DD',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        # NAS
        nas_model = 'ME4084'
        nas = self.topo.add_node(name='nas', model=nas_model, site=site, ntype=f.NodeType.NAS,
                                 node_id='3DB3R53',
                                 capacities=f.Capacities(unit=1, disk=100000))

        # DP switch
        switch_model = 'NCS 55A1-36H' # new switches have  NCS-57B1-6D24-SYS
        switch_ip = "192.168.12.3"
        switch = self.topo.add_node(name=dp_switch_name_id(site, switch_ip)[0],
                                    node_id=dp_switch_name_id(site, switch_ip)[1], site=site,
                                    ntype=f.NodeType.Switch, stitch_node=True)
        dp_ns = switch.add_network_service(name=switch.name+'-ns',
                                           node_id=switch.node_id + '-ns',
                                           nstype=f.ServiceType.MPLS, stitch_node=True)

        # add ports. no capacities are added, these are stitch ports - NetAM owns these
        # we specify the list of names of server ports these are connected to and initialize
        # everything at once (ports and links between them)
        dp_ports = ['HundredGigE0/0/0/5', 'HundredGigE0/0/0/13', 'HundredGigE0/0/0/15', 'HundredGigE0/0/0/9',
                    'HundredGigE0/0/0/17', 'HundredGigE0/0/0/19', 'HundredGigE0/0/0/21', 'HundredGigE0/0/0/25.1',
                    'HundredGigE0/0/0/25.2', 'HundredGigE0/0/0/25.3', 'HundredGigE0/0/0/25.4']
        server_ports = [[gpuw, 'uky-w1-shnic-p1'], [fnw, 'uky-w2-shnic-p1'], [fnw, 'uky-w2-nic1-p1'],
                        [fnw, 'uky-w2-nic1-p2'], [fnw, 'uky-w2-nic2-p1'], [fnw, 'uky-w2-nic2-p2'],
                        [snw, 'uky-w3-shnic-p1'], [snw, 'uky-w3-nic1-p1'], [snw, 'uky-w3-nic1-p2'],
                        [snw, 'uky-w3-nic2-p1'], [snw, 'uky-w3-nic2-p2']]

        # create dp switch ports and links to server ports
        link_idx = 1
        for dp, sr in zip(dp_ports, server_ports):
            sp = dp_ns.add_interface(name=dp, itype=f.InterfaceType.TrunkPort,
                                     node_id=dp_port_id(switch.name, dp), stitch_node=True)
            self.topo.add_link(name='l' + str(link_idx), ltype=f.LinkType.Patch,
                               interfaces=[sr[0].interfaces[sr[1]], sp],
                               node_id=sp.node_id + '-DAC')
            link_idx += 1

        self.topo.validate()
        #
        # delegations
        #
        # Capacity delegations go on network nodes (workers), components and interfaces.
        # They are not going on switches, switch fabrics. They are typically not pooled.
        # Label delegations and pools go on interfaces.
        #
        delegation1 = 'primary'

        self.topo.single_delegation(delegation_id=delegation1, label_pools=f.Pools(atype=f.DelegationType.LABEL),
                                    capacity_pools=f.Pools(atype=f.DelegationType.CAPACITY))

        self.topo.serialize(file_name='UKY-ad.graphml')

    def testLBNLSiteAd(self):
        # create a site advertisement
        site = 'LBNL'
        loc = f.Location(postal='1 Cyclotron Rd, Berkeley, CA 94720')
        head_model = 'R7515'
        worker_model = 'R7525'
        hn_cap = f.Capacities(core=32, cpu=1, unit=1, ram=128, disk=100000)
        network_worker_cap = f.Capacities(core=32, cpu=2, unit=1, ram=512, disk=4800)
        gpu_worker_cap = f.Capacities(core=32, cpu=2, unit=1, ram=512, disk=100000)
        #hn = self.topo.add_node(name='headnode', model=head_model, site=site,
        #                        node_id='702C4409-6635-4051-91A0-9C5A45CA28EC',
        #                        ntype=f.NodeType.Server, capacities=hn_cap)

        #
        # HOSTS
        #

        gpuw = self.topo.add_node(name='lbnl-w1',
                                  model=worker_model, site=site, location=loc,
                                  node_id='5B3BR53',
                                  ntype=f.NodeType.Server, capacities=gpu_worker_cap)
        fnw = self.topo.add_node(name='lbnl-w2',
                                 model=worker_model, site=site, location=loc,
                                 node_id='5B38R53',
                                 ntype=f.NodeType.Server, capacities=network_worker_cap)
        snw = self.topo.add_node(name='lbnl-w3',
                                 model=worker_model, site=site, location=loc,
                                 node_id='5B39R53',
                                 ntype=f.NodeType.Server, capacities=network_worker_cap)

        #
        # Disks
        #

        gpu_nvme1 = gpuw.add_component(name=gpuw.name + '-nvme1', model='P4510',
                                       node_id='PHLJ015301XE1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=f.Capacities(unit=1, disk=1000),
                                       labels=f.Labels(bdf='0000:21:00.0'))
        gpu_nvme2 = gpuw.add_component(name=gpuw.name + '-nvme2', model='P4510',
                                       node_id='PHLJ015301K31P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=f.Capacities(unit=1, disk=1000),
                                       labels=f.Labels(bdf='0000:22:00.0'))

        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301LQ1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='000:21:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ015301LE1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:22:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ015301M31P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:23:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ015301LS1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:24:00.0'))

        sn_nvme1 = snw.add_component(name=snw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301KV1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:21:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ015301RL1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:22:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ015301L91P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:23:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ015301SK1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities(unit=1, disk=1000),
                                     labels=f.Labels(bdf='0000:24:00.0'))

        #
        # GPUs (serial #s not available so made up of node serial # + uniq but
        # consistent string
        #

        gpu_gpu1 = gpuw.add_component(name=gpuw.name + '-gpu1', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu1',
                                      ctype=f.ComponentType.GPU,
                                      capacities=f.Capacities(unit=1),
                                      labels=f.Labels(bdf='0000:25:00.0'))
        gpu_gpu2 = gpuw.add_component(name=gpuw.name + '-gpu2', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu2',
                                      ctype=f.ComponentType.GPU,
                                      capacities=f.Capacities(unit=1),
                                      labels=f.Labels(bdf='0000:81:00.0'))

        fn_gpu1 = fnw.add_component(name=fnw.name + '-gpu1', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities(unit=1),
                                    labels=f.Labels(bdf='0000:25:00.0'))
        fn_gpu2 = fnw.add_component(name=fnw.name + '-gpu2', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities(unit=1),
                                    labels=f.Labels(bdf='0000:81:00.0'))

        sn_gpu1 = snw.add_component(name=snw.name + '-gpu1', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities(unit=1),
                                    labels=f.Labels(bdf='0000:25:00.0'))
        sn_gpu2 = snw.add_component(name=snw.name + '-gpu2', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities(unit=1),
                                    labels=f.Labels(bdf='0000:81:00.0'))

        #
        # NICs. Interface node ids are MAC addresses of the ports,
        # node id is concatenation of node serial # and unique name
        #

        # Usually slot 7, second port not connected (Slot 6)
        pf_id = '0000:a1:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:19:8C'
        vf_ids = ['0000:a1:00.2', '0000:a1:00.3', '0000:a1:00.4', '0000:a1:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:19:8D', '04:3F:72:B7:19:8E', '04:3F:72:B7:19:8F', '04:3F:72:B7:19:8A']
        vf_vlans = ['1001', '1002', '1003', '1004']
        gpuw_shnic = gpuw.add_component(name=gpuw.name + '-shnic', model='ConnectX-6',
                                        node_id=gpuw.node_id + '-shnic',
                                        network_service_node_id=gpuw.node_id + '-shnic-sf',
                                        # there is one interface and we need one name
                                        interface_node_ids=[mac_to_node_id(pf_mac)],
                                        interface_labels=[f.Labels(bdf=vf_ids,
                                                                                  mac=vf_macs,
                                                                                  vlan=vf_vlans)],
                                        capacities=f.Capacities(unit=4),
                                        labels=f.Labels(bdf=vf_ids),
                                        ctype=f.ComponentType.SharedNIC,
                                        details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:15:8C'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:15:8D', '04:3F:72:B7:15:8E', '04:3F:72:B7:15:8F', '04:3F:72:B7:15:8A']
        vf_vlans = ['1001', '1002', '1003', '1004']
        fnw_shnic = fnw.add_component(name=fnw.name + '-shnic', model='ConnectX-6',
                                      node_id=fnw.node_id + '-shnic',
                                      network_service_node_id=fnw.node_id + '-shnic-sf',
                                      # there is one interface and we need one name
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels(bdf=vf_ids,
                                                                                mac=vf_macs,
                                                                                vlan=vf_vlans)],
                                      capacities=f.Capacities(unit=4),
                                      labels=f.Labels(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:15:7C'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:15:7D', '04:3F:72:B7:15:7E', '04:3F:72:B7:15:7F', '04:3F:72:B7:15:7A']
        vf_vlans = ['1001', '1002', '1003', '1004']
        snw_shnic = snw.add_component(name=snw.name + '-shnic', model='ConnectX-6',
                                      node_id=snw.node_id + '-shnic',
                                      network_service_node_id=snw.node_id + '-shnic-sf',
                                      # there is one interface and we need one name
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels(bdf=vf_ids,
                                                                                mac=vf_macs,
                                                                                vlan=vf_vlans)],
                                      capacities=f.Capacities(unit=4),
                                      labels=f.Labels(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        #
        # Dataplane NICs
        # Usually Slot 3 and Slot 6

        fnw_nic1 = fnw.add_component(name=fnw.name + '-nic1', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic1',
                                     network_service_node_id=fnw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('04:3F:72:B7:15:6C'),
                                                         mac_to_node_id('04:3F:72:B7:15:6D')],
                                     interface_labels=[f.Labels(mac='04:3F:72:B7:15:6C',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='04:3F:72:B7:15:6D',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        fnw_nic2 = fnw.add_component(name=fnw.name + '-nic2', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic2',
                                     network_service_node_id=fnw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('04:3F:72:B7:18:AC'),
                                                         mac_to_node_id('04:3F:72:B7:18:AD')],
                                     interface_labels=[f.Labels(mac='04:3F:72:B7:18:AC',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='04:3F:72:B7:18:AD',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        snw_nic1 = snw.add_component(name=snw.name + '-nic1', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic1',
                                     network_service_node_id=snw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:91:75:12'),
                                                         mac_to_node_id('0C:42:A1:91:75:13')],
                                     interface_labels=[f.Labels(mac='0C:42:A1:91:75:12',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='0C:42:A1:91:75:13',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        snw_nic2 = snw.add_component(name=snw.name + '-nic2', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic2',
                                     network_service_node_id=snw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:91:75:0E'),
                                                         mac_to_node_id('0C:42:A1:91:75:0F')],
                                     interface_labels=[f.Labels(mac='0C:42:A1:91:75:0E',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='0C:42:A1:91:75:0F',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        # NAS
        nas_model = 'ME4084'
        nas = self.topo.add_node(name='nas', model=nas_model, site=site, ntype=f.NodeType.NAS,
                                 node_id='3DB2R53',
                                 capacities=f.Capacities(unit=1, disk=100000))
        # DP switch
        switch_model = 'NCS 55A1-36H' # new switches have  NCS-57B1-6D24-SYS
        switch_ip = "192.168.13.3"
        switch = self.topo.add_node(name=dp_switch_name_id(site, switch_ip)[0],
                                    node_id=dp_switch_name_id(site, switch_ip)[1], site=site,
                                    ntype=f.NodeType.Switch, stitch_node=True)
        dp_ns = switch.add_network_service(name=switch.name+'-ns',
                                           node_id=switch.node_id + '-ns',
                                           nstype=f.ServiceType.MPLS, stitch_node=True)

        # add ports. no capacities are added, these are stitch ports - NetAM owns these
        # we specify the list of names of server ports these are connected to and initialize
        # everything at once (ports and links between them)
        dp_ports = ['HundredGigE0/0/0/5', 'HundredGigE0/0/0/13', 'HundredGigE0/0/0/15', 'HundredGigE0/0/0/9',
                    'HundredGigE0/0/0/17', 'HundredGigE0/0/0/19', 'HundredGigE0/0/0/21', 'HundredGigE0/0/0/25.1',
                    'HundredGigE0/0/0/25.2', 'HundredGigE0/0/0/25.3', 'HundredGigE0/0/0/25.4']
        server_ports = [[gpuw, 'lbnl-w1-shnic-p1'], [fnw, 'lbnl-w2-shnic-p1'], [fnw, 'lbnl-w2-nic1-p1'],
                        [fnw, 'lbnl-w2-nic1-p2'], [fnw, 'lbnl-w2-nic2-p1'], [fnw, 'lbnl-w2-nic2-p2'],
                        [snw, 'lbnl-w3-shnic-p1'], [snw, 'lbnl-w3-nic1-p1'], [snw, 'lbnl-w3-nic1-p2'],
                        [snw, 'lbnl-w3-nic2-p1'], [snw, 'lbnl-w3-nic2-p2']]

        # create dp switch ports and links to server ports
        link_idx = 1
        for dp, sr in zip(dp_ports, server_ports):
            sp = dp_ns.add_interface(name=dp, itype=f.InterfaceType.TrunkPort,
                                     node_id=dp_port_id(switch.name, dp), stitch_node=True)
            self.topo.add_link(name='l' + str(link_idx), ltype=f.LinkType.Patch,
                               interfaces=[sr[0].interfaces[sr[1]], sp],
                               node_id=sp.node_id + '-DAC')
            link_idx += 1

        self.topo.validate()
        #
        # delegations
        #
        # Capacity delegations go on network nodes (workers), components and interfaces.
        # They are not going on switches, switch fabrics. They are typically not pooled.
        # Label delegations and pools go on interfaces.
        #
        delegation1 = 'primary'

        self.topo.single_delegation(delegation_id=delegation1,
                                    label_pools=f.Pools(atype=f.DelegationType.LABEL),
                                    capacity_pools=f.Pools(atype=f.DelegationType.CAPACITY))

        self.topo.serialize(file_name='LBNL-ad.graphml')

    def testNetworkAd(self):

        site = 'RENC'

        # DP switch
        switch_model = 'NCS 55A1-36H' # new switches have  NCS-57B1-6D24-SYS
        switch_ip = "192.168.11.3"
        switch = self.topo.add_node(name=dp_switch_name_id(site, switch_ip)[0], model=switch_model,
                                    node_id=dp_switch_name_id(site, switch_ip)[1], site=site,
                                    ntype=f.NodeType.Switch)
        dp_ns = switch.add_network_service(name=switch.name+'-ns',
                                           node_id=switch.node_id + '-ns',
                                           nstype=f.ServiceType.MPLS,
                                           labels=f.Labels(vlan_range='1-100'))
        dp_l3ns = switch.add_network_service(name=switch.name + '-l3ns',
                                             node_id=switch.node_id + '-l3ns',
                                             nstype=f.ServiceType.FABNetv4,
                                             labels=f.Labels(ipv4_range='192.168.1.1-192.168.1.255',
                                                             vlan_range='100-200'))
        # FABNetv4Ext - externally connected
        dp_l3nsext = switch.add_network_service(name=switch.name + '-l3nsext',
                                                node_id=switch.node_id + '-l3nsext',
                                                nstype=f.ServiceType.FABNetv4Ext,
                                                labels=f.Labels(ipv4_subnet=['123.1.15.1/24', '122.2.16.1/24'],
                                                                vlan_range='100-200'))
        dp_l3vpn = switch.add_network_service(name=switch.name + '-l3vpn',
                                              node_id=switch.node_id + '-l3vpn',
                                              nstype=f.ServiceType.L3VPN,
                                              # the IP range is what orchestrator uses to pick link endpoint addresses
                                              # for peering
                                              labels=f.Labels(asn='12345', ipv4_subnet='10.100.10.1/16'))

        # add ports
        port_caps = f.Capacities(bw=100)
        port_caps1 = f.Capacities(bw=25)
        port_labs = f.Labels(vlan_range='1-4096')

        dp_ports_100g = ['HundredGigE0/0/0/5', 'HundredGigE0/0/0/13', 'HundredGigE0/0/0/15', 'HundredGigE0/0/0/9',
                         'HundredGigE0/0/0/17', 'HundredGigE0/0/0/19', 'HundredGigE0/0/0/21']
        dp_ports_25g = ['HundredGigE0/0/0/25.1', 'HundredGigE0/0/0/25.2',
                        'HundredGigE0/0/0/25.3', 'HundredGigE0/0/0/25.4']

        for dp in dp_ports_100g:
            sp = dp_ns.add_interface(name=dp, itype=f.InterfaceType.TrunkPort,
                                     node_id=dp_port_id(switch.name, dp),
                                     labels=port_labs, capacities=port_caps)

        facility_port_facing_port = dp_ns.add_interface(name='HundredDigE0/0/0/99', itype=f.InterfaceType.TrunkPort,
                                                        node_id=dp_port_id(switch.name, 'HundredDigE0/0/0/99'),
                                                        labels=port_labs, capacities=port_caps)


        for dp in dp_ports_25g:
            sp = dp_ns.add_interface(name=dp, itype=f.InterfaceType.TrunkPort,
                                     node_id=dp_port_id(switch.name, dp),
                                     labels=port_labs, capacities=port_caps1)

        # FIXME: fake ports towards UKY and LBNL
        renc_uky = dp_ns.add_interface(name='HundredGigE0/0/0/26', itype=f.InterfaceType.TrunkPort,
                                       node_id=dp_port_id(switch.name, 'HundredGigE0/0/0/26'),
                                       capacities=port_caps)

        renc_lbnl = dp_ns.add_interface(name='HundredGigE0/0/0/27', itype=f.InterfaceType.TrunkPort,
                                        node_id=dp_port_id(switch.name, 'HundredGigE0/0/0/27'),
                                        capacities=port_caps)

        site = 'UKY'
        # DP switch
        switch_model = 'NCS 55A1-36H' # new switches have  NCS-57B1-6D24-SYS
        switch_ip = "192.168.12.3"
        switch = self.topo.add_node(name=dp_switch_name_id(site, switch_ip)[0], model=switch_model,
                                    node_id=dp_switch_name_id(site, switch_ip)[1], site=site,
                                    ntype=f.NodeType.Switch)
        dp_ns = switch.add_network_service(name=switch.name+'-ns',
                                           node_id=switch.node_id + '-ns',
                                           nstype=f.ServiceType.MPLS,
                                           labels=f.Labels(vlan_range=['1-100', '201-300']))
        dp_l3ns = switch.add_network_service(name=switch.name + '-l3ns',
                                             node_id=switch.node_id + '-l3ns',
                                             nstype=f.ServiceType.FABNetv4Ext,
                                             labels=f.Labels(ipv4_range='192.168.2.1-192.168.2.255',
                                                             vlan_range='100-200'))

        # add ports
        port_caps = f.Capacities(bw=100)
        port_caps1 = f.Capacities(bw=25)
        port_labs = f.Labels(vlan_range='1-4096')

        dp_ports_100g = ['HundredGigE0/0/0/5', 'HundredGigE0/0/0/13', 'HundredGigE0/0/0/15', 'HundredGigE0/0/0/9',
                         'HundredGigE0/0/0/17', 'HundredGigE0/0/0/19', 'HundredGigE0/0/0/21']
        dp_ports_25g = ['HundredGigE0/0/0/25.1', 'HundredGigE0/0/0/25.2',
                        'HundredGigE0/0/0/25.3', 'HundredGigE0/0/0/25.4']

        for dp in dp_ports_100g:
            sp = dp_ns.add_interface(name=dp, itype=f.InterfaceType.TrunkPort,
                                     node_id=dp_port_id(switch.name, dp),
                                     labels=port_labs, capacities=port_caps)

        for dp in dp_ports_25g:
            sp = dp_ns.add_interface(name=dp, itype=f.InterfaceType.TrunkPort,
                                     node_id=dp_port_id(switch.name, dp),
                                     labels=port_labs, capacities=port_caps1)

        # FIXME: fake ports towards RENC and LBNL
        uky_renc = dp_ns.add_interface(name='HundredGigE0/0/0/26', itype=f.InterfaceType.TrunkPort,
                                       node_id=dp_port_id(switch.name, 'HundredGigE0/0/0/26'),
                                       capacities=port_caps)

        uky_lbnl = dp_ns.add_interface(name='HundredGigE0/0/0/27', itype=f.InterfaceType.TrunkPort,
                                       node_id=dp_port_id(switch.name, 'HundredGigE0/0/0/27'),
                                       capacities=port_caps)

        site = 'LBNL'

        # DP switch
        switch_model = 'NCS 55A1-36H' # new switches have  NCS-57B1-6D24-SYS
        switch_ip = "192.168.13.3"
        switch = self.topo.add_node(name=dp_switch_name_id(site, switch_ip)[0], model=switch_model,
                                    node_id=dp_switch_name_id(site, switch_ip)[1], site=site,
                                    ntype=f.NodeType.Switch)
        dp_ns = switch.add_network_service(name=switch.name+'-ns',
                                           node_id=switch.node_id + '-ns',
                                           nstype=f.ServiceType.MPLS,
                                           labels=f.Labels(vlan_range='1-100'))
        dp_l3ns = switch.add_network_service(name=switch.name + '-l3ns',
                                             node_id=switch.node_id + '-l3ns',
                                             nstype=f.ServiceType.FABNetv4,
                                             labels=f.Labels(ipv4_range='192.168.2.1-192.168.2.255',
                                                             vlan_range='100-200'))

        # add ports
        port_caps = f.Capacities(bw=100)
        port_caps1 = f.Capacities(bw=25)
        port_labs = f.Labels(vlan_range='1-4096')

        dp_ports_100g = ['HundredGigE0/0/0/5', 'HundredGigE0/0/0/13', 'HundredGigE0/0/0/15', 'HundredGigE0/0/0/9',
                         'HundredGigE0/0/0/17', 'HundredGigE0/0/0/19', 'HundredGigE0/0/0/21']
        dp_ports_25g = ['HundredGigE0/0/0/25.1', 'HundredGigE0/0/0/25.2',
                        'HundredGigE0/0/0/25.3', 'HundredGigE0/0/0/25.4']

        for dp in dp_ports_100g:
            sp = dp_ns.add_interface(name=dp, itype=f.InterfaceType.TrunkPort,
                                     node_id=dp_port_id(switch.name, dp),
                                     labels=port_labs, capacities=port_caps)

        for dp in dp_ports_25g:
            sp = dp_ns.add_interface(name=dp, itype=f.InterfaceType.TrunkPort,
                                     node_id=dp_port_id(switch.name, dp),
                                     labels=port_labs, capacities=port_caps1)

        # FIXME: fake ports towards UKY and RENC
        lbnl_renc = dp_ns.add_interface(name='HundredGigE0/0/0/26', itype=f.InterfaceType.TrunkPort,
                                        node_id=dp_port_id(switch.name, 'HundredGigE0/0/0/26'),
                                        labels=f.Labels(local_name='HundredGigE 0/0/0/26',
                                                                       mac='20:00:00:00:00:10'),
                                        capacities=port_caps)

        lbnl_uky = dp_ns.add_interface(name='HundredGigE 0/0/0/27', itype=f.InterfaceType.TrunkPort,
                                       node_id=dp_port_id(switch.name, 'HundredGigE0/0/0/27'),
                                       labels=f.Labels(local_name='HundredGigE 0/0/0/27',
                                                                      mac='20:00:00:00:00:11'),
                                       capacities=port_caps)

        # add 3 links
        l1 = self.topo.add_link(name='l1', ltype=f.LinkType.L2Path,
                                interfaces=[renc_uky, uky_renc],
                                node_id=renc_uky.node_id + '-Wave')

        l2 = self.topo.add_link(name='l2', ltype=f.LinkType.L2Path,
                                interfaces=[uky_lbnl, lbnl_uky],
                                node_id=uky_lbnl.node_id + '-Wave')

        l3 = self.topo.add_link(name='l3', ltype=f.LinkType.L2Path,
                                interfaces=[renc_lbnl, lbnl_renc],
                                node_id=renc_lbnl.node_id + '-Wave')

        # add three separate facility nodes (and associated network services and interfaces)
        fac1 = self.topo.add_facility(name='RENCI-DTN', node_id='RENCI-DTN-id', site='RENC',
                                      capacities=f.Capacities(mtu=1500, bw=10))
        fac2 = self.topo.add_facility(name='RENCI-BEN', node_id='RENCI-BEN-id', site='RENC',
                                      # labels and capacities go onto facility interface
                                      labels=f.Labels(ipv4_range='192.168.1.1-192.168.1.10',
                                                      vlan_range='1-100'),
                                      capacities=f.Capacities(mtu=9000))
        fac3 = self.topo.add_facility(name='RENCI-Cloud', node_id='RENCI-Cloud-id', site='RENC',
                                      nstype=f.ServiceType.L3VPN,
                                      # nslabels go onto facility network service
                                      nslabels=f.Labels(asn='123456'))
        self.assertEqual(fac3.network_services['RENCI-Cloud-ns'].labels.asn, '123456')

        # connect them to links along with the port facing the facility
        fac1_port_link = self.topo.add_link(name='RENCI-DC-link1', node_id='RENCI-DC-link1-id',
                                            ltype=f.LinkType.L2Path,
                                            interfaces=[fac1.interface_list[0], # only one interface available
                                                        facility_port_facing_port])
        fac2_port_link = self.topo.add_link(name='RENCI-DC-link2', node_id='RENCI-DC-link2-id',
                                            ltype=f.LinkType.L2Path,
                                            interfaces=[fac2.interface_list[0], # only one interface available
                                                        facility_port_facing_port])
        fac3_port_link = self.topo.add_link(name='RENCI-DC-link3', node_id='RENCI-DC-link3-id',
                                            ltype=f.LinkType.L2Path,
                                            interfaces=[fac3.interface_list[0],
                                                        facility_port_facing_port])
        self.topo.validate()
        delegation1 = 'primary'
        print('RUNNING NETWORK AD DELEGATIONS')
        self.topo.single_delegation(delegation_id=delegation1,
                                    label_pools=f.Pools(atype=f.DelegationType.LABEL),
                                    capacity_pools=f.Pools(atype=f.DelegationType.CAPACITY))

        self.topo.serialize(file_name='Network-ad.graphml')

    def testRENCI_non_save(self):
        """
        Test extra things without saving - may not be true to an actual site advertisement.
        :return:
        """
        # create a site advertisement
        site = 'RENC'
        head_model = 'R7515'
        worker_model = 'R7525'
        hn_cap = f.Capacities(core=32, cpu=1, unit=1, ram=128, disk=100000)
        network_worker_cap = f.Capacities(core=32, cpu=2, unit=1, ram=512, disk=4800)
        gpu_worker_cap = f.Capacities(core=32, cpu=2, unit=1, ram=512, disk=100000)
        #hn = self.topo.add_node(name='headnode', model=head_model, site=site,
        #                        node_id='702C4409-6635-4051-91A0-9C5A45CA28EC',
        #                        ntype=f.NodeType.Server, capacities=hn_cap)

        #
        # HOSTS
        #

        gpuw = self.topo.add_node(name='renc-w1',
                                  model=worker_model, site=site,
                                  node_id='HX6VQ53',
                                  ntype=f.NodeType.Server,
                                  capacities=gpu_worker_cap)

        fnw = self.topo.add_node(name='renc-w2',
                                 model=worker_model, site=site,
                                 node_id='HX7LQ53',
                                 ntype=f.NodeType.Server,
                                 capacities=network_worker_cap)
        snw = self.topo.add_node(name='renc-w3',
                                 model=worker_model, site=site,
                                 node_id='HX7KQ53',
                                 ntype=f.NodeType.Server,
                                 capacities=network_worker_cap)

        #
        # Disks
        #

        nvme_cap = f.Capacities(unit=1, disk=1000)
        gpu_nvme1 = gpuw.add_component(name=gpuw.name + '-nvme1', model='P4510',
                                       node_id='PHLJ016004CC1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=nvme_cap,
                                       labels=f.Labels(bdf='0000:21:00.0'))
        gpu_nvme2 = gpuw.add_component(name=gpuw.name + '-nvme2', model='P4510',
                                       node_id='PHLJ0160047K1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=nvme_cap,
                                       labels=f.Labels(bdf='0000:22:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301TU1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='000:21:00.0'))
        fn_nvme2 = fnw.add_component(name=fnw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ016004CK1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:22:00.0'))
        fn_nvme3 = fnw.add_component(name=fnw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ016002P61P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:23:00.0'))
        fn_nvme4 = fnw.add_component(name=fnw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ016004CL1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:24:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301V81P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:21:00.0'))
        sn_nvme2 = snw.add_component(name=snw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ0160047L1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:22:00.0'))
        sn_nvme3 = snw.add_component(name=snw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ016004CJ1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:23:00.0'))
        sn_nvme4 = snw.add_component(name=snw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ016004C91P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels(bdf='0000:24:00.0'))

        #
        # GPUs (serial #s not available so made up of node serial # + uniq but
        # consistent string
        #

        unit_cap = f.Capacities(unit=1)
        gpu_gpu1 = gpuw.add_component(name=gpuw.name + '-gpu1', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu1',
                                      ctype=f.ComponentType.GPU,
                                      capacities=unit_cap,
                                      labels=f.Labels(bdf='0000:25:00.0'))
        gpu_gpu2 = gpuw.add_component(name=gpuw.name + '-gpu2', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu2',
                                      ctype=f.ComponentType.GPU,
                                      capacities=unit_cap,
                                      labels=f.Labels(bdf='0000:81:00.0'))

        fn_gpu1 = fnw.add_component(name=fnw.name + '-gpu1', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels(bdf='0000:25:00.0'))
        fn_gpu2 = fnw.add_component(name=fnw.name + '-gpu2', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels(bdf='0000:81:00.0'))

        sn_gpu1 = snw.add_component(name=snw.name + '-gpu1', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels(bdf='0000:25:00.0'))
        sn_gpu2 = snw.add_component(name=snw.name + '-gpu2', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels(bdf='0000:81:00.0'))

        #
        # NICs. Interface node ids are MAC addresses of the ports,
        # node id is concatenation of node serial # and unique name
        #

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:14:EC'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:14:ED', '04:3F:72:B7:14:EE', '04:3F:72:B7:14:EF', '04:3F:72:B7:14:F0']
        vf_vlans = ['1001', '1002', '1003', '1004']
        # Usually slot 7, second port not connected
        gpuw_shnic = gpuw.add_component(name=gpuw.name + '-shnic', model='ConnectX-6',
                                        node_id=gpuw.node_id + '-shnic',
                                        network_service_node_id=gpuw.node_id + '-shnic-sf',
                                        interface_node_ids=[mac_to_node_id(pf_mac)],
                                        interface_labels=[f.Labels(bdf=vf_ids,
                                                                                  mac=vf_macs,
                                                                                  vlan=vf_vlans)],
                                        capacities=f.Capacities(unit=4),
                                        labels=f.Labels(bdf=vf_ids),
                                        ctype=f.ComponentType.SharedNIC,
                                        details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        gpu_shnic_lab = gpuw.components[gpuw.name + '-shnic'].interfaces[gpuw.name + '-shnic' + '-p1'].labels
        print(f'Shared NIC labels {gpu_shnic_lab}')
        self.assertTrue(isinstance(gpu_shnic_lab.local_name, list))
        self.assertEqual(gpu_shnic_lab.local_name, ["p1", "p1", "p1", "p1"])

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:18:B4'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:18:B5', '04:3F:72:B7:18:B6', '04:3F:72:B7:18:B7', '04:3F:72:B7:18:B8']
        vf_vlans = ['1001', '1002', '1003', '1004']
        fnw_shnic = fnw.add_component(name=fnw.name + '-shnic', model='ConnectX-6',
                                      node_id=fnw.node_id + '-shnic',
                                      network_service_node_id=fnw.node_id + '-shnic-sf',
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels(bdf=vf_ids,
                                                                                mac=vf_macs,
                                                                                vlan=vf_vlans)],
                                      capacities=f.Capacities(unit=4),
                                      labels=f.Labels(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:16:14'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:16:15', '04:3F:72:B7:16:16', '04:3F:72:B7:16:17', '04:3F:72:B7:16:18']
        vf_vlans = ['1001', '1002', '1003', '1004']
        snw_shnic = snw.add_component(name=snw.name + '-shnic', model='ConnectX-6',
                                      node_id=snw.node_id + '-shnic',
                                      network_service_node_id=snw.node_id + '-shnic-sf',
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels(bdf=vf_ids,
                                                                                mac=vf_macs,
                                                                                vlan=vf_vlans)],
                                      capacities=f.Capacities(unit=4),
                                      labels=f.Labels(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        #
        # Dataplane NICs
        # Usually Slot 3 and Slot 6

        fnw_nic1 = fnw.add_component(name=fnw.name + '-nic1', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic1',
                                     network_service_node_id=fnw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('04:3F:72:B7:15:74'),
                                                         mac_to_node_id('04:3F:72:B7:15:75')],
                                     interface_labels=[f.Labels(mac='04:3F:72:B7:15:74',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='04:3F:72:B7:15:75',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        fnw_shnic_lab = fnw.components[fnw.name + '-nic1'].interfaces[fnw.name + '-nic1' + '-p1'].get_property('labels')
        print(f'Dedicated NIC labels {fnw_shnic_lab}')
        self.assertTrue(isinstance(fnw_shnic_lab.local_name, str))
        self.assertEqual(fnw_shnic_lab.local_name, "p1")

        fnw_nic2 = fnw.add_component(name=fnw.name + '-nic2', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic2',
                                     network_service_node_id=fnw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('04:3F:72:B7:19:5C'),
                                                         mac_to_node_id('04:3F:72:B7:19:5D')],
                                     interface_labels=[f.Labels(mac='04:3F:72:B7:19:5C',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='04:3F:72:B7:19:5D',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        snw_nic1 = snw.add_component(name=snw.name + '-nic1', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic1',
                                     network_service_node_id=snw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:D4'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:D5')],
                                     interface_labels=[f.Labels(mac='0C:42:A1:BE:8F:D4',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='0C:42:A1:BE:8F:D5',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        snw_nic2 = snw.add_component(name=snw.name + '-nic2', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic2',
                                     network_service_node_id=snw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:E8'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:E9')],
                                     interface_labels=[f.Labels(mac='0C:42:A1:BE:8F:E8',
                                                                               vlan_range='1-4096'),
                                                       f.Labels(mac='0C:42:A1:BE:8F:E9',
                                                                               vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities(unit=1),
                                     labels=f.Labels(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        # NAS
        nas_model = 'ME4084'
        nas = self.topo.add_node(name=site.lower() + '-nas', model=nas_model, site=site, ntype=f.NodeType.NAS,
                                 node_id='BDXTQ53',
                                 capacities=f.Capacities(unit=1, disk=100000))
        # DP switch
        switch_model = 'NCS 55A1-36H' # new switches have  NCS-57B1-6D24-SYS
        switch_ip = "192.168.11.3"
        switch = self.topo.add_node(name=dp_switch_name_id(site, switch_ip)[0],
                                    node_id=dp_switch_name_id(site, switch_ip)[1], site=site,
                                    ntype=f.NodeType.Switch, stitch_node=True)
        dp_ns = switch.add_network_service(name=switch.name+'-ns',
                                           node_id=switch.node_id + '-ns',
                                           nstype=f.ServiceType.MPLS, stitch_node=True)

        # add ports. no capacities are added, these are stitch ports - NetAM owns these
        # we specify the list of names of server ports these are connected to and initialize
        # everything at once (ports and links between them)
        dp_ports = ['HundredGigE0/0/0/5', 'HundredGigE0/0/0/13', 'HundredGigE0/0/0/15', 'HundredGigE0/0/0/9',
                    'HundredGigE0/0/0/17', 'HundredGigE0/0/0/19', 'HundredGigE0/0/0/21', 'HundredGigE0/0/0/25.1',
                    'HundredGigE0/0/0/25.2', 'HundredGigE0/0/0/25.3', 'HundredGigE0/0/0/25.4']
        server_ports = [[gpuw, 'renc-w1-shnic-p1'], [fnw, 'renc-w2-shnic-p1'], [fnw, 'renc-w2-nic1-p1'],
                        [fnw, 'renc-w2-nic1-p2'], [fnw, 'renc-w2-nic2-p1'], [fnw, 'renc-w2-nic2-p2'],
                        [snw, 'renc-w3-shnic-p1'], [snw, 'renc-w3-nic1-p1'], [snw, 'renc-w3-nic1-p2'],
                        [snw, 'renc-w3-nic2-p1'], [snw, 'renc-w3-nic2-p2']]

        # create dp switch ports and links to server ports
        link_idx = 1
        for dp, sr in zip(dp_ports, server_ports):
            sp = dp_ns.add_interface(name=dp, itype=f.InterfaceType.TrunkPort,
                                     node_id=dp_port_id(switch.name, dp), stitch_node=True)
            self.topo.add_link(name='l' + str(link_idx), ltype=f.LinkType.Patch,
                               interfaces=[sr[0].interfaces[sr[1]], sp],
                               node_id=sp.node_id + '-DAC')
            link_idx += 1

        delegation1 = 'primary'
        #####
        # define the pools for interfaces on the switch (this code is commented out, kept
        # around as an example)
        #####

        pools = f.Pools(atype=f.DelegationType.LABEL)
        # define two pools - one shared between shared NIC ports and one shared between all dataplane ports
        shared_pool = f.Pool(atype=f.DelegationType.LABEL, pool_id='shared_pool', delegation_id=delegation1,
                             defined_on=switch.interfaces['HundredGigE0/0/0/5'].node_id,
                             defined_for=[switch.interfaces['HundredGigE0/0/0/5'].node_id,
                                          switch.interfaces['HundredGigE0/0/0/13'].node_id,
                                          switch.interfaces['HundredGigE0/0/0/21'].node_id])
        shared_pool.set_pool_details(f.Labels(vlan_range='100-200',
                                                             ipv4_range='192.168.1.1-192.168.10.255'))
        pools.add_pool(pool=shared_pool)

        datanic_pool = f.Pool(atype=f.DelegationType.LABEL, pool_id='datanic_pool', delegation_id=delegation1,
                              defined_on=switch.interfaces['HundredGigE0/0/0/15'].node_id,
                              defined_for=[switch.interfaces['HundredGigE0/0/0/15'].node_id,
                                           switch.interfaces['HundredGigE0/0/0/9'].node_id,
                                           switch.interfaces['HundredGigE0/0/0/17'].node_id,
                                           switch.interfaces['HundredGigE0/0/0/19'].node_id,
                                           switch.interfaces['HundredGigE0/0/0/25.1'].node_id,
                                           switch.interfaces['HundredGigE0/0/0/25.2'].node_id,
                                           switch.interfaces['HundredGigE0/0/0/25.3'].node_id,
                                           switch.interfaces['HundredGigE0/0/0/25.4'].node_id
                                           ]
                              )
        datanic_pool.set_pool_details(f.Labels(vlan_range='1500-2000'))
        pools.add_pool(pool=datanic_pool)
        # have to reindex pools by delegation
        pools.build_index_by_delegation_id()
        pools.validate_pools()

        self.topo.validate()

        # form delegation using pools
        self.topo.single_delegation(delegation_id=delegation1,
                                    label_pools=pools,
                                    capacity_pools=f.Pools(atype=f.DelegationType.CAPACITY))

        _, node_props = self.topo.graph_model.get_node_properties(
            node_id=switch.interfaces['HundredGigE0/0/0/25.2'].node_id)
        self.assertEqual(node_props[ABCPropertyGraph.PROP_LABEL_DELEGATIONS], '{"primary": {"pool": "datanic_pool"}}')
        _, node_props = self.topo.graph_model.get_node_properties(
            node_id=switch.interfaces['HundredGigE0/0/0/5'].node_id)
        self.assertEqual(node_props[ABCPropertyGraph.PROP_LABEL_DELEGATIONS], '{"primary": {"pool_id": "shared_pool", '
                                                                              '"labels": {"ipv4_range": '
                                                                              '"192.168.1.1-192.168.10.255", '
                                                                              '"vlan_range": "100-200"}}}')