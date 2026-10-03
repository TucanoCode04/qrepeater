"""Configuration of the simulated network: topology, links and hardware timings.

Everything the simulation needs to know about the *hardware* lives here, so that
experiments can change distances, link quality or gate speeds without touching
the simulation code.
"""

from dataclasses import dataclass, field

# Light in optical fibre travels at ~2/3 c = 200 000 km/s, i.e. 5 us per km.
FIBRE_SPEED_KM_PER_S = 200_000
NS_PER_KM = 1e9 / FIBRE_SPEED_KM_PER_S


@dataclass(frozen=True)
class LinkConfig:
    """An elementary link between two neighbouring nodes.

    The entangled-pair source sits at the midpoint, so each photon travels
    length_km / 2 to reach its node.
    """
    length_km: float
    fidelity: float = 1.0


@dataclass(frozen=True)
class GateDurations:
    """How long the quantum processor takes per operation [ns]."""
    single_qubit_ns: float = 50.0
    two_qubit_ns: float = 500.0
    measure_ns: float = 1000.0


@dataclass(frozen=True)
class ChainConfig:
    """A linear chain: node_names[i] -- links[i] -- node_names[i+1].

    The first and last nodes are end nodes (1 memory slot each), every node in
    between is a repeater (2 slots: one per neighbour).
    """
    node_names: tuple
    links: tuple
    gates: GateDurations = field(default_factory=GateDurations)

    def __post_init__(self):
        if len(self.node_names) < 2:
            raise ValueError("A chain needs at least two nodes")
        if len(self.links) != len(self.node_names) - 1:
            raise ValueError(f"{len(self.node_names)} nodes need {len(self.node_names) - 1} links, "
                             f"got {len(self.links)}")

    @classmethod
    def alice_repeater_bob(cls, length_km=10.0, fidelity=1.0, gates=None):
        """Phase 1 topology: two identical links."""
        link = LinkConfig(length_km, fidelity)
        return cls(("Alice", "Repeater", "Bob"), (link, link), gates or GateDurations())
