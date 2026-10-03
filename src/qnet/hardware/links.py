"""Elementary links: connections that distribute Bell pairs between neighbours.

Phase 1 model ("midpoint source"):

    node A  <-- fibre L/2 --  [ source ]  -- fibre L/2 -->  node B

On trigger, the source emits two qubits in a Werner state; each travels through
its own QuantumChannel (delay = 5 us/km) and leaves the connection on port A or B.
No loss yet: every trigger delivers a pair. Phase 2 replaces this class with a
probabilistic, lossy, heralded link exposing the same interface (`trigger()`).
"""

from netsquid.components import ClassicalChannel, QSource, QuantumChannel
from netsquid.components.models import FibreDelayModel
from netsquid.components.qsource import SourceStatus
from netsquid.nodes import Connection, DirectConnection
from netsquid.qubits.dmtools import DenseDMRepr
from netsquid.qubits.state_sampler import StateSampler

from qnet.physics.states import werner_dm


class MidpointSourceLink(Connection):
    """Quantum connection with a Werner-pair source in the middle."""

    def __init__(self, name, length_km, fidelity):
        super().__init__(name)
        self.length_km = length_km
        self.fidelity = fidelity
        sampler = StateSampler([DenseDMRepr(werner_dm(fidelity))], [1.0])
        source = QSource(f"{name}_source", sampler, num_ports=2,
                         status=SourceStatus.EXTERNAL)  # emits only when triggered
        self.add_subcomponent(source, name="source")
        for source_port, side in (("qout0", "A"), ("qout1", "B")):
            channel = QuantumChannel(f"{name}_fibre_{side}", length=length_km / 2,
                                     models={"delay_model": FibreDelayModel()})
            self.add_subcomponent(channel, name=f"fibre_{side}")
            source.ports[source_port].connect(channel.ports["send"])
            channel.ports["recv"].forward_output(self.ports[side])

    def trigger(self):
        """Ask the source to emit one pair now."""
        self.subcomponents["source"].trigger()


def make_classical_connection(name, length_km):
    """Two-way classical fibre: messages arrive after length_km * 5 us."""
    def fibre(direction):
        return ClassicalChannel(f"{name}_{direction}", length=length_km,
                                models={"delay_model": FibreDelayModel()})
    return DirectConnection(name, channel_AtoB=fibre("AtoB"), channel_BtoA=fibre("BtoA"))
