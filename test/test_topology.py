from fim.user.topology import ExperimentTopology
from fim.user.node import Node

if __name__ == "__main__":

    t = ExperimentTopology()
    n1 = t.add_node(name='node1', site='RENC', cpu_cores=1, image_ref="https://some.image")
    print(n1)

