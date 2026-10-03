"""Protocols for entanglement swapping on a running network.

A NetSquid Protocol is a piece of node behaviour written as a generator: each
`yield self.await_...(...)` pauses it until that event happens in simulated time,
so the code reads top-to-bottom like the physical sequence of events.

    Repeater (SwapProtocol)                     Bob (CorrectionProtocol)
    wait until both slots receive a qubit       wait for own qubit AND the message
    run BellMeasurementProgram  (takes time)          |
    send (m1, m2) on classical fibre  -------------->  (arrives L km * 5 us later)
                                                run PauliCorrectionProgram
                                                -> A-B pair ready
"""

import netsquid as ns
from netsquid.components.component import Message
from netsquid.protocols import NodeProtocol, Signals

from qnet.operations.programs import BellMeasurementProgram, PauliCorrectionProgram


class SwapProtocol(NodeProtocol):
    """At a repeater: swap the qubits in two slots and send the outcome to one node."""

    def __init__(self, node, left_position, right_position, outcome_port):
        super().__init__(node, name=f"swap@{node.name}")
        self.left_position = left_position
        self.right_position = right_position
        self.outcome_port = outcome_port
        self.outcome = None
        self.qubits_ready_at = None
        self.outcome_sent_at = None

    def run(self):
        qmem = self.node.qmemory
        yield (self.await_port_input(qmem.ports[f"qin{self.left_position}"])
               & self.await_port_input(qmem.ports[f"qin{self.right_position}"]))
        self.qubits_ready_at = ns.sim_time()

        program = BellMeasurementProgram()
        qmem.execute_program(program, qubit_mapping=[self.left_position, self.right_position])
        yield self.await_program(qmem)
        self.outcome = (program.output["m1"][0], program.output["m2"][0])

        self.node.ports[self.outcome_port].tx_output(Message(list(self.outcome)))
        self.outcome_sent_at = ns.sim_time()
        self.send_signal(Signals.SUCCESS, self.outcome)


class CorrectionProtocol(NodeProtocol):
    """At an end node: wait for its qubit and the swap outcome, then apply the Pauli fix."""

    def __init__(self, node, position, outcome_port):
        super().__init__(node, name=f"correct@{node.name}")
        self.position = position
        self.outcome_port = outcome_port
        self.outcome_received_at = None
        self.completed_at = None

    def run(self):
        qmem = self.node.qmemory
        port = self.node.ports[self.outcome_port]
        yield (self.await_port_input(qmem.ports[f"qin{self.position}"])
               & self.await_port_input(port))
        self.outcome_received_at = ns.sim_time()
        m1, m2 = port.rx_input().items

        qmem.execute_program(PauliCorrectionProgram(m1, m2), qubit_mapping=[self.position])
        yield self.await_program(qmem)
        self.completed_at = ns.sim_time()
        self.send_signal(Signals.SUCCESS)
