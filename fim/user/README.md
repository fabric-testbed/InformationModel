# Experiment abstractions

## Overview

This package implements experimenter-facing abstractions for building and manipulating slices and underlying property
graph models.  It also supports building substrate advertisements and broker query models (BQMs) using slightly 
modified models.

To buils a slice model, start with
```
t = ExperimentTopology()
```

To build a substrate model, start with
```
t = SubstrateTopology()
```

To build a broker query model, start with
```
t = AdvertizedTopology()
```

And then use the abstractions shown below, to define and query a topology. SubstrateTopology elements
require more parameters to be specified in order to be valid (persistent, hardware-based
identifiers, MAC addresses etc). AdvertizedTopology elements are there largely for querying and do not
allow any meaningful manipulation.

## Installation

```bash
$ pip install fabric-fim 
```

## Example scripts

Some example scripts that *should* run.

### Simple script

```python
import fim.user as fu

t = fu.ExperimentTopology()
n1 = t.add_node(name='n1', site='RENC')
t.add_node(name='n2', site='RENC')
cap = fu.Capacities().__set_fields(ram=1000, core=8)
n1.set_property('capacities', cap)
nic1 = t.nodes['n1'].add_component(ctype=fu.ComponentType.SharedNIC, model='ConnectX-6', name='nic1')
nic2 = t.nodes['n2'].add_component(ctype=fu.ComponentType.SmartNIC, model='ConnectX-6', name='nic2')
cap = fu.Capacities()
cap.__set_fields(bw=50, unit=1)
lab = fu.Labels()
lab.__set_fields(ipv4="192.168.1.12")
nic1.set_properties(capacities=cap, labels=lab)
nic1.get_property('capacities')
nic1.unset_property('labels')
t.add_network_service(name='s1', interfaces=t.interface_list, ltype=fu.ServiceType.L2Bridge)
t.draw()
t.serialize('test_slice.graphml')
print(t)
```

For setting instance sizes vs. capacities two things should be possible: (a) set capacity_hints in request to the 
desired instance size and have the orchestrator fill in the allocated_capacities field and (b) set capacities field
in request and have the orchestrator fill in capacity_hints and allocated_capacities field accordingly. 

(a):
```
t = fu.ExperimentTopology()
n1 = t.add_node(name='n1', site='RENC')
caphint = fu.CapacityHints().set_fields(instance_type='fabric.c4.m16.d10')
n1.set_properties(capacity_hints=caphint)
... some time later after slice is provisioned
t.nodes['n1'].get_property('allocated_capacities') # will return Capacities object core=4, ram=16, disk=10
```
On orchestrator side you would then:
```
from fim.slivers.instance_catalog import InstanceCatalog
from fim.slivers.capacities_labels import Capacities
caphint=topo.nodes['n1'].get_property('capacity_hints')
cata = InstanceCatalog()
caps = cata.get_instance_capacities(instance_type=caphint.instance_type)
topo.nodes['n1'].set_properties(capacities=caps, allocated_capacities=caps)
# use caphint.instance_type when you get to AM
```
or (b):
```
t = fu.ExperimentTopology()
n1 = t.add_node(name='n1', site='RENC')
cap = Capacities().set_fields(core=3, ram=10, disk=10)
n1.set_properties(capacities=cap)
... some time later after slice is provisioned
t.nodes['n1'].get_property('allocated_capacities') # will return Capacities object core=4, ram=16, disk=10
t.nodes['n1'].get_property('capacity_hints') # will return CapacityHints object with instance_type='fabric.c4.m16.d10'
```

On orchestrator side instance size catalog can be used as follows:
```
from fim.slivers.instance_catalog import InstanceCatalog
from fim.slivers.capacities_labels import Capacities
cap = topo.nodes['n1'].get_property('capacities')
cata = InstanceCatalog()
it = cata.map_capacities_to_instance(cap=cap)
c_cap = cata.get_instance_capacities(instance_type=it)
caphints = CapacityHints().set_fields(instance_type=it)
topo.nodes['n1'].set_properties(capacity_hints=caphints, allocated_capacities=c_cap)
```

Parsing on orchestrator side inside the control framework
```python
import fim.graph.slices.networkx_asm as nx_asm

gi = nx_asm.NetworkXGraphImporter()
g = gi.import_graph_from_file_direct(graph_file='test_slice.graphml')
asm = nx_asm.NetworkxASM(graph_id=g.graph_id, importer=g.importer, logger=g.importer.log)
for nn_id in asm.get_all_network_nodes():
    sliver = asm.build_deep_node_sliver(node_id=nn_id)
    print(sliver)
```

## Pseudocode scripts

The following scripts show the general idea of how FIM is to be used but the implementation may
be different in package paths, function names and parameters. Use only for planning/design purposes.

### Create topology

```python
import time
from fabric_cf.orchestrator import OrchestratorProxy

from fim.experiment.topology import ExperimentTopology
from fim.experiment.node import Node
from fim.experiment.component import Component
from fim.experiment.link import Link

t = ExperimentTopology('MyTopology')

# defaults to type VM
node = t.add_node(name='Node1', site='RENC')

# two ways to add components. 
# 'node' is of type Node
# c1 and c2 are of type Component
c1 = node.add_component(Component.GPU, 'RTX6000', 'gpu1')
c2 = t.nodes['Node1'].add_component(Component.SmartNIC, 'ConnectX6', 'nic1')

node2 = t.add_node(name='Node2', site='UKY')
c3 = node2.add_component(Component.GPU, 'RTX6000', 'gpu2')

# add shared dataplane interface
c4 = node.add_component(Component.SharedNIC, 'ConnectX6', 'snic1')
# declare port to be access on it
i1 = node.components['snic1']._interfaces[0]
i1.set_mode(InterfaceMode.ACCESS)

# get the second port of the SmartNIC
i2 = c2._interfaces[1]
i2.set_mode(InterfaceMode.TRUNK)
# create a child interface on the trunk
i3 = i2.add_child_interface()

# create a 10Gbps link. add_link always takes a list of interfaces
l1 = t.add_link(interfaces=[i1, i3], bandwidth='10Gbps')

node.add_component(Component.GPU, 'RTX6000', 'gpu3')
# removal can be done by name
node.remove_component('gpu3')
```
### Visualize topology
```python
# use matplotlib.pylot to draw the derived node topology
# (or save to file with appropriate parameters) 
t.draw()
# draws something like node1 --10Gbps-- node2 
# can also have an option to draw 'component details', then it draws
# node1 -- nic1 --10Gbps-- node2 
```
### Query or update model without interacting with orchestrator

```python
node = t.nodes['Node1']
components = node.components()
print('Node1 components')
for c in components:
    print(c.type, c.model)

node.add_component(Component.FPGA, 'Alveo U280', 'fpga1')

all_interfaces = t._interfaces
node1_interfaces = node._interfaces
node2_interfaces = t.nodes['Node2']._interfaces

nodes = t.nodes  # list all nodes
links = t.links  # list all links as tuples of interface names (probably concatenations
# of node_name.interface_name.child_interface or node_name.component_name.interface_name)
node1_node2_link = t.links([node1_interfaces[1], node2_interfaces[0]])
```
### Save as GraphML
```python
graphml_string = t.serialize_to_string()

# or 

t.serialize_to_file('filename')
```

### Submit and modify slice

```python
# credential handling
# 
from fabric_cm.credmgr.credmgr_proxy import CredmgrProxy

credmgr_proxy = CredmgrProxy(credmgr_host)
tokens = credmgr_proxy.refresh_token(project_name=’p1’,
scope =’cf’,
refresh_token =’value’)

id_token = tokens.get(‘id_token’)

# instantiate orchestrator proxy (parameters undefined for now)
orchestrator = OrchestratorProxy(orchestrator_host)

# there are multiple options here - you can continue from previous script
# or you can do one of several things

# 1. you can rerun all the commands above creating object 't'
# 2. you can load t from a serialized description
t = ExperimentTopology('MyTopology', from_file='filename')

# create slice
status = orchestrator.create(id_token, t, 'MyExperimentX')

# create slice
status = orchestrator.create(t, 'MyExperimentX')

if status != OrchestratorProxy.Status.OK:
    raise BigStinkException("Orchestrator failed")

# check status
while orchestrator.status('MyExperimentX') == OrchestratorProxy.Status.Waiting:
    time.sleep(10)
    print('Still waiting')

slice = orchestrator.query('MyExperimentX')

new_topology = slice.topology

new_topology.nodes  # list nodes
new_topology.nodes['Node1']  # list properties of the node in concise form

node3 = new_topology.add_node('Node3', site='RENC')
nic2 = node3.add_component(Component.SmartNIC, 'Connectx6', 'nic1')

# connect port of nic1 of node3 to port of nic1 of node1
# by default ports are in access mode
# add another child to Node1's trunk port on nic1
i2 = new_topology.nodes['Node1'].components['nic1']._interfaces[1]
i4 = i2.add_child_interface()
new_topology.add_link(node3.components['nic1']._interfaces[0], i4)

status = orchestrator.modify(slice)

# etc etc.
```
### Other operations 
POA, delete, renew