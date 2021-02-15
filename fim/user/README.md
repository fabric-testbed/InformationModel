# Experiment abstractions

This package implements experimenter-facing abstractions for building and manipulating slices.


## Example scripts

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
i1 = node.components['snic1'].interfaces[0]
i1.set_mode(InterfaceMode.ACCESS)

# get the second port of the SmartNIC
i2 = c2.interfaces[1]
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

all_interfaces = t.interfaces
node1_interfaces = node.interfaces
node2_interfaces = t.nodes['Node2'].interfaces

nodes = t.nodes # list all nodes
links = t.links # list all links as tuples of interface names (probably concatenations
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
            scope=’cf’, 
            refresh_token=’value’)

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

new_topology.nodes # list nodes
new_topology.nodes['Node1'] # list properties of the node in concise form

node3 = new_topology.add_node('Node3', site='RENC')
nic2 = node3.add_component(Component.SmartNIC, 'Connectx6', 'nic1')

# connect port of nic1 of node3 to port of nic1 of node1
# by default ports are in access mode
# add another child to Node1's trunk port on nic1
i2 = new_topology.nodes['Node1'].components['nic1'].interfaces[1]
i4 = i2.add_child_interface()
new_topology.add_link(node3.components['nic1'].interfaces[0], i4)

status = orchestrator.modify(slice)

# etc etc.
```
### Other operations 
POA, delete, renew