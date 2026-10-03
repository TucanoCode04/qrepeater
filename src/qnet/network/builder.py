"""Build a NetSquid Network for a linear chain described by a ChainConfig.

Conventions (used by every protocol, so they live in one place):
  - end nodes have 1 memory slot (position 0);
  - repeaters have 2 slots: position 0 holds the qubit of the link to the LEFT
    neighbour, position 1 the qubit of the link to the RIGHT neighbour;
  - node ports are named "q_<neighbour>" (quantum) and "c_<neighbour>" (classical).
"""

from netsquid.nodes import Network, Node

from qnet.hardware.links import MidpointSourceLink, make_classical_connection
from qnet.hardware.memory import make_quantum_processor


def quantum_port(neighbour):
    return f"q_{neighbour}"


def classical_port(neighbour):
    return f"c_{neighbour}"


class ChainNetwork:
    """A NetSquid Network plus the bookkeeping to find nodes, links and slots."""

    def __init__(self, config):
        self.config = config
        self.names = list(config.node_names)
        self.network = Network("chain")
        self.nodes = {}
        self.links = []  # links[i] connects names[i] and names[i+1]

        for i, name in enumerate(self.names):
            num_positions = 1 if self.is_end_node(name) else 2
            node = Node(name, qmemory=make_quantum_processor(f"{name}_qmem", num_positions,
                                                             config.gates))
            self.nodes[name] = node
        self.network.add_nodes(list(self.nodes.values()))

        for i, link_config in enumerate(config.links):
            left, right = self.names[i], self.names[i + 1]
            self._connect(left, right, link_config)

    def is_end_node(self, name):
        return name in (self.names[0], self.names[-1])

    def node(self, name):
        return self.nodes[name]

    def position(self, node_name, neighbour):
        """Memory slot of `node_name` that stores its half of the link to `neighbour`."""
        if self.is_end_node(node_name):
            return 0
        return 0 if self.names.index(neighbour) < self.names.index(node_name) else 1

    def link(self, node1, node2):
        i, j = sorted((self.names.index(node1), self.names.index(node2)))
        if j != i + 1:
            raise ValueError(f"{node1} and {node2} are not neighbours")
        return self.links[i]

    def _connect(self, left, right, link_config):
        n_left, n_right = self.nodes[left], self.nodes[right]

        link = MidpointSourceLink(f"qlink_{left}-{right}", link_config.length_km,
                                  link_config.fidelity)
        self.network.add_connection(n_left, n_right, connection=link, label="quantum",
                                    port_name_node1=quantum_port(right),
                                    port_name_node2=quantum_port(left))
        self.links.append(link)
        # A qubit arriving on the node's quantum port goes straight into its memory slot.
        n_left.ports[quantum_port(right)].forward_input(
            n_left.qmemory.ports[f"qin{self.position(left, right)}"])
        n_right.ports[quantum_port(left)].forward_input(
            n_right.qmemory.ports[f"qin{self.position(right, left)}"])

        cconn = make_classical_connection(f"clink_{left}-{right}", link_config.length_km)
        self.network.add_connection(n_left, n_right, connection=cconn, label="classical",
                                    port_name_node1=classical_port(right),
                                    port_name_node2=classical_port(left))
