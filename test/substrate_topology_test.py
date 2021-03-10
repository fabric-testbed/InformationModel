import unittest

import fim.user as f
from fim.graph.abc_property_graph import ABCPropertyGraph


def mac_to_node_id(mac: str) -> str:
    # turn mac address into a unique string to act
    # as node id, but don't make it look like mac address
    return 'node_id-' + mac.replace(':', '-')


class AdTest(unittest.TestCase):

    def setUp(self) -> None:
        self.topo = f.SubstrateTopology()

    def tearDown(self) -> None:
        pass

    def testSiteAd(self):
        # create a site advertisement
        site = 'RENC'
        head_model = 'R7515'
        worker_model = 'R7525'
        hn_cap = f.Capacities()
        hn_cap.set_fields(core=32, cpu=1, unit=1, ram=128, disk=100000)
        network_worker_cap = f.Capacities()
        # only internal storage
        network_worker_cap.set_fields(core=32, cpu=2, unit=1, ram=512, disk=4800)
        gpu_worker_cap = f.Capacities()
        # has access to SAS NAS
        gpu_worker_cap.set_fields(core=32, cpu=2, unit=1, ram=512, disk=100000)
        #hn = self.topo.add_node(name='headnode', model=head_model, site=site,
        #                        node_id='702C4409-6635-4051-91A0-9C5A45CA28EC',
        #                        ntype=f.NodeType.Server, capacities=hn_cap)

        #
        # HOSTS
        #

        gpuw = self.topo.add_node(name='renc-w1',
                                  model=worker_model, site=site,
                                  node_id='HX6VQ53',
                                  ntype=f.NodeType.Server, capacities=gpu_worker_cap)
        fnw = self.topo.add_node(name='renc-w2',
                                 model=worker_model, site=site,
                                 node_id='HX7LQ53',
                                 ntype=f.NodeType.Server, capacities=network_worker_cap)
        snw = self.topo.add_node(name='renc-w3',
                                 model=worker_model, site=site,
                                 node_id='HX7KQ53',
                                 ntype=f.NodeType.Server, capacities=network_worker_cap)

        #
        # Disks
        #

        gpu_nvme1 = gpuw.add_component(name=gpuw.name + '-nvme1', model='P4510',
                                       node_id='PHLJ016004CC1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                       labels=f.Labels().set_fields(bdf='0000:21:00.0'))
        gpu_nvme2 = gpuw.add_component(name=gpuw.name + '-nvme2', model='P4510',
                                       node_id='PHLJ0160047K1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                       labels=f.Labels().set_fields(bdf='0000:22:00.0'))

        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301TU1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='000:21:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ016004CK1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:22:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ016002P61P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:23:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ016004CL1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:24:00.0'))

        sn_nvme1 = snw.add_component(name=snw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301V81P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:21:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ0160047L1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:22:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ016004CJ1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:23:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ016004C91P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:24:00.0'))

        #
        # GPUs (serial #s not available so made up of node serial # + uniq but
        # consistent string
        #

        gpu_gpu1 = gpuw.add_component(name=gpuw.name + '-gpu1', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu1',
                                      ctype=f.ComponentType.GPU,
                                      capacities=f.Capacities().set_fields(unit=1),
                                      labels=f.Labels().set_fields(bdf='0000:25:00.0'))
        gpu_gpu2 = gpuw.add_component(name=gpuw.name + '-gpu2', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu2',
                                      ctype=f.ComponentType.GPU,
                                      capacities=f.Capacities().set_fields(unit=1),
                                      labels=f.Labels().set_fields(bdf='0000:81:00.0'))

        fn_gpu1 = fnw.add_component(name=fnw.name + '-gpu1', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities().set_fields(unit=1),
                                    labels=f.Labels().set_fields(bdf='0000:25:00.0'))
        fn_gpu2 = fnw.add_component(name=fnw.name + '-gpu2', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities().set_fields(unit=1),
                                    labels=f.Labels().set_fields(bdf='0000:81:00.0'))

        sn_gpu1 = snw.add_component(name=snw.name + '-gpu1', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities().set_fields(unit=1),
                                    labels=f.Labels().set_fields(bdf='0000:25:00.0'))
        sn_gpu2 = snw.add_component(name=snw.name + '-gpu2', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=f.Capacities().set_fields(unit=1),
                                    labels=f.Labels().set_fields(bdf='0000:81:00.0'))

        #
        # NICs. Interface node ids are MAC addresses of the ports,
        # node id is concatenation of node serial # and unique name
        #

        # Usually slot 7, second port not connected
        gpuw_shnic = gpuw.add_component(name=gpuw.name + '-shnic', model='ConnectX-6',
                                        node_id=gpuw.node_id + '-shnic',
                                        switch_fabric_node_id=gpuw.node_id + '-shnic-sf',
                                        interface_node_ids=[mac_to_node_id('04:3F:72:B7:14:EC')],
                                        capacities=f.Capacities().set_fields(unit=1),
                                        labels=f.Labels().set_fields(bdf='0000:e2:00.0',
                                                                     mac='04:3F:72:B7:14:EC'),
                                        ctype=f.ComponentType.SharedNIC,
                                        details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        fnw_shnic = fnw.add_component(name=fnw.name + '-shnic', model='ConnectX-6',
                                      node_id=fnw.node_id + '-shnic',
                                      switch_fabric_node_id=fnw.node_id + '-shnic-sf',
                                      interface_node_ids=[mac_to_node_id('04:3F:72:B7:18:B4')],
                                      capacities=f.Capacities().set_fields(unit=1),
                                      labels=f.Labels().set_fields(bdf='0000:e2:00.0',
                                                                   mac='04:3F:72:B7:18:B4'),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        snw_shnic = snw.add_component(name=snw.name + '-shnic', model='ConnectX-6',
                                      node_id=snw.node_id + '-shnic',
                                      switch_fabric_node_id=snw.node_id + '-shnic-sf',
                                      interface_node_ids=[mac_to_node_id('04:3F:72:B7:16:14')],
                                      capacities=f.Capacities().set_fields(unit=1),
                                      labels=f.Labels().set_fields(bdf='0000:e2:00.0',
                                                                   mac='04:3F:72:B7:16:14'),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        #
        # Dataplane NICs
        # Usually Slot 3 and Slot 6

        fnw_nic1 = fnw.add_component(name=fnw.name + '-nic1', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic1',
                                     switch_fabric_node_id=fnw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('04:3F:72:B7:15:74'),
                                                         mac_to_node_id('04:3F:72:B7:15:75')],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:41:00.0', '0000:41:00.1'],
                                                                  mac=['04:3F:72:B7:15:74', '04:3F:72:B7:15:75']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        fnw_nic2 = fnw.add_component(name=fnw.name + '-nic2', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic2',
                                     switch_fabric_node_id=fnw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('04:3F:72:B7:19:5C'),
                                                         mac_to_node_id('04:3F:72:B7:19:5D')],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:a1:00.0', '0000:a1:00.1'],
                                                                  mac=['04:3F:72:B7:19:5C', '04:3F:72:B7:19:5D']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        snw_nic1 = snw.add_component(name=snw.name + '-nic1', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic1',
                                     switch_fabric_node_id=snw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:D4'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:D5')],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:41:00.0', '0000:41:00.1'],
                                                                  mac=['0C:42:A1:BE:8F:D4', '0C:42:A1:BE:8F:D5']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        snw_nic2 = snw.add_component(name=snw.name + '-nic2', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic2',
                                     switch_fabric_node_id=snw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:E8'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:E9')],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:a1:00.0', '0000:a1:00.1'],
                                                                  mac=['0C:42:A1:BE:8F:E8', '0C:42:A1:BE:8F:E9']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        # NAS
        nas_model = 'ME4084'
        nas = self.topo.add_node(name='nas', model=nas_model, site=site, ntype=f.NodeType.NAS,
                                 node_id='BDXTQ53',
                                 capacities=f.Capacities().set_fields(unit=1, disk=100000))
        # DP switch
        switch_model = 'NCS 55A1-36H'
        # FIXME: This is UKY's S/N - placeholder
        switch = self.topo.add_node(name=site + '-data-sw', model=switch_model, site=site,
                                    node_id='FOC2451R0XZ',
                                    capacities=f.Capacities().set_fields(unit=1),
                                    ntype=f.NodeType.Switch)
        dp_sf = switch.add_switch_fabric(name=switch.name+'-sf', layer=f.Layer.L2,
                                         node_id=switch.node_id + '-sf')
        # add ports
        port_caps = f.Capacities()
        port_caps1 = f.Capacities()
        port_caps.set_fields(bw=100)
        port_caps1.set_fields(bw=25)
        port_labs = f.Labels()
        port_labs.set_fields(vlan_range='1000-2000')
        # FIXME: don't have port MAC addresses yet - placeholders
        sp1 = dp_sf.add_interface(name='HundredGigE 0/0/0/5', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:00'),
                                  capacities=port_caps, labels=port_labs)

        sp2 = dp_sf.add_interface(name='HundredGigE 0/0/0/13', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:01'),
                                  capacities=port_caps, labels=port_labs)

        sp3 = dp_sf.add_interface(name='HundredGigE 0/0/0/15', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:02'),
                                  capacities=port_caps, labels=port_labs)
        sp4 = dp_sf.add_interface(name='HundredGigE 0/0/0/9', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:03'),
                                  capacities=port_caps, labels=port_labs)
        sp5 = dp_sf.add_interface(name='HundredGigE 0/0/0/17', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:04'),
                                  capacities=port_caps, labels=port_labs)
        sp6 = dp_sf.add_interface(name='HundredGigE 0/0/0/19', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:05'),
                                  capacities=port_caps, labels=port_labs)

        sp7 = dp_sf.add_interface(name='HundredGigE 0/0/0/21', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:06'),
                                  capacities=port_caps, labels=port_labs)

        # FIXME: what to do about breakout ports in slownets?
        sp8 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.1', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:07'),
                                  capacities=port_caps1, labels=port_labs)
        sp9 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.2', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:08'),
                                  capacities=port_caps1, labels=port_labs)
        sp10 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.3', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('00:00:00:00:00:09'),
                                   capacities=port_caps1, labels=port_labs)
        sp11 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.4', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('00:00:00:00:00:0A'),
                                   capacities=port_caps1, labels=port_labs)

        #
        # Links
        #
        # FIXME: Link node ids need to come from somewhere, could be an extension of interface ID
        # FIXME: on the switch, or something else
        l1 = self.topo.add_link(name='l1', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[gpuw_shnic.interfaces['renc-w1-shnic-p1'], sp1],
                                node_id=sp1.node_id + '-DAC')

        l2 = self.topo.add_link(name='l2', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_shnic.interfaces['renc-w2-shnic-p1'], sp2],
                                node_id=sp2.node_id + '-DAC')

        l3 = self.topo.add_link(name='l3', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic1.interfaces['renc-w2-nic1-p1'], sp3],
                                node_id=sp3.node_id + '-DAC')
        l4 = self.topo.add_link(name='l4', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic1.interfaces['renc-w2-nic1-p2'], sp4],
                                node_id=sp4.node_id + '-DAC')
        l5 = self.topo.add_link(name='l5', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic2.interfaces['renc-w2-nic2-p1'], sp5],
                                node_id=sp5.node_id + '-DAC')
        l6 = self.topo.add_link(name='l6', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic2.interfaces['renc-w2-nic2-p2'], sp6],
                                node_id=sp6.node_id + '-DAC')

        l8 = self.topo.add_link(name='l7', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[snw_shnic.interfaces['renc-w3-shnic-p1'], sp7],
                                node_id=sp7.node_id + '-DAC')

        l9 = self.topo.add_link(name='l8', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[snw_nic1.interfaces['renc-w3-nic1-p1'], sp8],
                                node_id=sp8.node_id + '-DAC')
        l10 = self.topo.add_link(name='l9', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                 interfaces=[snw_nic1.interfaces['renc-w3-nic1-p2'], sp9],
                                 node_id=sp9.node_id + '-DAC')
        l11 = self.topo.add_link(name='l10', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                 interfaces=[snw_nic2.interfaces['renc-w3-nic2-p1'], sp10],
                                 node_id=sp10.node_id + '-DAC')
        l12 = self.topo.add_link(name='l11', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                 interfaces=[snw_nic2.interfaces['renc-w3-nic2-p2'], sp11],
                                 node_id=sp11.node_id + '-DAC')
        #
        # delegations
        #
        # Capacity delegations go on network nodes (workers), components and interfaces.
        # They are not going on switches, switch fabrics. They are typically not pooled.
        # Label delegations and pools go on interfaces.
        #
        delegation1 = 'primary'

        # define the pools for interfaces on the switch
        pools = f.ARMPools(atype=f.DelegationType.LABEL)
        # define two pools - one shared between shared NIC ports and one shared between all dataplane ports
        shared_pool = f.Pool(atype=f.DelegationType.LABEL, pool_id='shared_pool', delegation_id=delegation1,
                             defined_on=switch.interfaces['HundredGigE 0/0/0/5'].node_id,
                             defined_for=[switch.interfaces['HundredGigE 0/0/0/5'].node_id,
                                          switch.interfaces['HundredGigE 0/0/0/13'].node_id,
                                          switch.interfaces['HundredGigE 0/0/0/21'].node_id])
        shared_pool.set_pool_details_from_labels(f.Labels().set_fields(vlan_range='100-200',
                                                                       ipv4_range='192.168.1.1-192.168.10.255'))

        pools.add_pool(pool=shared_pool)

        datanic_pool = f.Pool(atype=f.DelegationType.LABEL, pool_id='datanic_pool', delegation_id=delegation1,
                              defined_on=switch.interfaces['HundredGigE 0/0/0/15'].node_id,
                              defined_for=[switch.interfaces['HundredGigE 0/0/0/15'].node_id,
                                           switch.interfaces['HundredGigE 0/0/0/9'].node_id,
                                           switch.interfaces['HundredGigE 0/0/0/17'].node_id,
                                           switch.interfaces['HundredGigE 0/0/0/19'].node_id,
                                           switch.interfaces['HundredGigE 0/0/0/25.1'].node_id,
                                           switch.interfaces['HundredGigE 0/0/0/25.2'].node_id,
                                           switch.interfaces['HundredGigE 0/0/0/25.3'].node_id,
                                           switch.interfaces['HundredGigE 0/0/0/25.4'].node_id
                                           ]
                              )
        datanic_pool.set_pool_details_from_labels(f.Labels().set_fields(vlan_range='1500-2000'))
        pools.add_pool(pool=datanic_pool)
        # have to reindex pools by delegation
        pools.build_index_by_delegation_id()
        pools.validate_pools()

        self.topo.single_delegation(delegation_id=delegation1, label_pools=pools,
                                    capacity_pools=f.ARMPools(atype=f.DelegationType.CAPACITY))

        _, node_props = self.topo.graph_model.get_node_properties(node_id=switch.interfaces['HundredGigE 0/0/0/25.2'].node_id)
        self.assertEqual(node_props[ABCPropertyGraph.PROP_LABEL_DELEGATIONS], '[{"pool": "datanic_pool"}]')
        _, node_props = self.topo.graph_model.get_node_properties(node_id=switch.interfaces['HundredGigE 0/0/0/5'].node_id)
        self.assertEqual(node_props[ABCPropertyGraph.PROP_LABEL_DELEGATIONS], '[{"ipv4_range": '
                                                                              '"192.168.1.1-192.168.10.255", '
                                                                              '"vlan_range": "100-200", '
                                                                              '"label_pool": "shared_pool", '
                                                                              '"delegation": "primary"}, '
                                                                              '{"pool": "shared_pool"}]')
        self.topo.serialize(file_name='RENCI-ad.graphml')
        # print('\n\nALL NODES')
        # for n in self.topo.nodes.values():
        #     print(f'Node {n.name}:')
        #     print(n)
        #     for c in n.components.values():
        #        print(f'Component {c.name}')
        #        print(c)
        #        for i in c.interfaces.values():
        #            print(f'Interface {i.name}')
        #            print(i)
        #
        # print('\n\nSwitch interfaces')
        # for i in self.topo.nodes['dp_switch'].interfaces.values():
        #     print(f'Interface {i.name}')
        #     print(i)



