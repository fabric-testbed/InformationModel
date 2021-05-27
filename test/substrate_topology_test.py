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

    def testRENCSiteAd(self):
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

        nvme_cap = f.Capacities().set_fields(unit=1, disk=1000)
        gpu_nvme1 = gpuw.add_component(name=gpuw.name + '-nvme1', model='P4510',
                                       node_id='PHLJ016004CC1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=nvme_cap,
                                       labels=f.Labels().set_fields(bdf='0000:21:00.0'))
        gpu_nvme2 = gpuw.add_component(name=gpuw.name + '-nvme2', model='P4510',
                                       node_id='PHLJ0160047K1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=nvme_cap,
                                       labels=f.Labels().set_fields(bdf='0000:22:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301TU1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels().set_fields(bdf='000:21:00.0'))
        fn_nvme2 = fnw.add_component(name=fnw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ016004CK1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels().set_fields(bdf='0000:22:00.0'))
        fn_nvme3 = fnw.add_component(name=fnw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ016002P61P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels().set_fields(bdf='0000:23:00.0'))
        fn_nvme4 = fnw.add_component(name=fnw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ016004CL1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels().set_fields(bdf='0000:24:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301V81P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels().set_fields(bdf='0000:21:00.0'))
        sn_nvme2 = snw.add_component(name=snw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ0160047L1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels().set_fields(bdf='0000:22:00.0'))
        sn_nvme3 = snw.add_component(name=snw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ016004CJ1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels().set_fields(bdf='0000:23:00.0'))
        sn_nvme4 = snw.add_component(name=snw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ016004C91P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=nvme_cap,
                                     labels=f.Labels().set_fields(bdf='0000:24:00.0'))

        #
        # GPUs (serial #s not available so made up of node serial # + uniq but
        # consistent string
        #

        unit_cap = f.Capacities().set_fields(unit=1)
        gpu_gpu1 = gpuw.add_component(name=gpuw.name + '-gpu1', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu1',
                                      ctype=f.ComponentType.GPU,
                                      capacities=unit_cap,
                                      labels=f.Labels().set_fields(bdf='0000:25:00.0'))
        gpu_gpu2 = gpuw.add_component(name=gpuw.name + '-gpu2', model='RTX6000',
                                      node_id=gpuw.node_id + '-gpu2',
                                      ctype=f.ComponentType.GPU,
                                      capacities=unit_cap,
                                      labels=f.Labels().set_fields(bdf='0000:81:00.0'))

        fn_gpu1 = fnw.add_component(name=fnw.name + '-gpu1', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels().set_fields(bdf='0000:25:00.0'))
        fn_gpu2 = fnw.add_component(name=fnw.name + '-gpu2', model='Tesla T4',
                                    node_id=fnw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels().set_fields(bdf='0000:81:00.0'))

        sn_gpu1 = snw.add_component(name=snw.name + '-gpu1', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu1',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels().set_fields(bdf='0000:25:00.0'))
        sn_gpu2 = snw.add_component(name=snw.name + '-gpu2', model='Tesla T4',
                                    node_id=snw.node_id + '-gpu2',
                                    ctype=f.ComponentType.GPU,
                                    capacities=unit_cap,
                                    labels=f.Labels().set_fields(bdf='0000:81:00.0'))

        #
        # NICs. Interface node ids are MAC addresses of the ports,
        # node id is concatenation of node serial # and unique name
        #

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:14:EC'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:14:ED', '04:3F:72:B7:14:EE', '04:3F:72:B7:14:EF', '04:3F:72:B7:14:F0']
        vf_vlans = [1001, 1002, 1003, 1004]
        # Usually slot 7, second port not connected
        gpuw_shnic = gpuw.add_component(name=gpuw.name + '-shnic', model='ConnectX-6',
                                        node_id=gpuw.node_id + '-shnic',
                                        switch_fabric_node_id=gpuw.node_id + '-shnic-sf',
                                        interface_node_ids=[mac_to_node_id(pf_mac)],
                                        interface_labels=[f.Labels().set_fields(bdf=vf_ids,
                                                                                mac=vf_macs,
                                                                                vlan=vf_vlans)],
                                        capacities=f.Capacities().set_fields(unit=4),
                                        labels=f.Labels().set_fields(bdf=vf_ids),
                                        ctype=f.ComponentType.SharedNIC,
                                        details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:18:B4'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:18:B5', '04:3F:72:B7:18:B6', '04:3F:72:B7:18:B7', '04:3F:72:B7:18:B8']
        vf_vlans = [1001, 1002, 1003, 1004]
        fnw_shnic = fnw.add_component(name=fnw.name + '-shnic', model='ConnectX-6',
                                      node_id=fnw.node_id + '-shnic',
                                      switch_fabric_node_id=fnw.node_id + '-shnic-sf',
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels().set_fields(bdf=vf_ids,
                                                                              mac=vf_macs,
                                                                              vlan=vf_vlans)],
                                      capacities=f.Capacities().set_fields(unit=4),
                                      labels=f.Labels().set_fields(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:16:14'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:16:15', '04:3F:72:B7:16:16', '04:3F:72:B7:16:17', '04:3F:72:B7:16:18']
        vf_vlans = [1001, 1002, 1003, 1004]
        snw_shnic = snw.add_component(name=snw.name + '-shnic', model='ConnectX-6',
                                      node_id=snw.node_id + '-shnic',
                                      switch_fabric_node_id=snw.node_id + '-shnic-sf',
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels().set_fields(bdf=vf_ids,
                                                                              mac=vf_macs,
                                                                              vlan=vf_vlans)],
                                      capacities=f.Capacities().set_fields(unit=4),
                                      labels=f.Labels().set_fields(bdf=vf_ids),
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
                                     interface_labels=[f.Labels().set_fields(mac='04:3F:72:B7:15:74',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='04:3F:72:B7:15:75',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        fnw_nic2 = fnw.add_component(name=fnw.name + '-nic2', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic2',
                                     switch_fabric_node_id=fnw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('04:3F:72:B7:19:5C'),
                                                         mac_to_node_id('04:3F:72:B7:19:5D')],
                                     interface_labels=[f.Labels().set_fields(mac='04:3F:72:B7:19:5C',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='04:3F:72:B7:19:5D',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        snw_nic1 = snw.add_component(name=snw.name + '-nic1', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic1',
                                     switch_fabric_node_id=snw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:D4'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:D5')],
                                     interface_labels=[f.Labels().set_fields(mac='0C:42:A1:BE:8F:D4',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='0C:42:A1:BE:8F:D5',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        snw_nic2 = snw.add_component(name=snw.name + '-nic2', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic2',
                                     switch_fabric_node_id=snw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:E8'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:E9')],
                                     interface_labels=[f.Labels().set_fields(mac='0C:42:A1:BE:8F:E8',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='0C:42:A1:BE:8F:E9',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        # NAS
        nas_model = 'ME4084'
        nas = self.topo.add_node(name='nas', model=nas_model, site=site, ntype=f.NodeType.NAS,
                                 node_id='BDXTQ53',
                                 capacities=f.Capacities().set_fields(unit=1, disk=100000))
        # DP switch
        switch_model = 'NCS 55A1-36H'
        switch = self.topo.add_node(name=site + '-data-sw', model=switch_model, site=site,
                                    node_id='FOC2450R1BL',
                                    capacities=f.Capacities().set_fields(unit=1),
                                    ntype=f.NodeType.Switch)
        dp_sf = switch.add_switch_fabric(name=switch.name+'-sf', layer=f.Layer.L2,
                                         node_id=switch.node_id + '-sf')
        # add ports
        port_caps = f.Capacities()
        port_caps1 = f.Capacities()
        port_caps.set_fields(bw=100)
        port_caps1.set_fields(bw=25)

        # FIXME: don't have port MAC addresses yet - placeholders
        sp1 = dp_sf.add_interface(name='HundredGigE 0/0/0/5', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:00'),
                                  capacities=port_caps)

        sp2 = dp_sf.add_interface(name='HundredGigE 0/0/0/13', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:01'),
                                  capacities=port_caps)

        sp3 = dp_sf.add_interface(name='HundredGigE 0/0/0/15', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:02'),
                                  capacities=port_caps)
        sp4 = dp_sf.add_interface(name='HundredGigE 0/0/0/9', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:03'),
                                  capacities=port_caps)
        sp5 = dp_sf.add_interface(name='HundredGigE 0/0/0/17', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:04'),
                                  capacities=port_caps)
        sp6 = dp_sf.add_interface(name='HundredGigE 0/0/0/19', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:05'),
                                  capacities=port_caps)

        sp7 = dp_sf.add_interface(name='HundredGigE 0/0/0/21', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:06'),
                                  capacities=port_caps)

        # FIXME: what to do about breakout ports in slownets?
        sp8 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.1', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:07'),
                                  capacities=port_caps1)
        sp9 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.2', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:08'),
                                  capacities=port_caps1)
        sp10 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.3', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('00:00:00:00:00:09'),
                                   capacities=port_caps1)
        sp11 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.4', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('00:00:00:00:00:0A'),
                                   capacities=port_caps1)

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
        pools = f.Pools(atype=f.DelegationType.LABEL)
        # define two pools - one shared between shared NIC ports and one shared between all dataplane ports
        shared_pool = f.Pool(atype=f.DelegationType.LABEL, pool_id='shared_pool', delegation_id=delegation1,
                             defined_on=switch.interfaces['HundredGigE 0/0/0/5'].node_id,
                             defined_for=[switch.interfaces['HundredGigE 0/0/0/5'].node_id,
                                          switch.interfaces['HundredGigE 0/0/0/13'].node_id,
                                          switch.interfaces['HundredGigE 0/0/0/21'].node_id])
        shared_pool.set_pool_details(f.Labels().set_fields(vlan_range='100-200',
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
        datanic_pool.set_pool_details(f.Labels().set_fields(vlan_range='1500-2000'))
        pools.add_pool(pool=datanic_pool)
        # have to reindex pools by delegation
        pools.build_index_by_delegation_id()
        pools.validate_pools()

        # pools are blank - all delegations for interfaces are in the network ad
        self.topo.single_delegation(delegation_id=delegation1,
                                    label_pools=pools,
                                    capacity_pools=f.Pools(atype=f.DelegationType.CAPACITY))

        _, node_props = self.topo.graph_model.get_node_properties(node_id=switch.interfaces['HundredGigE 0/0/0/25.2'].node_id)
        self.assertEqual(node_props[ABCPropertyGraph.PROP_LABEL_DELEGATIONS], '{"primary": {"pool": "datanic_pool"}}')
        _, node_props = self.topo.graph_model.get_node_properties(node_id=switch.interfaces['HundredGigE 0/0/0/5'].node_id)
        self.assertEqual(node_props[ABCPropertyGraph.PROP_LABEL_DELEGATIONS], '{"primary": {"pool_id": '
                                                                              '"shared_pool", "labels": '
                                                                              '{"ipv4_range": '
                                                                              '"192.168.1.1-192.168.10.255", '
                                                                             '"vlan_range": "100-200"}}}')
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

    def testUKYSiteAd(self):
        # create a site advertisement
        site = 'UKY'
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

        gpuw = self.topo.add_node(name='uky-w1',
                                  model=worker_model, site=site,
                                  node_id='3JB2R53',
                                  ntype=f.NodeType.Server, capacities=gpu_worker_cap)
        fnw = self.topo.add_node(name='uky-w2',
                                 model=worker_model, site=site,
                                 node_id='3JB0R53',
                                 ntype=f.NodeType.Server, capacities=network_worker_cap)
        snw = self.topo.add_node(name='uky-w3',
                                 model=worker_model, site=site,
                                 node_id='3JB1R53',
                                 ntype=f.NodeType.Server, capacities=network_worker_cap)

        #
        # Disks
        #

        gpu_nvme1 = gpuw.add_component(name=gpuw.name + '-nvme1', model='P4510',
                                       node_id='PHLJ0160046A1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                       labels=f.Labels().set_fields(bdf='0000:21:00.0'))
        gpu_nvme2 = gpuw.add_component(name=gpuw.name + '-nvme2', model='P4510',
                                       node_id='PHLJ016003SU1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                       labels=f.Labels().set_fields(bdf='0000:22:00.0'))

        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ0160047A1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='000:21:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ0160041X1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:22:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ016100981P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:23:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ0161008L1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:24:00.0'))

        sn_nvme1 = snw.add_component(name=snw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ016100951P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:21:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ0160046F1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:22:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ0161000L1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:23:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ015301VG1P0FGN',
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

        pf_id = '0000:a1:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '0C:42:A1:EA:C7:60'
        vf_ids = ['0000:a1:00.2', '0000:a1:00.3', '0000:a1:00.4', '0000:a1:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['0C:42:A1:EA:C7:61', '0C:42:A1:EA:C7:62', '0C:42:A1:EA:C7:63', '0C:42:A1:EA:C7:64']
        vf_vlans = [1001, 1002, 1003, 1004]
        # Usually slot 7, second port not connected (Uky in slot 6)
        gpuw_shnic = gpuw.add_component(name=gpuw.name + '-shnic', model='ConnectX-6',
                                        node_id=gpuw.node_id + '-shnic',
                                        switch_fabric_node_id=gpuw.node_id + '-shnic-sf',
                                        # there is one interface and we need one name
                                        interface_node_ids=[mac_to_node_id(pf_mac)],
                                        interface_labels=[f.Labels().set_fields(bdf=vf_ids,
                                                                                mac=vf_macs,
                                                                                vlan=vf_vlans)],
                                        capacities=f.Capacities().set_fields(unit=4),
                                        labels=f.Labels().set_fields(bdf=vf_ids),
                                        ctype=f.ComponentType.SharedNIC,
                                        details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')
        # test that labels propagated to the port
        ilabs = gpuw_shnic.interface_list[0].get_property('labels')
        assert(ilabs.vlan == [1001, 1002, 1003, 1004])
        assert(ilabs.mac == ['0C:42:A1:EA:C7:61', '0C:42:A1:EA:C7:62', '0C:42:A1:EA:C7:63', '0C:42:A1:EA:C7:64'])

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '0C:42:A1:EA:C7:E8'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['0C:42:A1:EA:C7:E9', '0C:42:A1:EA:C7:EA', '0C:42:A1:EA:C7:EB', '0C:42:A1:EA:C7:EC']
        vf_vlans = [1001, 1002, 1003, 1004]
        fnw_shnic = fnw.add_component(name=fnw.name + '-shnic', model='ConnectX-6',
                                      node_id=fnw.node_id + '-shnic',
                                      switch_fabric_node_id=fnw.node_id + '-shnic-sf',
                                      # there is one interface and we need one name
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels().set_fields(bdf=vf_ids,
                                                                              mac=vf_macs,
                                                                              vlan=vf_vlans)],
                                      capacities=f.Capacities().set_fields(unit=4),
                                      labels=f.Labels().set_fields(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '0C:42:A1:78:F8:1C'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['0C:42:A1:78:F8:1D', '0C:42:A1:78:F8:1E', '0C:42:A1:78:F8:1F', '0C:42:A1:78:F8:20']
        vf_vlans = [1001, 1002, 1003, 1004]
        snw_shnic = snw.add_component(name=snw.name + '-shnic', model='ConnectX-6',
                                      node_id=snw.node_id + '-shnic',
                                      switch_fabric_node_id=snw.node_id + '-shnic-sf',
                                      # there is one interface and we need one name
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels().set_fields(bdf=vf_ids,
                                                                              mac=vf_macs,
                                                                              vlan=vf_vlans)],
                                      capacities=f.Capacities().set_fields(unit=4),
                                      labels=f.Labels().set_fields(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        #
        # Dataplane NICs
        # Usually Slot 3 and Slot 6

        fnw_nic1 = fnw.add_component(name=fnw.name + '-nic1', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic1',
                                     switch_fabric_node_id=fnw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:EA:C7:50'),
                                                         mac_to_node_id('0C:42:A1:EA:C7:51')],
                                     interface_labels=[f.Labels().set_fields(mac='0C:42:A1:EA:C7:50',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='0C:42:A1:EA:C7:51',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        ilabs = fnw_nic1.interface_list[0].get_property('labels')
        assert(ilabs.vlan_range == '1-4096')
        assert(ilabs.mac == '0C:42:A1:EA:C7:50' or ilabs.mac == '0C:42:A1:EA:C7:51')
        ilabs = fnw_nic1.interface_list[1].get_property('labels')
        assert (ilabs.vlan_range == '1-4096')
        assert (ilabs.mac == '0C:42:A1:EA:C7:51' or ilabs.mac == '0C:42:A1:EA:C7:50')

        fnw_nic2 = fnw.add_component(name=fnw.name + '-nic2', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic2',
                                     switch_fabric_node_id=fnw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:78:F8:04'),
                                                         mac_to_node_id('0C:42:A1:78:F8:05')],
                                     interface_labels=[f.Labels().set_fields(mac='0C:42:A1:78:F8:04',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='0C:42:A1:78:F8:05',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        snw_nic1 = snw.add_component(name=snw.name + '-nic1', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic1',
                                     switch_fabric_node_id=snw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:F8'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:F9')],
                                     interface_labels=[f.Labels().set_fields(mac='0C:42:A1:BE:8F:F8',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='0C:42:A1:BE:8F:F9',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        snw_nic2 = snw.add_component(name=snw.name + '-nic2', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic2',
                                     switch_fabric_node_id=snw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:BE:8F:DC'),
                                                         mac_to_node_id('0C:42:A1:BE:8F:DD')],
                                     interface_labels=[f.Labels().set_fields(mac='0C:42:A1:BE:8F:DC',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='0C:42:A1:BE:8F:DD',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        # NAS
        nas_model = 'ME4084'
        nas = self.topo.add_node(name='nas', model=nas_model, site=site, ntype=f.NodeType.NAS,
                                 node_id='3DB3R53',
                                 capacities=f.Capacities().set_fields(unit=1, disk=100000))
        # DP switch
        switch_model = 'NCS 55A1-36H'
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

        # FIXME: don't have port MAC addresses yet - placeholders
        sp1 = dp_sf.add_interface(name='HundredGigE 0/0/0/5', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:00'),
                                  capacities=port_caps)

        sp2 = dp_sf.add_interface(name='HundredGigE 0/0/0/13', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:01'),
                                  capacities=port_caps)

        sp3 = dp_sf.add_interface(name='HundredGigE 0/0/0/15', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:02'),
                                  capacities=port_caps)
        sp4 = dp_sf.add_interface(name='HundredGigE 0/0/0/9', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:03'),
                                  capacities=port_caps)
        sp5 = dp_sf.add_interface(name='HundredGigE 0/0/0/17', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:04'),
                                  capacities=port_caps)
        sp6 = dp_sf.add_interface(name='HundredGigE 0/0/0/19', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:05'),
                                  capacities=port_caps)

        sp7 = dp_sf.add_interface(name='HundredGigE 0/0/0/21', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:06'),
                                  capacities=port_caps)

        # FIXME: what to do about breakout ports in slownets?
        sp8 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.1', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:07'),
                                  capacities=port_caps1)
        sp9 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.2', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:08'),
                                  capacities=port_caps1)
        sp10 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.3', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('10:00:00:00:00:09'),
                                   capacities=port_caps1)
        sp11 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.4', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('10:00:00:00:00:0A'),
                                   capacities=port_caps1)

        #
        # Links
        #
        # FIXME: Link node ids need to come from somewhere, could be an extension of interface ID
        # FIXME: on the switch, or something else
        l1 = self.topo.add_link(name='l1', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[gpuw_shnic.interfaces['uky-w1-shnic-p1'], sp1],
                                node_id=sp1.node_id + '-DAC')

        l2 = self.topo.add_link(name='l2', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_shnic.interfaces['uky-w2-shnic-p1'], sp2],
                                node_id=sp2.node_id + '-DAC')

        l3 = self.topo.add_link(name='l3', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic1.interfaces['uky-w2-nic1-p1'], sp3],
                                node_id=sp3.node_id + '-DAC')
        l4 = self.topo.add_link(name='l4', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic1.interfaces['uky-w2-nic1-p2'], sp4],
                                node_id=sp4.node_id + '-DAC')
        l5 = self.topo.add_link(name='l5', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic2.interfaces['uky-w2-nic2-p1'], sp5],
                                node_id=sp5.node_id + '-DAC')
        l6 = self.topo.add_link(name='l6', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic2.interfaces['uky-w2-nic2-p2'], sp6],
                                node_id=sp6.node_id + '-DAC')

        l8 = self.topo.add_link(name='l7', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[snw_shnic.interfaces['uky-w3-shnic-p1'], sp7],
                                node_id=sp7.node_id + '-DAC')

        l9 = self.topo.add_link(name='l8', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[snw_nic1.interfaces['uky-w3-nic1-p1'], sp8],
                                node_id=sp8.node_id + '-DAC')
        l10 = self.topo.add_link(name='l9', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                 interfaces=[snw_nic1.interfaces['uky-w3-nic1-p2'], sp9],
                                 node_id=sp9.node_id + '-DAC')
        l11 = self.topo.add_link(name='l10', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                 interfaces=[snw_nic2.interfaces['uky-w3-nic2-p1'], sp10],
                                 node_id=sp10.node_id + '-DAC')
        l12 = self.topo.add_link(name='l11', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                 interfaces=[snw_nic2.interfaces['uky-w3-nic2-p2'], sp11],
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
        pools = f.Pools(atype=f.DelegationType.LABEL)
        # define two pools - one shared between shared NIC ports and one shared between all dataplane ports
        shared_pool = f.Pool(atype=f.DelegationType.LABEL, pool_id='shared_pool', delegation_id=delegation1,
                             defined_on=switch.interfaces['HundredGigE 0/0/0/5'].node_id,
                             defined_for=[switch.interfaces['HundredGigE 0/0/0/5'].node_id,
                                          switch.interfaces['HundredGigE 0/0/0/13'].node_id,
                                          switch.interfaces['HundredGigE 0/0/0/21'].node_id])
        shared_pool.set_pool_details(f.Labels().set_fields(vlan_range='100-200',
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
        datanic_pool.set_pool_details(f.Labels().set_fields(vlan_range='1500-2000'))
        pools.add_pool(pool=datanic_pool)
        # have to reindex pools by delegation
        pools.build_index_by_delegation_id()
        pools.validate_pools()

        self.topo.single_delegation(delegation_id=delegation1, label_pools=pools,
                                    capacity_pools=f.Pools(atype=f.DelegationType.CAPACITY))

        _, node_props = self.topo.graph_model.get_node_properties(node_id=switch.interfaces['HundredGigE 0/0/0/25.2'].node_id)
        self.assertEqual(node_props[ABCPropertyGraph.PROP_LABEL_DELEGATIONS], '{"primary": {"pool": "datanic_pool"}}')
        _, node_props = self.topo.graph_model.get_node_properties(node_id=switch.interfaces['HundredGigE 0/0/0/5'].node_id)
        self.assertEqual(node_props[ABCPropertyGraph.PROP_LABEL_DELEGATIONS], '{"primary": {"pool_id": "shared_pool", '
                                                                              '"labels": {"ipv4_range": '
                                                                              '"192.168.1.1-192.168.10.255", '
                                                                              '"vlan_range": "100-200"}}}')
        self.topo.serialize(file_name='UKY-ad.graphml')
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

    def testLBNLSiteAd(self):
        # create a site advertisement
        site = 'LBNL'
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

        gpuw = self.topo.add_node(name='lbnl-w1',
                                  model=worker_model, site=site,
                                  node_id='5B3BR53',
                                  ntype=f.NodeType.Server, capacities=gpu_worker_cap)
        fnw = self.topo.add_node(name='lbnl-w2',
                                 model=worker_model, site=site,
                                 node_id='5B38R53',
                                 ntype=f.NodeType.Server, capacities=network_worker_cap)
        snw = self.topo.add_node(name='lbnl-w3',
                                 model=worker_model, site=site,
                                 node_id='5B39R53',
                                 ntype=f.NodeType.Server, capacities=network_worker_cap)

        #
        # Disks
        #

        gpu_nvme1 = gpuw.add_component(name=gpuw.name + '-nvme1', model='P4510',
                                       node_id='PHLJ015301XE1P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                       labels=f.Labels().set_fields(bdf='0000:21:00.0'))
        gpu_nvme2 = gpuw.add_component(name=gpuw.name + '-nvme2', model='P4510',
                                       node_id='PHLJ015301K31P0FGN',
                                       ctype=f.ComponentType.NVME,
                                       capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                       labels=f.Labels().set_fields(bdf='0000:22:00.0'))

        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301LQ1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='000:21:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ015301LE1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:22:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ015301M31P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:23:00.0'))
        fn_nvme1 = fnw.add_component(name=fnw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ015301LS1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:24:00.0'))

        sn_nvme1 = snw.add_component(name=snw.name + '-nvme1', model='P4510',
                                     node_id='PHLJ015301KV1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:21:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme2', model='P4510',
                                     node_id='PHLJ015301RL1P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:22:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme3', model='P4510',
                                     node_id='PHLJ015301L91P0FGN',
                                     ctype=f.ComponentType.NVME,
                                     capacities=f.Capacities().set_fields(unit=1, disk=1000),
                                     labels=f.Labels().set_fields(bdf='0000:23:00.0'))
        sn_nvme1 = snw.add_component(name=snw.name + '-nvme4', model='P4510',
                                     node_id='PHLJ015301SK1P0FGN',
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

        # Usually slot 7, second port not connected (Slot 6)
        pf_id = '0000:a1:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:19:8C'
        vf_ids = ['0000:a1:00.2', '0000:a1:00.3', '0000:a1:00.4', '0000:a1:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:19:8D', '04:3F:72:B7:19:8E', '04:3F:72:B7:19:8F', '04:3F:72:B7:19:8A']
        vf_vlans = [1001, 1002, 1003, 1004]
        gpuw_shnic = gpuw.add_component(name=gpuw.name + '-shnic', model='ConnectX-6',
                                        node_id=gpuw.node_id + '-shnic',
                                        switch_fabric_node_id=gpuw.node_id + '-shnic-sf',
                                        # there is one interface and we need one name
                                        interface_node_ids=[mac_to_node_id(pf_mac)],
                                        interface_labels=[f.Labels().set_fields(bdf=vf_ids,
                                                                                mac=vf_macs,
                                                                                vlan=vf_vlans)],
                                        capacities=f.Capacities().set_fields(unit=4),
                                        labels=f.Labels().set_fields(bdf=vf_ids),
                                        ctype=f.ComponentType.SharedNIC,
                                        details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:15:8C'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:15:8D', '04:3F:72:B7:15:8E', '04:3F:72:B7:15:8F', '04:3F:72:B7:15:8A']
        vf_vlans = [1001, 1002, 1003, 1004]
        fnw_shnic = fnw.add_component(name=fnw.name + '-shnic', model='ConnectX-6',
                                      node_id=fnw.node_id + '-shnic',
                                      switch_fabric_node_id=fnw.node_id + '-shnic-sf',
                                      # there is one interface and we need one name
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels().set_fields(bdf=vf_ids,
                                                                              mac=vf_macs,
                                                                              vlan=vf_vlans)],
                                      capacities=f.Capacities().set_fields(unit=4),
                                      labels=f.Labels().set_fields(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        pf_id = '0000:e2:00.0' # we don't seem to need it, but I'd collect it anyway
        pf_mac = '04:3F:72:B7:15:7C'
        vf_ids = ['0000:e2:00.2', '0000:e2:00.3', '0000:e2:00.4', '0000:e2:00.5']
        # i don't know how VF macs are allocated, this is made-up /ib
        vf_macs = ['04:3F:72:B7:15:7D', '04:3F:72:B7:15:7E', '04:3F:72:B7:15:7F', '04:3F:72:B7:15:7A']
        vf_vlans = [1001, 1002, 1003, 1004]
        snw_shnic = snw.add_component(name=snw.name + '-shnic', model='ConnectX-6',
                                      node_id=snw.node_id + '-shnic',
                                      switch_fabric_node_id=snw.node_id + '-shnic-sf',
                                      # there is one interface and we need one name
                                      interface_node_ids=[mac_to_node_id(pf_mac)],
                                      interface_labels=[f.Labels().set_fields(bdf=vf_ids,
                                                                              mac=vf_macs,
                                                                              vlan=vf_vlans)],
                                      capacities=f.Capacities().set_fields(unit=4),
                                      labels=f.Labels().set_fields(bdf=vf_ids),
                                      ctype=f.ComponentType.SharedNIC,
                                      details='Shared NIC: Mellanox Technologies MT28908 Family [ConnectX-6]')

        #
        # Dataplane NICs
        # Usually Slot 3 and Slot 6

        fnw_nic1 = fnw.add_component(name=fnw.name + '-nic1', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic1',
                                     switch_fabric_node_id=fnw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('04:3F:72:B7:15:6C'),
                                                         mac_to_node_id('04:3F:72:B7:15:6D')],
                                     interface_labels=[f.Labels().set_fields(mac='04:3F:72:B7:15:6C',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='04:3F:72:B7:15:6D',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        fnw_nic2 = fnw.add_component(name=fnw.name + '-nic2', model='ConnectX-6',
                                     node_id=fnw.node_id + '-nic2',
                                     switch_fabric_node_id=fnw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('04:3F:72:B7:18:AC'),
                                                         mac_to_node_id('04:3F:72:B7:18:AD')],
                                     interface_labels=[f.Labels().set_fields(mac='04:3F:72:B7:18:AC',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='04:3F:72:B7:18:AD',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT28908 Family [ConnectX-6]')

        snw_nic1 = snw.add_component(name=snw.name + '-nic1', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic1',
                                     switch_fabric_node_id=snw.node_id + '-nic1-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:91:75:12'),
                                                         mac_to_node_id('0C:42:A1:91:75:13')],
                                     interface_labels=[f.Labels().set_fields(mac='0C:42:A1:91:75:12',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='0C:42:A1:91:75:13',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:41:00.0', '0000:41:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        snw_nic2 = snw.add_component(name=snw.name + '-nic2', model='ConnectX-5',
                                     node_id=snw.node_id + '-nic2',
                                     switch_fabric_node_id=snw.node_id + '-nic2-sf',
                                     interface_node_ids=[mac_to_node_id('0C:42:A1:91:75:0E'),
                                                         mac_to_node_id('0C:42:A1:91:75:0F')],
                                     interface_labels=[f.Labels().set_fields(mac='0C:42:A1:91:75:0E',
                                                                             vlan_range='1-4096'),
                                                       f.Labels().set_fields(mac='0C:42:A1:91:75:0F',
                                                                             vlan_range='1-4096')
                                                       ],
                                     ctype=f.ComponentType.SmartNIC,
                                     capacities=f.Capacities().set_fields(unit=1),
                                     labels=f.Labels().set_fields(bdf=['0000:a1:00.0', '0000:a1:00.1']),
                                     details='Mellanox Technologies MT27800 Family [ConnectX-5]')

        # NAS
        nas_model = 'ME4084'
        nas = self.topo.add_node(name='nas', model=nas_model, site=site, ntype=f.NodeType.NAS,
                                 node_id='3DB2R53',
                                 capacities=f.Capacities().set_fields(unit=1, disk=100000))
        # DP switch
        switch_model = 'NCS 55A1-36H'
        switch = self.topo.add_node(name=site + '-data-sw', model=switch_model, site=site,
                                    node_id='FOC2450R1AR',
                                    capacities=f.Capacities().set_fields(unit=1),
                                    ntype=f.NodeType.Switch)
        dp_sf = switch.add_switch_fabric(name=switch.name+'-sf', layer=f.Layer.L2,
                                         node_id=switch.node_id + '-sf')
        # add ports
        port_caps = f.Capacities()
        port_caps1 = f.Capacities()
        port_caps.set_fields(bw=100)
        port_caps1.set_fields(bw=25)

        # FIXME: don't have port MAC addresses yet - placeholders
        sp1 = dp_sf.add_interface(name='HundredGigE 0/0/0/5', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:00'),
                                  capacities=port_caps)

        sp2 = dp_sf.add_interface(name='HundredGigE 0/0/0/13', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:01'),
                                  capacities=port_caps)

        sp3 = dp_sf.add_interface(name='HundredGigE 0/0/0/15', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:02'),
                                  capacities=port_caps)
        sp4 = dp_sf.add_interface(name='HundredGigE 0/0/0/9', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:03'),
                                  capacities=port_caps)
        sp5 = dp_sf.add_interface(name='HundredGigE 0/0/0/17', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:04'),
                                  capacities=port_caps)
        sp6 = dp_sf.add_interface(name='HundredGigE 0/0/0/19', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:05'),
                                  capacities=port_caps)

        sp7 = dp_sf.add_interface(name='HundredGigE 0/0/0/21', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:06'),
                                  capacities=port_caps)

        # FIXME: what to do about breakout ports in slownets?
        sp8 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.1', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:07'),
                                  capacities=port_caps1)
        sp9 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.2', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:08'),
                                  capacities=port_caps1)
        sp10 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.3', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('20:00:00:00:00:09'),
                                   capacities=port_caps1)
        sp11 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.4', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('20:00:00:00:00:0A'),
                                   capacities=port_caps1)

        #
        # Links
        #
        # FIXME: Link node ids need to come from somewhere, could be an extension of interface ID
        # FIXME: on the switch, or something else
        l1 = self.topo.add_link(name='l1', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[gpuw_shnic.interfaces['lbnl-w1-shnic-p1'], sp1],
                                node_id=sp1.node_id + '-DAC')

        l2 = self.topo.add_link(name='l2', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_shnic.interfaces['lbnl-w2-shnic-p1'], sp2],
                                node_id=sp2.node_id + '-DAC')

        l3 = self.topo.add_link(name='l3', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic1.interfaces['lbnl-w2-nic1-p1'], sp3],
                                node_id=sp3.node_id + '-DAC')
        l4 = self.topo.add_link(name='l4', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic1.interfaces['lbnl-w2-nic1-p2'], sp4],
                                node_id=sp4.node_id + '-DAC')
        l5 = self.topo.add_link(name='l5', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic2.interfaces['lbnl-w2-nic2-p1'], sp5],
                                node_id=sp5.node_id + '-DAC')
        l6 = self.topo.add_link(name='l6', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[fnw_nic2.interfaces['lbnl-w2-nic2-p2'], sp6],
                                node_id=sp6.node_id + '-DAC')

        l8 = self.topo.add_link(name='l7', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[snw_shnic.interfaces['lbnl-w3-shnic-p1'], sp7],
                                node_id=sp7.node_id + '-DAC')

        l9 = self.topo.add_link(name='l8', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[snw_nic1.interfaces['lbnl-w3-nic1-p1'], sp8],
                                node_id=sp8.node_id + '-DAC')
        l10 = self.topo.add_link(name='l9', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                 interfaces=[snw_nic1.interfaces['lbnl-w3-nic1-p2'], sp9],
                                 node_id=sp9.node_id + '-DAC')
        l11 = self.topo.add_link(name='l10', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                 interfaces=[snw_nic2.interfaces['lbnl-w3-nic2-p1'], sp10],
                                 node_id=sp10.node_id + '-DAC')
        l12 = self.topo.add_link(name='l11', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                 interfaces=[snw_nic2.interfaces['lbnl-w3-nic2-p2'], sp11],
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
        pools = f.Pools(atype=f.DelegationType.LABEL)
        # define two pools - one shared between shared NIC ports and one shared between all dataplane ports
        shared_pool = f.Pool(atype=f.DelegationType.LABEL, pool_id='shared_pool', delegation_id=delegation1,
                             defined_on=switch.interfaces['HundredGigE 0/0/0/5'].node_id,
                             defined_for=[switch.interfaces['HundredGigE 0/0/0/5'].node_id,
                                          switch.interfaces['HundredGigE 0/0/0/13'].node_id,
                                          switch.interfaces['HundredGigE 0/0/0/21'].node_id])
        shared_pool.set_pool_details(f.Labels().set_fields(vlan_range='100-200',
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
        datanic_pool.set_pool_details(f.Labels().set_fields(vlan_range='1500-2000'))
        pools.add_pool(pool=datanic_pool)
        # have to reindex pools by delegation
        pools.build_index_by_delegation_id()
        pools.validate_pools()

        self.topo.single_delegation(delegation_id=delegation1, label_pools=pools,
                                    capacity_pools=f.Pools(atype=f.DelegationType.CAPACITY))

        _, node_props = self.topo.graph_model.get_node_properties(node_id=switch.interfaces['HundredGigE 0/0/0/25.2'].node_id)
        self.assertEqual(node_props[ABCPropertyGraph.PROP_LABEL_DELEGATIONS], '{"primary": {"pool": "datanic_pool"}}')
        _, node_props = self.topo.graph_model.get_node_properties(node_id=switch.interfaces['HundredGigE 0/0/0/5'].node_id)
        self.assertEqual(node_props[ABCPropertyGraph.PROP_LABEL_DELEGATIONS], '{"primary": {"pool_id": "shared_pool", '
                                                                              '"labels": '
                                                                              '{"ipv4_range": '
                                                                              '"192.168.1.1-192.168.10.255", '
                                                                              '"vlan_range": "100-200"}}}')
        self.topo.serialize(file_name='LBNL-ad.graphml')
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

    def testNetworkAd(self):

        site = 'RENC'

        # DP switch
        switch_model = 'NCS 55A1-36H'
        switch = self.topo.add_node(name=site + '-data-sw', model=switch_model, site=site,
                                    node_id='FOC2450R1BL',
                                    capacities=f.Capacities().set_fields(unit=1),
                                    ntype=f.NodeType.Switch, stitch_node=True)
        dp_sf = switch.add_switch_fabric(name=switch.name+'-sf', layer=f.Layer.L2,
                                         node_id=switch.node_id + '-sf', stitch_node=True)
        # add ports
        port_caps = f.Capacities()
        port_caps1 = f.Capacities()
        port_caps.set_fields(bw=100)
        port_caps1.set_fields(bw=25)
        # labels should be part of pool delegations, generally not defined on substrate ports
        # as native labels
        #port_labs = f.Labels()
        #port_labs.set_fields(vlan_range='1000-2000')
        # FIXME: don't have port MAC addresses yet - placeholders
        sp1 = dp_sf.add_interface(name='HundredGigE 0/0/0/5', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:00'),
                                  capacities=port_caps, stitch_node=True)

        sp2 = dp_sf.add_interface(name='HundredGigE 0/0/0/13', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:01'),
                                  capacities=port_caps, stitch_node=True)

        sp3 = dp_sf.add_interface(name='HundredGigE 0/0/0/15', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:02'),
                                  capacities=port_caps, stitch_node=True)
        sp4 = dp_sf.add_interface(name='HundredGigE 0/0/0/9', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:03'),
                                  capacities=port_caps, stitch_node=True)
        sp5 = dp_sf.add_interface(name='HundredGigE 0/0/0/17', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:04'),
                                  capacities=port_caps, stitch_node=True)
        sp6 = dp_sf.add_interface(name='HundredGigE 0/0/0/19', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:05'),
                                  capacities=port_caps, stitch_node=True)

        sp7 = dp_sf.add_interface(name='HundredGigE 0/0/0/21', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:06'),
                                  capacities=port_caps, stitch_node=True)

        # FIXME: what to do about breakout ports in slownets?
        sp8 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.1', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:07'),
                                  capacities=port_caps1, stitch_node=True)
        sp9 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.2', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('00:00:00:00:00:08'),
                                  capacities=port_caps1, stitch_node=True)
        sp10 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.3', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('00:00:00:00:00:09'),
                                   capacities=port_caps1, stitch_node=True)
        sp11 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.4', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('00:00:00:00:00:0A'),
                                   capacities=port_caps1, stitch_node=True)

        # FIXME: fake ports towards UKY and LBNL
        renc_uky = dp_sf.add_interface(name='HundredGigE 0/0/0/26', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('00:00:00:00:00:10'),
                                   capacities=port_caps)

        renc_lbnl = dp_sf.add_interface(name='HundredGigE 0/0/0/27', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('00:00:00:00:00:11'),
                                   capacities=port_caps)

        site = 'UKY'
        # DP switch
        switch_model = 'NCS 55A1-36H'
        switch = self.topo.add_node(name=site + '-data-sw', model=switch_model, site=site,
                                    node_id='FOC2451R0XZ',
                                    capacities=f.Capacities().set_fields(unit=1),
                                    ntype=f.NodeType.Switch, stitch_node=True)
        dp_sf = switch.add_switch_fabric(name=switch.name+'-sf', layer=f.Layer.L2,
                                         node_id=switch.node_id + '-sf',
                                         stitch_node=True)
        # add ports
        port_caps = f.Capacities()
        port_caps1 = f.Capacities()
        port_caps.set_fields(bw=100)
        port_caps1.set_fields(bw=25)
        # labels should be part of pool delegations, generally not defined on substrate ports
        # as native labels
        #port_labs = f.Labels()
        #port_labs.set_fields(vlan_range='1000-2000')
        # FIXME: don't have port MAC addresses yet - placeholders
        sp1 = dp_sf.add_interface(name='HundredGigE 0/0/0/5', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:00'),
                                  capacities=port_caps, stitch_node=True)

        sp2 = dp_sf.add_interface(name='HundredGigE 0/0/0/13', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:01'),
                                  capacities=port_caps, stitch_node=True)

        sp3 = dp_sf.add_interface(name='HundredGigE 0/0/0/15', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:02'),
                                  capacities=port_caps, stitch_node=True)
        sp4 = dp_sf.add_interface(name='HundredGigE 0/0/0/9', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:03'),
                                  capacities=port_caps, stitch_node=True)
        sp5 = dp_sf.add_interface(name='HundredGigE 0/0/0/17', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:04'),
                                  capacities=port_caps, stitch_node=True)
        sp6 = dp_sf.add_interface(name='HundredGigE 0/0/0/19', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:05'),
                                  capacities=port_caps, stitch_node=True)

        sp7 = dp_sf.add_interface(name='HundredGigE 0/0/0/21', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:06'),
                                  capacities=port_caps, stitch_node=True)

        # FIXME: what to do about breakout ports in slownets?
        sp8 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.1', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:07'),
                                  capacities=port_caps1, stitch_node=True)
        sp9 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.2', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('10:00:00:00:00:08'),
                                  capacities=port_caps1, stitch_node=True)
        sp10 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.3', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('10:00:00:00:00:09'),
                                   capacities=port_caps1, stitch_node=True)
        sp11 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.4', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('10:00:00:00:00:0A'),
                                   capacities=port_caps1, stitch_node=True)

        # FIXME: fake ports towards RENC and LBNL
        uky_renc = dp_sf.add_interface(name='HundredGigE 0/0/0/26', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('10:00:00:00:00:10'),
                                   capacities=port_caps)

        uky_lbnl = dp_sf.add_interface(name='HundredGigE 0/0/0/27', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('10:00:00:00:00:11'),
                                   capacities=port_caps)

        site = 'LBNL'

        # DP switch
        switch_model = 'NCS 55A1-36H'
        switch = self.topo.add_node(name=site + '-data-sw', model=switch_model, site=site,
                                    node_id='FOC2450R1AR',
                                    capacities=f.Capacities().set_fields(unit=1),
                                    ntype=f.NodeType.Switch, stitch_node=True)
        dp_sf = switch.add_switch_fabric(name=switch.name+'-sf', layer=f.Layer.L2,
                                         node_id=switch.node_id + '-sf', stitch_node=True)
        # add ports
        port_caps = f.Capacities()
        port_caps1 = f.Capacities()
        port_caps.set_fields(bw=100)
        port_caps1.set_fields(bw=25)
        # labels should be part of pool delegations, generally not defined on substrate ports
        # as native labels
        #port_labs = f.Labels()
        #port_labs.set_fields(vlan_range='1000-2000')
        # FIXME: don't have port MAC addresses yet - placeholders
        sp1 = dp_sf.add_interface(name='HundredGigE 0/0/0/5', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:00'),
                                  capacities=port_caps, stitch_node=True)

        sp2 = dp_sf.add_interface(name='HundredGigE 0/0/0/13', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:01'),
                                  capacities=port_caps, stitch_node=True)

        sp3 = dp_sf.add_interface(name='HundredGigE 0/0/0/15', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:02'),
                                  capacities=port_caps, stitch_node=True)
        sp4 = dp_sf.add_interface(name='HundredGigE 0/0/0/9', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:03'),
                                  capacities=port_caps, stitch_node=True)
        sp5 = dp_sf.add_interface(name='HundredGigE 0/0/0/17', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:04'),
                                  capacities=port_caps, stitch_node=True)
        sp6 = dp_sf.add_interface(name='HundredGigE 0/0/0/19', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:05'),
                                  capacities=port_caps, stitch_node=True)

        sp7 = dp_sf.add_interface(name='HundredGigE 0/0/0/21', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:06'),
                                  capacities=port_caps, stitch_node=True)

        # FIXME: what to do about breakout ports in slownets?
        sp8 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.1', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:07'),
                                  capacities=port_caps1, stitch_node=True)
        sp9 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.2', itype=f.InterfaceType.TrunkPort,
                                  node_id=mac_to_node_id('20:00:00:00:00:08'),
                                  capacities=port_caps1, stitch_node=True)
        sp10 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.3', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('20:00:00:00:00:09'),
                                   capacities=port_caps1, stitch_node=True)
        sp11 = dp_sf.add_interface(name='HundredGigE 0/0/0/25.4', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('20:00:00:00:00:0A'),
                                   capacities=port_caps1, stitch_node=True)

        # FIXME: fake ports towards UKY and RENC
        lbnl_renc = dp_sf.add_interface(name='HundredGigE 0/0/0/26', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('20:00:00:00:00:10'),
                                   capacities=port_caps)

        lbnl_uky = dp_sf.add_interface(name='HundredGigE 0/0/0/27', itype=f.InterfaceType.TrunkPort,
                                   node_id=mac_to_node_id('20:00:00:00:00:11'),
                                   capacities=port_caps)

        # add 3 links
        l1 = self.topo.add_link(name='l1', ltype=f.LinkType.L2Path, layer=f.Layer.L2,
                                interfaces=[renc_uky, uky_renc],
                                node_id=renc_uky.node_id + '-Wave')

        l2 = self.topo.add_link(name='l2', ltype=f.LinkType.L2Path, layer=f.Layer.L2,
                                interfaces=[uky_lbnl, lbnl_uky],
                                node_id=uky_lbnl.node_id + '-Wave')

        l3 = self.topo.add_link(name='l3', ltype=f.LinkType.L2Path, layer=f.Layer.L2,
                                interfaces=[renc_lbnl, lbnl_renc],
                                node_id=renc_lbnl.node_id + '-Wave')

        delegation1 = 'primary'
        self.topo.single_delegation(delegation_id=delegation1,
                                    label_pools=f.Pools(atype=f.DelegationType.LABEL),
                                    capacity_pools=f.Pools(atype=f.DelegationType.CAPACITY))

        self.topo.serialize(file_name='Network-ad.graphml')
