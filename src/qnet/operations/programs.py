"""Quantum programs: gate sequences executed *on* a QuantumProcessor.

Same circuits as qnet.physics.bell, but run by the hardware: each instruction
takes the time declared in hardware.memory, and the processor is busy meanwhile.
"""

from netsquid.components import instructions as instr
from netsquid.components.qprogram import QuantumProgram


class BellMeasurementProgram(QuantumProgram):
    """CNOT, H, then measure both qubits (destructively). Outputs "m1", "m2".

    Outcome meaning is identical to qnet.physics.bell: m2 = parity bit (X correction),
    m1 = phase bit (Z correction).
    """
    default_num_qubits = 2

    def program(self):
        q_left, q_right = self.get_qubit_indices(2)
        self.apply(instr.INSTR_CNOT, [q_left, q_right])
        self.apply(instr.INSTR_H, q_left)
        self.apply(instr.INSTR_MEASURE, q_left, output_key="m1", discard=True)
        self.apply(instr.INSTR_MEASURE, q_right, output_key="m2", discard=True)
        yield self.run()


class PauliCorrectionProgram(QuantumProgram):
    """Apply X^m2 then Z^m1 to one qubit."""
    default_num_qubits = 1

    def __init__(self, m1, m2):
        super().__init__()
        self.m1, self.m2 = m1, m2

    def program(self):
        (q,) = self.get_qubit_indices(1)
        if self.m2:
            self.apply(instr.INSTR_X, q)
        if self.m1:
            self.apply(instr.INSTR_Z, q)
        yield self.run()
