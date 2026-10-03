"""Quantum memories: NetSquid QuantumProcessors with a fixed set of operations.

A QuantumProcessor is a memory with numbered slots ("positions") that can also
run gates. Every gate it supports must be declared as a PhysicalInstruction,
which gives that gate a duration (and, from Phase 3 on, a noise model).
"""

from netsquid.components import QuantumProcessor, PhysicalInstruction
from netsquid.components import instructions as instr


def make_quantum_processor(name, num_positions, gates):
    """Memory with `num_positions` slots supporting X, Z, H, CNOT and measurement.

    Instructions are executed one after the other (parallel=False), so a
    program's duration is the sum of its instruction durations.
    """
    phys_instructions = [
        PhysicalInstruction(instr.INSTR_X, duration=gates.single_qubit_ns),
        PhysicalInstruction(instr.INSTR_Z, duration=gates.single_qubit_ns),
        PhysicalInstruction(instr.INSTR_H, duration=gates.single_qubit_ns),
        PhysicalInstruction(instr.INSTR_CNOT, duration=gates.two_qubit_ns),
        PhysicalInstruction(instr.INSTR_MEASURE, duration=gates.measure_ns),
    ]
    return QuantumProcessor(name, num_positions=num_positions,
                            phys_instructions=phys_instructions)
