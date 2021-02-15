import fim.user.topology as topo
import fim.user.node as node
import fim.user.component as comp
import fim.slivers.network_node as nnode
import fim.slivers.attached_components as atcomp
import fim.slivers.component_catalog as cata
import fim.slivers.interface_info as iinfo
import fim.slivers.capacities_labels as caplab

# push some definitions up to simplify import management

ExperimentTopology = topo.ExperimentTopology
SubstrateTopology = topo.SubstrateTopology
Node = node.Node
Component = comp.Component
NodeType = nnode.NodeType
ComponentType = atcomp.ComponentType
ComponentCatalog = cata.ComponentCatalog
InterfaceType = iinfo.InterfaceType
Capacities = caplab.Capacities
Labels = caplab.Labels
