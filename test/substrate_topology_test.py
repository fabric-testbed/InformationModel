import unittest

import fim.user as f


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
        hn = self.topo.add_node(name='headnode', model=head_model, site=site,
                                node_id='702C4409-6635-4051-91A0-9C5A45CA28EC',
                                ntype=f.NodeType.Server, capacities=hn_cap)
        gpu_worker = self.topo.add_node(name='gpuworker', model=worker_model, site=site,
                                        node_id='8CA64353-182D-4CF2-8A07-2ADFF7F9C42A',
                                        ntype=f.NodeType.Server, capacities=gpu_worker_cap)
        fastnet_worker = self.topo.add_node(name='fastnetworker', model=worker_model, site=site,
                                            node_id='B87900A2-5225-432A-92F8-60DD961597BE',
                                            ntype=f.NodeType.Server, capacities=network_worker_cap)
        slownet_worker = self.topo.add_node(name='slownetworker', model=worker_model, site=site,
                                            node_id='169A2327-D6BC-4B9D-AE3A-3396CFF57138',
                                            ntype=f.NodeType.Server, capacities=network_worker_cap)

        nvme1 = gpu_worker.add_component(name='nvme1', model='P4510',
                                         node_id='55E8A23A-EAB9-41BF-BE9F-F42BB5920046',
                                         ctype=f.ComponentType.NVME,
                                         capacities=f.Capacities().set_fields(disk=1000),
                                         labels=f.Labels().set_fields(bdf='00:00:01'))
        nvme2 = gpu_worker.add_component(name='nvme2', model='P4510',
                                         node_id='7BD64A0E-DBE0-4BA1-89B0-CE9D8E6959B0',
                                         ctype=f.ComponentType.NVME,
                                         capacities=f.Capacities().set_fields(disk=1000),
                                         labels=f.Labels().set_fields(bdf='00:00:02'))

        gpu1 = gpu_worker.add_component(name='gpu1', model='RTX6000',
                                        node_id='49B5D670-64BD-4E90-8915-73CDACAB0EB5',
                                        ctype=f.ComponentType.GPU,
                                        labels=f.Labels().set_fields(bdf='00:01:0f'))
        gpu2 = gpu_worker.add_component(name='gpu2', model='RTX6000',
                                        node_id='EEC1F433-F102-4E68-A6DD-C20059C71B76',
                                        ctype=f.ComponentType.GPU,
                                        labels=f.Labels().set_fields(bdf='00:02:0f'))
        nic0 = gpu_worker.add_component(name='nic0', model='ConnectX-6',
                                        node_id='B6D4ED83-03C0-4B37-90AD-966769952F66',
                                        switch_fabric_node_id='4E3B7A5E-5DC0-4D65-94B1-06B2E9519B08',
                                        interface_node_ids=['0FD7CD42-00F9-45A1-9813-2E39AEF25243'],
                                        labels=f.Labels().set_fields(bdf='00:03:0f'),
                                        ctype=f.ComponentType.SharedNIC,
                                        details='Shared NIC')
        nic1 = fastnet_worker.add_component(name='nic1', model='ConnectX-6',
                                            node_id='E84F69AB-D9BB-4F6E-99CF-CC08BF26B50E',
                                            switch_fabric_node_id='A5624045-C315-4FE5-A719-98E7891E7DBE',
                                            interface_node_ids=['752D4D79-B91B-4657-B744-6EDBE331D539'],
                                            ctype=f.ComponentType.SharedNIC,
                                            labels=f.Labels().set_fields(bdf='00:01:0f'),
                                            details='Dedicated SmartNIC')
        nic2 = fastnet_worker.add_component(name='nic2', model='ConnectX-6',
                                            node_id='631210E4-2064-4102-A6DB-1E6E33A7DA8A',
                                            switch_fabric_node_id='2ED64BEB-DCB1-4E80-87EF-E46960A7444D',
                                            interface_node_ids=['AEBC1418-37B8-438E-B752-E8C1304E7C33',
                                                                'B6615811-6DDC-43CC-B012-A46E8A1A21E6'],
                                            ctype=f.ComponentType.SmartNIC,
                                            labels=f.Labels().set_fields(bdf='00:02:0f'),
                                            details='Dedicated SmartNIC')
        nic3 = fastnet_worker.add_component(name='nic3', model='ConnectX-6',
                                            node_id='86F4EE34-6FD3-4CF5-A3BB-A2BA03884833',
                                            switch_fabric_node_id='49766FAD-9813-4E0B-B254-75012AF3ABE2',
                                            interface_node_ids=['E36A4783-D526-46E6-9833-5145C9D684CF',
                                                                'E3BBD95E-CA6D-400C-A3BF-4FE1A196F50D'],
                                            ctype=f.ComponentType.SmartNIC,
                                            labels=f.Labels().set_fields(bdf='00:03:0f'),
                                            details='Dedicated SmartNIC')
        nic4 = slownet_worker.add_component(name='nic4', model='ConnectX-6',
                                            node_id='40372F80-3517-4C5A-82A7-14782A513001',
                                            switch_fabric_node_id='64921F73-3719-4323-8B29-0A59329FA1E3',
                                            interface_node_ids=['0DD43A8F-B84F-44C0-87AC-878D9C30CA16'],
                                            ctype=f.ComponentType.SharedNIC,
                                            labels=f.Labels().set_fields(bdf='00:04:0f'),
                                            details='Shared NIC')
        nic5 = slownet_worker.add_component(name='nic5', model='ConnectX-5',
                                            node_id='054D0FF8-7D1F-403E-8900-87FDC6AF644A',
                                            switch_fabric_node_id='72F4189E-507A-4B01-B39E-D0080EBCF9FC',
                                            interface_node_ids=['5A104AFD-2C84-4E30-9BCE-59149531C310',
                                                                '8E0722EB-AD3E-4858-BD2E-2607C6F52405'],
                                            ctype=f.ComponentType.SmartNIC,
                                            labels=f.Labels().set_fields(bdf='00:05:0f'),
                                            details='Dedicated SmartNIC')
        nic6 = slownet_worker.add_component(name='nic6', model='ConnectX-5',
                                            node_id='D3AC3C42-8D0B-47C0-8420-D6D16A59DF10',
                                            switch_fabric_node_id='23FB9D1D-4026-4C52-A32A-8ED73FBCC6AD',
                                            interface_node_ids=['D1EEB715-69A3-4CC3-A90C-2F497B1358AD',
                                                                '900D122A-080D-4D29-9186-24AF4D53361B'],
                                            ctype=f.ComponentType.SmartNIC,
                                            labels=f.Labels().set_fields(bdf='00:06:0f'),
                                            details='Dedicated SmartNIC')
        # NAS
        nas_model = 'ME4084'
        nas = self.topo.add_node(name='nas', model=nas_model, site=site, ntype=f.NodeType.NAS,
                                 node_id='D6787DF8-D2AE-4C3C-B8DE-577CE69C4AEC',
                                 capacities=f.Capacities().set_fields(disk=100000))
        # DP switch
        switch_model = 'NCS500-24'
        switch = self.topo.add_node(name='dp_switch', model=switch_model, site=site,
                                    node_id='8D1D8073-71D5-4B71-86CD-1A8D5272926F',
                                    ntype=f.NodeType.Switch)
        dp_sf = switch.add_switch_fabric(name='sp_sf', layer=f.Layer.L2,
                                         node_id='DBA3C158-45B8-4DB0-B023-DAA52CE589FD')
        # add ports
        port_caps = f.Capacities()
        port_caps.set_fields(bw=100)
        port_labs = f.Labels()
        port_labs.set_fields(vlan_range='1000-2000')
        dp_sf.add_interface(name='p1', itype=f.InterfaceType.TrunkPort,
                            node_id='62FCEC64-9C21-489F-96A9-0A74702CFB6F',
                            capacities=port_caps, labels=port_labs)
        dp_sf.add_interface(name='p2', itype=f.InterfaceType.TrunkPort,
                            node_id='A8174EA2-BBD0-4C8B-ABC1-8615FC30C8E6',
                            capacities=port_caps, labels=port_labs)
        dp_sf.add_interface(name='p3', itype=f.InterfaceType.TrunkPort,
                            node_id='4B594B5F-2FA1-41FA-BF9E-7AB0EC970514',
                            capacities=port_caps, labels=port_labs)
        dp_sf.add_interface(name='p4', itype=f.InterfaceType.TrunkPort,
                            node_id='1A2DFA26-1F21-41E9-A97D-ABFB65BE5AF2',
                            capacities=port_caps, labels=port_labs)
        dp_sf.add_interface(name='p5', itype=f.InterfaceType.TrunkPort,
                            node_id='130FA579-BC0B-43BB-99AE-B7619955475B',
                            capacities=port_caps, labels=port_labs)
        dp_sf.add_interface(name='p6', itype=f.InterfaceType.TrunkPort,
                            node_id='9F906AA1-BC4A-40F3-8AE2-FCE8D00C54C0',
                            capacities=port_caps, labels=port_labs)
        dp_sf.add_interface(name='p7', itype=f.InterfaceType.TrunkPort,
                            node_id='0EDE076D-1979-4C85-B580-7A7563D7B71F',
                            capacities=port_caps, labels=port_labs)
        dp_sf.add_interface(name='p8', itype=f.InterfaceType.TrunkPort,
                            node_id='A286EAE5-3CEA-4D8F-BB1A-685957334917',
                            capacities=port_caps, labels=port_labs)
        dp_sf.add_interface(name='p9', itype=f.InterfaceType.TrunkPort,
                            node_id='0D2B98C0-80A1-47BB-B656-EDF4815E635C',
                            capacities=port_caps, labels=port_labs)
        dp_sf.add_interface(name='p10', itype=f.InterfaceType.TrunkPort,
                            node_id='71B46263-7723-45BC-A9EA-2AD090DC39AA',
                            capacities=port_caps, labels=port_labs)

        # add links
        l1 = self.topo.add_link(name='l1', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[nic0.interfaces['nic0_p1'], switch.interfaces['p1']],
                                node_id='D17E4DB8-73AE-442A-A645-41EB8419E485')
        l2 = self.topo.add_link(name='l2', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[nic1.interfaces['nic1_p1'], switch.interfaces['p2']],
                                node_id='3A1C21B5-6B18-466B-87D2-D5FEA0E54404')
        l3 = self.topo.add_link(name='l3', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[nic2.interfaces['nic2_p1'], switch.interfaces['p3']],
                                node_id='27746574-2AC9-40E8-926D-DB27FFE17BDF')
        l4 = self.topo.add_link(name='l4', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[nic2.interfaces['nic2_p2'], switch.interfaces['p4']],
                                node_id='DC647092-5E8F-4A63-BC10-D3D24F8F5C40')
        l5 = self.topo.add_link(name='l5', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[nic3.interfaces['nic3_p1'], switch.interfaces['p5']],
                                node_id='4981B23C-063B-4335-BF7A-D597CE549757')
        l6 = self.topo.add_link(name='l6', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[nic3.interfaces['nic3_p2'], switch.interfaces['p6']],
                                node_id='D9BE7849-15A1-4BE6-ACCE-B29A9608B0A4')
        l8 = self.topo.add_link(name='l7', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[nic4.interfaces['nic4_p1'], switch.interfaces['p7']],
                                node_id='4EEF35D3-D549-457B-9C3E-9359B6194482')
        l9 = self.topo.add_link(name='l8', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                interfaces=[nic5.interfaces['nic5_p1'], switch.interfaces['p8']],
                                node_id='AE47D890-72DF-413F-83C5-710E78CDAE22')
        # shows different ways of addressing interfaces
        l10 = self.topo.add_link(name='l9', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                 interfaces=[self.topo.nodes['slownetworker'].interfaces['nic5_p2'],
                                             switch.interfaces['p9']],
                                 node_id='7F3B02EB-ED52-442C-888A-FEF54BE8E296')
        l11 = self.topo.add_link(name='l10', ltype=f.LinkType.DAC, layer=f.Layer.L2,
                                 interfaces=[self.topo.interfaces['nic6_p1'], switch.interfaces['p10']],
                                 node_id='4E767FC3-9428-46B1-8143-B52B74889261')




